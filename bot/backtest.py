"""Data download, cost-accurate tick backtester, experiment log and gates.

Commands (run `python backtest.py <command> -h` for options):
  fetch        pull ticks + M1 bars + symbol spec from MT5 (Windows) and print the data report
  import-csv   load ticks from a CSV (MT5 "Export ticks" format or time,bid,ask)
  info         print the data report for data already on disk
  dev          run one improvement round on TRAIN and VALIDATION and log every variant
  select       rank logged candidates on validation (with deflated Sharpe)
  walkforward  walk-forward a finalist inside the development period
  run-all      round 1 for all three strategies, then select, plateau and walk-forward
  final        touch the FINAL TEST split once for one candidate and apply the go-live gates

The final-test split (most recent 25% of trading days) is never read by
dev/select/walkforward/run-all. `final` records every access in
results/final_test_log.json and refuses a second look unless told otherwise.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import config as C
from config import Config, SymbolSpec, load_config
from risk import RiskManager, lot_size
from strategy import (DAY_MS, MINUTE_MS, STRATEGIES, Bars, Signal, TradeFilters,
                      apply_min_stop, build_bars, fmt_utc, generate, grid_combos,
                      local_minutes, neighbors, server_to_utc_ms, strategy_params,
                      trail_stop_level)

MAX_ROUNDS = 5
MAX_COMBOS_PER_STRATEGY = 20
MIN_VAL_TRADES_FOR_SELECTION = 100
FINAL_MIN_TRADES = 300
FINAL_MIN_PF = 1.3


# ==========================================================================
# Data
# ==========================================================================
def tick_file(symbol: str) -> Path:
    return C.DATA_DIR / f"{symbol}_ticks.npz"


def m1_file(symbol: str) -> Path:
    return C.DATA_DIR / f"{symbol}_m1.npz"


def spec_file(symbol: str) -> Path:
    return C.DATA_DIR / f"{symbol}_spec.json"


def load_spec(symbol: str) -> SymbolSpec:
    p = spec_file(symbol)
    if p.exists():
        return SymbolSpec.from_json(p.read_text(encoding="utf-8"))
    print(f"WARNING: {p.name} not found; using built-in defaults for {symbol}. "
          "Run `backtest.py fetch` on the MT5 machine to get the real contract spec.")
    return SymbolSpec.from_defaults(symbol)


def m1_to_pseudo_ticks(m1: dict, point: float):
    """Four ticks per M1 bar (open, adverse-first extremes, close) with the bar spread.

    Bullish bars go O-L-H-C, bearish O-H-L-C. Lower fidelity than real ticks;
    the report labels results from this source.
    """
    o, h, l, c = m1["o"], m1["h"], m1["l"], m1["c"]
    bull = c >= o
    p1 = np.where(bull, l, h)
    p2 = np.where(bull, h, l)
    t = np.repeat(m1["t"], 4) + np.tile(np.array([0, 15_000, 30_000, 45_000], dtype="int64"), len(o))
    bid = np.column_stack([o, p1, p2, c]).ravel()
    spr = np.repeat(np.maximum(m1["spread_points"], 0) * point, 4)
    return t.astype("int64"), bid.astype(float), (bid + spr).astype(float)


@dataclass
class Market:
    symbol: str
    source: str
    spec: SymbolSpec
    t: np.ndarray
    bid: np.ndarray
    ask: np.ndarray
    bars: Bars
    bar_day: np.ndarray     # server day key of every bar


def load_market(cfg: Config, source: str = "ticks") -> Market:
    sym = cfg.symbol
    spec = load_spec(sym)
    if source == "ticks":
        p = tick_file(sym)
        if not p.exists():
            raise SystemExit(f"No tick data at {p}. Run `python backtest.py fetch --symbol {sym}` "
                             "on the Windows/MT5 machine, or `import-csv`.")
        z = np.load(p)
        t, bid, ask = z["t"].astype("int64"), z["bid"].astype(float), z["ask"].astype(float)
    elif source == "m1":
        p = m1_file(sym)
        if not p.exists():
            raise SystemExit(f"No M1 data at {p}. Run `python backtest.py fetch` first.")
        z = np.load(p)
        t, bid, ask = m1_to_pseudo_ticks({k: z[k] for k in z.files}, spec.point)
    else:
        raise SystemExit(f"unknown source {source}")
    order = np.argsort(t, kind="stable")
    t, bid, ask = t[order], bid[order], ask[order]
    if cfg.costs.extra_spread_price:
        ask = ask + cfg.costs.extra_spread_price
    bars = build_bars(t, bid, ask, cfg.filters.spread_median_bars)
    _, bar_day = local_minutes(bars.t, cfg.server_tz)
    return Market(sym, source, spec, t, bid, ask, bars, bar_day)


@dataclass
class Splits:
    days: np.ndarray        # unique server days, sorted
    train: tuple[int, int]  # [start_ms, end_ms)
    validation: tuple[int, int]
    final: tuple[int, int]
    n_days: dict

    @property
    def dev(self) -> tuple[int, int]:
        return self.train[0], self.validation[1]


def make_splits(mkt: Market, cfg: Config) -> Splits:
    days = np.unique(mkt.bar_day)
    n = len(days)
    if n < 8:
        raise SystemExit(f"Only {n} trading days of data: far too short to split.")
    i_val = int(round(n * cfg.splits.train))
    i_fin = int(round(n * (cfg.splits.train + cfg.splits.validation)))
    first_bar = {int(d): int(mkt.bars.t[np.searchsorted(mkt.bar_day, d)]) for d in days[[0, i_val, i_fin]]}
    end = int(mkt.t[-1]) + 1
    s_train, s_val, s_fin = first_bar[int(days[0])], first_bar[int(days[i_val])], first_bar[int(days[i_fin])]
    return Splits(days, (s_train, s_val), (s_val, s_fin), (s_fin, end),
                  {"train": i_val, "validation": i_fin - i_val, "final": n - i_fin})


def days_in(mkt: Market, start_ms: int, end_ms: int) -> int:
    m = (mkt.bars.t >= start_ms) & (mkt.bars.t < end_ms)
    return int(len(np.unique(mkt.bar_day[m])))


def data_report(mkt: Market, cfg: Config, m1: dict | None = None) -> str:
    lines = [f"Symbol {mkt.symbol} (broker name {mkt.spec.name}), source={mkt.source}, "
             f"spec from {mkt.spec.source}"]
    t = mkt.t
    tick_days = pd.Series(1, index=mkt.bar_day).groupby(level=0).size()
    per_day = pd.Series(mkt.bars.n, index=mkt.bar_day).groupby(level=0).sum()
    lines.append(f"{'Ticks' if mkt.source == 'ticks' else 'Pseudo-ticks'}: {len(t):,} from "
                 f"{fmt_utc(int(t[0]))} to {fmt_utc(int(t[-1]))} UTC")
    lines.append(f"M1 bars built: {len(mkt.bars):,}   trading days: {len(tick_days)}   "
                 f"median ticks/day: {int(per_day.median()):,}   days < 1,000 ticks: "
                 f"{int((per_day < 1000).sum())}")
    gaps = np.diff(t)
    big = np.argsort(gaps)[::-1][:50]
    odd = []
    for j in big:
        g = gaps[j] / 3_600_000
        start = datetime.fromtimestamp(t[j] / 1000, tz=timezone.utc)
        if g < 4:
            break
        weekend = start.weekday() >= 4 and g < 60
        if not weekend:
            odd.append(f"{fmt_utc(int(t[j]))} +{g:.1f}h")
    lines.append("Gaps > 4h outside weekends: " + (", ".join(odd[:8]) if odd else "none"))
    if m1 is not None and len(m1["t"]):
        lines.append(f"MT5 M1 rates: {len(m1['t']):,} bars from {fmt_utc(int(m1['t'][0]))} "
                     f"to {fmt_utc(int(m1['t'][-1]))} UTC")
    sp = make_splits(mkt, cfg)
    for name in ("train", "validation", "final"):
        a, b = getattr(sp, name)
        lines.append(f"  {name:<10} {fmt_utc(a)[:10]} -> {fmt_utc(b - 1)[:10]}  "
                     f"{sp.n_days[name]} trading days")
    nf = sp.n_days["final"]
    lines.append(f"300-trade gate: the final split has {nf} trading days, so a strategy must "
                 f"average >= {FINAL_MIN_TRADES / max(nf, 1):.2f} trades/day to reach 300 trades.")
    spreads = (mkt.ask - mkt.bid) / mkt.spec.point
    lines.append(f"Spread (points): median {np.median(spreads):.1f}, p90 {np.percentile(spreads, 90):.1f}")
    return "\n".join(lines)


# ==========================================================================
# Simulation
# ==========================================================================
@dataclass
class Trade:
    strategy: str
    note: str
    side: int
    signal_ms: int
    entry_ms: int
    entry_px: float
    exit_ms: int
    exit_px: float
    exit_reason: str
    lots: float
    pnl: float              # account currency, after commission
    pnl_points: float       # net price move in points (commission excluded)
    cost_points: float      # spread + slippage + commission, in points
    r_multiple: float       # pnl / amount risked
    latency_ms: int


def simulate(mkt: Market, signals: list[Signal], cfg: Config, filters: TradeFilters,
             start_ms: int, end_ms: int, slip_mult: float = 1.0,
             equity0: float | None = None) -> tuple[list[Trade], Counter]:
    spec = mkt.spec
    t, bid, ask = mkt.t, mkt.bid, mkt.ask
    slip = cfg.slippage() * slip_mult
    comm = cfg.commission()
    vpu = spec.value_per_price_unit
    lat = cfg.costs.latency_ms
    equity = cfg.starting_equity if equity0 is None else equity0
    risk = RiskManager(cfg.risk, equity, cfg.server_tz)
    open_trades: list[tuple[int, float]] = []
    trades: list[Trade] = []
    skips: Counter = Counter()
    last = len(t) - 1

    def settle(until_ms: int):
        nonlocal equity, open_trades
        keep = []
        for ex_ms, pnl in sorted(open_trades):
            if ex_ms <= until_ms:
                equity += pnl
                risk.on_close(ex_ms, pnl, equity)
            else:
                keep.append((ex_ms, pnl))
        open_trades = keep

    for s in signals:
        if s.time_ms < start_ms or s.time_ms >= end_ms:
            continue
        settle(s.time_ms)
        dec = int(mkt.bars.last_tick[s.bar_idx])
        reason = filters.check(s.time_ms, float(ask[dec] - bid[dec]), float(mkt.bars.spread_ref[s.bar_idx]))
        if reason:
            skips[reason.split(":")[0]] += 1
            continue
        reason = risk.can_open(s.time_ms, equity, len(open_trades))
        if reason:
            skips[reason.split(":")[0]] += 1
            continue
        e = int(np.searchsorted(t, s.time_ms + lat, side="left"))
        if e > last or t[e] - s.time_ms > 120_000 or t[e] >= end_ms:
            skips["no_ticks_after_signal"] += 1
            continue
        side = s.side
        spread_e = float(ask[e] - bid[e])
        entry = float(ask[e] + slip) if side > 0 else float(bid[e] - slip)
        sl_d, tp_d = apply_min_stop(s.sl_dist, s.tp_dist, spec.stops_level, spec.point, spread_e)
        lots = lot_size(equity, cfg.risk.risk_per_trade_pct, sl_d, spec, comm)
        if lots <= 0:
            skips["below_min_volume"] += 1
            continue
        sl, tp = entry - side * sl_d, entry + side * tp_d
        deadline = int(t[e]) + s.hold_min * MINUTE_MS
        d = min(int(np.searchsorted(t, deadline, side="left")), last)
        px = bid[e:d] if side > 0 else ask[e:d]
        stop = np.full(len(px), sl)
        if s.trail_activate_r > 0 and len(px) > 1:
            best = np.maximum.accumulate(px) if side > 0 else np.minimum.accumulate(px)
            best_prev = np.r_[entry, best[:-1]]        # stop is set from ticks already seen
            stop = trail_stop_level(best_prev, entry, sl, sl_d, side, s.trail_activate_r,
                                    s.trail_lock, s.trail_step_r)
        if side > 0:
            sl_hit, tp_hit = px <= stop, px > tp        # TP needs a trade-through
        else:
            sl_hit, tp_hit = px >= stop, px < tp
        i_sl = int(np.argmax(sl_hit)) if sl_hit.any() else None
        i_tp = int(np.argmax(tp_hit)) if tp_hit.any() else None
        if i_sl is not None and (i_tp is None or i_sl <= i_tp):
            k = e + i_sl
            lvl = float(stop[i_sl])
            exit_px = min(lvl, float(bid[k])) - slip if side > 0 else max(lvl, float(ask[k])) + slip
            why, exit_slip = ("trail" if lvl != sl else "sl"), slip
        elif i_tp is not None:
            k = e + i_tp
            exit_px, why, exit_slip = tp, "tp", 0.0
        else:
            k = d
            exit_px = float(bid[k]) - slip if side > 0 else float(ask[k]) + slip
            why = "time" if t[k] >= deadline else "end_of_data"
            exit_slip = slip
        move = (exit_px - entry) * side
        pnl = move * lots * vpu - 2.0 * comm * lots
        risk_amt = sl_d * lots * vpu + 2.0 * comm * lots
        cost_px = spread_e + slip + exit_slip + 2.0 * comm / vpu
        trades.append(Trade(s.strategy, s.note, side, s.time_ms, int(t[e]), entry, int(t[k]),
                            float(exit_px), why, lots, float(pnl), move / spec.point,
                            cost_px / spec.point, float(pnl / risk_amt), int(t[e] - s.time_ms)))
        risk.on_open(s.time_ms, equity)
        open_trades.append((int(t[k]), float(pnl)))
    settle(2**62)
    return trades, skips


# ==========================================================================
# Metrics
# ==========================================================================
METRIC_KEYS = ["trades", "win_rate", "pf", "sharpe", "max_dd_pct", "expectancy_pts",
               "expectancy_R", "avg_win_pts", "avg_loss_pts", "breakeven_wr", "avg_cost_pts",
               "net_return_pct", "sr_trade", "skew", "kurt"]


def metrics(trades: list[Trade], equity0: float, n_days: int, server_tz: str) -> dict:
    out = {k: float("nan") for k in METRIC_KEYS}
    out["trades"] = len(trades)
    if not trades:
        return out
    tr = sorted(trades, key=lambda x: x.exit_ms)
    pnl = np.array([x.pnl for x in tr])
    pts = np.array([x.pnl_points for x in tr])
    r = np.array([x.r_multiple for x in tr])
    wins = pnl > 0
    gp, gl = pnl[wins].sum(), -pnl[~wins].sum()
    out["pf"] = float(gp / gl) if gl > 0 else float("inf")
    out["win_rate"] = float(wins.mean())
    out["avg_win_pts"] = float(pts[wins].mean()) if wins.any() else 0.0
    out["avg_loss_pts"] = float(-pts[~wins].mean()) if (~wins).any() else 0.0
    denom = out["avg_win_pts"] + out["avg_loss_pts"]
    out["breakeven_wr"] = float(out["avg_loss_pts"] / denom) if denom > 0 else float("nan")
    out["expectancy_pts"] = float(pts.mean())
    out["expectancy_R"] = float(r.mean())
    out["avg_cost_pts"] = float(np.mean([x.cost_points for x in tr]))
    eq = equity0 + np.cumsum(pnl)
    peak = np.maximum.accumulate(np.r_[equity0, eq])[1:]
    out["max_dd_pct"] = float(np.max((peak - eq) / peak) * 100.0)
    out["net_return_pct"] = float((eq[-1] / equity0 - 1.0) * 100.0)
    _, exit_day = local_minutes(np.array([x.exit_ms for x in tr]), server_tz)
    daily = pd.Series(pnl, index=exit_day).groupby(level=0).sum()
    start_eq = equity0 + daily.cumsum().shift(1, fill_value=0.0)
    rets = (daily / start_eq).to_numpy()
    rets = np.r_[rets, np.zeros(max(n_days - len(rets), 0))]
    sd = rets.std(ddof=1) if len(rets) > 1 else 0.0
    out["sharpe"] = float(rets.mean() / sd * math.sqrt(252)) if sd > 0 else float("nan")
    if len(r) > 2 and r.std(ddof=1) > 0:
        out["sr_trade"] = float(r.mean() / r.std(ddof=1))
        out["skew"] = float(stats.skew(r))
        out["kurt"] = float(stats.kurtosis(r, fisher=False))
    return out


def deflated_sharpe(sr: float, n_obs: int, skew: float, kurt: float,
                    trial_srs: list[float], n_trials: int) -> float:
    """Bailey & Lopez de Prado deflated Sharpe ratio (per-observation SR)."""
    if not all(map(math.isfinite, [sr, skew, kurt])) or n_obs < 3:
        return float("nan")
    trials = np.array([x for x in trial_srs if math.isfinite(x)])
    var = float(trials.var(ddof=1)) if len(trials) > 1 else 0.0
    n = max(int(n_trials), 1)
    if n > 1 and var > 0:
        g = 0.5772156649
        sr0 = math.sqrt(var) * ((1 - g) * stats.norm.ppf(1 - 1.0 / n)
                                + g * stats.norm.ppf(1 - 1.0 / (n * math.e)))
    else:
        sr0 = 0.0
    den = 1 - skew * sr + (kurt - 1) / 4.0 * sr * sr
    if den <= 0:
        return float("nan")
    return float(stats.norm.cdf((sr - sr0) * math.sqrt(n_obs - 1) / math.sqrt(den)))


def fmt_metrics(m: dict) -> str:
    if not m["trades"]:
        return "n=0"
    return (f"n={m['trades']:>4} wr={m['win_rate']:.2f} pf={m['pf']:.2f} "
            f"expR={m['expectancy_R']:+.3f} exp={m['expectancy_pts']:+.1f}pt "
            f"cost={m['avg_cost_pts']:.1f}pt beWR={m['breakeven_wr']:.2f} "
            f"sh={m['sharpe']:+.2f} dd={m['max_dd_pct']:.1f}%")


# ==========================================================================
# Experiment log
# ==========================================================================
LOG_FIELDS = ["ts", "round", "symbol", "source", "strategy", "params", "reason", "split"] + METRIC_KEYS


def params_key(params: dict) -> str:
    return json.dumps(params, sort_keys=True)


def read_log(path: Path | None = None) -> list[dict]:
    path = path or C.EXPERIMENTS_FILE
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def append_log(rows: list[dict], path: Path | None = None) -> None:
    path = path or C.EXPERIMENTS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=LOG_FIELDS)
        if new:
            w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in LOG_FIELDS})


def variants_tried(log: list[dict], symbol: str, strategy: str | None = None) -> set[tuple[str, str]]:
    return {(r["strategy"], r["params"]) for r in log
            if r["symbol"] == symbol and (strategy is None or r["strategy"] == strategy)}


def check_budget(log: list[dict], symbol: str, round_no: int, planned: list[tuple[str, dict]]) -> None:
    if not 1 <= round_no <= MAX_ROUNDS:
        raise SystemExit(f"round must be 1..{MAX_ROUNDS} (budget)")
    for strat in {s for s, _ in planned}:
        seen = {p for s, p in variants_tried(log, symbol, strat)}
        new = {params_key(p) for s, p in planned if s == strat} - seen
        if len(seen) + len(new) > MAX_COMBOS_PER_STRATEGY:
            raise SystemExit(f"budget: {strat} on {symbol} would reach {len(seen) + len(new)} "
                             f"combinations (> {MAX_COMBOS_PER_STRATEGY}). Drop variants.")


# ==========================================================================
# Evaluation helpers
# ==========================================================================
class Evaluator:
    """Caches signals per (strategy, params) and runs splits."""

    def __init__(self, cfg: Config, mkt: Market):
        self.cfg, self.mkt = cfg, mkt
        self.splits = make_splits(mkt, cfg)
        self.filters = TradeFilters(cfg.filters, C.NEWS_FILE)
        self._sig: dict[tuple[str, str], list[Signal]] = {}

    def signals(self, strategy: str, params: dict) -> list[Signal]:
        key = (strategy, params_key(params))
        if key not in self._sig:
            self._sig[key] = generate(strategy, self.mkt.bars, params, self.cfg.server_tz)
        return self._sig[key]

    def run(self, strategy: str, params: dict, start_ms: int, end_ms: int,
            slip_mult: float = 1.0) -> tuple[dict, list[Trade], Counter]:
        trades, skips = simulate(self.mkt, self.signals(strategy, params), self.cfg, self.filters,
                                 start_ms, end_ms, slip_mult)
        m = metrics(trades, self.cfg.starting_equity, days_in(self.mkt, start_ms, end_ms),
                    self.cfg.server_tz)
        return m, trades, skips


def log_rows(ev: Evaluator, round_no: int, strategy: str, params: dict, reason: str) -> list[dict]:
    rows = []
    for split in ("train", "validation"):
        a, b = getattr(ev.splits, split)
        m, _, _ = ev.run(strategy, params, a, b)
        rows.append({"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                     "round": round_no, "symbol": ev.cfg.symbol, "source": ev.mkt.source,
                     "strategy": strategy, "params": params_key(params), "reason": reason,
                     "split": split, **m})
    return rows


def _f(r: dict, k: str) -> float:
    try:
        return float(r[k])
    except (KeyError, TypeError, ValueError):
        return float("nan")


def candidates(log: list[dict], symbol: str, source: str) -> list[dict]:
    """One record per (strategy, params) with train and validation metrics."""
    rec: dict[tuple[str, str], dict] = {}
    for r in log:
        if r["symbol"] != symbol or r["source"] != source:
            continue
        k = (r["strategy"], r["params"])
        rec.setdefault(k, {"strategy": r["strategy"], "params": r["params"]})[r["split"]] = r
    return [v for v in rec.values() if "train" in v and "validation" in v]


def rank_candidates(cands: list[dict], n_trials: int) -> list[dict]:
    val_srs = [_f(c["validation"], "sr_trade") for c in cands]
    out = []
    for c in cands:
        v, t = c["validation"], c["train"]
        n = int(_f(v, "trades") or 0)
        c["tstat_val"] = _f(v, "sr_trade") * math.sqrt(n) if n else float("nan")
        c["dsr_val"] = deflated_sharpe(_f(v, "sr_trade"), n, _f(v, "skew"), _f(v, "kurt"),
                                       val_srs, n_trials)
        c["eligible"] = (n >= MIN_VAL_TRADES_FOR_SELECTION and _f(t, "expectancy_R") > 0
                         and _f(v, "expectancy_R") > 0 and _f(v, "pf") >= 1.2)
        out.append(c)
    out.sort(key=lambda c: (c["eligible"], np.nan_to_num(c["tstat_val"], nan=-1e9)), reverse=True)
    return out


def plateau_check(ev: Evaluator, strategy: str, params: dict, round_no: int) -> tuple[bool, list[str]]:
    """>= 75% of one-step grid neighbours must show PF >= 1.1 and positive expectancy
    on VALIDATION. Neighbours not yet in the log are run and logged (they count
    toward the budget)."""
    log = read_log()
    nbrs = neighbors(strategy, params)
    if not nbrs:
        return False, ["no grid neighbours (params outside the grid): cannot show a plateau"]
    have = {r["params"]: r for r in log if r["symbol"] == ev.cfg.symbol and r["strategy"] == strategy
            and r["split"] == "validation" and r["source"] == ev.mkt.source}
    missing = [q for q in nbrs if params_key(q) not in have]
    if missing:
        check_budget(log, ev.cfg.symbol, round_no, [(strategy, q) for q in missing])
        rows = []
        for q in missing:
            rows += log_rows(ev, round_no, strategy, q, "plateau neighbour check")
        append_log(rows)
        have.update({r["params"]: r for r in rows if r["split"] == "validation"})
    notes, good = [], 0
    for q in nbrs:
        r = have[params_key(q)]
        ok = _f(r, "pf") >= 1.1 and _f(r, "expectancy_R") > 0
        good += ok
        diff = {k: q[k] for k in q if q[k] != params.get(k)}
        notes.append(f"{diff}: pf={_f(r, 'pf'):.2f} expR={_f(r, 'expectancy_R'):+.3f} {'ok' if ok else 'FAIL'}")
    return good / len(nbrs) >= 0.75, notes


def walkforward(ev: Evaluator, strategy: str, params: dict, folds: int = 5) -> dict:
    """Inside the development period only.

    fixed: the candidate's params on each later fold (stability over time).
    reoptimised: anchored walk-forward that re-picks params from the baseline
    grid on all prior folds (by t-stat of R, >= 30 trades), then trades the next fold.
    """
    mkt = ev.mkt
    a, b = ev.splits.dev
    m = (mkt.bars.t >= a) & (mkt.bars.t < b)
    days = np.unique(mkt.bar_day[m])
    chunks = np.array_split(days, folds)
    bounds = [int(mkt.bars.t[np.searchsorted(mkt.bar_day, ch[0])]) for ch in chunks] + [b]
    grid = [strategy_params(strategy, g) for g in grid_combos(strategy)]
    if params_key(params) not in {params_key(g) for g in grid}:
        grid.append(params)
    fixed, reopt_trades, picks = [], [], []
    for k in range(1, folds):
        s_is, e_is, s_oos, e_oos = bounds[0], bounds[k], bounds[k], bounds[k + 1]
        mf, _, _ = ev.run(strategy, params, s_oos, e_oos)
        fixed.append(mf)
        best, best_score = None, -1e18
        for g in grid:
            mi, _, _ = ev.run(strategy, g, s_is, e_is)
            if mi["trades"] >= 30 and math.isfinite(mi["sr_trade"]):
                score = mi["sr_trade"] * math.sqrt(mi["trades"])
                if score > best_score:
                    best, best_score = g, score
        if best is None:
            picks.append(None)
            continue
        picks.append({kk: best[kk] for kk in STRATEGIES[strategy]["grid"]})
        _, tr, _ = ev.run(strategy, best, s_oos, e_oos)
        reopt_trades += tr
    n_oos_days = days_in(mkt, bounds[1], b)
    return {"fixed_folds": fixed, "picks": picks,
            "reoptimised": metrics(reopt_trades, ev.cfg.starting_equity, n_oos_days, ev.cfg.server_tz),
            "fixed_positive_folds": sum(1 for f in fixed if f["trades"] and f["expectancy_R"] > 0)}


# ==========================================================================
# Commands
# ==========================================================================
def cmd_fetch(args, cfg: Config) -> None:
    from broker import MT5Broker  # Windows + MT5 only
    br = MT5Broker(cfg)
    br.connect()
    name = br.resolve_symbol(cfg.symbol)
    spec = br.symbol_spec(name)
    C.DATA_DIR.mkdir(parents=True, exist_ok=True)
    spec_file(cfg.symbol).write_text(spec.to_json(), encoding="utf-8")
    print(f"spec saved: {spec}")
    now = int(time.time() * 1000) + DAY_MS
    month = 31 * DAY_MS
    ts, bs, as_ = [], [], []
    empty_run, end = 0, now
    for i in range(args.max_months):
        start = end - month
        t, bid, ask = br.ticks_range(start, end)
        print(f"  ticks {fmt_utc(start)[:10]} -> {fmt_utc(end)[:10]}: {len(t):,}"
              + ("" if len(t) else f"  (last_error={br.last_error()})"))
        if len(t):
            ts.append(t); bs.append(bid); as_.append(ask)
            empty_run = 0
        else:
            empty_run += 1
            if empty_run >= 3:
                break
        end = start
    if ts:
        t = np.concatenate(ts[::-1]); bid = np.concatenate(bs[::-1]); ask = np.concatenate(as_[::-1])
        o = np.argsort(t, kind="stable")
        t, bid, ask = t[o], bid[o], ask[o]
        np.savez(tick_file(cfg.symbol), t=t, bid=bid, ask=ask)
        print(f"saved {len(t):,} ticks to {tick_file(cfg.symbol)}")
    else:
        print("MT5 returned NO ticks. Open the symbol chart in MT5, scroll back, and retry.")
    parts = []
    end = now
    for _ in range(max(1, args.max_months // 12 + 1)):
        start = end - 366 * DAY_MS
        r = br.rates_range_m1(start, end)
        if r is None:
            break
        parts.append(r)
        end = start
    m1 = None
    if parts:
        m1 = {k: np.concatenate([p[k] for p in parts[::-1]]) for k in parts[0]}
        o = np.argsort(m1["t"], kind="stable")
        m1 = {k: v[o] for k, v in m1.items()}
        _, uniq = np.unique(m1["t"], return_index=True)
        m1 = {k: v[uniq] for k, v in m1.items()}
        np.savez(m1_file(cfg.symbol), **m1)
        print(f"saved {len(m1['t']):,} M1 bars to {m1_file(cfg.symbol)}")
    br.shutdown()
    if ts:
        rep = data_report(load_market(cfg, "ticks"), cfg, m1)
    elif m1 is not None:
        rep = data_report(load_market(cfg, "m1"), cfg, m1)
    else:
        rep = "No data returned by MT5."
    (C.DATA_DIR / f"{cfg.symbol}_data_report.txt").write_text(rep, encoding="utf-8")
    print("\n=== DATA REPORT ===\n" + rep)


def cmd_import_csv(args, cfg: Config) -> None:
    path = Path(args.file)
    first = path.open(encoding="utf-8", errors="replace").readline()
    sep = "\t" if "\t" in first else ("," if "," in first else ";")
    df = pd.read_csv(path, sep=sep)
    cols = {c.strip("<> ").lower(): c for c in df.columns}
    if "date" in cols and "time" in cols:          # MT5 "Export ticks"
        ts = pd.to_datetime(df[cols["date"]].astype(str) + " " + df[cols["time"]].astype(str),
                            format="%Y.%m.%d %H:%M:%S.%f", errors="coerce")
        tz = args.tz or cfg.server_tz
    else:
        tcol = next((cols[c] for c in cols if c in ("time", "timestamp", "datetime", "time_msc")), None)
        if tcol is None:
            raise SystemExit(f"no time column in {list(df.columns)}")
        raw = df[tcol]
        ts = pd.to_datetime(raw, unit="ms") if np.issubdtype(raw.dtype, np.number) else pd.to_datetime(raw)
        tz = args.tz or "UTC"
    bid = pd.to_numeric(df[cols["bid"]], errors="coerce").replace(0, np.nan).ffill()
    ask = pd.to_numeric(df[cols["ask"]], errors="coerce").replace(0, np.nan).ffill()
    ok = ts.notna() & bid.notna() & ask.notna()
    local_ms = (ts[ok].astype("int64") // 1_000_000).to_numpy()
    t = server_to_utc_ms(local_ms, tz)
    o = np.argsort(t, kind="stable")
    C.DATA_DIR.mkdir(parents=True, exist_ok=True)
    np.savez(tick_file(cfg.symbol), t=t[o], bid=bid[ok].to_numpy()[o], ask=ask[ok].to_numpy()[o])
    print(f"imported {ok.sum():,} ticks (times read as {tz}) -> {tick_file(cfg.symbol)}")
    print(data_report(load_market(cfg, "ticks"), cfg))


def cmd_info(args, cfg: Config) -> None:
    mkt = load_market(cfg, args.source)
    m1 = None
    if m1_file(cfg.symbol).exists():
        z = np.load(m1_file(cfg.symbol))
        m1 = {k: z[k] for k in z.files}
    print(data_report(mkt, cfg, m1))


def _print_table(title: str, rows: list[tuple[str, dict, dict]]) -> None:
    print(f"\n{title}")
    for label, mt, mv in rows:
        print(f"  {label}\n      train: {fmt_metrics(mt)}\n      valid: {fmt_metrics(mv)}")


def _short(strategy: str, params: dict) -> str:
    keys = list(STRATEGIES[strategy]["grid"])
    extra = {k: v for k, v in params.items()
             if k not in keys and v != STRATEGIES[strategy]["defaults"].get(k)}
    core = ", ".join(f"{k}={params[k]}" for k in keys)
    return f"{strategy}[{core}{'; ' + json.dumps(extra) if extra else ''}]"


def run_round(ev: Evaluator, round_no: int, plan: list[tuple[str, dict, str]]) -> None:
    log = read_log()
    tried = variants_tried(log, ev.cfg.symbol)
    plan = [(s, p, r) for s, p, r in plan if (s, params_key(p)) not in tried]
    if not plan:
        print("all planned variants are already in the log")
        return
    check_budget(log, ev.cfg.symbol, round_no, [(s, p) for s, p, _ in plan])
    rows_out, table = [], []
    for s, p, reason in plan:
        rows = log_rows(ev, round_no, s, p, reason)
        rows_out += rows
        table.append((_short(s, p), rows[0], rows[1]))
    append_log(rows_out)
    _print_table(f"Round {round_no} on {ev.cfg.symbol} ({ev.mkt.source}), "
                 f"costs: commission {ev.cfg.commission()}/lot/side, slippage {ev.cfg.slippage()} "
                 f"per side, latency {ev.cfg.costs.latency_ms} ms", table)
    total = len(variants_tried(read_log(), ev.cfg.symbol))
    print(f"\nTotal variants tried on {ev.cfg.symbol}: {total}")


def cmd_dev(args, cfg: Config) -> None:
    ev = Evaluator(cfg, load_market(cfg, args.source))
    names = list(STRATEGIES) if args.strategy == "all" else [args.strategy]
    plan = []
    if args.round == 1:
        for s in names:
            reason = "baseline grid: " + "; ".join(STRATEGIES[s]["reasons"].values())
            plan += [(s, strategy_params(s, g), reason) for g in grid_combos(s)]
    else:
        if not args.variants:
            raise SystemExit("rounds 2-5 need --variants file.json with a reason per variant")
        for v in json.loads(Path(args.variants).read_text(encoding="utf-8")):
            if not v.get("reason", "").strip():
                raise SystemExit(f"variant without a reason: {v}")
            if v["strategy"] not in STRATEGIES:
                raise SystemExit(f"unknown strategy {v['strategy']} (register it in strategy.py)")
            plan.append((v["strategy"], resolve_variant(v, cfg, ev.mkt.source), v["reason"]))
    run_round(ev, args.round, plan)


def resolve_variant(v: dict, cfg: Config, source: str) -> dict:
    """Full params of a variant.

    base: "best" = the strategy's top logged candidate by validation t-stat
    (train/validation only, never the final split); a dict = explicit params;
    absent = strategy defaults. `"trail": true` copies the trailing-stop
    settings from config, so the logged params record the exact values.
    """
    strat, base = v["strategy"], v.get("base")
    if base == "best":
        log = read_log()
        ranked = rank_candidates([c for c in candidates(log, cfg.symbol, source)
                                  if c["strategy"] == strat], len(variants_tried(log, cfg.symbol)))
        if not ranked:
            raise SystemExit(f"base 'best' needs round-1 results for {strat} on {cfg.symbol}")
        params = json.loads(ranked[0]["params"])
    elif isinstance(base, dict):
        params = strategy_params(strat, base)
    else:
        params = strategy_params(strat)
    over = dict(v.get("params") or {})
    if over.get("trail"):
        over = {**cfg.trail.as_params(), **over}
    params.update(over)
    return strategy_params(strat, params)


def cmd_select(args, cfg: Config, ev: Evaluator | None = None, top: int = 10) -> list[dict]:
    log = read_log()
    source = args.source
    n_trials = len(variants_tried(log, cfg.symbol))
    ranked = rank_candidates(candidates(log, cfg.symbol, source), n_trials)
    print(f"\nCandidates on {cfg.symbol} ({source}); variants tried = {n_trials}. "
          f"Eligible = >= {MIN_VAL_TRADES_FOR_SELECTION} validation trades, positive expectancy "
          "on train and validation, validation PF >= 1.2. Ranked by validation t-stat of R.")
    for c in ranked[:top]:
        p = json.loads(c["params"])
        print(f"  {'ELIGIBLE' if c['eligible'] else 'not eligible'}  {_short(c['strategy'], p)}  "
              f"t={c['tstat_val']:+.2f} DSR={c['dsr_val']:.2f}")
        print(f"      train: {fmt_metrics({k: _f(c['train'], k) for k in METRIC_KEYS} | {'trades': int(_f(c['train'], 'trades'))})}")
        print(f"      valid: {fmt_metrics({k: _f(c['validation'], k) for k in METRIC_KEYS} | {'trades': int(_f(c['validation'], 'trades'))})}")
    if n_trials > 1:
        print(f"\nMultiple-testing warning: {n_trials} variants were tried. A DSR below 0.95 means "
              "the best validation result is not distinguishable from luck at that trial count.")
    return ranked


def report_walkforward(ev: Evaluator, strategy: str, params: dict, folds: int) -> dict:
    wf = walkforward(ev, strategy, params, folds)
    print(f"\nWalk-forward (development period only, {folds} folds) for {_short(strategy, params)}")
    for i, f in enumerate(wf["fixed_folds"], 1):
        print(f"  fixed params, fold {i}: {fmt_metrics(f)}")
    print(f"  fixed params positive in {wf['fixed_positive_folds']}/{folds - 1} folds")
    print(f"  re-optimised picks per fold: {wf['picks']}")
    print(f"  re-optimised OOS: {fmt_metrics(wf['reoptimised'])}")
    return wf


def cmd_walkforward(args, cfg: Config) -> None:
    ev = Evaluator(cfg, load_market(cfg, args.source))
    params = strategy_params(args.strategy, json.loads(args.params or "{}"))
    report_walkforward(ev, args.strategy, params, args.folds)


def cmd_run_all(args, cfg: Config) -> None:
    ev = Evaluator(cfg, load_market(cfg, args.source))
    print(data_report(ev.mkt, cfg))
    plan = []
    for s in STRATEGIES:
        reason = "baseline grid: " + "; ".join(STRATEGIES[s]["reasons"].values())
        plan += [(s, strategy_params(s, g), reason) for g in grid_combos(s)]
    run_round(ev, 1, plan)
    ranked = cmd_select(args, cfg)
    finalists = [c for c in ranked if c["eligible"]][:3]
    if not finalists:
        print("\nNO CANDIDATE is eligible on validation. Nothing should go to the final test. "
              "Next: an improvement round (dev --round 2 --variants ...) or a different strategy.")
        return
    for c in finalists:
        p = json.loads(c["params"])
        ok, notes = plateau_check(ev, c["strategy"], p, 1)
        print(f"\nPlateau check {_short(c['strategy'], p)}: {'PASS' if ok else 'FAIL'}")
        for n in notes:
            print("   ", n)
        report_walkforward(ev, c["strategy"], p, args.folds)
    print("\nPick ONE finalist and run `backtest.py final --strategy ... --params '...'` once.")


def cmd_final(args, cfg: Config) -> None:
    C.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    access = json.loads(C.FINAL_TEST_LOG.read_text()) if C.FINAL_TEST_LOG.exists() else []
    prior = [a for a in access if a["symbol"] == cfg.symbol]
    if prior and not args.second_look:
        raise SystemExit(f"The final test for {cfg.symbol} was already used on {prior[0]['ts']} "
                         f"({prior[0]['strategy']}). Re-running it contaminates the test. "
                         "Pass --second-look only if you accept that, and report it.")
    ev = Evaluator(cfg, load_market(cfg, args.source))
    strategy = args.strategy
    params = strategy_params(strategy, json.loads(args.params or "{}"))
    access.append({"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   "symbol": cfg.symbol, "strategy": strategy, "params": params,
                   "second_look": bool(prior)})
    C.FINAL_TEST_LOG.write_text(json.dumps(access, indent=2))
    a, b = ev.splits.final
    m1, trades, skips = ev.run(strategy, params, a, b, 1.0)
    m2, _, _ = ev.run(strategy, params, a, b, 2.0)
    plateau_ok, notes = plateau_check(ev, strategy, params, max(1, int(args.round)))
    log = read_log()
    n_trials = len(variants_tried(log, cfg.symbol))
    val_srs = [_f(r, "sr_trade") for r in log if r["symbol"] == cfg.symbol and r["split"] == "validation"]
    dsr = deflated_sharpe(m1["sr_trade"], m1["trades"], m1["skew"], m1["kurt"], val_srs, n_trials)
    gates = {
        f"profit factor > {FINAL_MIN_PF}": bool(m1["pf"] > FINAL_MIN_PF),
        f"trades >= {FINAL_MIN_TRADES}": bool(m1["trades"] >= FINAL_MIN_TRADES),
        "profitable with 2x slippage": bool(m2["trades"] > 0 and m2["net_return_pct"] > 0),
        "plateau (validation neighbours)": bool(plateau_ok),
    }
    passed = all(gates.values())
    print(f"\nFINAL TEST {cfg.symbol} {fmt_utc(a)[:10]} -> {fmt_utc(b - 1)[:10]} "
          f"({ev.splits.n_days['final']} days), {_short(strategy, params)}")
    print(f"  1x slippage: {fmt_metrics(m1)}")
    print(f"  2x slippage: {fmt_metrics(m2)}")
    print(f"  exits: {dict(Counter(t.exit_reason for t in trades))}   skipped signals: {dict(skips)}")
    print(f"  variants tried on {cfg.symbol}: {n_trials}; deflated Sharpe (final test) = {dsr:.3f}")
    for n in notes:
        print("   plateau:", n)
    for g, ok in gates.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {g}")
    print(f"\n  RESULT: {'ALL GATES PASSED' if passed else 'GATES NOT PASSED: do not trade this'}")
    if prior:
        print("  NOTE: this was a SECOND look at the final test; treat the result as contaminated.")
    out = {"symbol": cfg.symbol, "strategy": strategy, "params": params, "passed_gates": passed,
           "gates": gates, "final_metrics": m1, "final_metrics_2x_slippage": m2,
           "deflated_sharpe": dsr, "variants_tried": n_trials, "source": ev.mkt.source,
           "second_look": bool(prior),
           "costs": {"commission_per_lot_side": cfg.commission(), "slippage_price": cfg.slippage(),
                     "latency_ms": cfg.costs.latency_ms,
                     "extra_spread_price": cfg.costs.extra_spread_price},
           "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    if passed or not C.CHOSEN_FILE.exists():
        C.CHOSEN_FILE.write_text(json.dumps(out, indent=2, default=str))
        print(f"  written: {C.CHOSEN_FILE}")
    pd.DataFrame([asdict(t) for t in trades]).to_csv(
        C.RESULTS_DIR / f"final_trades_{cfg.symbol}_{strategy}.csv", index=False)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--symbol", default=None, help="base symbol, e.g. XAUUSD or BTCUSD")
        p.add_argument("--source", default="ticks", choices=["ticks", "m1"])
        return p
    p = common(sub.add_parser("fetch"))
    p.add_argument("--max-months", type=int, default=120)
    p = common(sub.add_parser("import-csv"))
    p.add_argument("--file", required=True)
    p.add_argument("--tz", default=None, help="timezone of the CSV times (default: server tz for MT5 exports, else UTC)")
    common(sub.add_parser("info"))
    p = common(sub.add_parser("dev"))
    p.add_argument("--strategy", default="all", choices=["all", *STRATEGIES])
    p.add_argument("--round", type=int, default=1)
    p.add_argument("--variants", default=None)
    common(sub.add_parser("select"))
    p = common(sub.add_parser("walkforward"))
    p.add_argument("--strategy", required=True, choices=list(STRATEGIES))
    p.add_argument("--params", default="{}")
    p.add_argument("--folds", type=int, default=5)
    p = common(sub.add_parser("run-all"))
    p.add_argument("--folds", type=int, default=5)
    p = common(sub.add_parser("final"))
    p.add_argument("--strategy", required=True, choices=list(STRATEGIES))
    p.add_argument("--params", default="{}")
    p.add_argument("--round", type=int, default=1, help="round used if plateau neighbours must be run")
    p.add_argument("--second-look", action="store_true")
    return ap


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)
    cfg = load_config(symbol=args.symbol)
    {"fetch": cmd_fetch, "import-csv": cmd_import_csv, "info": cmd_info, "dev": cmd_dev,
     "select": cmd_select, "walkforward": cmd_walkforward, "run-all": cmd_run_all,
     "final": cmd_final}[args.cmd](args, cfg)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except RuntimeError as exc:        # BrokerError (no MT5 / terminal problems)
        print(f"ERROR: {exc}")
        sys.exit(1)
