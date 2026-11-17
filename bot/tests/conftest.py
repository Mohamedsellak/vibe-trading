import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config as C  # noqa: E402
from strategy import Bars  # noqa: E402


def make_bars(t0_ms, o, h, l, c, spread=0.1, n=10):
    """Bars helper: consecutive 1-minute bars starting at t0_ms."""
    o, h, l, c = (np.asarray(x, dtype=float) for x in (o, h, l, c))
    k = len(c)
    t = t0_ms + np.arange(k, dtype="int64") * 60_000
    sp = np.full(k, spread)
    return Bars(t=t, o=o, h=h, l=l, c=c, spread=sp, spread_ref=sp.copy(),
                n=np.full(k, n, dtype="int64"), last_tick=np.arange(k, dtype="int64"))


@pytest.fixture
def tmp_project(tmp_path, monkeypatch):
    """Redirect every data/result path of the project into a temp folder."""
    for name, rel in [("DATA_DIR", "data"), ("RESULTS_DIR", "results"), ("LOG_DIR", "logs")]:
        (tmp_path / rel).mkdir()
        monkeypatch.setattr(C, name, tmp_path / rel)
    monkeypatch.setattr(C, "EXPERIMENTS_FILE", tmp_path / "results" / "experiments.csv")
    monkeypatch.setattr(C, "FINAL_TEST_LOG", tmp_path / "results" / "final_test_log.json")
    monkeypatch.setattr(C, "CHOSEN_FILE", tmp_path / "results" / "chosen_strategy.json")
    monkeypatch.setattr(C, "NEWS_FILE", tmp_path / "news.csv")
    monkeypatch.setattr(C, "TRADE_DB", tmp_path / "logs" / "bot.sqlite")
    monkeypatch.setattr(C, "ENV_FILE", tmp_path / ".env")
    return tmp_path


class FakeMT5:
    """Minimal stand-in for the MetaTrader5 package."""
    TRADE_ACTION_DEAL, TRADE_ACTION_SLTP = 1, 6
    ORDER_TYPE_BUY, ORDER_TYPE_SELL = 0, 1
    POSITION_TYPE_BUY, POSITION_TYPE_SELL = 0, 1
    ORDER_FILLING_FOK, ORDER_FILLING_IOC, ORDER_FILLING_RETURN = 0, 1, 2
    ORDER_TIME_GTC = 0
    COPY_TICKS_ALL = -1
    TIMEFRAME_M1 = 1

    def __init__(self, trade_mode=0, symbols=("XAUUSDm",), filling_mode=1):
        self.trade_mode = trade_mode
        self.symbols = set(symbols)
        self.filling_mode = filling_mode
        self.results = []          # queued order_send results
        self.sent = []
        self.positions = []
        self.deals = {}
        self.bid, self.ask, self.tick_ms = 2000.00, 2000.20, 1_700_000_000_000
        self.ticks = None
        self.is_connected = True

    def initialize(self, **kw):
        self.init_kwargs = kw
        return True

    def shutdown(self):
        pass

    def last_error(self):
        return (1, "fake")

    def terminal_info(self):
        return SimpleNamespace(trade_allowed=True, connected=self.is_connected) if self.is_connected else None

    def account_info(self):
        return SimpleNamespace(login=123, server="Exness-MT5Trial", balance=10_000.0,
                               equity=10_000.0, currency="USD", trade_mode=self.trade_mode)

    def symbol_info(self, name):
        if name not in self.symbols:
            return None
        return SimpleNamespace(name=name, point=0.001, digits=3, trade_tick_size=0.001,
                               trade_tick_value=0.1, trade_contract_size=100.0, volume_min=0.01,
                               volume_max=200.0, volume_step=0.01, trade_stops_level=0,
                               trade_freeze_level=0, filling_mode=self.filling_mode, visible=True)

    def symbols_get(self, pattern):
        key = pattern.strip("*")
        return [SimpleNamespace(name=s) for s in self.symbols if key in s]

    def symbol_select(self, name, enable):
        return name in self.symbols

    def symbol_info_tick(self, name):
        return SimpleNamespace(bid=self.bid, ask=self.ask, time_msc=self.tick_ms,
                               time=self.tick_ms // 1000)

    def order_send(self, req):
        self.sent.append(dict(req))
        if self.results:
            r = self.results.pop(0)
        else:
            r = {"retcode": 10009}
        price = req.get("price", 0.0)
        return SimpleNamespace(retcode=r["retcode"], comment=r.get("comment", ""),
                               price=r.get("price", price), volume=req.get("volume", 0.0),
                               order=r.get("order", 555), deal=r.get("deal", 777))

    def positions_get(self, symbol=None):
        return tuple(self.positions)

    def history_deals_get(self, position=None):
        return self.deals.get(position, ())

    def copy_ticks_range(self, symbol, a, b, flags):
        return self.ticks

    def copy_ticks_from(self, symbol, a, count, flags):
        return self.ticks


def tick_array(times_ms, bids, asks):
    dt = np.dtype([("time", "i8"), ("bid", "f8"), ("ask", "f8"), ("last", "f8"),
                   ("volume", "u8"), ("time_msc", "i8"), ("flags", "u4"), ("volume_real", "f8")])
    a = np.zeros(len(times_ms), dtype=dt)
    a["time_msc"] = times_ms
    a["time"] = np.asarray(times_ms) // 1000
    a["bid"], a["ask"] = bids, asks
    return a
