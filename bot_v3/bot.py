"""bot_v3: high-frequency gold swarm scalper for MetaTrader 5.   Run:  python bot.py

Keys while running: r = report.  Ctrl+C = stop (asks before closing trades).
Kill switch: create a file named STOP in this folder -> closes all bot trades and exits.
"""
from __future__ import annotations

import os
import re
import sys
import time
from collections import deque
from dataclasses import dataclass

import config as default_config
import display
import risk
import strategy as st
from broker import Broker, LockedMT5, ProcessExecutor, ThreadExecutor, new_cmd
from report import Journal, build_report

HERE = os.path.dirname(os.path.abspath(__file__))
INF = float("inf")


@dataclass
class Trade:
    ticket: int
    side: str
    mode: str
    role: str                 # probe / entry / extend / adopted
    open_price: float
    entry_mid: float
    open_time: float
    risk_money: float         # money lost if its stop fills (counted against the 15% cap)
    volume: float
    sl: float = 0.0
    tp: float = 0.0
    closing: bool = False     # a close order is in the queue: never send a 2nd one
    missing_since: float = 0.0


class Swarm:
    def __init__(self, broker, spec, executor, journal, cfg=default_config, news=None, real=False):
        self.b, self.spec, self.ex, self.j, self.cfg = broker, spec, executor, journal, cfg
        self.name = spec.name
        self.news = news or risk.NewsCalendar()
        self.real = real
        self.lot = risk.lot_size(spec)
        self.ms = st.MarketState(cfg.DIR_WINDOW_S, cfg.SPREAD_WINDOW_S, cfg.VOL_WINDOW_S)
        self.slip = risk.SlipStats(cfg.SLIP_SAMPLES)          # market orders (opens + bot closes)
        self.stop_slip = risk.SlipStats(cfg.SLIP_SAMPLES)     # broker stop fills vs the stop level
        self.rate = risk.RateCap(cfg.MAX_ORDERS_PER_MIN)
        self.rolling = risk.RollingNet(cfg.ROLLING_TRADES)
        for p in journal.last_closed(cfg.ROLLING_TRADES, cfg.VERSION):
            self.rolling.add(p)
        self.trades: dict[int, Trade] = {}
        self.live = {}
        self.cmds = {}                       # id -> command still waiting for its result
        self.dir = st.Direction()
        self.next_check, self.decide_now = 0.0, False
        self.plan = None
        self.acct, self._acct_t, self.margin_per_order = None, -INF, None
        self.connected = True
        self.status, self.note, self.block = "starting", "", "starting"
        self.halted, self.halt_reason = False, ""
        self.basket_until = self.no_money_until = self.market_closed_until = self.auto_pause_until = 0.0
        self._auto_reset = False
        self.last_stop = {st.BUY: -INF, st.SELL: -INF}
        self.last_probe = -INF
        self.block_time, self._last_t = {}, None
        self.start_balance = self.start_equity = None
        self.equity_peak, self.dd_money, self.dd_pct = 0.0, 0.0, 0.0
        self.floating = self.realized_today = 0.0
        self._realized_t = -INF
        self.opened_t, self.closed_t = deque(), deque()       # for trades per minute
        self.order_ms = deque(maxlen=100)
        self.orders_sent = self.closed_n = 0
        self.unknown_seen = {}
        self.started = False
        self._session_t = -INF
        self.now = 0.0

    # ---------------- helpers ----------------
    def mode(self, now):
        m = self.cfg.START_MODE.upper()
        if m in ("A", "B"):
            return m
        return "A" if int(now // (self.cfg.ALTERNATE_EVERY_MIN * 60)) % 2 == 0 else "B"

    def pnl_price(self, t):
        return (self.ms.bid - t.open_price) if t.side == st.BUY else (t.open_price - self.ms.ask)

    def pending_opens(self):
        return sum(1 for c in self.cmds.values() if c["kind"] == "open")

    def open_risk(self):
        return sum(t.risk_money for t in self.trades.values()) + self.pending_opens() * (
            self.plan.risk_money if self.plan else 0.0)

    def max_trades(self):
        if not self.plan or not self.acct:
            return 0
        return risk.max_trades(self.acct.equity, self.plan, self.lot, self.cfg)

    def latency_ms(self):
        return sum(self.order_ms) / len(self.order_ms) if self.order_ms else 0.0

    def orders_per_trade(self):
        return self.orders_sent / self.closed_n if self.closed_n >= 5 else 1.5

    def realistic_tpm(self):
        return risk.realistic_trades_per_min(self.latency_ms(), self.orders_per_trade(), self.cfg.MAX_ORDERS_PER_MIN)

    def per_min(self, dq, now):
        while dq and dq[0] < now - 60:
            dq.popleft()
        return len(dq)

    def day_start(self, now):
        """Start of today in SERVER time, as a UTC epoch."""
        off = self.cfg.SERVER_UTC_OFFSET_HOURS * 3600
        server = now + off
        return server - server % 86400 - off

    def rolling_warning(self):
        r = self.rolling
        return r.count >= self.cfg.WARN_MIN_TRADES and r.mean() < 0

    def _account(self, now, force=False):
        if force or now - self._acct_t >= 1.0:
            a = self.b.account()
            if a is not None:
                self.acct = a
                self.margin_per_order = self.b.margin_needed(self.spec, st.BUY, self.lot, self.ms.ask or None)
            self._acct_t = now
        return self.acct

    def _dev(self):
        return risk.deviation_points(self.spec, self.ms.median_spread(), self.cfg.DEVIATION_X_SPREAD)

    # ---------------- main step ----------------
    def adopt_existing(self, now):
        """At startup: take over the bot's own open trades (same magic number)."""
        ps = self.b.positions(self.name) or []
        for p in ps:
            self._adopt(p, now)
        self.started = True
        return len(ps)

    def loop_once(self, now):
        self.now = now
        cfg = self.cfg
        for r in self.ex.results():
            self._on_result(r, now)
        self._expire_cmds(now)
        tick = self.b.tick(self.name)
        if tick is None:
            self.status = "no price (market closed or disconnected)"
            self._count(now, "no price")
            return
        key = getattr(tick, "time_msc", None)
        self.ms.update(now, tick.bid, tick.ask, (key, tick.bid, tick.ask) if key else None)
        positions = self.b.positions(self.name)
        if positions is None:                      # MT5 did not answer: decide nothing this loop
            self.status = "MT5 did not return positions - retrying"
            return
        self._sync(positions, now)
        acct = self._account(now)
        if acct is None:
            self.status = "no account info from MT5"
            return
        if self.start_balance is None:
            self.start_balance, self.start_equity = acct.balance, acct.equity
        self.equity_peak = max(self.equity_peak, acct.equity)
        dd = self.equity_peak - acct.equity
        if dd > self.dd_money:
            self.dd_money, self.dd_pct = dd, 100 * dd / self.equity_peak
        self._update_plan()
        self.floating = sum(p.profit + p.swap for p in self.live.values())
        if now - self._realized_t >= 5:
            self.realized_today, self._realized_t = self.j.realized_since(self.day_start(now)), now
        if self._auto_reset and now >= self.auto_pause_until:
            self._auto_reset = False
            self.rolling.reset()
            self.j.event("info", "auto-pause over: the next 100 trades are judged from zero")

        day_start_balance = acct.balance - self.realized_today
        if cfg.DAILY_LOSS_PCT and not self.halted and day_start_balance > 0 and \
                self.realized_today + self.floating <= -cfg.DAILY_LOSS_PCT / 100 * day_start_balance:
            self.halted, self._halted_day = True, self.day_start(now)
            self.halt_reason = f"daily loss limit ({cfg.DAILY_LOSS_PCT}% of today's start): no entries until tomorrow"
            self.j.event("warn", self.halt_reason + "; closing all")
            self.close_all("daily loss limit", now)
        if self.halted and getattr(self, "_halted_day", None) is not None and self.day_start(now) > self._halted_day:
            self.halted, self.halt_reason, self._halted_day = False, "", None
            self.j.event("info", "new server day: daily loss limit reset")
        if self.live and risk.basket_hit(self.floating, acct.equity, cfg):
            self.j.event("warn", f"BASKET STOP: floating {self.floating:.2f} reached {cfg.BASKET_STOP_PCT}% "
                         f"of equity. Closing all, pause {cfg.BASKET_COOLDOWN_S}s")
            self.close_all("basket stop", now)
            self.basket_until = now + cfg.BASKET_COOLDOWN_S

        if now >= self.next_check:
            self.next_check = now + cfg.DIR_CHECK_S
            self._direction(now)
            self.decide_now = True
        self.block = self._entry_block(now)
        if self.decide_now:
            self.decide_now = False
            self._decide(now)
        self._count(now, self.block)
        self._set_status()
        if now - self._session_t >= 60:
            self.save_session(now)

    def _update_plan(self):
        cfg, ms = self.cfg, self.ms
        med = ms.median_spread()
        slip = self.slip.expected(med, cfg.SLIP_PRIOR_X_SPREAD)
        stop_slip = self.stop_slip.expected(med, cfg.SLIP_PRIOR_X_SPREAD)
        self.plan = risk.make_plan(self.spec, self.lot, med, ms.spread, slip, stop_slip, cfg)

    def _direction(self, now):
        cfg = self.cfg
        if self.ms.move(now) is None:
            self.dir = st.Direction()
            return
        mids, _ = self.ms.window(now)
        d = st.direction(mids, self.plan.cost, cfg.DIR_MOVE_X_COST, cfg.DIR_MIN_IMBALANCE, cfg.DIR_MIN_TICKS)
        if d.state != self.dir.state:
            self.j.event("signal", f"direction {d.state}: move {d.move / self.spec.point:+.0f} pts, "
                         f"ticks {d.ups} up / {d.downs} down", show=d.state != st.FLAT)
        self.dir = d

    def _count(self, now, block):
        """Add the time since the last loop to the reason the bot could not enter (for the report)."""
        if self._last_t is not None:
            dt = min(now - self._last_t, 2.0)
            if block:
                key = re.sub(r"\s*\(.*\)|:.*", "", block).strip()
            else:
                key = "in trades" if self.trades else "free to enter"
            self.block_time[key] = self.block_time.get(key, 0.0) + dt
        self._last_t = now

    def _set_status(self):
        buys = sum(1 for t in self.trades.values() if t.side == st.BUY)
        sells = len(self.trades) - buys
        head = f"{buys} BUY / {sells} SELL open" if self.trades else "flat"
        if self.block:
            self.status = f"{head} | waiting: {self.block}"
        else:
            self.status = f"{head} | {self.note or 'ready'}"

    # ---------------- entry gates ----------------
    def _entry_block(self, now):
        cfg, ms, p, a = self.cfg, self.ms, self.plan, self.acct
        if self.halted:
            return self.halt_reason
        if now < self.auto_pause_until:
            return f"auto-pause: net per trade negative ({(self.auto_pause_until - now) / 60:.0f} min left)"
        if now < self.basket_until:
            return f"cooldown after basket stop ({self.basket_until - now:.0f}s)"
        if now < self.no_money_until:
            return f"no money from broker: paused ({self.no_money_until - now:.0f}s)"
        if now < self.market_closed_until:
            return f"market closed ({self.market_closed_until - now:.0f}s)"
        if not risk.active_session(cfg.SESSIONS, now):
            return "outside session"
        news = self.news.active(now, (self.spec.currency_base, self.spec.currency_profit))
        if news:
            return f"news pause: {news}"
        if ms.move(now) is None or len(ms.spreads) < 10 or len(ms.moves) < 10:
            return "warming up (measuring spread and moves)"
        if ms.spread > cfg.SPREAD_SPIKE_X_MEDIAN * ms.median_spread():
            return "spread spike"
        cb = risk.cost_block(p, ms.spread, p.slip, cfg)
        if cb:
            return cb
        if ms.vol() < cfg.MIN_VOL_X_COST * p.cost:
            return "too quiet: 5-second moves smaller than the cost"
        big = risk.stop_too_big(a.equity, p, cfg)
        if big:
            return big
        if self.rate.left(now) <= 0:
            return "order rate cap"
        if not risk.margin_ok(self.margin_per_order, self.pending_opens() + 1, a.margin_free, cfg):
            return "not enough free margin"
        return None

    # ---------------- decisions ----------------
    def _decide(self, now):
        cfg, p = self.cfg, self.plan
        poss = [st.Pos(t.ticket, t.side, self.pnl_price(t), t.entry_mid, t.open_time, t.role)
                for t in self.trades.values() if not t.closing and t.ticket in self.live]
        pend = self.pending_opens()
        slots = 0
        if self.acct and p:
            slots = risk.free_slots(self.acct.equity, self.open_risk(), len(self.trades) + pend, p, self.lot, cfg)
            slots = min(slots, cfg.MAX_PENDING_OPENS - pend, self.rate.left(now))
            if self.margin_per_order:
                fit = int(cfg.MARGIN_USE_MAX_PCT / 100 * self.acct.margin_free // self.margin_per_order) - pend
                slots = min(slots, fit)
        blocked = {s for s in (st.BUY, st.SELL) if now - self.last_stop[s] < cfg.SAME_SIDE_PAUSE_AFTER_STOP_S}
        probe_ready = (now - self.last_probe >= cfg.PROBE_COOLDOWN_S and pend == 0
                       and self.dir.ups + self.dir.downs >= cfg.DIR_MIN_TICKS)
        mode = self.mode(now)
        actions, note = st.decide(self.dir.state, poss, self.ms.mid, mode, max(0, slots),
                                  self.block is None, probe_ready, cfg, blocked)
        self.note = note
        if any(a.kind == "open" for a in actions):
            self._account(now, force=True)       # fresh free margin before sending opens
        for a in actions:
            if a.kind == "close":
                self._send_close(self.trades[a.ticket], a.reason, now)
            else:
                self._send_open(a.side, a.role, mode, now)

    def _send_open(self, side, role, mode, now):
        p, a = self.plan, self.acct
        # free-margin check before EVERY order (all opens still in the queue + this one)
        if a is None or not risk.margin_ok(self.margin_per_order, self.pending_opens() + 1, a.margin_free, self.cfg):
            self.note = "not enough free margin"
            return False
        cmd = new_cmd("open", side=side, volume=self.lot, sl_dist=p.sl_dist, tp_dist=p.tp_dist,
                      deviation=self._dev(), comment=f"v3 {mode} {role}", role=role, mode=mode,
                      entry_mid=self.ms.mid, spread=self.ms.spread, risk_money=p.risk_money,
                      cost=p.cost, cost_money=p.cost_money, target=p.target_move, stop=p.stop_move,
                      be_wr=p.breakeven_winrate)
        cmd["sent_at"] = now
        self.cmds[cmd["id"]] = cmd
        self.ex.submit(cmd)
        self.rate.record(now)
        self.orders_sent += 1
        if role == "probe":
            self.last_probe = now
        return True

    def _send_close(self, t, reason, now):
        pos = self.live.get(t.ticket)
        if pos is None or t.closing:
            return False
        t.closing = True
        cmd = new_cmd("close", ticket=t.ticket, pos_type=pos.type, volume=pos.volume, deviation=self._dev(),
                      comment=f"v3 {reason}", reason=reason, side=t.side)
        cmd["sent_at"] = now
        self.cmds[cmd["id"]] = cmd
        self.ex.submit(cmd)
        self.rate.record(now)          # counted, but a close is never blocked by the rate cap
        self.orders_sent += 1
        return True

    def close_all(self, reason, now):
        for t in list(self.trades.values()):
            self._send_close(t, reason, now)

    # ---------------- order results ----------------
    def _expire_cmds(self, now):
        """An order with no answer for 30 s: forget it, so it cannot block the bot forever."""
        if hasattr(self.ex, "alive") and not self.ex.alive() and not self.halted:
            self.halted, self.halt_reason = True, "order process died: no new orders (restart the bot)"
            self.j.event("error", self.halt_reason)
        for cid, c in list(self.cmds.items()):
            if now - c["sent_at"] > 30:
                self.cmds.pop(cid)
                t = self.trades.get(c.get("ticket"))
                if t:
                    t.closing = False
                self.j.event("warn", f"no answer for the {c['kind']} order after 30 s: forgotten")

    def _on_result(self, r, now):
        cmd = self.cmds.pop(r["id"], None)
        if cmd is None:
            return
        if r.get("latency_ms"):
            self.order_ms.append(r["latency_ms"])
        if cmd["kind"] == "open":
            self._on_open(cmd, r, now)
        else:
            self._on_close(cmd, r, now)

    def _on_open(self, cmd, r, now):
        side, sp = cmd["side"], self.spec
        if not r.get("ok"):
            if r.get("stale"):
                self.j.event("info", f"dropped a stale {side} open (waited {r['queue_ms']:.0f} ms)", show=False)
            elif r.get("no_money"):
                self.no_money_until = now + self.cfg.NO_MONEY_PAUSE_S
                self.j.event("error", f"open {side} refused: not enough money. No new orders for "
                             f"{self.cfg.NO_MONEY_PAUSE_S}s")
            elif r.get("market_closed"):
                self.market_closed_until = now + 60
                self.j.event("warn", "market closed: retry in 60s")
            else:
                self.j.event("error", f"open {side} failed: {r.get('message')}")
            return
        price, req = r["price"], r["req_price"]
        adverse = (price - req) if side == st.BUY else (req - price)
        self.slip.add(adverse)
        mpp = sp.money_per_price(cmd["volume"])
        t = self.trades.get(r["ticket"])
        if t is None:
            t = Trade(r["ticket"], side, cmd["mode"], cmd["role"], price, cmd["entry_mid"], now,
                      cmd["risk_money"], cmd["volume"], r.get("sl", 0.0), r.get("tp", 0.0))
            self.trades[t.ticket] = t
        else:                      # already picked up from the position list: fill in what we know
            t.mode, t.role, t.entry_mid, t.risk_money = cmd["mode"], cmd["role"], cmd["entry_mid"], cmd["risk_money"]
        self.unknown_seen.pop(t.ticket, None)
        self.opened_t.append(now)
        self.j.open_trade(ticket=t.ticket, symbol=self.name, side=side, mode=cmd["mode"], role=cmd["role"],
                          session=self.j.session_id, open_time=now, open_price=price, entry_mid=cmd["entry_mid"],
                          req_open_price=req, open_slip_pts=adverse / sp.point, open_latency_ms=r["latency_ms"],
                          open_queue_ms=r["queue_ms"], spread_open=cmd["spread"],
                          spread_cost=cmd["spread"] * mpp, cost_pts=cmd["cost"] / sp.point,
                          cost_money=cmd["cost_money"], target_pts=cmd["target"] / sp.point,
                          stop_pts=cmd["stop"] / sp.point, risk_money=cmd["risk_money"],
                          breakeven_wr=cmd["be_wr"], sl=t.sl, tp=t.tp, volume=cmd["volume"],
                          version=self.cfg.VERSION)
        self.j.event("open", f"{cmd['role'].upper()} {side} #{t.ticket} @ {price:.{sp.digits}f} "
                     f"[{cmd['mode']}] slip {adverse / sp.point:+.0f} pts, {r['latency_ms']:.0f} ms "
                     f"(+{r['queue_ms']:.0f} queue)")

    def _on_close(self, cmd, r, now):
        t = self.trades.get(cmd["ticket"])
        if t is None:
            return
        if r.get("ok"):
            deals, out = self.b.closing_deals(t.ticket, tries=3)
            req, price = r["req_price"], r["price"]
            if out:
                price = out[-1].price
                pnl = sum(d.profit + d.swap + d.commission + getattr(d, "fee", 0.0) for d in deals)
            else:
                pnl = ((price - t.open_price) if t.side == st.BUY else (t.open_price - price)) * \
                    self.spec.money_per_price(t.volume)
            adverse = (req - price) if t.side == st.BUY else (price - req)
            self.slip.add(adverse)
            self._record_close(t, now, price, cmd["reason"], pnl, adverse / self.spec.point, r["latency_ms"])
            return
        t.closing = False
        if r.get("gone"):              # its broker target or stop fired first: the position sync logs it
            return
        if r.get("market_closed"):
            self.market_closed_until = now + 60
        self.j.event("error", f"close #{t.ticket} ({cmd['reason']}) failed: {r.get('message')}")

    # ---------------- positions ----------------
    def _sync(self, positions, now):
        self.live = {p.ticket: p for p in positions}
        for ticket, t in list(self.trades.items()):
            if ticket in self.live:
                p = self.live[ticket]
                t.sl, t.tp, t.missing_since = p.sl, p.tp, 0.0
            elif not t.closing:
                self._resolve_missing(t, now)
        for ticket, p in self.live.items():
            if ticket in self.trades:
                continue
            # A fill can show in the position list before its result arrives: wait 3 s before adopting.
            first = self.unknown_seen.setdefault(ticket, now)
            if now - first >= 3.0:
                self._adopt(p, now)

    def _adopt(self, p, now):
        side = st.BUY if p.type == self.b.mt5.POSITION_TYPE_BUY else st.SELL
        row = self.j.row(p.ticket)
        mode, role = (row["mode"], row["role"]) if row else ("?", "adopted")
        sl_dist = abs(p.price_open - p.sl) if p.sl else (self.plan.sl_dist if self.plan else 0.0)
        risk_money = sl_dist * self.spec.money_per_price(p.volume)
        t = Trade(p.ticket, side, mode or "?", role or "adopted", p.price_open,
                  row["entry_mid"] if row and row["entry_mid"] else p.price_open,
                  row["open_time"] if row and row["open_time"] else now, risk_money, p.volume, p.sl, p.tp)
        self.trades[p.ticket] = t
        self.unknown_seen.pop(p.ticket, None)
        if not row:
            self.j.open_trade(ticket=p.ticket, symbol=self.name, side=side, mode="?", role="adopted",
                              session=self.j.session_id, open_time=now, open_price=p.price_open,
                              spread_open=0.0, spread_cost=0.0, risk_money=risk_money, sl=p.sl, tp=p.tp,
                              volume=p.volume, version=self.cfg.VERSION)
        self.j.event("info", f"adopted #{p.ticket} {side} {p.volume} @ {p.price_open}")

    def _resolve_missing(self, t, now):
        """A trade is gone: its broker target or stop fired, or someone closed it by hand."""
        mt5 = self.b.mt5
        deals, out = self.b.closing_deals(t.ticket)
        if not out:
            if self.b.still_open(t.ticket):
                return
            t.missing_since = t.missing_since or now
            if now - t.missing_since >= 60:
                self._record_close(t, now, 0.0, "closed outside bot (no history)", 0.0, None, None)
            return
        d = out[-1]
        if d.reason == mt5.DEAL_REASON_TP:
            reason, level = "target", t.tp
        elif d.reason == mt5.DEAL_REASON_SL:
            reason, level = "stop", t.sl
        elif d.reason == getattr(mt5, "DEAL_REASON_SO", 6):
            reason, level = "stop out", 0.0
        else:
            reason, level = "closed outside bot", 0.0
        slip = None
        if level and d.price:
            adverse = (level - d.price) if t.side == st.BUY else (d.price - level)
            slip = adverse / self.spec.point
            if reason == "stop":
                self.stop_slip.add(adverse)
        pnl = sum(x.profit + x.swap + x.commission + getattr(x, "fee", 0.0) for x in deals)
        self._record_close(t, now, d.price, reason, pnl, slip, None)
        if reason == "stop":
            self.last_stop[t.side] = now
        if reason == "target":
            self.decide_now = True        # 5. reopen at once in the current direction

    def _record_close(self, t, now, price, reason, pnl, slip_pts, latency):
        pts = 0.0
        if price:
            pts = ((price - t.open_price) if t.side == st.BUY else (t.open_price - price)) / self.spec.point
        self.j.close_trade(t.ticket, close_time=now, close_price=price, close_reason=reason,
                           close_slip_pts=slip_pts, close_latency_ms=latency, pnl=pnl, pnl_points=pts)
        self.trades.pop(t.ticket, None)
        self.live.pop(t.ticket, None)
        self.realized_today += pnl
        self.closed_t.append(now)
        self.closed_n += 1
        self.rolling.add(pnl)
        self._check_auto_pause(now)
        extra = f", {latency:.0f} ms" if latency is not None else ""
        self.j.event("close", f"CLOSED {t.side} #{t.ticket} by {reason}: {pnl:+.2f} ({pts:+.0f} pts){extra}")

    def _check_auto_pause(self, now):
        cfg, r = self.cfg, self.rolling
        if cfg.AUTO_PAUSE_ON_NEGATIVE and r.full and r.mean() < 0 and now >= self.auto_pause_until:
            self.auto_pause_until = now + cfg.AUTO_PAUSE_MIN * 60
            self._auto_reset = True
            self.j.event("warn", f"AUTO-PAUSE: last {r.count} trades lost {r.mean():+.3f} per trade after spread. "
                         f"No new entries for {cfg.AUTO_PAUSE_MIN} min")

    # ---------------- shutdown ----------------
    def close_everything(self, reason, now):
        """Stop the order worker, then close every bot trade directly. Returns how many are left."""
        self.ex.stop()
        for r in self.ex.results():
            self._on_result(r, now)
        ps = self.b.positions(self.name)
        if ps is not None:
            self.live = {p.ticket: p for p in ps}
            for p in ps:
                if p.ticket not in self.trades:
                    self._adopt(p, now)
        for t in list(self.trades.values()):
            pos = self.live.get(t.ticket)
            if pos is None:
                self._resolve_missing(t, now)
                continue
            res = self.b.close(self.spec, t.ticket, pos.type, pos.volume, self._dev() * 3, f"v3 {reason}")
            if res.ok or res.gone:
                deals, out = self.b.closing_deals(t.ticket, tries=5)
                price = out[-1].price if out else res.price
                pnl = sum(d.profit + d.swap + d.commission + getattr(d, "fee", 0.0) for d in deals)
                self._record_close(t, now, price, reason, pnl, None, res.latency_ms)
            else:
                self.j.event("error", f"could not close #{t.ticket}: {res.message}")
        left = self.b.positions(self.name)
        return len(left) if left is not None else -1

    def save_session(self, now):
        self._session_t = now
        self.j.update_session(end=now, max_dd_money=self.dd_money, max_dd_pct=self.dd_pct,
                              blocks=self.block_time, orders=self.orders_sent, order_ms=self.latency_ms())
        self.j.flush()


# ---------------- startup ----------------
def plan_lines(sw, equity):
    """What the bot will do with this account, in numbers (printed at startup)."""
    sw._update_plan()
    p, sp, cfg = sw.plan, sw.spec, sw.cfg
    n = risk.max_trades(equity, p, sw.lot, cfg)
    big = risk.stop_too_big(equity, p, cfg)
    pts = 1 / sp.point
    return [
        f"spread now {sw.ms.spread * pts:.0f} pts. Cost of one round trip (spread + 2x expected slippage) = "
        f"{p.cost * pts:.0f} pts = {p.cost_money:.3f} money at {sw.lot} lot = the MINIMUM PROFITABLE TARGET",
        f"target: mid price moves {p.target_move * pts:.0f} pts our way -> net win about {p.win_money:+.3f}",
        f"stop:   mid price moves {p.stop_move * pts:.0f} pts against us -> loss about {-p.risk_money:+.3f}",
        f"one stop = {p.risk_money:.3f} = {100 * p.risk_money / equity:.2f}% of equity {equity:.2f}. "
        f"Max open trades from the {cfg.MAX_TOTAL_STOP_RISK_PCT}% cap: {n}. "
        f"Worst case, all stopped: {n * p.risk_money:.2f} = {100 * n * p.risk_money / equity:.1f}% of equity",
        f"break-even win rate {p.breakeven_winrate:.0%}; a coin flip wins {p.coinflip_winrate:.0%} of the time. "
        f"The direction signal must add the difference.",
    ] + ([f"[bold red]{big}: the bot will not open trades on this balance.[/]"] if big else [])


def check_server_clock(broker, name, cfg, journal, console):
    t = broker.tick(name)
    if t is None:
        return
    seen = (t.time - time.time()) / 3600
    if abs(seen) < 15 and abs(seen - cfg.SERVER_UTC_OFFSET_HOURS) > 0.6:
        msg = (f"server clock looks like UTC{round(seen):+d} but config says UTC{cfg.SERVER_UTC_OFFSET_HOURS:+d}. "
               f"Check SERVER_UTC_OFFSET_HOURS.")
        console.print(f"[yellow]{msg}[/]")
        journal.event("warn", msg)


def main():
    cfg = default_config
    os.chdir(HERE)
    console = display.make_console()
    if os.path.exists(cfg.STOP_FILE):
        console.print("[bold yellow]A STOP file is in this folder. Delete it, then start again.[/]")
        return 1
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(HERE, ".env"))
    except ImportError:
        pass
    try:
        import MetaTrader5 as mt5_module
    except ImportError:
        console.print("[red]MetaTrader5 package not found. Run: pip install -r requirements.txt (Windows only)[/]")
        return 1
    mt5 = LockedMT5(mt5_module)
    journal = Journal(cfg.DB_FILE, cfg.LOG_DIR)
    broker = Broker(mt5, cfg.MAGIC, log=lambda msg: journal.event("warn", msg), retries=cfg.ORDER_RETRIES)
    login_kw = dict(login=os.getenv("MT5_LOGIN"), password=os.getenv("MT5_PASSWORD"),
                    server=os.getenv("MT5_SERVER"), path=os.getenv("MT5_PATH"))
    if not broker.connect(**login_kw):
        console.print(f"[red]Cannot connect to MetaTrader 5 ({mt5.last_error()}). Is it open and logged in?[/]")
        return 1
    acct, term = broker.account(), broker.terminal()
    real = acct.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO      # contest accounts count as REAL, to be safe
    display.banner(console, acct, real)
    journal.event("info", f"start v{cfg.VERSION}: {'REAL' if real else 'DEMO'} account {acct.login} on {acct.server}")
    if real and not display.confirm_real(console):
        console.print("Not confirmed. Nothing was traded.")
        mt5.shutdown()
        return 0
    if acct.margin_mode != mt5.ACCOUNT_MARGIN_MODE_RETAIL_HEDGING:
        console.print("[red]This account is not HEDGING. bot_v3 holds BUYs and SELLs at once. Exiting.[/]")
        mt5.shutdown()
        return 1
    if not term.trade_allowed:
        console.print("[red]'Algo Trading' is off in MetaTrader 5. Turn it on and restart.[/]")
        mt5.shutdown()
        return 1
    name = broker.resolve(cfg.SYMBOL)
    if not name:
        console.print(f"[red]{cfg.SYMBOL} not found at this broker.[/]")
        mt5.shutdown()
        return 1
    spec = broker.spec(name)
    lot = risk.lot_size(spec)
    console.print(f"{cfg.SYMBOL} -> [bold]{name}[/]: lot {lot} (min {spec.vol_min}, step {spec.vol_step}), "
                  f"contract {spec.contract_size}, point {spec.point}, tick value {spec.tick_value}, "
                  f"stops level {spec.stops_level} pts, filling {spec.filling_mode}")

    max_age = cfg.OPEN_MAX_AGE_MS / 1000
    ex = None
    if cfg.EXECUTOR == "process":
        console.print("starting the order process (its own MT5 connection) ...")
        ex = ProcessExecutor({k: v for k, v in login_kw.items() if v}, name, cfg.MAGIC, cfg.ORDER_RETRIES, max_age)
        if not ex.wait_ready():
            msg = f"order process failed ({(ex.ready or {}).get('message', 'no answer')}): using a thread instead"
            console.print(f"[yellow]{msg}[/]")
            journal.event("warn", msg)
            ex.stop(1)
            ex = None
    if ex is None:
        ex = ThreadExecutor(broker, spec, max_age)
    journal.event("info", f"order executor: {ex.name}")

    news = risk.NewsCalendar.load(cfg.NEWS_FILE)
    sw = Swarm(broker, spec, ex, journal, cfg, news, real)
    journal.start_session(cfg.VERSION, ex.name, acct.balance, acct.equity)
    n = sw.adopt_existing(time.time())
    console.print(f"news blackout events: {len(news.events)}   adopted open trades: {n}   "
                  f"start mode: {cfg.START_MODE}")
    t = broker.tick(name)
    if t:
        for _ in range(3):
            sw.ms.update(time.time(), t.bid, t.ask)
        for line in plan_lines(sw, acct.equity):
            console.print(line)
            journal.event("info", display.plain(line), show=False)
    check_server_clock(broker, name, cfg, journal, console)
    if sw.rolling.full and sw.rolling.mean() < 0:
        sw._check_auto_pause(time.time())
    run(sw, console)
    mt5.shutdown()
    return 0


def print_report(sw, console):
    now = time.time()
    rows = sw.j.closed_since(sw.j.session_start)
    lines = build_report(rows, (now - sw.j.session_start) / 3600, sw.start_balance or 0.0,
                         getattr(sw.acct, "currency", ""), sw.block_time, sw.dd_money, sw.dd_pct,
                         f"SESSION REPORT since {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(sw.j.session_start))}",
                         sw.orders_sent)
    tpm = sw.realistic_tpm()
    lines.append(f"speed: order latency {sw.latency_ms():.0f} ms avg, {sw.orders_per_trade():.2f} orders per trade "
                 f"-> realistic max {tpm:.0f} trades per minute"
                 + ("" if tpm >= 100 else " (100 trades per minute is NOT possible at this latency)"))
    for line in lines:
        console.print(line)
    sw.j.log.info("report\n" + "\n".join(display.plain(x) for x in lines))


def run(sw, console, max_seconds=None):
    cfg, j = sw.cfg, sw.j
    j.event("info", "bot running")
    wait, next_try, next_check, next_screen = 1, 0.0, 0.0, 0.0
    how, t_end = "ctrl+c", (time.time() + max_seconds) if max_seconds else None
    try:
        with display.live(console) as live:
            while True:
                now = time.time()
                if os.path.exists(cfg.STOP_FILE):
                    j.event("warn", "STOP file found: closing all bot trades and exiting")
                    for _ in range(3):
                        if sw.close_everything("kill switch", now) == 0:
                            break
                        time.sleep(1)
                    how = "kill switch"
                    break
                if t_end and now >= t_end:
                    how = "time limit"
                    break
                if now >= next_check:
                    sw.connected, next_check = sw.b.connected(), now + 1
                if sw.connected:
                    sw.loop_once(now)
                    wait = 1
                elif now >= next_try:
                    if sw.b.reconnect():
                        sw.connected = True
                        j.event("info", "reconnected")
                    else:
                        sw.status = f"DISCONNECTED - next retry in {wait}s"
                        j.event("warn", sw.status)
                        next_try, wait = now + wait, min(wait * 2, cfg.RECONNECT_MAX_S)
                j.flush()
                if display.read_key() == "r":
                    print_report(sw, live.console)
                if now >= next_screen:
                    live.update(display.render(sw), refresh=True)
                    next_screen = now + cfg.SCREEN_REFRESH_S
                time.sleep(max(0.0, cfg.LOOP_MS / 1000 - (time.time() - now)))
    except KeyboardInterrupt:
        how = "ctrl+c"
    if how == "ctrl+c":
        left = sw.b.positions(sw.name) or []
        answer = ""
        if left:
            try:
                answer = input(f"\n{len(left)} bot trade(s) still open. Close them all now? (y/N): ")
            except (KeyboardInterrupt, EOFError):
                answer = ""
        if answer.strip().lower() == "y":
            console.print(f"closed. still open: {sw.close_everything('manual stop', time.time())}")
        else:
            sw.ex.stop()
            if left:
                console.print("[yellow]Trades left open, each with its broker stop and target. "
                              "Restart the bot to manage them again.[/]")
    elif how == "time limit":
        sw.ex.stop()
    j.event("info", f"bot stopped ({how})")
    sw.save_session(time.time())
    print_report(sw, console)
    j.flush(force=True)
    return how


if __name__ == "__main__":
    sys.exit(main())
