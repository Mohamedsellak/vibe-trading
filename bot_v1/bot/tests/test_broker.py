from types import SimpleNamespace

import numpy as np
import pytest

from broker import BrokerError, MT5Broker
from config import load_config
from conftest import FakeMT5, tick_array


def broker(**kw):
    mt5 = FakeMT5(**kw)
    br = MT5Broker(load_config(), mt5_module=mt5, sleep=lambda s: None)
    br.connect()
    br.resolve_symbol("XAUUSD")
    br.symbol_spec()
    return br, mt5


def test_resolves_suffixed_symbol_and_reads_spec():
    br, _ = broker()
    assert br.symbol == "XAUUSDm"
    assert br.spec.contract_size == 100.0 and br.spec.point == 0.001 and br.spec.source == "mt5"


def test_unknown_symbol_raises():
    br, _ = broker()
    with pytest.raises(BrokerError):
        br.resolve_symbol("EURUSD")


def test_account_modes():
    assert broker(trade_mode=0)[0].is_demo()
    br, _ = broker(trade_mode=2)
    assert not br.is_demo() and br.account_mode() == "real"


def test_open_retries_requote_then_fills_and_measures_slippage():
    br, mt5 = broker()
    mt5.results = [{"retcode": 10004}, {"retcode": 10009, "price": 2000.25, "order": 555}]
    mt5.positions = [SimpleNamespace(ticket=555, magic=br.cfg.execution.magic, time_msc=1, type=0,
                                     volume=0.1, price_open=2000.25, symbol="XAUUSDm")]
    res = br.open_market(1, 0.1, 2.0, 3.0, "test")
    assert res.ok and res.attempts == 2 and res.ticket == 555
    assert np.isclose(res.slippage_points, (2000.25 - 2000.20) / 0.001)
    req = mt5.sent[-1]
    assert req["type"] == mt5.ORDER_TYPE_BUY and req["magic"] == br.cfg.execution.magic
    assert np.isclose(req["sl"], 1998.2) and np.isclose(req["tp"], 2003.2)
    assert req["type_filling"] == mt5.ORDER_FILLING_FOK


def test_invalid_fill_switches_filling_mode():
    br, mt5 = broker(filling_mode=3)
    mt5.results = [{"retcode": 10030}, {"retcode": 10030}, {"retcode": 10009}]
    res = br.open_market(-1, 0.1, 2.0, 3.0)
    assert res.ok
    assert [r["type_filling"] for r in mt5.sent] == [0, 1, 2]


def test_market_closed_is_not_retried():
    br, mt5 = broker()
    mt5.results = [{"retcode": 10018}]
    res = br.open_market(1, 0.1, 2.0, 3.0)
    assert not res.ok and res.retcode == 10018 and len(mt5.sent) == 1


def test_retries_exhausted():
    br, mt5 = broker()
    mt5.results = [{"retcode": 10021}] * 10
    res = br.open_market(1, 0.1, 2.0, 3.0)
    assert not res.ok and len(mt5.sent) == br.cfg.execution.max_retries + 1


def test_close_uses_opposite_side_and_position_ticket():
    br, mt5 = broker()
    pos = SimpleNamespace(ticket=42, type=mt5.POSITION_TYPE_BUY, volume=0.3, symbol="XAUUSDm")
    res = br.close_position(pos)
    req = mt5.sent[-1]
    assert res.ok and req["position"] == 42 and req["type"] == mt5.ORDER_TYPE_SELL
    assert req["price"] == mt5.bid and req["volume"] == 0.3


def test_positions_filtered_by_magic_and_closed_pnl():
    br, mt5 = broker()
    mine = SimpleNamespace(ticket=1, magic=br.cfg.execution.magic)
    other = SimpleNamespace(ticket=2, magic=999)
    mt5.positions = [mine, other]
    assert [p.ticket for p in br.positions()] == [1]
    mt5.deals[1] = (SimpleNamespace(profit=-10.0, commission=-0.7, swap=0.0, fee=0.0, time_msc=5),
                    SimpleNamespace(profit=25.0, commission=-0.7, swap=-0.1, fee=0.0, time_msc=9))
    pnl, t = br.closed_position_pnl(1)
    assert np.isclose(pnl, 13.5) and t == 9


def test_ticks_converted_from_server_time(monkeypatch):
    br, mt5 = broker()
    br.cfg.server_tz = "Europe/Athens"              # a UTC+2/+3 broker
    srv = np.array([1_751_371_200_000 + 3 * 3_600_000])   # 2025-07-01 15:00 server = 12:00 UTC
    mt5.ticks = tick_array(srv, [1.0], [1.1])
    t, bid, ask = br.ticks_range(0, 1)
    assert t[0] == 1_751_371_200_000 and bid[0] == 1.0


def test_disconnected_terminal_reconnects():
    br, mt5 = broker()
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        return None if calls["n"] == 1 else SimpleNamespace(trade_allowed=True, connected=True)
    mt5.terminal_info = flaky
    br.ensure_connected()
    assert calls["n"] >= 2


def test_fetch_stops_when_server_clock_does_not_match(tmp_project):
    import time as _t
    import backtest as BT
    mt5 = FakeMT5()
    mt5.tick_ms = int(_t.time() * 1000) + 3 * 3_600_000     # a UTC+3 server, e.g. MetaQuotes-Demo
    cfg = load_config(symbol="XAUUSD")                        # SERVER_TZ=UTC (Exness)
    br = MT5Broker(cfg, mt5_module=mt5, sleep=lambda s: None)
    with pytest.raises(SystemExit, match="UTC\\+3.0h") as err:
        BT.cmd_fetch(SimpleNamespace(max_months=1), cfg, broker=br)
    assert "PC clock" in str(err.value) and "time.is" in str(err.value)
    assert not (BT.ticks_dir("XAUUSD") / "t.npy").exists()   # nothing was saved


def test_clock_check_passes_for_utc_server(tmp_project, capsys):
    import time as _t
    import backtest as BT
    mt5 = FakeMT5()
    mt5.tick_ms = int(_t.time() * 1000)
    cfg = load_config(symbol="XAUUSD")
    br = MT5Broker(cfg, mt5_module=mt5, sleep=lambda s: None)
    br.connect(); br.resolve_symbol("XAUUSD")
    BT.check_server_clock(br, cfg)
    assert "server clock OK" in capsys.readouterr().out
