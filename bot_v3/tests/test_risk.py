"""Cost check, equity-based sizing, margin check, order-rate cap, sessions, rolling result."""
from datetime import datetime, timezone

import pytest

import risk
from broker import Spec
from helpers import make_cfg

GOLD = Spec("XAUUSDm", 0.001, 3, 0.001, 0.1, 100.0, 0.01, 200.0, 0.01, 0, 0, 1, "XAU", "USD")
CFG = make_cfg(TARGET_X_COST=2.0, STOP_X_TARGET=1.25, MAX_TOTAL_STOP_RISK_PCT=15, MAX_OPEN_TRADES=20,
               MAX_TOTAL_LOTS_X_MIN=20, MAX_ONE_STOP_PCT=5, MARGIN_USE_MAX_PCT=50, BASKET_STOP_PCT=8,
               MIN_TARGET_X_COST_NOW=1.5)


def plan(spread=0.24, slip=0.06):
    return risk.make_plan(GOLD, 0.01, spread, spread, slip, slip, CFG)


def utc(*a):
    return datetime(*a, tzinfo=timezone.utc).timestamp()


def test_lot_is_symbol_minimum():
    assert risk.lot_size(GOLD) == 0.01


def test_plan_numbers_come_from_measured_cost():
    p = plan()
    assert p.cost == pytest.approx(0.36)               # spread 0.24 + 2 x 0.06 slippage
    assert p.target_move == pytest.approx(0.72)
    assert p.stop_move == pytest.approx(0.90)
    assert p.tp_dist == pytest.approx(0.48)            # the BUY starts one spread down
    assert p.sl_dist == pytest.approx(1.14)
    assert p.risk_money == pytest.approx(1.26)         # 0.01 lot of gold = 1.0 money per 1.0 price
    assert p.cost_money == pytest.approx(0.36)         # minimum profitable target, in money
    assert p.win_money == pytest.approx(0.36)
    assert p.coinflip_winrate == pytest.approx(0.9 / 1.62)
    assert 0.7 < p.breakeven_winrate < 0.85


def test_cost_check_blocks_when_spread_jumps():
    p = plan()
    assert risk.cost_block(p, 0.24, 0.06, CFG) is None
    assert risk.cost_block(p, 0.40, 0.06, CFG) is not None     # cost now 0.52, target 0.72 < 1.5 x 0.52


def test_slippage_prior_then_measured_never_negative():
    s = risk.SlipStats(50)
    assert s.expected(0.24, 0.25) == pytest.approx(0.06)
    for x in (-0.1, -0.05, -0.2, -0.1, -0.1):
        s.add(x)
    assert s.expected(0.24, 0.25) == 0.0


def test_equity_based_sizing():
    p = plan()                                       # one stop = 1.26
    assert risk.max_trades(100, p, 0.01, CFG) == 11  # 15.00 // 1.26
    assert risk.max_trades(1000, p, 0.01, CFG) == 20  # capped by MAX_OPEN_TRADES
    assert risk.max_trades(5, p, 0.01, CFG) == 0
    # worst case: every open trade stopped out stays inside the 15% cap
    n = risk.max_trades(100, p, 0.01, CFG)
    assert n * p.risk_money <= 0.15 * 100
    assert risk.free_slots(100, 10 * 1.26, 10, p, 0.01, CFG) == 1
    assert risk.free_slots(100, 11 * 1.26, 11, p, 0.01, CFG) == 0


def test_stop_too_big_for_small_account():
    p = plan()
    assert risk.stop_too_big(20, p, CFG)              # 1.26 = 6.3% of 20
    assert risk.stop_too_big(100, p, CFG) is None


def test_margin_check():
    assert risk.margin_ok(2.0, 2, 10.0, CFG)          # 4 <= 50% of 10
    assert not risk.margin_ok(2.0, 3, 10.0, CFG)      # 6 > 5
    assert risk.margin_ok(None, 3, 10.0, CFG)         # MT5 cannot tell: the broker decides


def test_basket_stop():
    assert risk.basket_hit(-8.0, 92.0, CFG)           # 8 of 100
    assert not risk.basket_hit(-7.0, 93.0, CFG)


def test_order_rate_cap():
    r = risk.RateCap(3)
    for t in (0, 1, 2):
        r.record(t)
    assert r.left(10) == 0
    assert r.left(60.5) == 1 and r.left(61.5) == 2 and r.left(62.5) == 3


def test_realistic_trades_per_minute():
    # 840 ms per order (Exness demo gold) -> 71 orders a minute at most
    assert risk.realistic_trades_per_min(840, 1.0, 1000) == pytest.approx(71.4, abs=0.1)
    assert risk.realistic_trades_per_min(840, 2.0, 1000) == pytest.approx(35.7, abs=0.1)
    assert risk.realistic_trades_per_min(840, 1.5, 60) == pytest.approx(40)
    assert risk.realistic_trades_per_min(840, 1.0, 1000) < 100        # 100 a minute: impossible


def test_sessions_follow_summer_time():
    import config
    s = config.SESSIONS
    assert risk.active_session(s, utc(2026, 7, 15, 7, 30)) == "London"       # 08:30 in London (BST)
    assert risk.active_session(s, utc(2026, 1, 14, 7, 30)) is None           # 07:30 in London (GMT)
    assert risk.active_session(s, utc(2026, 1, 14, 16, 45)) == "New York"    # London closed, NY 11:45
    assert risk.active_session(s, utc(2026, 7, 18, 12, 0)) is None           # Saturday


def test_news_blackout(tmp_path):
    f = tmp_path / "news.csv"
    f.write_text("utc_time,currency,minutes_before,minutes_after,event\n2026-12-04 13:30,USD,15,30,NFP\n")
    cal = risk.NewsCalendar.load(str(f))
    assert cal.active(utc(2026, 12, 4, 13, 20), ("XAU", "USD")) == "NFP"
    assert cal.active(utc(2026, 12, 4, 14, 5), ("XAU", "USD")) is None


def test_rolling_net():
    r = risk.RollingNet(3)
    for x in (0.1, -0.5, 0.1):
        r.add(x)
    assert r.full and r.mean() < 0
    r.add(0.5)
    assert r.mean() > 0
