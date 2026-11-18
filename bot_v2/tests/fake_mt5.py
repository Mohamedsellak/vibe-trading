"""A small fake of the MetaTrader5 module: symbols, ticks, positions, deals, bars."""
from types import SimpleNamespace as NS


class FakeMT5:
    TIMEFRAME_M1 = 1
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
    TRADE_RETCODE_PRICE_CHANGED = 10020
    TRADE_RETCODE_PRICE_OFF = 10021
    TRADE_RETCODE_TOO_MANY_REQUESTS = 10024
    TRADE_RETCODE_INVALID_FILL = 10030
    TRADE_RETCODE_CONNECTION = 10031
    DEAL_ENTRY_IN, DEAL_ENTRY_OUT, DEAL_ENTRY_INOUT, DEAL_ENTRY_OUT_BY = 0, 1, 2, 3
    DEAL_REASON_CLIENT, DEAL_REASON_EXPERT, DEAL_REASON_SL, DEAL_REASON_TP, DEAL_REASON_SO = 0, 3, 4, 5, 6
    ACCOUNT_TRADE_MODE_DEMO, ACCOUNT_TRADE_MODE_REAL = 0, 2
    ACCOUNT_MARGIN_MODE_RETAIL_HEDGING = 2

    def __init__(self):
        self.symbols, self.ticks, self.rates = {}, {}, {}
        self.open_positions, self.deals, self.sent = {}, [], []
        self.fail_next = []          # retcodes to return before the next success
        self.accepted_filling = None  # if set, other filling modes get INVALID_FILL
        self.next_ticket = 1000
        self.is_connected = True
        self.auto_stops = True

    # ----- test helpers -----
    def add_symbol(self, name="XAUUSDm", point=0.01, digits=2, tick_value=1.0, contract=100.0,
                   vol_min=0.01, vol_step=0.01, vol_max=200.0, stops_level=0, filling=1,
                   base="XAU", profit="USD"):
        self.symbols[name] = NS(name=name, point=point, digits=digits, trade_tick_size=point,
                                trade_tick_value=tick_value, trade_contract_size=contract,
                                volume_min=vol_min, volume_max=vol_max, volume_step=vol_step,
                                trade_stops_level=stops_level, trade_freeze_level=0,
                                filling_mode=filling, currency_base=base, currency_profit=profit)

    def set_tick(self, name, bid, ask, t=0):
        self.ticks[name] = NS(bid=round(bid, 5), ask=round(ask, 5), time=int(t))
        if self.auto_stops:          # like a broker: stops and targets fire on the server
            tk = self.ticks[name]
            for p in [p for p in self.open_positions.values() if p.symbol == name]:
                px = tk.bid if p.type == 0 else tk.ask
                sgn = 1 if p.type == 0 else -1
                if p.sl and sgn * (px - p.sl) <= 0:
                    self._close(p, px, self.DEAL_REASON_SL, p.magic)
                elif p.tp and sgn * (px - p.tp) >= 0:
                    self._close(p, px, self.DEAL_REASON_TP, p.magic)

    def set_bars(self, name, closes):
        self.rates[name] = [{"high": c + 0.05, "low": c - 0.05, "close": c} for c in closes]

    def _mpp(self, sym, vol):
        s = self.symbols[sym]
        return s.trade_tick_value / s.trade_tick_size * vol

    def _profit(self, p):
        t = self.ticks[p.symbol]
        diff = (t.bid - p.price_open) if p.type == 0 else (p.price_open - t.ask)
        return diff * self._mpp(p.symbol, p.volume)

    def _close(self, p, price, reason, magic):
        diff = (price - p.price_open) if p.type == 0 else (p.price_open - price)
        self.deals.append(NS(ticket=len(self.deals) + 1, position_id=p.ticket, entry=self.DEAL_ENTRY_OUT,
                             reason=reason, price=price, profit=diff * self._mpp(p.symbol, p.volume),
                             swap=0.0, commission=0.0, fee=0.0, magic=magic, symbol=p.symbol))
        del self.open_positions[p.ticket]

    def hit_sl(self, ticket):
        p = self.open_positions[ticket]
        self._close(p, p.sl, self.DEAL_REASON_SL, p.magic)

    def set_bars_atr(self, name, closes, rng):
        """Bars whose high-low range is rng, so ATR is about rng (when closes move less than that)."""
        self.rates[name] = [{"high": c + rng / 2, "low": c - rng / 2, "close": c} for c in closes]

    def add_position(self, symbol, side, volume, price, magic, sl=0.0, tp=0.0):
        self.next_ticket += 1
        p = NS(ticket=self.next_ticket, symbol=symbol, type=0 if side == "BUY" else 1, volume=volume,
               price_open=price, sl=sl, tp=tp, magic=magic, profit=0.0, swap=0.0, time=0)
        self.open_positions[p.ticket] = p
        self.deals.append(NS(ticket=len(self.deals) + 1, position_id=p.ticket, entry=self.DEAL_ENTRY_IN,
                             reason=self.DEAL_REASON_EXPERT, price=price, profit=0.0, swap=0.0,
                             commission=0.0, fee=0.0, magic=magic, symbol=symbol))
        return p

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
        return NS(login=1, trade_mode=0, margin_mode=2, currency="USD", balance=1000.0,
                  server="Fake-Demo", leverage=100)

    def symbol_info(self, name):
        return self.symbols.get(name)

    def symbol_select(self, name, enable=True):
        return name in self.symbols

    def symbols_get(self, group="*"):
        key = group.strip("*")
        return [s for n, s in self.symbols.items() if key in n]

    def symbol_info_tick(self, name):
        return self.ticks.get(name)

    def copy_rates_from_pos(self, name, tf, start, count):
        return self.rates.get(name, [])[-count:]

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
        self.sent.append(dict(req))
        if self.fail_next:
            return NS(retcode=self.fail_next.pop(0), comment="fake fail", order=0, price=0.0, deal=0)
        if self.accepted_filling is not None and req.get("type_filling") != self.accepted_filling \
                and req["action"] == self.TRADE_ACTION_DEAL:
            return NS(retcode=self.TRADE_RETCODE_INVALID_FILL, comment="bad fill", order=0, price=0.0, deal=0)
        if req["action"] == self.TRADE_ACTION_SLTP:
            p = self.open_positions[req["position"]]
            p.sl, p.tp = req["sl"], req.get("tp", p.tp)
            return NS(retcode=self.TRADE_RETCODE_DONE, comment="", order=0, price=0.0, deal=0)
        t = self.ticks[req["symbol"]]
        if "position" in req:
            p = self.open_positions[req["position"]]
            price = t.bid if p.type == 0 else t.ask
            self._close(p, price, self.DEAL_REASON_EXPERT, req["magic"])
            return NS(retcode=self.TRADE_RETCODE_DONE, comment="", order=0, price=price, deal=len(self.deals))
        side = "BUY" if req["type"] == self.ORDER_TYPE_BUY else "SELL"
        price = t.ask if side == "BUY" else t.bid
        p = self.add_position(req["symbol"], side, req["volume"], price, req["magic"], req.get("sl", 0.0),
                              req.get("tp", 0.0))
        return NS(retcode=self.TRADE_RETCODE_DONE, comment="", order=p.ticket, price=price, deal=len(self.deals))
