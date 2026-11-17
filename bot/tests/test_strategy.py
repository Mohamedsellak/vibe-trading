from datetime import datetime, timezone

import numpy as np

from config import FilterConfig
from conftest import make_bars
from strategy import (STRATEGIES, TradeFilters, apply_min_stop, build_bars, efficiency_ratio,
                      grid_combos, local_minutes, neighbors, server_to_utc_ms, signals_breakout,
                      signals_meanrev, signals_sweep, strategy_params, utc_to_server_ms)


def ms(y, mo, d, h=0, mi=0, s=0):
    return int(datetime(y, mo, d, h, mi, s, tzinfo=timezone.utc).timestamp() * 1000)


def test_build_bars_ohlc_and_spread():
    t0 = ms(2026, 1, 5, 10)
    t = np.array([t0, t0 + 10_000, t0 + 50_000, t0 + 61_000, t0 + 119_000])
    bid = np.array([1.0, 3.0, 2.0, 5.0, 4.0])
    ask = bid + np.array([0.1, 0.1, 0.4, 0.2, 0.2])
    b = build_bars(t, bid, ask)
    assert len(b) == 2
    assert (b.o[0], b.h[0], b.l[0], b.c[0]) == (1.0, 3.0, 1.0, 2.0)
    assert (b.o[1], b.h[1], b.l[1], b.c[1]) == (5.0, 5.0, 4.0, 4.0)
    assert np.isclose(b.spread[0], 0.2) and list(b.last_tick) == [2, 4] and list(b.n) == [3, 2]


def test_local_minutes_handles_dst():
    summer, winter = ms(2026, 7, 1, 7, 0), ms(2026, 1, 15, 8, 0)
    mod, _ = local_minutes(np.array([summer, winter]), "Europe/London")
    assert list(mod) == [480, 480]                   # both are 08:00 London time
    mod, _ = local_minutes(np.array([ms(2026, 7, 1, 13, 30), ms(2026, 1, 15, 14, 30)]), "America/New_York")
    assert list(mod) == [570, 570]                   # both 09:30 New York


def test_server_time_round_trip():
    utc = np.array([ms(2026, 7, 1, 12), ms(2026, 12, 1, 12)])
    srv = utc_to_server_ms(utc, "Europe/Athens")
    assert list((srv - utc) // 3_600_000) == [3, 2]
    assert np.array_equal(server_to_utc_ms(srv, "Europe/Athens"), utc)
    assert np.array_equal(server_to_utc_ms(utc, "UTC"), utc)


def test_grids_respect_budget_and_neighbors():
    for name in STRATEGIES:
        assert len(grid_combos(name)) <= 20
        assert set(STRATEGIES[name]["reasons"]) == set(STRATEGIES[name]["grid"])
    p = strategy_params("breakout", {"range_min": 60, "exp_mult": 1.5, "tp_r": 1.0})
    nb = neighbors("breakout", p)
    assert len(nb) == 4                              # 30 / 1.0, 2.0 / 2.0
    assert all(sum(q[k] != p[k] for k in p) == 1 for q in nb)


def _flat_then(t0, n_flat, base=100.0, wiggle=0.05):
    c = base + wiggle * np.where(np.arange(n_flat) % 2 == 0, 1, -1)
    return list(c), list(c + 0.05), list(c - 0.05), list(c)


def test_breakout_fires_once_on_expanded_close_above_range():
    t0 = ms(2026, 1, 15, 6, 30)                       # winter: London open 08:00 UTC
    o, h, l, c = _flat_then(t0, 90)                  # 06:30 .. 07:59
    o += [100.0]; h += [102.0]; l += [99.9]; c += [101.8]          # 08:00 bar breaks out
    for _ in range(5):
        o.append(101.8); h.append(103.5); l.append(101.7); c.append(103.4)
    b = make_bars(t0, o, h, l, c)
    p = strategy_params("breakout", {"range_min": 60, "exp_mult": 1.5, "tp_r": 2.0})
    sigs = signals_breakout(b, p)
    assert len(sigs) == 1
    s = sigs[0]
    assert s.side == 1 and s.note == "london" and s.bar_idx == 90
    assert s.time_ms == b.t[90] + 60_000
    assert np.isclose(s.tp_dist, 2.0 * s.sl_dist)


def test_breakout_needs_volatility_expansion():
    t0 = ms(2026, 1, 15, 6, 30)
    o, h, l, c = _flat_then(t0, 90)
    o += [100.0]; h += [100.25]; l += [100.0]; c += [100.25]       # small drift through the high
    b = make_bars(t0, o, h, l, c)
    assert signals_breakout(b, strategy_params("breakout", {"exp_mult": 2.0})) == []


def test_meanrev_long_below_band_and_vwap_in_range():
    t0 = ms(2026, 1, 15, 9, 0)
    o, h, l, c = _flat_then(t0, 60, wiggle=0.5)
    o += [99.5]; h += [99.6]; l += [97.4]; c += [97.5]
    b = make_bars(t0, o, h, l, c)
    p = strategy_params("meanrev", {"bb_k": 2.0, "er_max": 0.3, "sl_atr": 1.5})
    sigs = signals_meanrev(b, p)
    assert len(sigs) == 1 and sigs[0].side == 1 and sigs[0].bar_idx == 60
    assert sigs[0].tp_dist > 0


def test_meanrev_regime_filter_blocks_trend():
    t0 = ms(2026, 1, 15, 9, 0)
    c = list(100.0 - 0.2 * np.arange(61))           # steady downtrend: ER = 1
    b = make_bars(t0, c, [x + 0.05 for x in c], [x - 0.3 for x in c], c)
    assert signals_meanrev(b, strategy_params("meanrev", {"er_max": 0.3})) == []


def test_sweep_long_after_asia_low_is_reclaimed():
    t0 = ms(2026, 1, 15, 0, 0)
    n = 8 * 60                                      # 00:00 .. 07:59
    o, h, l, c = _flat_then(t0, n, base=100.5, wiggle=0.2)
    o += [100.4]; h += [100.5]; l += [99.0]; c += [100.6]           # 08:00 sweeps and reclaims
    b = make_bars(t0, o, h, l, c)
    p = strategy_params("sweep", {"pierce_atr": 0.1, "confirm_bars": 1, "tp_r": 1.5})
    sigs = signals_sweep(b, p)
    assert len(sigs) == 1
    s = sigs[0]
    assert s.side == 1 and s.note == "asia_low" and s.bar_idx == n
    asia_low = min(l[:360])
    assert l[n] < asia_low
    assert np.isclose(s.tp_dist, 1.5 * s.sl_dist)


def test_sweep_without_reclaim_does_not_fire():
    t0 = ms(2026, 1, 15, 0, 0)
    n = 8 * 60
    o, h, l, c = _flat_then(t0, n, base=100.5, wiggle=0.2)
    for _ in range(5):
        o.append(99.5); h.append(99.6); l.append(99.0); c.append(99.2)
    b = make_bars(t0, o, h, l, c)
    assert signals_sweep(b, strategy_params("sweep", {"confirm_bars": 3})) == []


def test_efficiency_ratio_bounds():
    er = efficiency_ratio(np.arange(50, dtype=float), 10)
    assert np.isclose(er[-1], 1.0)


def test_filters_news_rollover_spread(tmp_path):
    news = tmp_path / "news.csv"
    news.write_text("utc_time,minutes_before,minutes_after,event\n2026-03-06 13:30,15,30,US NFP\n")
    f = TradeFilters(FilterConfig(), news)
    assert f.check(ms(2026, 3, 6, 13, 20), 0.1, 0.1) == "news:US NFP"
    assert f.check(ms(2026, 3, 6, 14, 5), 0.1, 0.1) is None
    # 17:00 New York = 21:00 UTC in summer, 22:00 UTC in winter
    assert f.rollover_blocked(ms(2026, 7, 1, 21, 0)) and f.rollover_blocked(ms(2026, 1, 15, 22, 0))
    assert not f.rollover_blocked(ms(2026, 7, 1, 23, 30))
    assert f.check(ms(2026, 3, 9, 12), 0.5, 0.2) == "spread"
    assert f.check(ms(2026, 3, 9, 12), 0.3, 0.2) is None
    assert f.check(ms(2026, 3, 9, 12), 0.3, float("nan")) == "spread"


def test_apply_min_stop():
    assert apply_min_stop(0.5, 1.0, 0, 0.001, 0.2) == (0.5, 1.0)
    sl, tp = apply_min_stop(0.05, 0.1, 100, 0.001, 0.02)
    assert np.isclose(sl, 0.12) and np.isclose(tp, 0.12)


# ---- trailing stop and New York-only variants ----
from strategy import generate, trail_stop_level  # noqa: E402


def test_trail_stop_level_long_and_short():
    # entry 100, risk 2, activate at +1R, lock 50%, steps of 0.1R (=0.2)
    f = lambda best, side=1, sl0=98.0: float(trail_stop_level(best, 100.0, sl0, 2.0, side, 1.0, 0.5, 0.1))
    assert f(101.9) == 98.0                         # below activation: initial stop
    assert np.isclose(f(102.0), 101.0)              # +1R: locks 50% of +2.0
    assert np.isclose(f(102.3), 101.0)              # moves only in 0.2 steps
    assert np.isclose(f(102.4), 101.2)
    assert np.isclose(f(98.0, side=-1, sl0=102.0), 99.0)    # short mirror
    assert f(98.5, side=-1, sl0=102.0) == 102.0


def test_generate_attaches_trail_settings():
    t0 = ms(2026, 1, 15, 0, 0)
    n = 8 * 60
    o, h, l, c = _flat_then(t0, n, base=100.5, wiggle=0.2)
    o += [100.4]; h += [100.5]; l += [99.0]; c += [100.6]
    b = make_bars(t0, o, h, l, c)
    base = {"pierce_atr": 0.1, "confirm_bars": 1}
    plain = generate("sweep", b, base, "UTC")
    trailed = generate("sweep", b, {**base, "trail": True, "trail_activate_r": 1.0,
                                    "trail_lock": 0.5, "trail_step_r": 0.1}, "UTC")
    assert plain[0].trail_activate_r == 0.0
    assert (trailed[0].trail_activate_r, trailed[0].trail_lock, trailed[0].trail_step_r) == (1.0, 0.5, 0.1)
    assert trailed[0].sl_dist == plain[0].sl_dist   # same entry logic


def test_ny_only_breakout_skips_london():
    t0 = ms(2026, 1, 15, 6, 30)
    o, h, l, c = _flat_then(t0, 90)
    o += [100.0]; h += [102.0]; l += [99.9]; c += [101.8]
    b = make_bars(t0, o, h, l, c)
    p = {"range_min": 60, "exp_mult": 1.5}
    assert len(generate("breakout", b, p, "UTC")) == 1
    assert generate("breakout", b, {**p, "session": "newyork"}, "UTC") == []


def _meanrev_bars(start_hour):
    t0 = ms(2026, 1, 15, start_hour, 0)
    o, h, l, c = _flat_then(t0, 60, wiggle=0.5)
    o += [99.5]; h += [99.6]; l += [97.4]; c += [97.5]
    return make_bars(t0, o, h, l, c)


def test_ny_only_meanrev_and_sweep_use_new_york_hours():
    p = {"bb_k": 2.0, "er_max": 0.3, "session": "newyork"}
    assert generate("meanrev", _meanrev_bars(9), p, "UTC") == []      # 10:00 UTC = 05:00 New York
    assert len(generate("meanrev", _meanrev_bars(14), p, "UTC")) == 1  # 15:00 UTC = 10:00 New York
    t0 = ms(2026, 1, 15, 0, 0)
    for minute, expected in ((8 * 60, 0), (14 * 60, 1)):              # 08:00 vs 14:00 UTC sweep
        o, h, l, c = _flat_then(t0, minute, base=100.5, wiggle=0.2)
        o += [100.4]; h += [100.5]; l += [99.0]; c += [100.6]
        sigs = generate("sweep", make_bars(t0, o, h, l, c),
                        {"pierce_atr": 0.1, "confirm_bars": 1, "session": "newyork"}, "UTC")
        assert len(sigs) == expected


def test_server_tz_accepts_offsets_and_rejects_garbage():
    import pytest
    from config import normalize_tz
    assert normalize_tz("UTC") == "UTC" and normalize_tz("gmt") == "UTC"
    assert normalize_tz("UTC+2") == "Etc/GMT-2" and normalize_tz("GMT-5") == "Etc/GMT+5"
    assert normalize_tz("UTC+0") == "UTC" and normalize_tz("Europe/Athens") == "Europe/Athens"
    utc = np.array([ms(2026, 7, 1, 12)])
    assert (utc_to_server_ms(utc, normalize_tz("UTC+2")) - utc)[0] == 2 * 3_600_000
    with pytest.raises(SystemExit):
        normalize_tz("UTC plus two")



def test_symbol_costs_come_from_env_but_code_can_override(tmp_path, monkeypatch):
    import config as C
    env = tmp_path / ".env"
    env.write_text("COMMISSION_XAUUSD=0\nSLIPPAGE_XAUUSD=0.07\n")
    cfg = C.load_config(env_path=env, symbol="XAUUSD")
    assert cfg.commission() == 0.0 and cfg.slippage() == 0.07
    cfg.costs.commission_per_lot_side = 3.0          # a later explicit setting wins
    assert cfg.commission() == 3.0


def test_trend_filter_keeps_only_trades_with_the_trend():
    from strategy import trend_slope
    t0 = ms(2026, 1, 15, 0, 0)
    n = 8 * 60
    base = list(np.linspace(95.0, 100.5, n))        # steady uptrend into 08:00
    o = base[:]; h = [x + 0.1 for x in base]; l = [x - 0.1 for x in base]; c = base[:]
    asia_low = min(l[:360])
    o += [100.4]; h += [100.5]; l += [asia_low - 2.0]; c += [asia_low + 0.3]   # sweep + reclaim
    b = make_bars(t0, o, h, l, c)
    assert trend_slope(b)[-1] > 0
    p = {"pierce_atr": 0.1, "confirm_bars": 1, "max_sl_atr": 100.0}
    plain = generate("sweep", b, p, "UTC")
    assert {s.side for s in plain} == {1, -1}         # a long and a short against the trend
    kept = generate("sweep", b, {**p, "trend_filter": True}, "UTC")
    assert [s.side for s in kept] == [1]              # only the long, with the uptrend, survives
