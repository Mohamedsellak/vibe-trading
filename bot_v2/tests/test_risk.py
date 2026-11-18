from datetime import datetime, timezone

import config
import risk
from broker import Spec


def spec(**kw):
    base = dict(name="X", point=0.01, digits=2, tick_size=0.01, tick_value=1.0, contract_size=100,
                vol_min=0.01, vol_max=50.0, vol_step=0.01, stops_level=0, freeze_level=0,
                filling_mode=1, currency_base="XAU", currency_profit="USD")
    base.update(kw)
    return Spec(**base)


def epoch(y, mo, d, h, mi=0):
    return datetime(y, mo, d, h, mi, tzinfo=timezone.utc).timestamp()


# ----- sizing -----
def test_lot_defaults_to_symbol_minimum():
    assert risk.lot_size(spec(vol_min=0.01)) == 0.01
    assert risk.lot_size(spec(vol_min=0.1, vol_step=0.1)) == 0.1


def test_lot_rounds_down_to_step_and_clamps():
    assert risk.lot_size(spec(), 0.057) == 0.05
    assert risk.lot_size(spec(), 0.001) == 0.01          # never below minimum
    assert risk.lot_size(spec(vol_max=0.5), 3.0) == 0.5   # never above maximum
    assert risk.lot_size(spec(vol_min=1, vol_step=1, vol_max=100), 2.7) == 2


def test_stop_distance_respects_broker_stop_level():
    s = spec(stops_level=500)                 # 5.00 price away minimum
    assert risk.stop_distance(s, dist=1.5, spread=0.2) > 5.0
    assert risk.stop_distance(spec(), dist=1.5, spread=0.2) == 1.5


def test_deviation_comes_from_spread_and_point():
    assert risk.deviation_points(spec(), spread=0.2, spreads=1.0) == 20
    assert risk.deviation_points(spec(point=0.00001), spread=0.00012, spreads=1.0) == 12


# ----- filters -----
def test_spread_block():
    cfg = config.symbol_config("XAUUSD")
    assert risk.spread_block(0.2, 0.2, 1.5, cfg) is None                              # target 7.5 spreads
    assert risk.spread_block(0.4, 0.2, 1.5, cfg).startswith("spread too high")         # 2x median
    assert "vs volatility" in risk.spread_block(0.2, 0.2, 1.1, cfg)                   # target 5.5 spreads < 6


def test_limit_block():
    cfg = dict(max_trades=2)
    assert risk.limit_block(0, 0, 0.0, 0.01, cfg, 5, 0.1) is None
    assert risk.limit_block(2, 2, 0.02, 0.01, cfg, 5, 0.1) == "max trades for this symbol"
    assert risk.limit_block(1, 5, 0.05, 0.01, cfg, 5, 0.1) == "max trades overall"
    assert risk.limit_block(1, 1, 0.10, 0.01, cfg, 5, 0.1) == "max total lots"


def test_sessions_in_server_time():
    s = [("Mon-Fri", "07:00", "20:00")]
    assert risk.in_session(s, epoch(2026, 11, 18, 10))          # Wednesday 10:00
    assert not risk.in_session(s, epoch(2026, 11, 18, 21))      # after close
    assert not risk.in_session(s, epoch(2026, 11, 21, 10))      # Saturday
    assert risk.in_session(config.ALWAYS_OPEN, epoch(2026, 11, 22, 23, 59))   # BTC Sunday night


def test_news_blackout_window_and_currency(tmp_path):
    f = tmp_path / "news.csv"
    f.write_text("# comment\nutc_time,currency,minutes_before,minutes_after,event\n"
                 "2026-12-04 13:30,USD,15,30,NFP\n2026-12-05 08:00,EUR,10,10,ECB\n")
    cal = risk.NewsCalendar.load(str(f))
    t = epoch(2026, 12, 4, 13, 30)
    assert cal.active(t - 14 * 60, ["XAU", "USD"]) == "NFP"
    assert cal.active(t + 29 * 60, ["BTC", "USD"]) == "NFP"
    assert cal.active(t - 16 * 60, ["XAU", "USD"]) is None
    assert cal.active(t, ["EUR", "GBP"]) is None
    assert risk.NewsCalendar.load(str(tmp_path / "missing.csv")).events == []


def test_shipped_news_file_parses():
    import os
    cal = risk.NewsCalendar.load(os.path.join(os.path.dirname(config.__file__), config.NEWS_FILE))
    assert len(cal.events) >= 3


# ----- flip protections -----
def test_flip_cooldown_and_hourly_max():
    g = risk.FlipGuard(cooldown_s=60, max_per_hour=2)
    assert g.allowed(0)[0]
    g.record(0)
    ok, why = g.allowed(30)
    assert not ok and "cooldown" in why
    assert g.allowed(61)[0]
    g.record(61)
    ok, why = g.allowed(200)
    assert not ok and why == "max flips this hour"
    assert g.allowed(3601)[0]          # first flip left the 1-hour window
    assert g.count(3601) == 1


def test_zero_flips_per_hour_disables_flips():
    assert not risk.FlipGuard(60, 0).allowed(0)[0]
