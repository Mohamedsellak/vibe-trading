"""MetaTrader 5 access: symbol info, orders with retries, and the order executor.

The mt5 module is passed in, so tests can use a fake one.
Every number about the symbol comes from symbol_info(), never from constants here.

Why an executor: order_send() blocks until the broker answers (about 0.5-1 s on Exness demo gold).
If the main loop sent orders itself, it would stop watching prices for that long.
- ProcessExecutor (default): a 2nd Python process with its OWN MT5 connection sends the orders.
  The main process keeps reading ticks every 15 ms, whatever the order latency.
- ThreadExecutor (fallback): a worker thread. The MetaTrader5 package is not documented as
  thread-safe, so every MT5 call in the whole program goes through one lock (LockedMT5).
  Orders then still pause tick reading while they are sent.
- SyncExecutor: sends at once, in the caller. Used by the tests.
One worker = one order at a time, in the order received (closes first). So two orders for the
same trade can never race each other, and the bot never queues a 2nd close for a ticket.
"""
from __future__ import annotations

import itertools
import queue
import threading
import time
from dataclasses import dataclass, asdict


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
    latency_ms: float = 0.0     # order_send() call: request out -> broker answer
    market_closed: bool = False
    message: str = ""
    gone: bool = False          # the position was already closed (its broker stop or target fired)
    no_money: bool = False      # broker said: not enough free margin
    sl: float = 0.0
    tp: float = 0.0


class LockedMT5:
    """The mt5 module with one lock around every function call (thread mode)."""

    def __init__(self, mt5):
        self._m = mt5
        self._lock = threading.RLock()
        self._wrapped = {}

    def __getattr__(self, name):
        v = getattr(self._m, name)
        if not callable(v) or isinstance(v, type):
            return v
        f = self._wrapped.get(name)
        if f is None:
            def f(*a, _v=v, **k):
                with self._lock:
                    return _v(*a, **k)
            self._wrapped[name] = f
        return f


class Broker:
    def __init__(self, mt5, magic, log=None, retries=2, retry_sleep=0.05):
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
                      getattr(m, "TRADE_RETCODE_FROZEN", 10029)}
        self.GONE = getattr(m, "TRADE_RETCODE_POSITION_CLOSED", 10036)
        self.NO_MONEY = getattr(m, "TRADE_RETCODE_NO_MONEY", 10019)

    # ---------- connection ----------
    def connect(self, **kw):
        self._login = {k: v for k, v in kw.items() if v}
        if "login" in self._login:
            self._login["login"] = int(self._login["login"])
        ok = self.mt5.initialize(**self._login)
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

    def margin_needed(self, spec, side, volume, price):
        """Margin for this order from MT5 itself, or None if MT5 cannot tell."""
        m = self.mt5
        kind = m.ORDER_TYPE_BUY if side == "BUY" else m.ORDER_TYPE_SELL
        try:
            return m.order_calc_margin(kind, spec.name, volume, price)
        except Exception:
            return None

    # ---------- symbols ----------
    def resolve(self, base):
        """Find the broker's real name for a symbol (Exness may add a suffix, e.g. XAUUSDm)."""
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

    # ---------- positions and history ----------
    def positions(self, symbol=None):
        """The bot's open positions, or None if MT5 could not answer (an error is never 'no trades')."""
        ps = self.mt5.positions_get(symbol=symbol) if symbol else self.mt5.positions_get()
        if ps is None:
            code = self.mt5.last_error()
            if code and code[0] not in (0, 1):
                return None
            ps = ()
        return [p for p in ps if p.magic == self.magic]

    def still_open(self, ticket):
        return bool(self.mt5.positions_get(ticket=ticket))

    def closing_deals(self, ticket, tries=1, wait=0.03):
        """(all deals, out deals) of a position. History can lag a few ms after a close."""
        outs = (self.mt5.DEAL_ENTRY_OUT, self.mt5.DEAL_ENTRY_OUT_BY)
        for i in range(tries):
            deals = list(self.mt5.history_deals_get(position=ticket) or [])
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
            if res.retcode == self.NO_MONEY:
                last.no_money = True
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
        """Market order with a broker-side stop loss and take profit, set in the same request.
        sl_dist / tp_dist are price distances from the price we ask for.
        The broker runs both on its server: no bot delay, and they work even if the bot dies."""
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

        def widen():                     # broker said "invalid stops": too close, move both out
            meta["sl"] *= 1.5
            meta["tp"] *= 1.5

        res = self._send(spec, build, widen)
        if res.ok:
            pos = self.mt5.positions_get(ticket=res.ticket)
            if pos:
                res.price = pos[0].price_open
                res.sl, res.tp = pos[0].sl, pos[0].tp
        return res

    def close(self, spec, ticket, pos_type, volume, deviation, comment):
        m = self.mt5
        is_buy = pos_type == m.POSITION_TYPE_BUY

        def build(t):
            price = t.bid if is_buy else t.ask
            req = dict(action=m.TRADE_ACTION_DEAL, symbol=spec.name, volume=volume,
                       type=m.ORDER_TYPE_SELL if is_buy else m.ORDER_TYPE_BUY,
                       position=ticket, price=price, deviation=int(deviation),
                       magic=self.magic, comment=comment[:31], type_time=m.ORDER_TIME_GTC)
            return req, price

        return self._send(spec, build)


# ---------------- executor ----------------
_ids = itertools.count(1)


def new_cmd(kind, **kw):
    """An order command. kind = 'open' or 'close'."""
    return dict(id=next(_ids), kind=kind, created=time.time(), **kw)


def execute(broker, spec, cmd, max_age_s):
    """Run one command. Returns a plain dict (it may cross a process boundary)."""
    start = time.time()
    out = dict(id=cmd["id"], kind=cmd["kind"], queue_ms=(start - cmd["created"]) * 1000)
    if cmd["kind"] == "open" and start - cmd["created"] > max_age_s:
        out.update(ok=False, stale=True, message="stale: waited too long in the queue")
        return out
    if not broker.connected():
        broker.reconnect()
    try:
        if cmd["kind"] == "open":
            res = broker.market_order(spec, cmd["side"], cmd["volume"], cmd["sl_dist"], cmd["tp_dist"],
                                      cmd["deviation"], cmd["comment"])
        else:
            res = broker.close(spec, cmd["ticket"], cmd["pos_type"], cmd["volume"], cmd["deviation"],
                               cmd["comment"])
        out.update(asdict(res))
    except Exception as e:          # never let one bad order kill the worker
        out.update(ok=False, message=f"{type(e).__name__}: {e}")
    out["done"] = time.time()
    return out


def _worker_loop(broker, spec, close_q, open_q, res_q, max_age_s, stop_flag=None):
    while stop_flag is None or not stop_flag.is_set():
        try:
            cmd = close_q.get_nowait()          # closes always go first
        except queue.Empty:
            try:
                cmd = open_q.get(timeout=0.005)
            except queue.Empty:
                continue
        if cmd is None:
            return
        res_q.put(execute(broker, spec, cmd, max_age_s))


def process_main(close_q, open_q, res_q, login_kw, symbol, magic, retries, max_age_s, module="MetaTrader5"):
    """Entry point of the order process (Windows 'spawn': must be a module-level function)."""
    import importlib
    mt5 = importlib.import_module(module)
    broker = Broker(mt5, magic, retries=retries)
    ok = broker.connect(**login_kw)
    if not ok:
        res_q.put(dict(id=0, kind="ready", ok=False, message=f"initialize failed {mt5.last_error()}"))
        return
    res_q.put(dict(id=0, kind="ready", ok=True, message=""))
    try:
        _worker_loop(broker, broker.spec(symbol), close_q, open_q, res_q, max_age_s)
    except KeyboardInterrupt:      # Ctrl+C reaches both processes: the main one decides what to close
        pass
    finally:
        mt5.shutdown()


class _QueueExecutor:
    def __init__(self):
        self.inflight = {}           # id -> cmd

    def submit(self, cmd):
        self.inflight[cmd["id"]] = cmd
        (self.close_q if cmd["kind"] == "close" else self.open_q).put(cmd)

    def results(self):
        out = []
        while True:
            try:
                r = self.res_q.get_nowait()
            except queue.Empty:
                break
            except Exception:        # a closed multiprocessing queue
                break
            if r.get("kind") == "ready":
                self.ready = r
                continue
            out.append(r)
            self.inflight.pop(r["id"], None)
        return out


class ThreadExecutor(_QueueExecutor):
    name = "thread"

    def __init__(self, broker, spec, max_age_s):
        super().__init__()
        self.close_q, self.open_q, self.res_q = queue.Queue(), queue.Queue(), queue.Queue()
        self._stop = threading.Event()
        self.ready = dict(ok=True)
        self.t = threading.Thread(target=_worker_loop, daemon=True,
                                  args=(broker, spec, self.close_q, self.open_q, self.res_q, max_age_s, self._stop))
        self.t.start()

    def stop(self, wait=3.0):
        self.close_q.put(None)
        self._stop.set()
        self.t.join(wait)


class ProcessExecutor(_QueueExecutor):
    name = "process"

    def __init__(self, login_kw, symbol, magic, retries, max_age_s, module="MetaTrader5"):
        super().__init__()
        import multiprocessing as mp
        ctx = mp.get_context("spawn")
        self.close_q, self.open_q, self.res_q = ctx.Queue(), ctx.Queue(), ctx.Queue()
        self.ready = None
        self.p = ctx.Process(target=process_main, daemon=True,
                             args=(self.close_q, self.open_q, self.res_q, login_kw, symbol, magic,
                                   retries, max_age_s, module))
        self.p.start()

    def wait_ready(self, timeout=20.0):
        end = time.time() + timeout
        while time.time() < end and self.ready is None:
            try:
                r = self.res_q.get(timeout=0.2)
            except queue.Empty:
                if not self.p.is_alive():
                    break
                continue
            if r.get("kind") == "ready":
                self.ready = r
        return bool(self.ready and self.ready.get("ok"))

    def alive(self):
        return self.p.is_alive()

    def stop(self, wait=5.0):
        try:
            self.close_q.put(None)
        except Exception:
            pass
        self.p.join(wait)
        if self.p.is_alive():
            self.p.terminate()


class SyncExecutor:
    """Runs each command at once (tests and simulations). Results come out on the next results()."""
    name = "sync"

    def __init__(self, broker, spec, max_age_s=10.0):
        self.b, self.spec, self.max_age_s = broker, spec, max_age_s
        self.inflight, self._done = {}, []

    def submit(self, cmd):
        self.inflight[cmd["id"]] = cmd
        self._done.append(execute(self.b, self.spec, cmd, self.max_age_s))

    def results(self):
        out, self._done = self._done, []
        for r in out:
            self.inflight.pop(r["id"], None)
        return out

    def stop(self, wait=0):
        pass
