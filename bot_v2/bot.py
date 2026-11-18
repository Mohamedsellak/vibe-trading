"""bot_v2: live MT5 trading loop. Run:  python bot.py

Keys while running: r = print session report.  Ctrl+C = stop (asks before closing trades).
Kill switch: create a file named STOP in this folder -> closes all bot trades and exits.
"""
from __future__ import annotations

import os
import re
import sys
import time
from dataclasses import dataclass

import config
import display
import risk
import strategy as st
from broker import Broker
from report import Journal, build_report

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_SPREAD_SAMPLES = 10      # seconds of spread history before the first entry


@dataclass
class TradeMeta:
    ticket: int
    side: str
    kind: str                # base / add / flip / adopted
    basket: int
    volume: float
    open_price: float
    open_time: float
    unit: float              # ATR frozen at open (price); all exit distances are in this unit
    peak: float = -1e9       # best PnL seen, in ATR
    adverse_since: float | None = None
    sl: float = 0.0
    tp: float = 0.0
    lock_sl: bool = False    # broker SL moved into profit by the trailing stop
    last_modify: float = 0.0
    missing: int = 0         # loops the position was gone without close history


@dataclass
class Ctx:
    """Account-wide numbers shared by all symbols during one loop."""
    total_open: int
    total_lots: float
    max_total: int
    max_lots: float
    halted: bool = False
    halt_reason: str = ""


class SymbolTrader:
    def __init__(self, base, name, cfg, broker, journal, news, offset_h):
        self.base, self.name, self.cfg = base, name, cfg
        self.b, self.j, self.news = broker, journal, news
        self.offset_s = offset_h * 3600
        self.spec = broker.spec(name)
        self.lot = risk.lot_size(self.spec, cfg["lot"])
        self.ms = st.MarketState(cfg["dir_lookback_s"], cfg["spread_window_s"])
        self.flips = risk.FlipGuard(cfg["flip_cooldown_s"], cfg["max_flips_per_hour"])
        self.trades: dict[int, TradeMeta] = {}
        self.live = {}
        self.bars, self._bars_t = [], -1e9
        self.direction = self.trend = st.FLAT
        self.chop = (True, "warming up")
        self.atr = 0.0               # ATR of finished 1-minute bars (price)
        self.block_time = {}         # why no entry: seconds per reason (for the report)
        self._last_step_t = None
        self.status = "starting"
        self.paused_until = self.market_closed_until = self.no_money_until = 0.0
        self._acct, self._acct_t = None, -1e9
        self.pending_flip_from = None
        self.last_stop = (None, -1e9)    # (side, time) of the last stop loss
        self.last_entry = -1e9
        self.basket = 0
        self.floating = self.worst_floating = self.realized_today = 0.0
        self.ctx, self.now = None, 0.0
        self._last_signal = None
        # Trades the journal says are open: adopted if still live, reconciled if closed meanwhile.
        for r in journal.open_rows(name):
            self.trades[r["ticket"]] = TradeMeta(r["ticket"], r["side"], r["kind"], r["basket"],
                                                 r["volume"], r["open_price"], r["open_time"], r["unit"] or 0.0)
            self.basket = max(self.basket, r["basket"] or 0)

    # ---------------- main step ----------------
    def step(self, now, ctx, positions):
        self.ctx, self.now = ctx, now
        cfg, ms = self.cfg, self.ms
        tick = self.b.tick(self.name)
        if tick is None:
            self.status = "no price (market closed or disconnected)"
            return
        ms.update(now, tick.bid, tick.ask)
        if now - self._bars_t >= 1.0:          # 1-minute bars change slowly: read them once per second
            n = max(3 * cfg["trend_slow"], cfg["chop_bars"], cfg["atr_period"] + 2) + 1
            self.bars = self.b.rates_m1(self.name, n)
            self._bars_t = now
            self.atr = st.atr(self.bars[:-1], cfg["atr_period"])     # finished bars only
            closes = [c for _, _, c in self.bars]
            self.trend = st.trend(closes, self.atr, cfg["trend_fast"], cfg["trend_slow"],
                                  cfg["trend_deadband_atr"])
            self.chop = st.choppy(self.bars, cfg["chop_bars"], cfg["chop_min_straightness"])
        unit = self.atr                        # 0 until enough bars: then no entries and no exits by ATR
        self.direction = st.direction(ms.move(now), self.atr, cfg["dir_min_move_atr"])
        sig = (self.direction, self.trend, self.chop[0])
        if sig != self._last_signal:
            self.j.event(self.name, "signal", f"direction {self.direction}, trend {self.trend}"
                         f"{', ' + self.chop[1] if self.chop[0] else ''}", show=False)
            self._last_signal = sig

        self._sync(positions, now, unit)
        self.floating = sum(p.profit + p.swap for p in self.live.values())
        self.worst_floating = min(self.worst_floating, self.floating)
        if self.live and self.floating <= -cfg["basket_stop_money"]:
            self.j.event(self.name, "warn", f"BASKET STOP: floating {self.floating:.2f} "
                         f"<= -{cfg['basket_stop_money']}; closing all, pause {cfg['basket_cooldown_s']}s")
            self.close_all("basket stop", now)
            self.paused_until = now + cfg["basket_cooldown_s"]
            self._set_status(f"cooldown after basket stop ({cfg['basket_cooldown_s']}s)")
            self._count_block(now, "cooldown after basket stop")
            return

        self._manage(now, tick)
        block = ctx.halt_reason if ctx.halted else self._entries(now, tick, unit, ctx)
        self._set_status(block)
        self._count_block(now, block)

    def _count_block(self, now, block):
        """Add the time since the last step to the current entry-block reason (numbers stripped)."""
        if self._last_step_t is not None:
            dt = min(now - self._last_step_t, 2.0)
            key = re.sub(r"\s*\(.*\)|:.*", "", block).strip() if block else (
                "in trade" if self.trades else "free to enter")
            self.block_time[key] = self.block_time.get(key, 0.0) + dt
        self._last_step_t = now

    def _set_status(self, block):
        if self.trades:
            n = {}
            for m in self.trades.values():
                n[m.side] = n.get(m.side, 0) + 1
            s = "in trade: " + ", ".join(f"{v} {k}" for k, v in n.items())
            self.status = s + (f" | {block}" if block else "")
        else:
            self.status = block or "ready"

    # ---------------- positions ----------------
    def _sync(self, positions, now, unit):
        self.live = {p.ticket: p for p in positions}
        for ticket, m in list(self.trades.items()):
            if ticket in self.live:
                m.sl, m.tp = self.live[ticket].sl, self.live[ticket].tp
                if not m.unit and unit > 0:
                    m.unit = unit
            else:
                self._resolve_missing(m, now)
        for ticket, p in self.live.items():
            if ticket not in self.trades:
                self._adopt(p, unit, now)

    def _adopt(self, p, unit, now):
        side = st.BUY if p.type == self.b.mt5.POSITION_TYPE_BUY else st.SELL
        row = self.j.row(p.ticket)
        if row:
            kind, basket, u = row["kind"], row["basket"], row["unit"] or unit
        else:
            kind, u = "adopted", unit
            basket = self.basket if self.trades else self.j.next_basket()
            self.j.open_trade(ticket=p.ticket, symbol=self.name, side=side, kind=kind, basket=basket,
                              volume=p.volume, open_time=now, open_price=p.price_open, unit=u,
                              spread_open=0.0, spread_cost=0.0, sl=p.sl, version=config.VERSION)
        self.basket = basket
        m = TradeMeta(p.ticket, side, kind, basket, p.volume, p.price_open, now, u, sl=p.sl, tp=p.tp)
        self.trades[p.ticket] = m
        self.j.event(self.name, "info", f"adopted #{p.ticket} {side} {p.volume} @ {p.price_open}")

    def _deal_pnl(self, deals):
        return sum(d.profit + d.swap + d.commission + getattr(d, "fee", 0.0) for d in deals)

    def _resolve_missing(self, m, now):
        """A trade we track is gone: the broker closed it (stop) or someone closed it by hand."""
        mt5 = self.b.mt5
        deals, out = self.b.closing_deals(m.ticket)
        if not out:
            if self.b.still_open(m.ticket):    # a glitch in the position list, not a close
                m.missing = 0
                return
            m.missing += 1
            if m.missing < 600:                # about 60 s of no history before giving up
                return
            self._record_close(m, now, 0.0, "closed outside bot (no history)", 0.0, None, None)
            return
        d = out[-1]
        if d.reason == mt5.DEAL_REASON_SL:
            reason = "trailing stop (broker SL)" if (m.lock_sl or self._locked(m)) else "stop loss"
        elif d.reason == mt5.DEAL_REASON_TP:
            reason = "target (broker TP)"
        elif d.reason == mt5.DEAL_REASON_SO:
            reason = "stop out"
        else:
            reason = "closed outside bot"
        self._record_close(m, now, d.price, reason, self._deal_pnl(deals), None, None)
        if reason == "stop loss":
            self.pending_flip_from = m.side
            self.last_stop = (m.side, now)

    def _record_close(self, m, now, price, reason, pnl, slip, latency, was_live=False):
        pts = 0.0
        if price:
            pts = ((price - m.open_price) if m.side == st.BUY else (m.open_price - price)) / self.spec.point
        self.j.close_trade(m.ticket, close_time=now, close_price=price, close_reason=reason,
                           close_slip_pts=slip, close_latency_ms=latency, pnl=pnl, pnl_points=pts,
                           peak_units=m.peak if m.peak > -1e8 else None)
        self.trades.pop(m.ticket, None)
        self.live.pop(m.ticket, None)
        if was_live and self.ctx:
            self.ctx.total_open -= 1
            self.ctx.total_lots -= m.volume
        self.realized_today += pnl
        extra = f", slip {slip:+.0f} pts, {latency:.0f} ms" if latency is not None else ""
        self.j.event(self.name, "close", f"CLOSED #{m.ticket} {m.side} {m.kind} by {reason}: "
                     f"{pnl:+.2f} ({pts:+.0f} pts){extra}")

    def _close(self, m, reason, now):
        pos = self.live.get(m.ticket)
        if pos is None:
            return False
        dev = risk.deviation_points(self.spec, self.ms.median_spread(), self.cfg["deviation_spreads"])
        res = self.b.close(self.spec, pos, dev, f"v2 {reason}")
        if res.gone:          # the broker's own stop or target closed it first: logged on the next loop
            return False
        if not res.ok:
            if res.market_closed:
                self.market_closed_until = now + 60
            self.j.event(self.name, "error", f"close #{m.ticket} ({reason}) failed: {res.message}")
            return False
        deals, out = self.b.closing_deals(m.ticket, tries=5)
        if out:
            price, pnl = out[-1].price, self._deal_pnl(deals)
        else:   # history not there yet: estimate from prices
            price = res.price
            diff = (price - m.open_price) if m.side == st.BUY else (m.open_price - price)
            pnl = diff * self.spec.money_per_price(m.volume)
        slip = ((res.req_price - res.price) if m.side == st.BUY else (res.price - res.req_price)) / self.spec.point
        self._record_close(m, now, price, reason, pnl, slip, res.latency_ms, was_live=True)
        return True

    def close_all(self, reason, now):
        for m in list(self.trades.values()):
            self._close(m, reason, now)

    # ---------------- exits ----------------
    def _manage(self, now, tick):
        for m in list(self.trades.values()):
            if m.ticket not in self.live or not m.unit:
                continue
            u = st.pnl_units(m.side, m.open_price, tick.bid, tick.ask, m.unit)
            m.peak = max(m.peak, u)
            reason = st.exit_reason(u, m.peak, now - m.open_time, self.cfg,
                                    broker_tp=m.tp > 0, broker_trail=self._locked(m))
            if reason:
                self._close(m, reason, now)
                continue
            self._trail_sl(m, tick, now)

    @staticmethod
    def _locked(m):
        return st.is_locked(m.side, m.open_price, m.sl)

    def _trail_sl(self, m, tick, now):
        """Move the broker SL behind the best price, so the profit is protected at the broker too."""
        lock_u = st.trail_level(m.peak, self.cfg)
        if lock_u is None or now - m.last_modify < 0.5:
            return
        sp = self.spec
        gap = (sp.stops_level + sp.freeze_level + 1) * sp.point
        step = 0.1 * m.unit
        if m.side == st.BUY:
            sl = sp.round_price(m.open_price + lock_u * m.unit)
            if sl > tick.bid - gap or sl <= m.sl + step:
                return
        else:
            sl = sp.round_price(m.open_price - lock_u * m.unit)
            if sl < tick.ask + gap or (m.sl and sl >= m.sl - step):
                return
        m.last_modify = now
        if self.b.modify_sl(self.live[m.ticket], sl):
            m.sl, m.lock_sl = sl, True
            self.j.event(self.name, "info", f"#{m.ticket} broker SL moved to {sl} (locks profit)", show=False)

    # ---------------- entries ----------------
    def _entry_block(self, now, ctx):
        cfg, ms = self.cfg, self.ms
        if now < self.paused_until:
            return f"cooldown after basket stop ({self.paused_until - now:.0f}s)"
        if now < self.market_closed_until:
            return "market closed"
        if now < self.no_money_until:
            return f"not enough free margin: paused ({self.no_money_until - now:.0f}s)"
        if not risk.in_session(cfg["sessions"], now + self.offset_s):
            return "outside session"
        title = self.news.active(now, (self.spec.currency_base, self.spec.currency_profit))
        if title:
            return f"news pause: {title}"
        if ms.move(now) is None or len(ms.spreads) < MIN_SPREAD_SAMPLES or self.atr <= 0:
            return "warming up"
        sb = risk.spread_block(ms.spread, ms.median_spread(), cfg["target_atr"] * self.atr, cfg)
        if sb:
            return sb
        if self.chop[0]:
            return self.chop[1]
        if self.direction == st.FLAT:
            return "waiting for direction"
        if self.trend != self.direction:
            return f"trend disagrees (direction {self.direction}, trend {self.trend})"
        if now - self.last_entry < cfg["entry_gap_s"]:
            return "short pause between entries"
        return risk.limit_block(len(self.trades), ctx.total_open, ctx.total_lots, self.lot, cfg,
                                ctx.max_total, ctx.max_lots)

    def _entries(self, now, tick, unit, ctx):
        block = self._entry_block(now, ctx)
        if block:
            return block
        want = st.side_of(self.direction)
        if any(m.side != want for m in self.trades.values()):
            return "opposite trades still open: waiting for their exit"   # no hedging against ourselves
        mine = [m for m in self.trades.values() if m.side == want]
        stop_side, stop_t = self.last_stop
        if want == stop_side and now - stop_t < self.cfg["dir_lookback_s"]:
            # the direction window still holds the move that just failed: wait for a fresh one
            return "fresh signal needed after stop loss"
        if not mine:
            kind = "base"
            if self.pending_flip_from and want != self.pending_flip_from:
                ok, why = self.flips.allowed(now)
                if not ok:
                    return why
                kind = "flip"
            sl_dist, why = self._stop_plan(want, kind, unit, tick, mine, now)
            if why:
                return why
            self._open(want, kind, unit, tick, now, sl_dist)
            return None
        adds = sum(1 for m in mine if m.kind == "add")
        if adds >= self.cfg["max_adds"]:
            return "max adds reached"
        if not st.should_add([self._locked(m) for m in mine], adds, self.cfg):
            return "add waits until all stops lock profit"
        sl_dist, why = self._stop_plan(want, "add", unit, tick, mine, now)
        if why:
            return why
        self._open(want, "add", unit, tick, now, sl_dist)
        return None

    def _account(self, now):
        """Account info, read at most once per second."""
        if now - self._acct_t >= 1.0:
            self._acct, self._acct_t = self.b.account(), now
        return self._acct

    def _stop_plan(self, side, kind, unit, tick, mine, now):
        """Stop distance (price) for a new trade, or the reason it cannot open now.
        An add shares the basket's locked stop: if the move ends, the whole basket leaves together."""
        sp, cfg = self.spec, self.cfg
        price = tick.ask if side == st.BUY else tick.bid
        dist = cfg["stop_atr"] * unit
        if kind == "add":
            stops = [m.sl for m in mine if m.sl]
            best = max(stops) if side == st.BUY else min(stops)
            room = (price - best) if side == st.BUY else (best - price)
            if room < cfg["add_min_room_atr"] * unit:
                return None, "add waits: price too close to the basket stop"
            dist = min(dist, room)
        sl_dist = risk.stop_distance(sp, dist, tick.ask - tick.bid)
        acct = self._account(now)
        if acct is not None:
            loss = sl_dist * sp.money_per_price(self.lot)
            if config.MAX_RISK_PCT > 0 and loss > config.MAX_RISK_PCT / 100 * acct.equity:
                return None, (f"stop too big for this account (one stop = {loss:.2f}, "
                              f"over {config.MAX_RISK_PCT}% of equity {acct.equity:.2f})")
            need = self.b.margin_needed(sp, side, self.lot, price)
            if need is not None and need > acct.margin_free:
                return None, f"not enough free margin (need {need:.2f}, free {acct.margin_free:.2f})"
        return sl_dist, None

    def _open(self, side, kind, unit, tick, now, sl_dist):
        sp, cfg = self.spec, self.cfg
        spread = tick.ask - tick.bid
        tp_dist = risk.stop_distance(sp, cfg["target_atr"] * unit, spread)
        dev = risk.deviation_points(sp, self.ms.median_spread(), cfg["deviation_spreads"])
        self.last_entry = now
        res = self.b.market_order(sp, side, self.lot, sl_dist, tp_dist, dev, f"v2 {kind}")   # order first, log after
        self.j.event(self.name, "signal", f"entry signal {side} ({kind}): direction {self.direction}, "
                     f"trend {self.trend}, spread {spread / sp.point:.0f} pts, ATR {unit / sp.point:.0f} pts",
                     show=False)
        if not res.ok:
            if res.market_closed:
                self.market_closed_until = now + 60
            if res.no_money:
                self.no_money_until = now + config.NO_MONEY_PAUSE_S
                self.j.event(self.name, "error", f"open {side} ({kind}) failed: not enough free margin. "
                             f"No entries on this symbol for {config.NO_MONEY_PAUSE_S} s.")
                return False
            self.j.event(self.name, "error", f"open {side} ({kind}) failed: {res.message}")
            return False
        if not self.trades:
            self.basket = self.j.next_basket()
        slip = ((res.price - res.req_price) if side == st.BUY else (res.req_price - res.price)) / sp.point
        sgn = 1 if side == st.BUY else -1
        sl = res.sl or sp.round_price(res.price - sgn * sl_dist)
        tp = res.tp or sp.round_price(res.price + sgn * tp_dist)
        m = TradeMeta(res.ticket, side, kind, self.basket, self.lot, res.price, now, unit, sl=sl, tp=tp)
        self.trades[res.ticket] = m
        self.j.open_trade(ticket=res.ticket, symbol=self.name, side=side, kind=kind, basket=self.basket,
                          volume=self.lot, open_time=now, open_price=res.price, req_open_price=res.req_price,
                          open_slip_pts=slip, open_latency_ms=res.latency_ms, spread_open=spread,
                          spread_cost=spread * sp.money_per_price(self.lot), unit=unit, sl=sl, tp=tp,
                          version=config.VERSION)
        if self.ctx:
            self.ctx.total_open += 1
            self.ctx.total_lots += self.lot
        if kind == "flip":
            self.flips.record(now)
        self.pending_flip_from = None
        label = {"base": "OPENED", "add": "PYRAMID ADD", "flip": "FLIPPED to"}[kind]
        self.j.event(self.name, "add" if kind == "add" else "flip" if kind == "flip" else "open",
                     f"{label} {side} {self.lot} @ {res.price:.{sp.digits}f} | stop {sl_dist / sp.point:.0f} pts"
                     f" | target {tp_dist / sp.point:.0f} pts | slip {slip:+.0f} pts | {res.latency_ms:.0f} ms")
        return True


class Bot:
    def __init__(self, broker, journal, traders, max_total, max_lots, daily_loss_limit, offset_h):
        self.b, self.j, self.traders = broker, journal, traders
        self.max_total, self.max_lots = max_total, max_lots
        self.daily_loss_limit = daily_loss_limit
        self.offset_s = offset_h * 3600
        self.halted, self.halt_reason = False, ""
        self.conn_status = ""
        self._realized_t = -1e9
        self._halted_on = 0.0
        self._errors = {}

    def day_start(self, now):
        """Start of today in SERVER time, as a normal UTC epoch."""
        server = now + self.offset_s
        return server - server % 86400 - self.offset_s

    def loop_once(self, now):
        positions = self.b.positions()
        if positions is None:                  # MT5 did not answer: skip this loop, decide nothing
            self.conn_status = "MT5 did not return positions - retrying"
            return
        by_sym = {}
        for p in positions:
            by_sym.setdefault(p.symbol, []).append(p)
        ctx = Ctx(len(positions), sum(p.volume for p in positions), self.max_total, self.max_lots,
                  self.halted, self.halt_reason)
        if now - self._realized_t >= 5:
            start = self.day_start(now)
            for tr in self.traders:
                tr.realized_today = self.j.realized_since(tr.name, start)
            self._realized_t = now
        for tr in self.traders:
            try:
                tr.step(now, ctx, by_sym.get(tr.name, []))
                self._errors.pop(tr.name, None)
            except Exception as e:   # one symbol's problem must not stop the others
                msg = f"{type(e).__name__}: {e}"
                tr.status = f"error: {msg}"
                if self._errors.get(tr.name) != msg:
                    self.j.event(tr.name, "error", msg)
                    self._errors[tr.name] = msg
        if self.daily_loss_limit > 0 and not self.halted:
            day = sum(tr.realized_today + tr.floating for tr in self.traders)
            if day <= -self.daily_loss_limit:
                self.halted, self.halt_reason = True, f"daily loss limit hit ({day:.2f}): no more entries today"
                self._halted_on = self.day_start(now)
                self.j.event(None, "warn", self.halt_reason + "; closing all trades")
                self.close_everything("daily loss limit", now)
        if self.halted and self.day_start(now) > self._halted_on:   # new server day: trade again
            self.halted, self.halt_reason = False, ""
            self.j.event(None, "info", "new day: daily loss limit reset")

    def close_everything(self, reason, now):
        """Close every bot trade on every symbol. Returns how many are still open."""
        for tr in self.traders:
            ps = self.b.positions(tr.name)
            if ps is not None:
                tr._sync(ps, now, tr.atr)
            tr.close_all(reason, now)
        left = self.b.positions()
        return len(left) if left is not None else -1


# ---------------- startup / shutdown ----------------
def stop_preview(tr, equity):
    """One line at startup: how much one stop costs right now, and if the risk cap allows it."""
    cfg, sp = tr.cfg, tr.spec
    bars = tr.b.rates_m1(tr.name, cfg["atr_period"] + 3)
    atr = st.atr(bars[:-1], cfg["atr_period"])
    if atr <= 0 or not equity:
        return f"{tr.name}: one stop = unknown yet (no ATR)", True
    loss = cfg["stop_atr"] * atr * sp.money_per_price(tr.lot)
    pct = 100 * loss / equity
    ok = config.MAX_RISK_PCT <= 0 or pct <= config.MAX_RISK_PCT
    verdict = "ok" if ok else f"over the {config.MAX_RISK_PCT}% cap: this symbol will NOT trade on this balance"
    return f"{tr.name}: one stop now = {loss:.2f} ({pct:.1f}% of equity {equity:.2f}) - {verdict}", ok



def check_server_offset(broker, traders, journal, console):
    newest = max((t.time for t in (broker.tick(tr.name) for tr in traders) if t), default=None)
    if newest is None:
        return
    seen = (newest - time.time()) / 3600
    if abs(seen) < 15 and abs(seen - config.SERVER_UTC_OFFSET_HOURS) > 0.6:
        msg = (f"server clock looks like UTC{round(seen):+d} but config says "
               f"UTC{config.SERVER_UTC_OFFSET_HOURS:+d}. Check SERVER_UTC_OFFSET_HOURS.")
        console.print(f"[yellow]{msg}[/]")
        journal.event(None, "warn", msg)


def main():
    os.chdir(HERE)
    console = display.make_console()
    if os.path.exists(config.STOP_FILE):
        console.print("[bold yellow]A STOP file is in this folder. Delete it, then start again.[/]")
        return 1
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(HERE, ".env"))
    except ImportError:
        pass
    try:
        import MetaTrader5 as mt5
    except ImportError:
        console.print("[red]MetaTrader5 package not found. On Windows run: pip install -r requirements.txt[/]")
        return 1

    journal = Journal(config.DB_FILE, config.LOG_DIR)
    broker = Broker(mt5, config.MAGIC, log=lambda msg: journal.event(None, "warn", msg),
                    retries=config.ORDER_RETRIES)
    if not broker.connect(os.getenv("MT5_LOGIN"), os.getenv("MT5_PASSWORD"),
                          os.getenv("MT5_SERVER"), os.getenv("MT5_PATH")):
        console.print(f"[red]Cannot connect to MetaTrader 5 ({mt5.last_error()}). "
                      "Is the terminal open and logged in?[/]")
        return 1
    acct, term = broker.account(), broker.terminal()
    real = acct.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO     # contest accounts count as REAL, to be safe
    display.banner(console, acct, real)
    journal.event(None, "info", f"start: {'REAL' if real else 'DEMO'} account {acct.login} on {acct.server}")
    if real and not display.confirm_real(console):
        console.print("Not confirmed. Nothing was traded.")
        mt5.shutdown()
        return 0
    if acct.margin_mode != mt5.ACCOUNT_MARGIN_MODE_RETAIL_HEDGING:
        console.print("[red]This account is not HEDGING. bot_v2 needs a hedging account. Exiting.[/]")
        mt5.shutdown()
        return 1
    if not term.trade_allowed:
        console.print("[red]'Algo Trading' is switched off in MetaTrader 5. Turn it on and restart.[/]")
        mt5.shutdown()
        return 1

    news = risk.NewsCalendar.load(config.NEWS_FILE)
    console.print(f"news blackout events loaded: {len(news.events)}")
    traders = []
    for base in config.SYMBOLS:
        name = broker.resolve(base)
        if not name:
            console.print(f"[yellow]{base}: not found at this broker, skipped[/]")
            journal.event(None, "warn", f"{base} not found, skipped")
            continue
        journal.add_symbol(name)
        tr = SymbolTrader(base, name, config.symbol_config(base), broker, journal, news,
                          config.SERVER_UTC_OFFSET_HOURS)
        s = tr.spec
        console.print(f"{base} -> [bold]{name}[/]: lot {tr.lot} (min {s.vol_min}, step {s.vol_step}), "
                      f"contract {s.contract_size}, point {s.point}, stops level {s.stops_level} pts")
        journal.event(name, "info", f"symbol {name}: lot {tr.lot}, point {s.point}, tick value {s.tick_value}, "
                      f"contract {s.contract_size}, stops level {s.stops_level}, filling {s.filling_mode}", show=False)
        traders.append(tr)
    if not traders:
        console.print("[red]No symbols available. Exiting.[/]")
        mt5.shutdown()
        return 1
    for tr in traders:
        line, ok = stop_preview(tr, acct.equity)
        console.print(line if ok else f"[bold yellow]{line}[/]")
        journal.event(tr.name, "info" if ok else "warn", line, show=False)
    check_server_offset(broker, traders, journal, console)
    bot = Bot(broker, journal, traders, config.MAX_TRADES_TOTAL, config.MAX_TOTAL_LOTS,
              config.DAILY_LOSS_LIMIT, config.SERVER_UTC_OFFSET_HOURS)
    bot.account, bot.real = acct, real
    run(bot, console)
    mt5.shutdown()
    return 0


def print_report(bot, console):
    lines = build_report(bot.j, {tr.name: tr.worst_floating for tr in bot.traders},
                         getattr(getattr(bot, "account", None), "currency", ""),
                         {tr.name: tr.block_time for tr in bot.traders})
    for line in lines:
        console.print(line)
    bot.j.log.info("report\n" + "\n".join(display.plain(x) for x in lines))


def run(bot, console):
    j = bot.j
    j.event(None, "info", "bot running")
    wait, next_try, next_check, next_screen = 1, 0.0, 0.0, 0.0
    connected, how = True, "ctrl+c"
    try:
        with display.live(console) as live:
            while True:
                now = time.time()
                if os.path.exists(config.STOP_FILE):
                    j.event(None, "warn", "STOP file found: closing all bot trades and exiting")
                    for _ in range(3):
                        if bot.close_everything("kill switch", now) == 0:
                            break
                        time.sleep(1)
                    how = "kill switch"
                    break
                if now >= next_check:
                    connected, next_check = bot.b.connected(), now + 1
                if connected:
                    bot.conn_status = ""
                    bot.loop_once(now)
                    wait = 1
                elif now >= next_try:
                    if bot.b.reconnect():
                        connected, bot.conn_status = True, ""
                        j.event(None, "info", "reconnected")
                    else:
                        bot.conn_status = f"DISCONNECTED - next retry in {wait}s"
                        j.event(None, "warn", bot.conn_status)
                        next_try, wait = now + wait, min(wait * 2, config.RECONNECT_MAX_S)
                j.flush()
                if display.read_key() == "r":
                    print_report(bot, live.console)
                if now >= next_screen:
                    live.update(display.render(bot), refresh=True)
                    next_screen = now + config.SCREEN_REFRESH_S
                time.sleep(max(0.0, config.LOOP_MS / 1000 - (time.time() - now)))
    except KeyboardInterrupt:
        how = "ctrl+c"
    if how == "ctrl+c":
        left = bot.b.positions() or []
        if left:
            try:
                answer = input(f"\n{len(left)} bot trade(s) still open. Close them all now? (y/N): ")
            except (KeyboardInterrupt, EOFError):
                answer = ""
            if answer.strip().lower() == "y":
                left = bot.close_everything("manual stop", time.time())
                console.print(f"closed. still open: {left}")
            else:
                console.print("[yellow]Trades left open, each with its broker stop loss. "
                              "Restart the bot to manage them again.[/]")
    j.event(None, "info", f"bot stopped ({how})")
    print_report(bot, console)
    j.flush(force=True)


if __name__ == "__main__":
    sys.exit(main())
