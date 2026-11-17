"""The only module that talks to MetaTrader 5.

`MetaTrader5` is imported lazily, so everything else (backtests, unit tests)
runs on any OS. Tests inject a fake module through `MT5Broker(mt5_module=...)`.

Time convention: MT5 returns server wall-clock time encoded as epoch seconds
(and expects the same encoding in requests). This module converts to and
from true UTC milliseconds using `server_tz` (Exness = UTC).
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np

from config import Config, SymbolSpec
from strategy import round_price, server_to_utc_ms, utc_to_server_ms

log = logging.getLogger("broker")

# Trade server return codes (MQL5 ENUM_TRADE_RETURN_CODES)
RC_REQUOTE = 10004
RC_PLACED = 10008
RC_DONE = 10009
RC_DONE_PARTIAL = 10010
RC_TIMEOUT = 10012
RC_INVALID_VOLUME = 10014
RC_INVALID_STOPS = 10016
RC_MARKET_CLOSED = 10018
RC_NO_MONEY = 10019
RC_PRICE_CHANGED = 10020
RC_PRICE_OFF = 10021
RC_TOO_MANY = 10024
RC_AUTOTRADING_SERVER = 10026
RC_AUTOTRADING_CLIENT = 10027
RC_LOCKED = 10028
RC_FROZEN = 10029
RC_INVALID_FILL = 10030
RC_CONNECTION = 10031

RETRYABLE = {RC_REQUOTE, RC_TIMEOUT, RC_PRICE_CHANGED, RC_PRICE_OFF, RC_TOO_MANY,
             RC_CONNECTION, RC_LOCKED, RC_FROZEN}
SUCCESS = {RC_DONE, RC_DONE_PARTIAL, RC_PLACED}

ACCOUNT_TRADE_MODE_DEMO = 0
ACCOUNT_TRADE_MODE_CONTEST = 1
ACCOUNT_TRADE_MODE_REAL = 2

SYMBOL_FILLING_FOK = 1
SYMBOL_FILLING_IOC = 2


class BrokerError(RuntimeError):
    pass


@dataclass
class OrderResult:
    ok: bool
    retcode: int
    comment: str
    ticket: int            # position ticket (for opens) or deal/order id
    requested_price: float
    fill_price: float
    volume: float
    latency_ms: float      # order_send round trip, last attempt
    total_ms: float        # first attempt to final answer, retries included
    attempts: int
    slippage_points: float  # positive = worse than requested


class MT5Broker:
    def __init__(self, cfg: Config, mt5_module=None, sleep=time.sleep):
        if mt5_module is None:
            try:
                import MetaTrader5 as mt5_module  # noqa: N813
            except ImportError as exc:  # pragma: no cover - depends on OS
                raise BrokerError(
                    "MetaTrader5 package not available. It runs only on Windows "
                    "with the MT5 terminal installed: pip install MetaTrader5") from exc
        self.mt5 = mt5_module
        self.cfg = cfg
        self.sleep = sleep
        self.symbol: str | None = None
        self.spec: SymbolSpec | None = None

    # ---------------- connection ----------------
    def connect(self) -> None:
        kwargs = {}
        if self.cfg.mt5_path:
            kwargs["path"] = self.cfg.mt5_path
        if self.cfg.mt5_login:
            kwargs.update(login=int(self.cfg.mt5_login), password=self.cfg.mt5_password or "",
                          server=self.cfg.mt5_server or "")
        if not self.mt5.initialize(**kwargs):
            raise BrokerError(f"initialize() failed: {self.mt5.last_error()}")
        term = self.mt5.terminal_info()
        if term is None:
            raise BrokerError(f"terminal_info() failed: {self.mt5.last_error()}")
        if not getattr(term, "trade_allowed", True):
            raise BrokerError("Algo trading is disabled in the terminal (enable the Algo Trading button)")
        acc = self.mt5.account_info()
        if acc is None:
            raise BrokerError(f"account_info() failed: {self.mt5.last_error()}")
        log.info("connected login=%s server=%s mode=%s balance=%.2f %s", acc.login, acc.server,
                 self.account_mode(), acc.balance, acc.currency)

    def connected(self) -> bool:
        term = self.mt5.terminal_info()
        return bool(term is not None and getattr(term, "connected", True))

    def ensure_connected(self) -> None:
        """Reconnect with exponential backoff; raises after reconnect_max_wait_s."""
        if self.connected():
            return
        waited, delay = 0.0, 1.0
        while waited < self.cfg.execution.reconnect_max_wait_s:
            log.warning("terminal disconnected, reconnecting in %.0fs", delay)
            self.sleep(delay)
            waited += delay
            try:
                self.mt5.shutdown()
                self.connect()
                if self.connected():
                    if self.symbol:
                        self.mt5.symbol_select(self.symbol, True)
                    return
            except BrokerError as exc:
                log.warning("reconnect failed: %s", exc)
            delay = min(delay * 2, 15.0)
        raise BrokerError("could not reconnect to the MT5 terminal")

    def shutdown(self) -> None:
        self.mt5.shutdown()

    # ---------------- account ----------------
    def account_mode(self) -> str:
        acc = self.mt5.account_info()
        mode = getattr(acc, "trade_mode", None)
        return {ACCOUNT_TRADE_MODE_DEMO: "demo", ACCOUNT_TRADE_MODE_CONTEST: "contest",
                ACCOUNT_TRADE_MODE_REAL: "real"}.get(mode, f"unknown({mode})")

    def is_demo(self) -> bool:
        return self.account_mode() == "demo"

    def account_login(self) -> int:
        return int(self.mt5.account_info().login)

    def equity(self) -> float:
        return float(self.mt5.account_info().equity)

    def balance(self) -> float:
        return float(self.mt5.account_info().balance)

    # ---------------- symbols ----------------
    def resolve_symbol(self, base: str) -> str:
        """Exact name first, then broker variants such as XAUUSDm / XAUUSDc."""
        info = self.mt5.symbol_info(base)
        if info is None:
            cands = self.mt5.symbols_get(f"*{base}*") or ()
            names = sorted((s.name for s in cands if s.name.upper().startswith(base.upper())),
                           key=len)
            if not names:
                raise BrokerError(f"symbol {base} not found on this server")
            if len(names) > 1:
                log.info("symbol candidates for %s: %s (using %s)", base, names, names[0])
            name = names[0]
        else:
            name = info.name
        if not self.mt5.symbol_select(name, True):
            raise BrokerError(f"symbol_select({name}) failed: {self.mt5.last_error()}")
        self.symbol = name
        return name

    def symbol_spec(self, name: str | None = None) -> SymbolSpec:
        name = name or self.symbol
        i = self.mt5.symbol_info(name)
        if i is None:
            raise BrokerError(f"symbol_info({name}) failed: {self.mt5.last_error()}")
        spec = SymbolSpec(name=name, point=float(i.point), digits=int(i.digits),
                          tick_size=float(i.trade_tick_size), tick_value=float(i.trade_tick_value),
                          contract_size=float(i.trade_contract_size),
                          volume_min=float(i.volume_min), volume_max=float(i.volume_max),
                          volume_step=float(i.volume_step), stops_level=int(i.trade_stops_level),
                          freeze_level=int(i.trade_freeze_level), filling_mode=int(i.filling_mode),
                          source="mt5")
        self.spec = spec
        return spec

    def filling_candidates(self) -> list[int]:
        """Filling modes allowed by the symbol bitmask, best first."""
        fm = self.spec.filling_mode if self.spec else 0
        out = []
        if fm & SYMBOL_FILLING_FOK:
            out.append(self.mt5.ORDER_FILLING_FOK)
        if fm & SYMBOL_FILLING_IOC:
            out.append(self.mt5.ORDER_FILLING_IOC)
        out.append(self.mt5.ORDER_FILLING_RETURN)
        return out

    # ---------------- time ----------------
    def _to_mt5_dt(self, utc_ms: int) -> datetime:
        server_ms = int(utc_to_server_ms(np.array([utc_ms]), self.cfg.server_tz)[0])
        return datetime.fromtimestamp(server_ms / 1000, tz=timezone.utc)

    def server_offset_minutes(self) -> float | None:
        """Observed (tick time - real UTC) in minutes, or None if quotes are stale."""
        t = self.mt5.symbol_info_tick(self.symbol)
        if t is None:
            return None
        diff_min = (t.time_msc / 1000.0 - time.time()) / 60.0
        rounded = round(diff_min / 30.0) * 30.0
        if abs(diff_min - rounded) > 5:      # last tick is old: market closed
            return None
        return rounded

    # ---------------- market data ----------------
    def latest_tick(self) -> tuple[int, float, float] | None:
        t = self.mt5.symbol_info_tick(self.symbol)
        if t is None or t.bid <= 0 or t.ask <= 0:
            return None
        utc = int(server_to_utc_ms(np.array([t.time_msc]), self.cfg.server_tz)[0])
        return utc, float(t.bid), float(t.ask)

    def _ticks_to_arrays(self, raw) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        if raw is None or len(raw) == 0:
            z = np.array([], dtype="int64")
            return z, np.array([], dtype=float), np.array([], dtype=float)
        tms = np.asarray(raw["time_msc"], dtype="int64")
        bid = np.asarray(raw["bid"], dtype=float)
        ask = np.asarray(raw["ask"], dtype=float)
        keep = (bid > 0) & (ask > 0)
        return server_to_utc_ms(tms[keep], self.cfg.server_tz), bid[keep], ask[keep]

    def ticks_range(self, from_utc_ms: int, to_utc_ms: int, symbol: str | None = None):
        raw = self.mt5.copy_ticks_range(symbol or self.symbol, self._to_mt5_dt(from_utc_ms),
                                        self._to_mt5_dt(to_utc_ms), self.mt5.COPY_TICKS_ALL)
        return self._ticks_to_arrays(raw)

    def ticks_from(self, from_utc_ms: int, count: int = 100_000):
        raw = self.mt5.copy_ticks_from(self.symbol, self._to_mt5_dt(from_utc_ms), count,
                                       self.mt5.COPY_TICKS_ALL)
        return self._ticks_to_arrays(raw)

    def rates_range_m1(self, from_utc_ms: int, to_utc_ms: int, symbol: str | None = None):
        raw = self.mt5.copy_rates_range(symbol or self.symbol, self.mt5.TIMEFRAME_M1,
                                        self._to_mt5_dt(from_utc_ms), self._to_mt5_dt(to_utc_ms))
        if raw is None or len(raw) == 0:
            return None
        t = server_to_utc_ms(np.asarray(raw["time"], dtype="int64") * 1000, self.cfg.server_tz)
        return {"t": t, "o": np.asarray(raw["open"], float), "h": np.asarray(raw["high"], float),
                "l": np.asarray(raw["low"], float), "c": np.asarray(raw["close"], float),
                "spread_points": np.asarray(raw["spread"], float),
                "tick_volume": np.asarray(raw["tick_volume"], float)}

    def last_error(self):
        return self.mt5.last_error()

    # ---------------- positions ----------------
    def positions(self) -> list:
        magic = self.cfg.execution.magic
        return [p for p in (self.mt5.positions_get(symbol=self.symbol) or ()) if p.magic == magic]

    def closed_position_pnl(self, position_ticket: int) -> tuple[float, int] | None:
        """(profit + commission + swap + fee, close time UTC ms) of a closed position."""
        deals = self.mt5.history_deals_get(position=position_ticket)
        if not deals:
            return None
        pnl = sum(float(d.profit) + float(getattr(d, "commission", 0.0)) + float(d.swap)
                  + float(getattr(d, "fee", 0.0)) for d in deals)
        last_ms = max(int(d.time_msc) for d in deals)
        return pnl, int(server_to_utc_ms(np.array([last_ms]), self.cfg.server_tz)[0])

    # ---------------- orders ----------------
    def _send(self, build_request, side: int) -> OrderResult:
        """Send with retries. `build_request(price)` rebuilds the request on each attempt."""
        ex = self.cfg.execution
        t_first = time.perf_counter()
        fills = self.filling_candidates()
        fill_idx = 0
        last_rc, last_comment, latency = -1, "", 0.0
        price = 0.0
        attempt = 0
        while attempt < ex.max_retries + 1:
            attempt += 1
            tick = self.mt5.symbol_info_tick(self.symbol)
            if tick is None:
                self.ensure_connected()
                continue
            price = float(tick.ask if side > 0 else tick.bid)
            req = build_request(price)
            req["type_filling"] = fills[fill_idx]
            t0 = time.perf_counter()
            res = self.mt5.order_send(req)
            latency = (time.perf_counter() - t0) * 1000.0
            if res is None:
                last_rc, last_comment = -1, str(self.mt5.last_error())
                self.ensure_connected()
                self.sleep(ex.retry_backoff_ms / 1000.0 * attempt)
                continue
            last_rc, last_comment = int(res.retcode), str(getattr(res, "comment", ""))
            if last_rc in SUCCESS:
                fill = float(res.price) if getattr(res, "price", 0) else price
                pt = self.spec.point if self.spec else 1.0
                slip = (fill - price) * side / pt
                ticket = int(getattr(res, "order", 0) or getattr(res, "deal", 0))
                return OrderResult(True, last_rc, last_comment, ticket, price, fill,
                                   float(getattr(res, "volume", req.get("volume", 0.0))), latency,
                                   (time.perf_counter() - t_first) * 1000.0, attempt, slip)
            if last_rc == RC_INVALID_FILL and fill_idx + 1 < len(fills):
                fill_idx += 1
                attempt -= 1               # a filling-mode switch is not a retry
                continue
            if last_rc in RETRYABLE:
                log.warning("retcode %s (%s), retry %d", last_rc, last_comment, attempt)
                self.sleep(ex.retry_backoff_ms / 1000.0 * attempt)
                continue
            break                           # market closed, no money, invalid stops ...
        return OrderResult(False, last_rc, last_comment, 0, price, 0.0, 0.0, latency,
                           (time.perf_counter() - t_first) * 1000.0, attempt, 0.0)

    def open_market(self, side: int, volume: float, sl_dist: float, tp_dist: float,
                    comment: str = "") -> OrderResult:
        """Market order. SL/TP are placed relative to the price at each attempt."""
        spec, mt5 = self.spec, self.mt5

        def build(price: float) -> dict:
            sl = price - side * sl_dist
            tp = price + side * tp_dist
            return {"action": mt5.TRADE_ACTION_DEAL, "symbol": self.symbol, "volume": volume,
                    "type": mt5.ORDER_TYPE_BUY if side > 0 else mt5.ORDER_TYPE_SELL,
                    "price": price, "sl": round_price(sl, spec.tick_size, spec.digits),
                    "tp": round_price(tp, spec.tick_size, spec.digits),
                    "deviation": self.cfg.execution.deviation_points,
                    "magic": self.cfg.execution.magic, "comment": comment[:31],
                    "type_time": mt5.ORDER_TIME_GTC}
        res = self._send(build, side)
        if res.ok:
            # On hedging accounts the position ticket equals the opening order ticket.
            pos = [p for p in self.positions() if p.ticket == res.ticket]
            if not pos:
                pos = sorted(self.positions(), key=lambda p: p.time_msc)[-1:]
            if pos:
                res.ticket = int(pos[0].ticket)
        return res

    def close_position(self, pos, comment: str = "close") -> OrderResult:
        mt5 = self.mt5
        side = -1 if pos.type == mt5.POSITION_TYPE_BUY else 1   # side of the closing deal

        def build(price: float) -> dict:
            return {"action": mt5.TRADE_ACTION_DEAL, "symbol": pos.symbol, "volume": pos.volume,
                    "type": mt5.ORDER_TYPE_BUY if side > 0 else mt5.ORDER_TYPE_SELL,
                    "position": pos.ticket, "price": price,
                    "deviation": self.cfg.execution.deviation_points,
                    "magic": self.cfg.execution.magic, "comment": comment[:31],
                    "type_time": mt5.ORDER_TIME_GTC}
        return self._send(build, side)

    def modify_sltp(self, pos, sl: float, tp: float) -> bool:
        spec = self.spec
        req = {"action": self.mt5.TRADE_ACTION_SLTP, "symbol": pos.symbol, "position": pos.ticket,
               "sl": round_price(sl, spec.tick_size, spec.digits),
               "tp": round_price(tp, spec.tick_size, spec.digits),
               "magic": self.cfg.execution.magic}
        for attempt in range(self.cfg.execution.max_retries + 1):
            res = self.mt5.order_send(req)
            if res is not None and res.retcode in SUCCESS:
                return True
            rc = getattr(res, "retcode", -1)
            if rc not in RETRYABLE and res is not None:
                log.error("modify_sltp failed retcode=%s %s", rc, getattr(res, "comment", ""))
                return False
            self.sleep(self.cfg.execution.retry_backoff_ms / 1000.0 * (attempt + 1))
        return False
