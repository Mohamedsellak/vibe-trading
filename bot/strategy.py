"""Signals, indicators, time helpers and trade filters.

Pure numpy/pandas. The backtester and the live bot call exactly the same
functions: bars are built from ticks with `build_bars`, and a strategy
function turns bars into a list of `Signal`s. Live trading acts only on a
signal whose decision time equals the close of the last completed bar.

All timestamps are UTC epoch milliseconds. Broker server time is converted
to UTC in broker.py / backtest.py before it reaches this module.
"""
from __future__ import annotations

import bisect
import csv
import itertools
import math
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

MINUTE_MS = 60_000
DAY_MS = 86_400_000
UTC_NAMES = {"UTC", "GMT", "ETC/UTC", "ETC/GMT", "Z"}


# --------------------------------------------------------------------------
# Time helpers
# --------------------------------------------------------------------------
def _is_utc(tz: str) -> bool:
    return tz.upper() in UTC_NAMES


def server_to_utc_ms(ms, server_tz: str) -> np.ndarray:
    """MT5 reports times as server wall-clock encoded as epoch. Convert to UTC."""
    arr = np.asarray(ms, dtype="int64")
    if _is_utc(server_tz):
        return arr
    idx = pd.to_datetime(arr, unit="ms")
    loc = idx.tz_localize(server_tz, ambiguous=np.zeros(len(idx), dtype=bool),
                          nonexistent="shift_forward")
    return loc.tz_convert("UTC").as_unit("ms").asi8.astype("int64")


def utc_to_server_ms(ms, server_tz: str) -> np.ndarray:
    arr = np.asarray(ms, dtype="int64")
    if _is_utc(server_tz):
        return arr
    idx = pd.to_datetime(arr, unit="ms", utc=True).tz_convert(server_tz).tz_localize(None)
    return idx.as_unit("ms").asi8.astype("int64")


def local_minutes(t_ms, tz: str) -> tuple[np.ndarray, np.ndarray]:
    """(minute of local day, local day number) for UTC epoch-ms times. DST aware."""
    local_ms = utc_to_server_ms(t_ms, tz)
    return ((local_ms % DAY_MS) // MINUTE_MS).astype("int64"), (local_ms // DAY_MS).astype("int64")


def hhmm(text: str) -> int:
    h, m = text.split(":")
    return int(h) * 60 + int(m)


def fmt_utc(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


# --------------------------------------------------------------------------
# Bars
# --------------------------------------------------------------------------
@dataclass
class Bars:
    t: np.ndarray          # bar open time, UTC ms
    o: np.ndarray          # bid OHLC (what MT5 charts show)
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    spread: np.ndarray     # mean ask-bid inside the bar
    spread_ref: np.ndarray  # rolling median of `spread` (spread filter reference)
    n: np.ndarray          # tick count (tick volume)
    last_tick: np.ndarray  # index of the bar's last tick in the tick arrays

    def __len__(self) -> int:
        return len(self.t)

    def close_time(self, i: int) -> int:
        return int(self.t[i]) + MINUTE_MS


def build_bars(t_ms: np.ndarray, bid: np.ndarray, ask: np.ndarray,
               spread_median_bars: int = 60, chunk: int = 5_000_000) -> Bars:
    """1-minute bid bars from ticks. Minutes without ticks produce no bar.

    Works in chunks, so 100M+ ticks (memory-mapped from disk) never need a
    full-size temporary array.
    """
    n = len(t_ms)
    if n == 0:
        empty = np.array([], dtype=float)
        return Bars(np.array([], dtype="int64"), empty, empty, empty, empty, empty, empty,
                    np.array([], dtype="int64"), np.array([], dtype="int64"))
    parts, prev = [], None
    for a in range(0, n, chunk):
        k = np.asarray(t_ms[a:a + chunk]) // MINUTE_MS
        if prev is None or k[0] != prev:
            parts.append(np.array([a], dtype="int64"))
        parts.append(np.flatnonzero(k[1:] != k[:-1]).astype("int64") + 1 + a)
        prev = k[-1]
    starts = np.concatenate(parts)
    ends = np.r_[starts[1:], n] - 1
    cnt = (ends - starts + 1).astype("int64")
    spread = (np.add.reduceat(ask, starts, dtype=np.float64)
              - np.add.reduceat(bid, starts, dtype=np.float64)) / cnt
    ref = pd.Series(spread).rolling(spread_median_bars, min_periods=5).median().to_numpy(copy=True)
    return Bars(t=(np.asarray(t_ms[starts], dtype="int64") // MINUTE_MS) * MINUTE_MS,
                o=np.array(bid[starts], dtype=float),
                h=np.array(np.maximum.reduceat(bid, starts), dtype=float),
                l=np.array(np.minimum.reduceat(bid, starts), dtype=float),
                c=np.array(bid[ends], dtype=float), spread=spread, spread_ref=ref,
                n=cnt, last_tick=ends.astype("int64"))


# --------------------------------------------------------------------------
# Indicators (all causal: value at i uses bars <= i only)
# --------------------------------------------------------------------------
def atr(b: Bars, n: int = 14) -> np.ndarray:
    prev_c = np.r_[np.nan, b.c[:-1]]
    tr = np.nanmax(np.vstack([b.h - b.l, np.abs(b.h - prev_c), np.abs(b.l - prev_c)]), axis=0)
    return pd.Series(tr).ewm(alpha=1.0 / n, adjust=False, min_periods=n).mean().to_numpy()


def sma(x: np.ndarray, n: int) -> np.ndarray:
    return pd.Series(x).rolling(n, min_periods=n).mean().to_numpy()


def rolling_std(x: np.ndarray, n: int) -> np.ndarray:
    return pd.Series(x).rolling(n, min_periods=n).std(ddof=0).to_numpy()


def efficiency_ratio(x: np.ndarray, n: int) -> np.ndarray:
    """Kaufman ER: |net move| / path length over n bars. Low = ranging."""
    s = pd.Series(x)
    change = (s - s.shift(n)).abs()
    path = s.diff().abs().rolling(n, min_periods=n).sum()
    return (change / path.replace(0.0, np.nan)).to_numpy()


def session_vwap(b: Bars, server_tz: str) -> tuple[np.ndarray, np.ndarray]:
    """VWAP and its std, anchored at each server-day open, tick-count weighted."""
    _, day = local_minutes(b.t, server_tz)
    tp = (b.h + b.l + b.c) / 3.0
    w = b.n.astype(float)
    df = pd.DataFrame({"day": day, "w": w, "wp": w * tp, "wp2": w * tp * tp})
    g = df.groupby("day", sort=False)
    cw, cwp, cwp2 = g["w"].cumsum(), g["wp"].cumsum(), g["wp2"].cumsum()
    vwap = (cwp / cw).to_numpy()
    var = np.maximum((cwp2 / cw).to_numpy() - vwap * vwap, 0.0)
    return vwap, np.sqrt(var)


# --------------------------------------------------------------------------
# Signals
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Signal:
    bar_idx: int
    time_ms: int       # decision time = close of bar `bar_idx`, UTC ms
    side: int          # +1 buy, -1 sell
    sl_dist: float     # price distance from the fill to the stop loss
    tp_dist: float     # price distance from the fill to the take profit
    hold_min: int      # time stop
    strategy: str
    note: str = ""
    trail_activate_r: float = 0.0   # 0 = no trailing stop
    trail_lock: float = 0.0         # fraction of open profit the stop locks in
    trail_step_r: float = 0.0       # stop moves in steps of this many R


def trail_stop_level(best_px, entry: float, sl0: float, sl_dist: float, side: int,
                     activate_r: float, lock: float, step_r: float):
    """Trailing stop given the best price seen since entry (bid for longs, ask for shorts).

    Inactive until open profit reaches activate_r x the initial risk. Then the
    stop sits at entry + lock x open profit, moved from the initial stop only in
    whole steps of step_r x risk, so it never moves back. The backtester and
    the live bot both use this function, so they trail identically.
    """
    best = np.asarray(best_px, dtype=float)
    mfe = (best - entry) * side
    cand = entry + side * lock * mfe
    moved = side * (cand - sl0)
    step = step_r * sl_dist
    if step > 0:
        moved = np.floor(moved / step) * step
    lvl = sl0 + side * np.maximum(moved, 0.0)
    return np.where(mfe >= activate_r * sl_dist, lvl, sl0)


def ny_session_mask(b: Bars, p: dict) -> np.ndarray:
    """True for bars inside the New York session when p['session'] == 'newyork'."""
    if p.get("session", "all") != "newyork":
        return np.ones(len(b), dtype=bool)
    mod, _ = local_minutes(b.t, "America/New_York")
    return (mod >= hhmm(p["ny_start"])) & (mod < hhmm(p["ny_end"]))


def _prev_atr(a: np.ndarray, i: int) -> float:
    return float(a[i - 1]) if i > 0 else float("nan")


def signals_breakout(b: Bars, p: dict, server_tz: str = "UTC") -> list[Signal]:
    """Volatility-expansion breakout of the pre-open range at London / New York open.

    Range = high/low of the `range_min` minutes before the open (exchange local
    time, DST handled). In the first `entry_window_min` minutes after the open,
    the first bar that closes beyond the range AND whose own range is at least
    `exp_mult` x ATR triggers a trade in the breakout direction.
    """
    a = atr(b, p["atr_n"])
    out: list[Signal] = []
    for name, tz, open_txt in (("london", "Europe/London", p["london_open"]),
                               ("newyork", "America/New_York", p["ny_open"])):
        if p.get("session", "all") == "newyork" and name != "newyork":
            continue
        mod, day = local_minutes(b.t, tz)
        open_m = hhmm(open_txt)
        in_range = (mod >= open_m - p["range_min"]) & (mod < open_m)
        in_window = (mod >= open_m) & (mod < open_m + p["entry_window_min"])
        if not in_range.any():
            continue
        rg = (pd.DataFrame({"day": day[in_range], "h": b.h[in_range], "l": b.l[in_range]})
              .groupby("day").agg(hi=("h", "max"), lo=("l", "min"), cnt=("h", "size")))
        ranges = {int(d): (r.hi, r.lo, r.cnt) for d, r in rg.iterrows()}
        need = 0.8 * p["range_min"]
        done: set[int] = set()
        for i in np.flatnonzero(in_window):
            d = int(day[i])
            if d in done or d not in ranges:
                continue
            hi, lo, cnt = ranges[d]
            if cnt < need:                      # thin pre-open data: skip the session
                done.add(d)
                continue
            av = _prev_atr(a, i)
            if not np.isfinite(av) or av <= 0:
                continue
            if b.h[i] - b.l[i] < p["exp_mult"] * av:
                continue
            buf = p["buffer_atr"] * av
            if b.c[i] > hi + buf:
                side = 1
            elif b.c[i] < lo - buf:
                side = -1
            else:
                continue
            sl = p["sl_atr"] * av
            out.append(Signal(int(i), b.close_time(i), side, sl, p["tp_r"] * sl,
                              p["hold_min"], "breakout", name))
            done.add(d)
    out.sort(key=lambda s: s.time_ms)
    return out


def signals_meanrev(b: Bars, p: dict, server_tz: str = "UTC") -> list[Signal]:
    """VWAP + Bollinger fade, only when the efficiency ratio says the market ranges.

    Buy when the close is below the lower band AND below session VWAP; sell
    mirrored. Target = middle band at signal time, stop = sl_atr x ATR.
    """
    a = atr(b, p["atr_n"])
    mid = sma(b.c, p["bb_n"])
    sd = rolling_std(b.c, p["bb_n"])
    upper, lower = mid + p["bb_k"] * sd, mid - p["bb_k"] * sd
    er = efficiency_ratio(b.c, p["er_n"])
    vwap, _ = session_vwap(b, server_tz)
    mod, _ = local_minutes(b.t, "UTC")
    active = (mod >= p["active_start_utc"]) & (mod < p["active_end_utc"]) & ny_session_mask(b, p)
    with np.errstate(invalid="ignore"):
        longs = (b.c < lower) & (b.c < vwap)
        shorts = (b.c > upper) & (b.c > vwap)
        ok = active & (er < p["er_max"]) & np.isfinite(mid) & np.isfinite(a)
    out: list[Signal] = []
    last = -10**9
    for i in np.flatnonzero(ok & (longs | shorts)):
        if i - last < p["min_gap_bars"]:
            continue
        av = _prev_atr(a, i)
        if not np.isfinite(av) or av <= 0:
            continue
        side = 1 if longs[i] else -1
        tp = abs(mid[i] - b.c[i])
        if tp < p["min_tp_atr"] * av:           # target too close to pay costs
            continue
        out.append(Signal(int(i), b.close_time(i), side, p["sl_atr"] * av, float(tp),
                          p["hold_min"], "meanrev"))
        last = i
    return out


def signals_sweep(b: Bars, p: dict, server_tz: str = "UTC") -> list[Signal]:
    """Liquidity sweep of the Asian-session high/low, then reversal.

    During the active window, a bar trades beyond the Asian low by at least
    pierce_atr x ATR (stops run). If a bar closes back above the Asian low
    within `confirm_bars` bars (sweep bar included), buy. Stop sits beyond the
    sweep extreme; target is tp_r x risk. One trade per side per day.
    """
    a = atr(b, p["atr_n"])
    mod, day = local_minutes(b.t, "UTC")
    asia = (mod >= p["asia_start_utc"]) & (mod < p["asia_end_utc"])
    active = (mod >= p["active_start_utc"]) & (mod < p["active_end_utc"]) & ny_session_mask(b, p)
    if not asia.any():
        return []
    lv = (pd.DataFrame({"day": day[asia], "h": b.h[asia], "l": b.l[asia]})
          .groupby("day").agg(hi=("h", "max"), lo=("l", "min"), cnt=("h", "size")))
    need = 0.6 * (p["asia_end_utc"] - p["asia_start_utc"])
    levels = {int(d): (r.hi, r.lo) for d, r in lv.iterrows() if r.cnt >= need}
    state: dict[int, dict] = {}
    out: list[Signal] = []
    for i in np.flatnonzero(active):
        d = int(day[i])
        if d not in levels:
            continue
        av = _prev_atr(a, i)
        if not np.isfinite(av) or av <= 0:
            continue
        hi, lo = levels[d]
        st = state.setdefault(d, {"L": None, "S": None, "Ldone": False, "Sdone": False})
        for side, key in ((1, "L"), (-1, "S")):
            if st[key + "done"]:
                continue
            level = lo if side == 1 else hi
            beyond = (b.l[i] < level - p["pierce_atr"] * av) if side == 1 else \
                     (b.h[i] > level + p["pierce_atr"] * av)
            if st[key] is None:
                if not beyond:
                    continue
                st[key] = [i, b.l[i] if side == 1 else b.h[i]]
            start, ext = st[key]
            ext = min(ext, b.l[i]) if side == 1 else max(ext, b.h[i])
            st[key][1] = ext
            if i - start >= p["confirm_bars"]:   # no reclaim in time: sweep failed
                st[key] = None
                continue
            reclaimed = b.c[i] > level if side == 1 else b.c[i] < level
            if not reclaimed:
                continue
            stop = ext - p["sl_buf_atr"] * av if side == 1 else ext + p["sl_buf_atr"] * av
            sl = abs(b.c[i] - stop)
            st[key + "done"] = True
            if 0.5 * av <= sl <= p["max_sl_atr"] * av:
                out.append(Signal(int(i), b.close_time(i), side, float(sl), p["tp_r"] * sl,
                                  p["hold_min"], "sweep", "asia_low" if side == 1 else "asia_high"))
    out.sort(key=lambda s: s.time_ms)
    return out


# Defaults, baseline grids (round 1) and the reason for every searched dimension.
STRATEGIES: dict[str, dict] = {
    "breakout": {
        "fn": signals_breakout,
        "defaults": {"atr_n": 14, "london_open": "08:00", "ny_open": "09:30",
                     "range_min": 60, "entry_window_min": 60, "exp_mult": 1.5,
                     "buffer_atr": 0.0, "sl_atr": 1.5, "tp_r": 1.5, "hold_min": 30,
                     "session": "all", "ny_start": "08:00", "ny_end": "16:00", "trail": False},
        "grid": {"range_min": [30, 60], "exp_mult": [1.0, 1.5, 2.0], "tp_r": [1.0, 2.0]},
        "reasons": {
            "range_min": "how much pre-open consolidation defines the level liquidity sits behind",
            "exp_mult": "require a real volatility expansion, not a drift through the level",
            "tp_r": "trade-off between follow-through length and hit rate after costs",
        },
    },
    "meanrev": {
        "fn": signals_meanrev,
        "defaults": {"atr_n": 14, "bb_n": 20, "bb_k": 2.0, "er_n": 30, "er_max": 0.3,
                     "sl_atr": 1.5, "min_tp_atr": 0.5, "hold_min": 20, "min_gap_bars": 10,
                     "active_start_utc": 420, "active_end_utc": 1200,
                     "session": "all", "ny_start": "08:00", "ny_end": "16:00", "trail": False},
        "grid": {"bb_k": [2.0, 2.5], "er_max": [0.2, 0.3], "sl_atr": [1.0, 1.5, 2.0]},
        "reasons": {
            "bb_k": "how stretched price must be before liquidity-provision pays",
            "er_max": "regime filter: only fade when recent path is choppy, not trending",
            "sl_atr": "room for noise versus size of the loss when the range breaks",
        },
    },
    "sweep": {
        "fn": signals_sweep,
        "defaults": {"atr_n": 14, "asia_start_utc": 0, "asia_end_utc": 360,
                     "active_start_utc": 420, "active_end_utc": 1200, "pierce_atr": 0.2,
                     "confirm_bars": 3, "sl_buf_atr": 0.2, "max_sl_atr": 4.0, "tp_r": 1.5,
                     "hold_min": 45, "session": "all", "ny_start": "08:00", "ny_end": "16:00", "trail": False},
        "grid": {"pierce_atr": [0.1, 0.3], "confirm_bars": [1, 3], "tp_r": [1.0, 1.5, 2.0]},
        "reasons": {
            "pierce_atr": "a sweep must run far enough to trigger resting stops",
            "confirm_bars": "how fast the reclaim must happen to count as rejection",
            "tp_r": "trade-off between reversal length and hit rate after costs",
        },
    },
}


def strategy_params(name: str, overrides: dict | None = None) -> dict:
    p = dict(STRATEGIES[name]["defaults"])
    p.update(overrides or {})
    return p


def grid_combos(name: str) -> list[dict]:
    grid = STRATEGIES[name]["grid"]
    keys = list(grid)
    return [dict(zip(keys, vals)) for vals in itertools.product(*(grid[k] for k in keys))]


def generate(name: str, bars: Bars, params: dict, server_tz: str) -> list[Signal]:
    p = strategy_params(name, params)
    sigs = STRATEGIES[name]["fn"](bars, p, server_tz)
    if p.get("trail"):
        sigs = [replace(s, trail_activate_r=float(p["trail_activate_r"]),
                        trail_lock=float(p["trail_lock"]), trail_step_r=float(p["trail_step_r"]))
                for s in sigs]
    return sigs


def neighbors(name: str, params: dict) -> list[dict]:
    """Grid points one step away in exactly one searched dimension."""
    grid = STRATEGIES[name]["grid"]
    out = []
    for k, vals in grid.items():
        if params.get(k) not in vals:
            continue
        j = vals.index(params[k])
        for jj in (j - 1, j + 1):
            if 0 <= jj < len(vals):
                q = dict(params)
                q[k] = vals[jj]
                out.append(q)
    return out


# --------------------------------------------------------------------------
# Trade filters shared by backtest and live bot
# --------------------------------------------------------------------------
class TradeFilters:
    def __init__(self, fcfg, news_path: Path | None = None):
        self.cfg = fcfg
        self.roll_start = hhmm(fcfg.rollover_start_local)
        self.roll_end = hhmm(fcfg.rollover_end_local)
        self.news: list[tuple[int, int, str]] = []
        if news_path is not None and Path(news_path).exists():
            self.news = load_news(Path(news_path), fcfg.news_minutes_before,
                                  fcfg.news_minutes_after)
        self._starts = [s for s, _, _ in self.news]

    def news_blocked(self, t_ms: int) -> str | None:
        j = bisect.bisect_right(self._starts, t_ms) - 1
        while j >= 0:
            s, e, label = self.news[j]
            if s <= t_ms < e:
                return label
            if t_ms - s > 6 * 3_600_000:      # windows are short; stop scanning back
                break
            j -= 1
        return None

    def rollover_blocked(self, t_ms: int) -> bool:
        mod, _ = local_minutes(np.array([t_ms]), self.cfg.rollover_tz)
        m = int(mod[0])
        if self.roll_start <= self.roll_end:
            return self.roll_start <= m < self.roll_end
        return m >= self.roll_start or m < self.roll_end

    def spread_ok(self, spread: float, ref: float) -> bool:
        if not np.isfinite(ref) or ref <= 0:
            return False
        return spread <= self.cfg.spread_max_mult * ref

    def check(self, t_ms: int, spread: float, ref: float) -> str | None:
        """Return a block reason, or None when an entry is allowed."""
        if self.rollover_blocked(t_ms):
            return "rollover"
        label = self.news_blocked(t_ms)
        if label:
            return f"news:{label}"
        if not self.spread_ok(spread, ref):
            return "spread"
        return None


def load_news(path: Path, default_before: int, default_after: int) -> list[tuple[int, int, str]]:
    """CSV columns: utc_time (YYYY-MM-DD HH:MM), minutes_before, minutes_after, event."""
    rows = []
    with path.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(line for line in fh if not line.lstrip().startswith("#")):
            when = (r.get("utc_time") or "").strip()
            if not when:
                continue
            dt = datetime.strptime(when, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            t = int(dt.timestamp() * 1000)
            before = int(r.get("minutes_before") or default_before)
            after = int(r.get("minutes_after") or default_after)
            rows.append((t - before * MINUTE_MS, t + after * MINUTE_MS,
                         (r.get("event") or "news").strip()))
    rows.sort()
    return rows


def apply_min_stop(sl_dist: float, tp_dist: float, stops_level: int, point: float,
                   spread: float = 0.0) -> tuple[float, float]:
    """Widen SL/TP to the broker's minimum stop distance (stops level + spread)."""
    min_d = stops_level * point + (spread if stops_level > 0 else 0.0)
    return max(sl_dist, min_d), max(tp_dist, min_d)


def round_price(x: float, tick_size: float, digits: int) -> float:
    if tick_size > 0:
        x = round(x / tick_size) * tick_size
    return round(x, digits)


def is_finite(x: float) -> bool:
    return x is not None and math.isfinite(x)
