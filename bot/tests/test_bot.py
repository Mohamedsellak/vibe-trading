from types import SimpleNamespace

import numpy as np

import bot as B
import config as C
from broker import MT5Broker
from config import load_config
from conftest import FakeMT5, tick_array
from strategy import MINUTE_MS, Signal


def test_live_guard():
    assert B.live_guard("demo", False, 1)
    assert not B.live_guard("real", False, 1)
    assert not B.live_guard("real", True, 7, input_fn=lambda _: "yes")
    assert B.live_guard("real", True, 7, input_fn=lambda _: "TRADE LIVE 7")
    assert not B.live_guard("contest", False, 7)


def test_strategy_guard():
    good = {"symbol": "XAUUSD", "passed_gates": True}
    bad = {"symbol": "XAUUSD", "passed_gates": False}
    assert B.strategy_guard(None, "XAUUSD", "demo", False)
    assert B.strategy_guard(good, "XAUUSD", "demo", False) is None
    assert B.strategy_guard(good, "BTCUSD", "demo", False)
    assert B.strategy_guard(bad, "XAUUSD", "demo", False)
    assert B.strategy_guard(bad, "XAUUSD", "demo", True) is None
    assert B.strategy_guard(bad, "XAUUSD", "real", True)


def make_bot(tmp_project, monkeypatch):
    mt5 = FakeMT5()
    now = B.now_ms()
    mt5.tick_ms = now
    times = now - np.arange(3000, 0, -1) * 2000
    mt5.ticks = tick_array(times, np.full(3000, 2000.0), np.full(3000, 2000.2))
    cfg = load_config()
    br = MT5Broker(cfg, mt5_module=mt5, sleep=lambda s: None)
    br.connect(); br.resolve_symbol("XAUUSD"); br.symbol_spec()
    chosen = {"symbol": "XAUUSD", "strategy": "sweep", "params": {"hold_min": 45}, "passed_gates": True}
    bot = B.Bot(cfg, br, chosen, B.TradeLog(C.TRADE_DB))
    bot.start()
    return bot, mt5


def test_entry_logs_signal_order_and_position(tmp_project, monkeypatch):
    bot, mt5 = make_bot(tmp_project, monkeypatch)
    boundary = (B.now_ms() // MINUTE_MS) * MINUTE_MS
    monkeypatch.setattr(B, "generate", lambda name, bars, p, tz: [
        Signal(len(bars) - 1, boundary, 1, 2.0, 3.0, 45, "sweep", "asia_low")])
    mt5.ticks = tick_array(np.array([boundary - 1000]), [2000.0], [2000.2])
    bot.t = np.r_[bot.t, boundary - 1000]; bot.bid = np.r_[bot.bid, 2000.0]; bot.ask = np.r_[bot.ask, 2000.2]
    mt5.results = [{"retcode": 10009, "price": 2000.21, "order": 900}]
    real_send = mt5.order_send

    def send_and_open(req):                          # the position appears only after the fill
        res = real_send(req)
        mt5.positions = [SimpleNamespace(ticket=900, magic=bot.cfg.execution.magic, time_msc=boundary,
                                         type=0, volume=req["volume"], price_open=res.price,
                                         symbol="XAUUSDm")]
        return res
    mt5.order_send = send_and_open
    bot.on_bar_close(boundary)
    db = bot.db.db
    assert db.execute("SELECT decision, reason FROM signals").fetchall() == [("enter", "")]
    row = db.execute("SELECT action, ok, slippage_points, send_latency_ms FROM orders").fetchone()
    assert row[0] == "open" and row[1] == 1 and np.isclose(row[2], 10.0) and row[3] >= 0
    assert 900 in bot.db.open_positions()
    assert bot.risk.state.trades_today == 1


def test_time_stop_and_sl_close_are_recorded(tmp_project, monkeypatch):
    bot, mt5 = make_bot(tmp_project, monkeypatch)
    now = B.now_ms()
    bot.db.add_open(1, now - 1000, "sweep", 1, 0.1, 2000.0, now - 3_600_000)    # deadline passed
    bot.db.add_open(2, now + 3_600_000, "sweep", 1, 0.1, 2000.0, now - 60_000)  # SL hit at broker
    mt5.positions = [SimpleNamespace(ticket=1, magic=bot.cfg.execution.magic, type=0, volume=0.1,
                                     symbol="XAUUSDm", time_msc=now)]
    mt5.deals[1] = (SimpleNamespace(profit=5.0, commission=-0.7, swap=0.0, fee=0.0, time_msc=now),)
    mt5.deals[2] = (SimpleNamespace(profit=-20.0, commission=-0.7, swap=0.0, fee=0.0, time_msc=now),)
    bot.manage_positions()
    reasons = dict(bot.db.db.execute("SELECT ticket, close_reason FROM trades").fetchall())
    assert reasons == {1: "time_stop", 2: "sl_tp_or_manual"}
    assert mt5.sent[-1]["position"] == 1


def test_restart_adopts_open_positions(tmp_project, monkeypatch):
    mt5 = FakeMT5()
    mt5.tick_ms = B.now_ms()
    mt5.ticks = tick_array(np.array([B.now_ms() - 1000]), [2000.0], [2000.2])
    cfg = load_config()
    br = MT5Broker(cfg, mt5_module=mt5, sleep=lambda s: None)
    br.connect(); br.resolve_symbol("XAUUSD"); br.symbol_spec()
    mt5.positions = [SimpleNamespace(ticket=77, magic=cfg.execution.magic, time_msc=B.now_ms() - 60_000,
                                     type=1, volume=0.2, price_open=2001.0, symbol="XAUUSDm")]
    bot = B.Bot(cfg, br, {"symbol": "XAUUSD", "strategy": "sweep", "params": {"hold_min": 45},
                          "passed_gates": True}, B.TradeLog(C.TRADE_DB))
    bot.start()
    pos = bot.db.open_positions()[77]
    assert pos["side"] == -1 and pos["deadline_ms"] > B.now_ms()


def test_kill_switch_flattens_and_stops(tmp_project, monkeypatch):
    bot, mt5 = make_bot(tmp_project, monkeypatch)
    bot.risk.state.peak_equity = 20_000.0           # equity 10k = 50% drawdown
    mt5.positions = [SimpleNamespace(ticket=5, magic=bot.cfg.execution.magic, type=0, volume=0.1,
                                     symbol="XAUUSDm", time_msc=0)]
    assert bot.check_risk() is False
    assert mt5.sent[-1]["position"] == 5
    assert bot.db.load_state("risk_XAUUSD")["halted"] is True


def test_trailing_stop_moves_broker_sl(tmp_project, monkeypatch):
    bot, mt5 = make_bot(tmp_project, monkeypatch)
    now = B.now_ms()
    bot.db.add_open(11, now + 3_600_000, "sweep", 1, 0.1, 2000.0, now - 60_000, 2.0, (1.0, 0.5, 0.1))
    bot.t = np.r_[bot.t, now - 30_000, now - 20_000]          # bid ran to 2004.0 = +2R
    bot.bid = np.r_[bot.bid, 2003.0, 2004.0]
    bot.ask = np.r_[bot.ask, 2003.2, 2004.2]
    mt5.bid, mt5.ask = 2003.5, 2003.7
    pos = SimpleNamespace(ticket=11, magic=bot.cfg.execution.magic, type=0, volume=0.1, sl=1998.0,
                          tp=2010.0, symbol="XAUUSDm", time_msc=now)
    mt5.positions = [pos]
    bot.manage_positions()
    req = mt5.sent[-1]
    assert req["action"] == mt5.TRADE_ACTION_SLTP and req["position"] == 11
    assert np.isclose(req["sl"], 2002.0) and req["tp"] == 2010.0   # entry + 50% of +4.0
    pos.sl = 2002.0
    n = len(mt5.sent)
    bot.manage_positions()                                   # no improvement: no new request
    assert len(mt5.sent) == n
