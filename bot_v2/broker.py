"""Thin wrapper around the MetaTrader5 module.

The mt5 module is passed in, so tests can use a fake one.
Every number about a symbol comes from symbol_info(), never from constants here.
"""
from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class Spec:
    name: str
    point: float
    digits: int
    tick_size: float
    tick_value: float          # account money per tick per 1 lot
    contract_size: float
    vol_min: float
    vol_max: float
    vol_step: float
    stops_level: int           # in points
    freeze_level: int          # in points
    filling_mode: int          # bitmask from symbol_info
    currency_base: str
    currency_profit: str

    def money_per_price(self, volume):
        """Account money for a 1.0 price move with this volume."""
        return self.tick_value / self.tick_size * volume

    def round_price(self, price):
        return round(round(price / self.tick_size) * self.tick_size, self.digits)


@dataclass
class OrderResult:
    ok: bool
    ticket: int = 0
    price: float = 0.0          # fill price
    req_price: float = 0.0      # price we asked for
    retcode: int = 0
    latency_ms: float = 0.0
    market_closed: bool = False
    message: str = ""
    gone: bool = False          # the position was already closed (by its broker stop or target)
    sl: float = 0.0             # stop and target the broker really holds (after a fill)
    tp: float = 0.0


class Broker:
    def __init__(self, mt5, magic, log=None, retries=3, retry_sleep=0.2):
        self.mt5 = mt5
        self.magic = magic
        self.log = log or (lambda msg: None)
        self.retries = retries
        self.retry_sleep = retry_sleep
        self._login = {}
        self._filling = {}
        m = mt5
        self.DONE = {m.TRADE_RETCODE_DONE, m.TRADE_RETCODE_DONE_PARTIAL}
        self.RETRY = {m.TRADE_RETCODE_REQUOTE, m.TRADE_RETCODE_PRICE_CHANGED,
                      m.TRADE_RETCODE_PRICE_OFF, m.TRADE_RETCODE_TIMEOUT,
                      m.TRADE_RETCODE_CONNECTION, m.TRADE_RETCODE_TOO_MANY_REQUESTS,
                      getattr(m, "TRADE_RETCODE_FROZEN", 10029)}      # price at the stop: broker is acting
        self.GONE = getattr(m, "TRADE_RETCODE_POSITION_CLOSED", 10036)

    # ---------- connection ----------
    def connect(self, login=None, password=None, server=None, path=None):
        kw = {}
        if path:
            kw["path"] = path
        if login:
            kw.update(login=int(login), password=password or "", server=server or "")
        self._login = kw
        ok = self.mt5.initialize(**kw)
        if not ok:
            self.log(f"MT5 initialize failed: {self.mt5.last_error()}")
        return bool(ok)

    def connected(self):
        info = self.mt5.terminal_info()
        return info is not None and bool(info.connected)

    def reconnect(self):
        try:
            self.mt5.shutdown()
        except Exception:
            pass
        return bool(self.mt5.initialize(**self._login)) and self.connected()

    def account(self):
        return self.mt5.account_info()

    def terminal(self):
        return self.mt5.terminal_info()

    # ---------- symbols ----------
    def resolve(self, base):
        """Find the broker's real name for a symbol (Exness may add a suffix)."""
        if self.mt5.symbol_info(base) is not None:
            self.mt5.symbol_select(base, True)
            return base
        found = self.mt5.symbols_get(group=f"*{base}*") or []
        names = sorted((s.name for s in found if s.name.upper().startswith(base.upper())), key=len)
        for name in names:
            if self.mt5.symbol_select(name, True):
                return name
        return None

    def spec(self, name):
        s = self.mt5.symbol_info(name)
        if s is None:
            raise RuntimeError(f"symbol_info({name}) returned nothing")
        return Spec(
            name=name, point=s.point, digits=s.digits,
            tick_size=s.trade_tick_size or s.point, tick_value=s.trade_tick_value,
            contract_size=s.trade_contract_size,
            vol_min=s.volume_min, vol_max=s.volume_max, vol_step=s.volume_step,
            stops_level=int(s.trade_stops_level), freeze_level=int(s.trade_freeze_level),
            filling_mode=int(s.filling_mode),
            currency_base=s.currency_base, currency_profit=s.currency_profit,
        )

    def tick(self, name):
        t = self.mt5.symbol_info_tick(name)
        if t is None or not t.bid or not t.ask:
            return None
        return t

    def rates_m1(self, name, count):
        r = self.mt5.copy_rates_from_pos(name, self.mt5.TIMEFRAME_M1, 0, count)
        if r is None:
            return []
        return [(float(x["high"]), float(x["low"]), float(x["close"])) for x in r]

    # ---------- positions and history ----------
    def positions(self, symbol=None):
        """The bot's open positions, or None if MT5 could not answer (never mistake an error for 'no trades')."""
        ps = self.mt5.positions_get(symbol=symbol) if symbol else self.mt5.positions_get()
        if ps is None:
            code = self.mt5.last_error()
            if code and code[0] not in (0, 1):     # 1 = success / nothing found
                return None
            ps = ()
        return [p for p in ps if p.magic == self.magic]

    def still_open(self, ticket):
        return bool(self.mt5.positions_get(ticket=ticket))

    def deals_for_position(self, ticket):
        return list(self.mt5.history_deals_get(position=ticket) or [])

    def closing_deals(self, ticket, tries=1, wait=0.05):
        """(all deals, out deals) of a position. History can lag a few ms after a close."""
        outs = (self.mt5.DEAL_ENTRY_OUT, self.mt5.DEAL_ENTRY_OUT_BY)
        for i in range(tries):
            deals = self.deals_for_position(ticket)
            out = [d for d in deals if d.entry in outs]
            if out:
                return deals, out
            if i + 1 < tries:
                time.sleep(wait)
        return [], []

    # ---------- orders ----------
    def _filling_for(self, spec):
        if spec.name in self._filling:
            return self._filling[spec.name]
        m = self.mt5
        if spec.filling_mode & getattr(m, "SYMBOL_FILLING_FOK", 1):
            f = m.ORDER_FILLING_FOK
        elif spec.filling_mode & getattr(m, "SYMBOL_FILLING_IOC", 2):
            f = m.ORDER_FILLING_IOC
        else:
            f = m.ORDER_FILLING_RETURN
        self._filling[spec.name] = f
        return f

    def _next_filling(self, spec):
        m = self.mt5
        order = [m.ORDER_FILLING_FOK, m.ORDER_FILLING_IOC, m.ORDER_FILLING_RETURN]
        cur = self._filling_for(spec)
        self._filling[spec.name] = order[(order.index(cur) + 1) % 3]

    def _send(self, spec, build, widen_stops=None):
        """Send with retries. build(tick) returns (request, requested_price)."""
        m = self.mt5
        last = OrderResult(ok=False, message="no attempt")
        for attempt in range(self.retries + 1):
            t = self.tick(spec.name)
            if t is None:
                last = OrderResult(ok=False, message="no price")
                time.sleep(self.retry_sleep)
                continue
            req, price = build(t)
            req["type_filling"] = self._filling_for(spec)
            t0 = time.perf_counter()
            res = m.order_send(req)
            ms = (time.perf_counter() - t0) * 1000
            if res is None:
                last = OrderResult(ok=False, req_price=price, latency_ms=ms,
                                   message=f"order_send returned None {m.last_error()}")
                time.sleep(self.retry_sleep)
                continue
            if res.retcode in self.DONE:
                return OrderResult(ok=True, ticket=res.order, price=res.price or price,
                                   req_price=price, retcode=res.retcode, latency_ms=ms)
            last = OrderResult(ok=False, req_price=price, retcode=res.retcode, latency_ms=ms,
                               message=f"retcode {res.retcode} {res.comment}")
            if res.retcode == m.TRADE_RETCODE_MARKET_CLOSED:
                last.market_closed = True
                return last
            if res.retcode == self.GONE:
                last.gone = True
                return last
            if res.retcode == m.TRADE_RETCODE_INVALID_FILL:
                self._next_filling(spec)
                continue
            if res.retcode == m.TRADE_RETCODE_INVALID_STOPS and widen_stops:
                widen_stops()
                continue
            if res.retcode not in self.RETRY:
                return last
            time.sleep(self.retry_sleep)
        return last

    def market_order(self, spec, side, volume, sl_dist, tp_dist, deviation, comment):
        """Market order with a broker-side stop loss and take profit, sl_dist / tp_dist (price) away.
        The broker runs both on its server, so they work with no bot delay and even if the bot stops."""
        m = self.mt5
        meta = {"sl": sl_dist, "tp": tp_dist}

        def build(t):
            price = t.ask if side == "BUY" else t.bid
            sgn = 1 if side == "BUY" else -1
            sl = spec.round_price(price - sgn * meta["sl"])
            tp = spec.round_price(price + sgn * meta["tp"]) if meta["tp"] else 0.0
            req = dict(action=m.TRADE_ACTION_DEAL, symbol=spec.name, volume=volume,
                       type=m.ORDER_TYPE_BUY if side == "BUY" else m.ORDER_TYPE_SELL,
                       price=price, sl=sl, tp=tp, deviation=int(deviation), magic=self.magic,
                       comment=comment[:31], type_time=m.ORDER_TIME_GTC)
            return req, price

        def widen():
            meta["sl"] *= 1.5
            meta["tp"] *= 1.5

        res = self._send(spec, build, widen)
        if res.ok:
            pos = self.mt5.positions_get(ticket=res.ticket)
            if pos:
                res.price = pos[0].price_open
                res.sl, res.tp = pos[0].sl, pos[0].tp
        return res

    def close(self, spec, pos, deviation, comment):
        m = self.mt5
        is_buy = pos.type == m.POSITION_TYPE_BUY

        def build(t):
            price = t.bid if is_buy else t.ask
            req = dict(action=m.TRADE_ACTION_DEAL, symbol=spec.name, volume=pos.volume,
                       type=m.ORDER_TYPE_SELL if is_buy else m.ORDER_TYPE_BUY,
                       position=pos.ticket, price=price, deviation=int(deviation),
                       magic=self.magic, comment=comment[:31], type_time=m.ORDER_TIME_GTC)
            return req, price

        return self._send(spec, build)

    def modify_sl(self, pos, sl):
        m = self.mt5
        req = dict(action=m.TRADE_ACTION_SLTP, symbol=pos.symbol, position=pos.ticket,
                   sl=sl, tp=pos.tp, magic=self.magic)
        res = m.order_send(req)
        return res is not None and res.retcode in self.DONE
