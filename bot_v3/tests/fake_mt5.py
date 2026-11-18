"""A small fake of the MetaTrader5 module: one symbol, ticks, positions with broker SL/TP, deals."""
import time
from types import SimpleNamespace as NS


class FakeMT5:
    ORDER_TYPE_BUY, ORDER_TYPE_SELL = 0, 1
    POSITION_TYPE_BUY, POSITION_TYPE_SELL = 0, 1
    TRADE_ACTION_DEAL, TRADE_ACTION_SLTP = 1, 6
    ORDER_FILLING_FOK, ORDER_FILLING_IOC, ORDER_FILLING_RETURN = 0, 1, 2
    SYMBOL_FILLING_FOK, SYMBOL_FILLING_IOC = 1, 2
    ORDER_TIME_GTC = 0
    TRADE_RETCODE_REQUOTE = 10004
    TRADE_RETCODE_DONE = 10009
    TRADE_RETCODE_DONE_PARTIAL = 10010
    TRADE_RETCODE_TIMEOUT = 10012
    TRADE_RETCODE_INVALID_STOPS = 10016
    TRADE_RETCODE_MARKET_CLOSED = 10018
    TRADE_RETCODE_NO_MONEY = 10019
    TRADE_RETCODE_PRICE_CHANGED = 10020
    TRADE_RETCODE_PRICE_OFF = 10021
    TRADE_RETCODE_TOO_MANY_REQUESTS = 10024
    TRADE_RETCODE_FROZEN = 10029
    TRADE_RETCODE_INVALID_FILL = 10030
    TRADE_RETCODE_CONNECTION = 10031
    TRADE_RETCODE_POSITION_CLOSED = 10036
    DEAL_ENTRY_IN, DEAL_ENTRY_OUT, DEAL_ENTRY_INOUT, DEAL_ENTRY_OUT_BY = 0, 1, 2, 3
    DEAL_REASON_CLIENT, DEAL_REASON_EXPERT, DEAL_REASON_SL, DEAL_REASON_TP, DEAL_REASON_SO = 0, 3, 4, 5, 6
    ACCOUNT_TRADE_MODE_DEMO, ACCOUNT_TRADE_MODE_REAL = 0, 2
    ACCOUNT_MARGIN_MODE_RETAIL_HEDGING = 2

    def __init__(self):
        self.symbols, self.ticks = {}, {}
        self.open_positions, self.deals, self.sent = {}, [], []
        self.fail_next = []           # retcodes to return before the next success
        self.next_ticket = 1000
        self.is_connected = True
        self.balance, self.margin_free_override = 1000.0, None
        self.margin_per_lot = 400.0   # 0.01 lot -> 4.0
        self.latency_s = 0.0          # sleep inside order_send (like a real broker round trip)
        self._msc = 0

    # ----- test helpers -----
    def add_symbol(self, name="XAUUSDm", point=0.001, digits=3, tick_value=0.1, contract=100.0,
                   vol_min=0.01, vol_step=0.01, vol_max=200.0, stops_level=0, filling=1,
                   base="XAU", profit="USD"):
        """Defaults = Exness XAUUSDm (Standard): point 0.001, tick value 0.1, contract 100."""
        self.symbols[name] = NS(name=name, point=point, digits=digits, trade_tick_size=point,
                                trade_tick_value=tick_value, trade_contract_size=contract,
                                volume_min=vol_min, volume_max=vol_max, volume_step=vol_step,
                                trade_stops_level=stops_level, trade_freeze_level=0,
                                filling_mode=filling, currency_base=base, currency_profit=profit)

    def set_tick(self, name, bid, ask, t=0):
        self._msc += 1
        self.ticks[name] = NS(bid=round(bid, 3), ask=round(ask, 3), time=int(t), time_msc=self._msc)
        tk = self.ticks[name]
        for p in [p for p in self.open_positions.values() if p.symbol == name]:
            px = tk.bid if p.type == 0 else tk.ask
            sgn = 1 if p.type == 0 else -1
            if p.sl and sgn * (px - p.sl) <= 0:            # broker stop fires, fills at the market
                self._close(p, px, self.DEAL_REASON_SL, p.magic)
            elif p.tp and sgn * (px - p.tp) >= 0:          # broker target fires
                self._close(p, px, self.DEAL_REASON_TP, p.magic)

    def _mpp(self, sym, vol):
        s = self.symbols[sym]
        return s.trade_tick_value / s.trade_tick_size * vol

    def _profit(self, p):
        t = self.ticks[p.symbol]
        diff = (t.bid - p.price_open) if p.type == 0 else (p.price_open - t.ask)
        return diff * self._mpp(p.symbol, p.volume)

    def _close(self, p, price, reason, magic):
        diff = (price - p.price_open) if p.type == 0 else (p.price_open - price)
        profit = diff * self._mpp(p.symbol, p.volume)
        self.balance += profit
        self.deals.append(NS(ticket=len(self.deals) + 1, position_id=p.ticket, entry=self.DEAL_ENTRY_OUT,
                             reason=reason, price=price, profit=profit, swap=0.0, commission=0.0, fee=0.0,
                             magic=magic, symbol=p.symbol))
        del self.open_positions[p.ticket]

    def add_position(self, symbol, side, volume, price, magic, sl=0.0, tp=0.0, comment=""):
        self.next_ticket += 1
        p = NS(ticket=self.next_ticket, symbol=symbol, type=0 if side == "BUY" else 1, volume=volume,
               price_open=price, sl=sl, tp=tp, magic=magic, profit=0.0, swap=0.0, time=0, comment=comment)
        self.open_positions[p.ticket] = p
        self.deals.append(NS(ticket=len(self.deals) + 1, position_id=p.ticket, entry=self.DEAL_ENTRY_IN,
                             reason=self.DEAL_REASON_EXPERT, price=price, profit=0.0, swap=0.0,
                             commission=0.0, fee=0.0, magic=magic, symbol=symbol))
        return p

    @property
    def equity(self):
        return self.balance + sum(self._profit(p) for p in self.open_positions.values())

    # ----- MetaTrader5 API -----
    def initialize(self, **kw):
        return True

    def shutdown(self):
        pass

    def last_error(self):
        return (1, "fake")

    def terminal_info(self):
        return NS(connected=self.is_connected, trade_allowed=True)

    def account_info(self):
        used = sum(self.margin_per_lot * p.volume for p in self.open_positions.values())
        free = self.equity - used if self.margin_free_override is None else self.margin_free_override
        return NS(login=1, trade_mode=0, margin_mode=2, currency="USD", balance=self.balance,
                  equity=self.equity, margin_free=free, server="Fake-Demo", leverage=200)

    def order_calc_margin(self, kind, symbol, volume, price):
        return self.margin_per_lot * volume

    def symbol_info(self, name):
        return self.symbols.get(name)

    def symbol_select(self, name, enable=True):
        return name in self.symbols

    def symbols_get(self, group="*"):
        key = group.strip("*")
        return [s for n, s in self.symbols.items() if key in n]

    def symbol_info_tick(self, name):
        return self.ticks.get(name)

    def positions_get(self, symbol=None, ticket=None):
        ps = list(self.open_positions.values())
        if symbol:
            ps = [p for p in ps if p.symbol == symbol]
        if ticket:
            ps = [p for p in ps if p.ticket == ticket]
        for p in ps:
            p.profit = self._profit(p)
        return tuple(ps)

    def history_deals_get(self, *args, position=None):
        if position is not None:
            return tuple(d for d in self.deals if d.position_id == position)
        return tuple(self.deals)

    def order_send(self, req):
        if self.latency_s:
            time.sleep(self.latency_s)
        self.sent.append(dict(req))
        if self.fail_next:
            return NS(retcode=self.fail_next.pop(0), comment="fake fail", order=0, price=0.0, deal=0)
        t = self.ticks[req["symbol"]]
        if "position" in req:
            p = self.open_positions.get(req["position"])
            if p is None:
                return NS(retcode=self.TRADE_RETCODE_POSITION_CLOSED, comment="gone", order=0, price=0.0, deal=0)
            price = t.bid if p.type == 0 else t.ask
            self._close(p, price, self.DEAL_REASON_EXPERT, req["magic"])
            return NS(retcode=self.TRADE_RETCODE_DONE, comment="", order=0, price=price, deal=len(self.deals))
        side = "BUY" if req["type"] == self.ORDER_TYPE_BUY else "SELL"
        price = t.ask if side == "BUY" else t.bid
        p = self.add_position(req["symbol"], side, req["volume"], price, req["magic"], req.get("sl", 0.0),
                              req.get("tp", 0.0), req.get("comment", ""))
        return NS(retcode=self.TRADE_RETCODE_DONE, comment="", order=p.ticket, price=price, deal=len(self.deals))
