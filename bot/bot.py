"""Live/demo trading loop for the single strategy chosen by `backtest.py final`.

    python bot.py                       # demo account (default)
    python bot.py --allow-failed-gates  # demo only: forward-test a candidate that failed a gate
    python bot.py --live                # real account: asks for a typed confirmation

Safety: at startup the account type is read from MT5. A real (or contest)
account is refused unless --live is given AND the typed confirmation matches.
"""
from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

import config as C
from config import Config, load_chosen, load_config
from risk import RiskManager, RiskState, lot_size
from strategy import (MINUTE_MS, TradeFilters, apply_min_stop, build_bars, generate,
                      server_to_utc_ms, trail_stop_level, utc_to_server_ms)

log = logging.getLogger("bot")


def now_ms() -> int:
    return int(time.time() * 1000)


# --------------------------------------------------------------------------
# Safety checks (pure functions, unit tested)
# --------------------------------------------------------------------------
def live_guard(mode: str, live_flag: bool, login: int, input_fn=input) -> bool:
    """True if trading may start on this account."""
    if mode == "demo":
        return True
    if not live_flag:
        print(f"REFUSED: account {login} is a {mode.upper()} account. This bot trades demo "
              "accounts only unless started with --live.")
        return False
    expected = f"TRADE LIVE {login}"
    answer = input_fn(f"Account {login} is a {mode.upper()} account with real money.\n"
                      f"Type exactly '{expected}' to continue: ")
    if answer.strip() != expected:
        print("Confirmation did not match. Exiting without trading.")
        return False
    return True


def strategy_guard(chosen: dict | None, symbol: str, mode: str, allow_failed: bool) -> str | None:
    """None if the chosen strategy may run, else the refusal reason."""
    if chosen is None:
        return "no results/chosen_strategy.json: run `backtest.py final` first"
    if not symbol.upper().startswith(str(chosen.get("symbol", "")).upper()):
        return f"chosen strategy is for {chosen.get('symbol')}, config SYMBOL is {symbol}"
    if not chosen.get("passed_gates"):
        if mode != "demo":
            return "chosen strategy did not pass the go-live gates: refusing a real account"
        if not allow_failed:
            return ("chosen strategy did not pass the go-live gates. Use --allow-failed-gates "
                    "to forward-test it on demo anyway")
    return None


def expected_offset_minutes(server_tz: str, at_ms: int) -> float:
    return float((int(utc_to_server_ms(np.array([at_ms]), server_tz)[0]) - at_ms) / MINUTE_MS)


# --------------------------------------------------------------------------
# SQLite log
# --------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS events (ts TEXT, kind TEXT, msg TEXT);
CREATE TABLE IF NOT EXISTS signals (ts TEXT, bar_close_utc TEXT, strategy TEXT, note TEXT,
    side INTEGER, sl_dist REAL, tp_dist REAL, spread REAL, spread_ref REAL, decision TEXT, reason TEXT);
CREATE TABLE IF NOT EXISTS orders (ts TEXT, action TEXT, ticket INTEGER, side INTEGER, volume REAL,
    requested REAL, fill REAL, sl REAL, tp REAL, retcode INTEGER, comment TEXT, send_latency_ms REAL,
    total_ms REAL, signal_to_fill_ms REAL, attempts INTEGER, slippage_points REAL, ok INTEGER);
CREATE TABLE IF NOT EXISTS trades (ticket INTEGER PRIMARY KEY, open_ts TEXT, close_ts TEXT,
    strategy TEXT, side INTEGER, volume REAL, entry REAL, pnl REAL, close_reason TEXT);
CREATE TABLE IF NOT EXISTS open_positions (ticket INTEGER PRIMARY KEY, deadline_ms INTEGER,
    strategy TEXT, side INTEGER, volume REAL, entry REAL, open_ms INTEGER, sl_dist REAL,
    trail_act REAL, trail_lock REAL, trail_step REAL);
CREATE TABLE IF NOT EXISTS equity (ts TEXT, equity REAL, balance REAL);
CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT);
"""


class TradeLog:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path))
        self.db.executescript(SCHEMA)
        cols = {r[1] for r in self.db.execute("PRAGMA table_info(open_positions)")}
        for col in ("sl_dist", "trail_act", "trail_lock", "trail_step"):   # older databases
            if col not in cols:
                self.db.execute(f"ALTER TABLE open_positions ADD COLUMN {col} REAL DEFAULT 0")
        self.db.commit()

    @staticmethod
    def ts(ms: int | None = None) -> str:
        return datetime.fromtimestamp((ms or now_ms()) / 1000, tz=timezone.utc).isoformat(timespec="milliseconds")

    def event(self, kind: str, msg: str) -> None:
        self.db.execute("INSERT INTO events VALUES (?,?,?)", (self.ts(), kind, msg))
        self.db.commit()

    def signal(self, s, spread, ref, decision, reason="") -> None:
        self.db.execute("INSERT INTO signals VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (self.ts(), self.ts(s.time_ms), s.strategy, s.note, s.side, s.sl_dist,
                         s.tp_dist, spread, ref, decision, reason))
        self.db.commit()

    def order(self, action, res, side, sl=None, tp=None, signal_ms=None) -> None:
        s2f = (now_ms() - signal_ms) if signal_ms else None
        self.db.execute("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (self.ts(), action, res.ticket, side, res.volume, res.requested_price,
                         res.fill_price, sl, tp, res.retcode, res.comment, res.latency_ms,
                         res.total_ms, s2f, res.attempts, res.slippage_points, int(res.ok)))
        self.db.commit()

    def add_open(self, ticket, deadline_ms, strategy, side, volume, entry, open_ms,
                 sl_dist=0.0, trail=(0.0, 0.0, 0.0)) -> None:
        self.db.execute("INSERT OR REPLACE INTO open_positions (ticket, deadline_ms, strategy, side, "
                        "volume, entry, open_ms, sl_dist, trail_act, trail_lock, trail_step) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (ticket, deadline_ms, strategy, side, volume, entry, open_ms, sl_dist, *trail))
        self.db.commit()

    def open_positions(self) -> dict[int, dict]:
        cur = self.db.execute("SELECT ticket, deadline_ms, strategy, side, volume, entry, open_ms, "
                              "sl_dist, trail_act, trail_lock, trail_step FROM open_positions")
        return {r[0]: {"deadline_ms": r[1], "strategy": r[2], "side": r[3], "volume": r[4],
                       "entry": r[5], "open_ms": r[6], "sl_dist": r[7] or 0.0,
                       "trail_act": r[8] or 0.0, "trail_lock": r[9] or 0.0,
                       "trail_step": r[10] or 0.0} for r in cur.fetchall()}

    def close_trade(self, ticket, info, close_ms, pnl, reason) -> None:
        self.db.execute("INSERT OR REPLACE INTO trades VALUES (?,?,?,?,?,?,?,?,?)",
                        (ticket, self.ts(info["open_ms"]), self.ts(close_ms), info["strategy"],
                         info["side"], info["volume"], info["entry"], pnl, reason))
        self.db.execute("DELETE FROM open_positions WHERE ticket=?", (ticket,))
        self.db.commit()

    def equity(self, eq, bal) -> None:
        self.db.execute("INSERT INTO equity VALUES (?,?,?)", (self.ts(), eq, bal))
        self.db.commit()

    def save_state(self, key: str, value: dict) -> None:
        self.db.execute("INSERT OR REPLACE INTO state VALUES (?,?)", (key, json.dumps(value)))
        self.db.commit()

    def load_state(self, key: str) -> dict | None:
        r = self.db.execute("SELECT value FROM state WHERE key=?", (key,)).fetchone()
        return json.loads(r[0]) if r else None


# --------------------------------------------------------------------------
# Bot
# --------------------------------------------------------------------------
class Bot:
    def __init__(self, cfg: Config, broker, chosen: dict, db: TradeLog):
        self.cfg, self.br, self.db = cfg, broker, db
        self.strategy = chosen["strategy"]
        self.params = chosen["params"]
        self.hold_min = int(self.params.get("hold_min", 30))
        self.filters = TradeFilters(cfg.filters, C.NEWS_FILE)
        self.t = np.array([], dtype="int64")
        self.bid = np.array([], dtype=float)
        self.ask = np.array([], dtype=float)
        self.last_boundary = 0
        self.offset_verified = False
        self.risk: RiskManager | None = None
        self.last_equity_log = 0
        self.flattened_day = -1

    # ---- startup ----
    def start(self) -> None:
        eq = self.br.equity()
        saved = self.db.load_state(f"risk_{self.cfg.symbol}")
        state = RiskState(**saved) if saved else None
        self.risk = RiskManager(self.cfg.risk, eq, self.cfg.server_tz, state)
        if self.risk.state.halted:
            raise SystemExit(f"Kill switch is active ({self.risk.state.halt_reason}). Review the "
                             "logs, then delete the 'risk_*' row in the state table to reset.")
        self.sync_positions()
        start = now_ms() - self.cfg.execution.tick_buffer_hours * 3_600_000
        self.t, self.bid, self.ask = self.br.ticks_range(start, now_ms() + MINUTE_MS)
        self.last_boundary = (now_ms() // MINUTE_MS) * MINUTE_MS
        self.db.event("start", f"strategy={self.strategy} params={json.dumps(self.params)} "
                      f"symbol={self.br.symbol} spec={self.br.spec} warmup_ticks={len(self.t)}")
        log.info("warm-up: %d ticks; strategy %s %s", len(self.t), self.strategy, self.params)

    def sync_positions(self) -> None:
        """Adopt open positions with our magic number after a restart."""
        known = self.db.open_positions()
        live = {p.ticket: p for p in self.br.positions()}
        for ticket, p in live.items():
            if ticket not in known:
                open_utc = int(server_to_utc_ms(np.array([int(p.time_msc)]), self.cfg.server_tz)[0])
                side = 1 if p.type == self.br.mt5.POSITION_TYPE_BUY else -1
                sl_dist = abs(float(p.price_open) - float(p.sl)) if getattr(p, "sl", 0) else 0.0
                self.db.add_open(ticket, open_utc + self.hold_min * MINUTE_MS, self.strategy, side,
                                 float(p.volume), float(p.price_open), open_utc, sl_dist,
                                 self.trail_params())
                self.db.event("sync", f"adopted position {ticket}")
        for ticket in known:
            if ticket not in live:
                self.record_closed(ticket, known[ticket], "closed_while_offline")
        log.info("positions in sync: %d open", len(live))

    # ---- data ----
    def poll_ticks(self) -> None:
        last = int(self.t[-1]) if len(self.t) else now_ms() - 60_000
        t, bid, ask = self.br.ticks_from(last - 1000)
        keep = t > last
        if keep.any():
            self.t = np.r_[self.t, t[keep]]
            self.bid = np.r_[self.bid, bid[keep]]
            self.ask = np.r_[self.ask, ask[keep]]
        cutoff = now_ms() - self.cfg.execution.tick_buffer_hours * 3_600_000
        if len(self.t) and self.t[0] < cutoff:
            j = int(np.searchsorted(self.t, cutoff))
            self.t, self.bid, self.ask = self.t[j:], self.bid[j:], self.ask[j:]

    def verify_offset(self) -> None:
        if self.offset_verified:
            return
        seen = self.br.server_offset_minutes()
        if seen is None:
            return          # stale quotes (market closed); check again later
        want = expected_offset_minutes(self.cfg.server_tz, now_ms())
        if abs(seen - want) > 1:
            raise SystemExit(f"Server time offset is {seen:+.0f} min but SERVER_TZ={self.cfg.server_tz} "
                             f"implies {want:+.0f} min. Fix SERVER_TZ in .env before trading.")
        self.offset_verified = True
        self.db.event("clock", f"server offset verified: {seen:+.0f} min")

    # ---- positions ----
    def trail_params(self) -> tuple[float, float, float]:
        if not self.params.get("trail"):
            return (0.0, 0.0, 0.0)
        return (float(self.params["trail_activate_r"]), float(self.params["trail_lock"]),
                float(self.params["trail_step_r"]))

    def update_trail(self, pos, info: dict) -> None:
        """Move the broker-side SL with the same rule the backtester uses."""
        if info["trail_act"] <= 0 or info["sl_dist"] <= 0:
            return
        m = self.t >= info["open_ms"]
        if not m.any():
            return
        side, entry, sl_d = info["side"], info["entry"], info["sl_dist"]
        best = float(self.bid[m].max()) if side > 0 else float(self.ask[m].min())
        sl0 = entry - side * sl_d
        lvl = float(trail_stop_level(best, entry, sl0, sl_d, side, info["trail_act"],
                                     info["trail_lock"], info["trail_step"]))
        spec = self.br.spec
        cur = float(getattr(pos, "sl", 0.0) or sl0)
        if side * (lvl - cur) <= spec.tick_size / 2:
            return                       # no improvement: never loosen, never spam modifies
        tick = self.br.latest_tick()
        if tick is None:
            return
        _, bid, ask = tick
        min_gap = max(spec.stops_level, spec.freeze_level) * spec.point
        if (side > 0 and lvl > bid - min_gap) or (side < 0 and lvl < ask + min_gap):
            return                       # too close to price for the broker; try next loop
        if self.br.modify_sltp(pos, lvl, float(getattr(pos, "tp", 0.0))):
            self.db.event("trail", f"ticket {pos.ticket} SL {cur:.5f} -> {lvl:.5f}")
            log.info("trail %s SL -> %.5f", pos.ticket, lvl)

    def record_closed(self, ticket: int, info: dict, reason: str) -> None:
        res = self.br.closed_position_pnl(ticket)
        pnl, close_ms = res if res else (0.0, now_ms())
        self.db.close_trade(ticket, info, close_ms, pnl, reason)
        self.risk.on_close(close_ms, pnl, self.br.equity())
        self.save_risk()
        log.info("position %s closed (%s) pnl=%.2f", ticket, reason, pnl)

    def manage_positions(self) -> None:
        known = self.db.open_positions()
        live = {p.ticket: p for p in self.br.positions()}
        t_now = now_ms()
        for ticket, info in known.items():
            if ticket not in live:
                self.record_closed(ticket, info, "sl_tp_or_manual")
            elif t_now >= info["deadline_ms"]:
                res = self.br.close_position(live[ticket], "time stop")
                self.db.order("close_time_stop", res, -info["side"])
                if res.ok:
                    self.record_closed(ticket, info, "time_stop")
                else:
                    log.error("time-stop close failed retcode=%s %s", res.retcode, res.comment)
            else:
                self.update_trail(live[ticket], info)

    def flatten(self, why: str) -> None:
        for p in self.br.positions():
            res = self.br.close_position(p, why[:20])
            self.db.order("close_" + why[:12], res, 0)
        self.db.event("flatten", why)
        known = self.db.open_positions()
        live = {p.ticket for p in self.br.positions()}
        for ticket, info in known.items():
            if ticket not in live:
                self.record_closed(ticket, info, why)

    def save_risk(self) -> None:
        self.db.save_state(f"risk_{self.cfg.symbol}", self.risk.to_dict())

    def check_risk(self) -> bool:
        """False when the bot must stop."""
        eq = self.br.equity()
        self.risk.update_equity(now_ms(), eq)
        if now_ms() - self.last_equity_log > 60_000:
            self.db.equity(eq, self.br.balance())
            self.last_equity_log = now_ms()
            self.save_risk()
        if self.risk.state.halted:
            self.flatten("kill_switch")
            self.save_risk()
            log.critical("KILL SWITCH: %s. Positions closed, bot stopping.", self.risk.state.halt_reason)
            return False
        if self.risk.daily_loss_hit(eq) and self.flattened_day != self.risk.state.day_key:
            self.flatten("max_daily_loss")
            self.flattened_day = self.risk.state.day_key
            log.warning("max daily loss hit: flat until the next server day")
        return True

    # ---- signals ----
    def on_bar_close(self, boundary: int) -> None:
        m = self.t < boundary
        if m.sum() < 100 or boundary - int(self.t[m][-1]) > 2 * MINUTE_MS:
            return                       # no fresh data (market closed / weekend)
        bars = build_bars(self.t[m], self.bid[m], self.ask[m], self.cfg.filters.spread_median_bars)
        sigs = [s for s in generate(self.strategy, bars, self.params, self.cfg.server_tz)
                if s.time_ms == boundary]
        for s in sigs:
            self.try_enter(s, bars)

    def try_enter(self, s, bars) -> None:
        tick = self.br.latest_tick()
        if tick is None:
            self.db.signal(s, None, None, "skip", "no_tick")
            return
        _, bid, ask = tick
        spread, ref = ask - bid, float(bars.spread_ref[s.bar_idx])
        reason = self.filters.check(s.time_ms, spread, ref)
        if not reason:
            reason = self.risk.can_open(now_ms(), self.br.equity(), len(self.br.positions()))
        if reason:
            self.db.signal(s, spread, ref, "skip", reason)
            log.info("signal %s %+d skipped: %s", s.strategy, s.side, reason)
            return
        spec = self.br.spec
        sl_d, tp_d = apply_min_stop(s.sl_dist, s.tp_dist, spec.stops_level, spec.point, spread)
        lots = lot_size(self.br.equity(), self.cfg.risk.risk_per_trade_pct, sl_d, spec,
                        self.cfg.commission())
        if lots <= 0:
            self.db.signal(s, spread, ref, "skip", "below_min_volume")
            return
        self.db.signal(s, spread, ref, "enter")
        res = self.br.open_market(s.side, lots, sl_d, tp_d, f"{s.strategy} {s.note}")
        self.db.order("open", res, s.side, res.fill_price - s.side * sl_d if res.ok else None,
                      res.fill_price + s.side * tp_d if res.ok else None, s.time_ms)
        if not res.ok:
            log.error("open failed retcode=%s %s", res.retcode, res.comment)
            return
        t_open = now_ms()
        self.db.add_open(res.ticket, t_open + s.hold_min * MINUTE_MS, s.strategy, s.side, lots,
                         res.fill_price, t_open, sl_d,
                         (s.trail_activate_r, s.trail_lock, s.trail_step_r))
        self.risk.on_open(t_open, self.br.equity())
        self.save_risk()
        log.info("OPEN %s %+d %.2f lots @ %.5f (req %.5f, slip %.1f pt, send %.0f ms, "
                 "signal->fill %.0f ms)", s.strategy, s.side, lots, res.fill_price,
                 res.requested_price, res.slippage_points, res.latency_ms, t_open - s.time_ms)

    # ---- main loop ----
    def run(self, max_loops: int | None = None) -> None:
        loops = 0
        interval = self.cfg.execution.loop_interval_ms / 1000.0
        while max_loops is None or loops < max_loops:
            loops += 1
            try:
                self.br.ensure_connected()
                self.verify_offset()
                self.poll_ticks()
                self.manage_positions()
                if not self.check_risk():
                    return
                boundary = (now_ms() // MINUTE_MS) * MINUTE_MS
                if boundary > self.last_boundary and now_ms() - boundary >= 300:
                    self.last_boundary = boundary
                    if self.offset_verified:
                        self.on_bar_close(boundary)
            except SystemExit:
                raise
            except Exception as exc:  # keep running; every failure is logged
                log.exception("loop error: %s", exc)
                self.db.event("error", repr(exc))
                time.sleep(2.0)
            time.sleep(interval)


def setup_logging() -> None:
    C.LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s",
                        handlers=[logging.FileHandler(C.LOG_DIR / "bot.log", encoding="utf-8"),
                                  logging.StreamHandler(sys.stdout)])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--live", action="store_true", help="allow a real account (asks for confirmation)")
    ap.add_argument("--allow-failed-gates", action="store_true",
                    help="demo only: run a chosen strategy that failed a go-live gate")
    args = ap.parse_args(argv)
    setup_logging()
    cfg = load_config()
    from broker import MT5Broker
    br = MT5Broker(cfg)
    br.connect()
    mode = br.account_mode()
    if not live_guard(mode, args.live, br.account_login()):
        br.shutdown()
        return 2
    chosen = load_chosen()
    why = strategy_guard(chosen, cfg.symbol, mode, args.allow_failed_gates)
    if why:
        print("REFUSED:", why)
        br.shutdown()
        return 2
    if not chosen.get("passed_gates"):
        log.warning("Running a strategy that FAILED the go-live gates (demo forward test only).")
    br.resolve_symbol(cfg.symbol)
    br.symbol_spec()
    db = TradeLog(C.TRADE_DB)
    bot = Bot(cfg, br, chosen, db)
    bot.start()
    try:
        bot.run()
    except KeyboardInterrupt:
        log.info("stopped by user (open positions keep their broker-side SL/TP)")
    finally:
        bot.save_risk()
        br.shutdown()
    return 0


if __name__ == "__main__":
    from broker import BrokerError
    try:
        sys.exit(main())
    except BrokerError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
