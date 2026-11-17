import json
from datetime import datetime, timezone

import numpy as np
import pytest

import backtest as BT
import config as C
from config import SymbolSpec, load_config
from strategy import MINUTE_MS, Signal, TradeFilters, build_bars, local_minutes


def ms(y, mo, d, h=0, mi=0, s=0):
    return int(datetime(y, mo, d, h, mi, s, tzinfo=timezone.utc).timestamp() * 1000)


def spec():
    # 1.0 price move on 1 lot = $100 (gold-like), point 0.01 for easy arithmetic
    return SymbolSpec(name="XAUUSD", point=0.01, digits=2, tick_size=0.01, tick_value=1.0,
                      contract_size=100.0, volume_min=0.01, volume_max=100.0, volume_step=0.01)


def market(t, bid, spread=0.2):
    t = np.asarray(t, dtype="int64"); bid = np.asarray(bid, dtype=float)
    ask = bid + spread
    bars = build_bars(t, bid, ask, 60)
    bars.spread_ref[:] = spread                     # spread filter always satisfied
    _, day = local_minutes(bars.t, "UTC")
    return BT.Market("XAUUSD", "ticks", spec(), t, bid, ask, bars, day)


def cfg_for_test(commission=3.0, slip=0.05, latency=250):
    cfg = load_config()
    cfg.symbol = "XAUUSD"
    cfg.costs.commission_per_lot_side = commission
    cfg.costs.slippage_price = slip
    cfg.costs.latency_ms = latency
    cfg.risk.risk_per_trade_pct = 1.0
    cfg.risk.max_daily_loss_pct = 50.0
    cfg.risk.max_drawdown_pct = 90.0
    return cfg


def path_ticks(t0, prices, step_ms=1000):
    return [t0 + i * step_ms for i in range(len(prices))], prices


def one_signal(bar_idx, time_ms, side=1, sl=2.0, tp=3.0, hold=5):
    return [Signal(bar_idx, time_ms, side, sl, tp, hold, "test")]


def run(mkt, sigs, cfg, **kw):
    f = TradeFilters(cfg.filters, None)
    return BT.simulate(mkt, sigs, cfg, f, 0, 2**62, **kw)


T0 = ms(2026, 3, 2, 10)                             # Monday 10:00 UTC, outside rollover


def test_take_profit_long_costs_and_pnl(monkeypatch):
    cfg = cfg_for_test()
    prices = [100.0] * 61 + [100.5, 101.0, 102.0, 103.0, 103.6, 104.0] + [104.0] * 300
    t, p = path_ticks(T0, prices)
    mkt = market(t, p)
    sig = one_signal(0, T0 + MINUTE_MS)             # decision at 10:01:00
    trades, _ = run(mkt, sig, cfg)
    assert len(trades) == 1
    tr = trades[0]
    # first tick >= 10:01:00.250 is 10:01:01 (price 100.5): entry = ask + slip
    assert tr.entry_ms == T0 + 61_000 and np.isclose(tr.entry_px, 100.5 + 0.2 + 0.05)
    assert tr.exit_reason == "tp" and np.isclose(tr.exit_px, tr.entry_px + 3.0)
    lots = tr.lots
    assert np.isclose(tr.pnl, 3.0 * lots * 100 - 2 * 3.0 * lots)
    assert np.isclose(tr.cost_points, (0.2 + 0.05 + 0.0 + 2 * 3.0 / 100) / 0.01)
    assert tr.latency_ms == 1000


def test_take_profit_needs_trade_through():
    cfg = cfg_for_test(slip=0.0)
    entry_bid = 100.0
    tp_level = entry_bid + 0.2 + 1.0                 # entry at ask 100.2, tp 1.0 away
    prices = [100.0] * 62 + [tp_level] * 30 + [100.0] * 400
    t, p = path_ticks(T0, prices)
    trades, _ = run(market(t, p), one_signal(0, T0 + MINUTE_MS, tp=1.0, sl=5.0, hold=3), cfg)
    assert trades[0].exit_reason == "time"           # touching TP exactly is not a fill


def test_stop_loss_gap_fills_at_worse_price():
    cfg = cfg_for_test(slip=0.05)
    prices = [100.0] * 63 + [95.0] + [95.0] * 100    # gap far through the stop
    t, p = path_ticks(T0, prices)
    trades, _ = run(market(t, p), one_signal(0, T0 + MINUTE_MS, sl=2.0, tp=3.0), cfg)
    tr = trades[0]
    assert tr.exit_reason == "sl" and np.isclose(tr.exit_px, 95.0 - 0.05)
    assert tr.r_multiple < -1.0                      # gap loses more than 1R


def test_short_time_stop_exits_at_ask():
    cfg = cfg_for_test(slip=0.0, commission=0.0)
    prices = [100.0] * 2000
    t, p = path_ticks(T0, prices)
    trades, _ = run(market(t, p), one_signal(0, T0 + MINUTE_MS, side=-1, hold=5), cfg)
    tr = trades[0]
    assert tr.exit_reason == "time" and np.isclose(tr.entry_px, 100.0) and np.isclose(tr.exit_px, 100.2)
    assert tr.exit_ms >= tr.entry_ms + 5 * MINUTE_MS
    assert np.isclose(tr.pnl_points, -20.0)          # paid exactly the spread


def _trail_signal(time_ms, act=1.0, lock=0.5, step=0.1):
    return [Signal(0, time_ms, 1, 2.0, 10.0, 30, "test", "", act, lock, step)]


def test_trailing_stop_locks_profit():
    cfg = cfg_for_test(slip=0.0, commission=0.0)
    # entry at ask 100.2; price runs to bid 104.2 (+2R), then falls back below entry
    prices = [100.0] * 62 + list(np.linspace(100.0, 104.2, 40)) + list(np.linspace(104.2, 97.0, 40)) + [97.0] * 2000
    t, p = path_ticks(T0, prices)
    mkt = market(t, p)
    tr, _ = run(mkt, _trail_signal(T0 + MINUTE_MS), cfg)
    plain, _ = run(mkt, one_signal(0, T0 + MINUTE_MS, sl=2.0, tp=10.0, hold=30), cfg)
    assert tr[0].exit_reason == "trail" and tr[0].pnl > 0
    # best bid 104.2 -> mfe 4.0 -> candidate 102.2; moved from 98.2 in 0.2 steps = 102.2
    assert np.isclose(tr[0].exit_px, 102.2, atol=0.11)
    assert plain[0].exit_reason == "sl" and plain[0].pnl < 0


def test_trailing_not_activated_keeps_initial_stop():
    cfg = cfg_for_test(slip=0.0, commission=0.0)
    prices = [100.0] * 62 + [101.0] * 20 + [97.0] * 100   # +0.8 then through the stop
    t, p = path_ticks(T0, prices)
    tr, _ = run(market(t, p), _trail_signal(T0 + MINUTE_MS), cfg)
    assert tr[0].exit_reason == "sl"


def test_double_slippage_costs_more():
    cfg = cfg_for_test(slip=0.05)
    prices = [100.0] * 2000
    t, p = path_ticks(T0, prices)
    mkt = market(t, p)
    a, _ = run(mkt, one_signal(0, T0 + MINUTE_MS), cfg)
    b, _ = run(mkt, one_signal(0, T0 + MINUTE_MS), cfg, slip_mult=2.0)
    assert b[0].pnl < a[0].pnl


def test_spread_filter_skips_entry():
    cfg = cfg_for_test()
    t, p = path_ticks(T0, [100.0] * 2000)
    mkt = market(t, p, spread=0.2)
    mkt.bars.spread_ref[:] = 0.05                    # live spread is 4x the median
    trades, skips = run(mkt, one_signal(0, T0 + MINUTE_MS), cfg)
    assert trades == [] and skips["spread"] == 1


def test_only_one_open_position():
    cfg = cfg_for_test()
    t, p = path_ticks(T0, [100.0] * 3000)
    mkt = market(t, p)
    sigs = one_signal(0, T0 + MINUTE_MS, hold=10) + one_signal(2, T0 + 3 * MINUTE_MS, hold=10)
    trades, skips = run(mkt, sigs, cfg)
    assert len(trades) == 1 and skips["max_open_positions"] == 1


def test_metrics_and_breakeven():
    mk = lambda pnl, pts, r: BT.Trade("s", "", 1, 0, 0, 0, T0 + int(abs(pnl)) * 1000, 0, "tp",
                                      1, pnl, pts, 10.0, r, 0)
    trades = [mk(100, 50, 1.0), mk(100, 50, 1.0), mk(-50, -25, -0.5)]
    m = BT.metrics(trades, 10_000, 5, "UTC")
    assert m["trades"] == 3 and np.isclose(m["pf"], 4.0) and np.isclose(m["win_rate"], 2 / 3)
    assert np.isclose(m["breakeven_wr"], 25 / 75)
    assert np.isclose(m["avg_cost_pts"], 10.0)


def test_deflated_sharpe_falls_with_more_trials():
    srs = list(np.random.default_rng(0).normal(0, 0.05, 50))
    few = BT.deflated_sharpe(0.12, 400, 0.0, 3.0, srs, 2)
    many = BT.deflated_sharpe(0.12, 400, 0.0, 3.0, srs, 200)
    assert 0 <= many < few <= 1


def test_budget_enforced():
    log = [{"symbol": "XAUUSD", "strategy": "sweep", "params": json.dumps({"x": i})} for i in range(19)]
    BT.check_budget(log, "XAUUSD", 2, [("sweep", {"x": 100})])
    with pytest.raises(SystemExit):
        BT.check_budget(log, "XAUUSD", 2, [("sweep", {"x": 100}), ("sweep", {"x": 101})])
    with pytest.raises(SystemExit):
        BT.check_budget(log, "XAUUSD", 6, [])


def _random_walk_ticks(days=48, seed=1):
    """Synthetic random walk, weekdays only. FOR PIPELINE TESTS ONLY, not for evaluation."""
    rng = np.random.default_rng(seed)
    ts, ps = [], []
    price = 2000.0
    day0 = ms(2026, 1, 5)
    d = 0
    while len(ts) < days:
        start = day0 + d * 86_400_000
        d += 1
        if datetime.fromtimestamp(start / 1000, tz=timezone.utc).weekday() >= 5:
            continue
        t = start + np.arange(0, 86_400_000 - 3_600_000, 5_000, dtype="int64")
        steps = rng.normal(0, 0.08, len(t))
        p = price + np.cumsum(steps)
        price = float(p[-1])
        ts.append(t); ps.append(p)
    t = np.concatenate(ts); p = np.concatenate(ps)
    return t, p, p + 0.15


def test_end_to_end_pipeline_on_synthetic_data(tmp_project, capsys):
    t, bid, ask = _random_walk_ticks()
    np.savez(C.DATA_DIR / "XAUUSD_ticks.npz", t=t, bid=bid, ask=ask)
    (C.DATA_DIR / "XAUUSD_spec.json").write_text(spec().to_json())
    cfg = load_config(symbol="XAUUSD")
    BT.main(["info", "--symbol", "XAUUSD"])
    out = capsys.readouterr().out
    assert "trading days: 48" in out and "final" in out
    BT.main(["dev", "--symbol", "XAUUSD", "--round", "1"])
    log = BT.read_log()
    n_grid = sum(len(BT.grid_combos(s)) for s in BT.STRATEGIES)
    assert len(log) == 2 * n_grid and {r["split"] for r in log} == {"train", "validation"}
    # dev never touches the final split
    ev = BT.Evaluator(cfg, BT.load_market(cfg))
    fin_start = ev.splits.final[0]
    assert ev.splits.train[1] <= ev.splits.validation[0] and ev.splits.validation[1] <= fin_start
    BT.main(["select", "--symbol", "XAUUSD"])
    # round 2: the shipped trailing-stop and New York-only variants are logged and counted
    BT.main(["dev", "--symbol", "XAUUSD", "--round", "2",
             "--variants", str(C.BASE_DIR / "variants" / "round2_trail_ny.json")])
    log = BT.read_log()
    r2 = [r for r in log if r["round"] == "2" and r["split"] == "validation"]
    assert len(r2) == 6 and all(r["reason"] for r in r2)
    assert len(BT.variants_tried(log, "XAUUSD")) == n_grid + 6
    for strat in ("breakout", "meanrev", "sweep"):
        assert len(BT.variants_tried(log, "XAUUSD", strat)) == 14
    trailed = [json.loads(r["params"]) for r in r2 if json.loads(r["params"]).get("trail")]
    assert len(trailed) == 3 and all(p["trail_activate_r"] == cfg.trail.activate_r and
                                     p["trail_lock"] == cfg.trail.lock_fraction for p in trailed)
    assert sum(json.loads(r["params"])["session"] == "newyork" for r in r2) == 3
    BT.main(["walkforward", "--symbol", "XAUUSD", "--strategy", "sweep", "--folds", "3"])
    BT.main(["final", "--symbol", "XAUUSD", "--strategy", "sweep"])
    out = capsys.readouterr().out
    assert "FINAL TEST" in out and "RESULT:" in out
    chosen = json.loads(C.CHOSEN_FILE.read_text())
    assert chosen["strategy"] == "sweep" and "passed_gates" in chosen
    with pytest.raises(SystemExit):                  # a second look is refused
        BT.main(["final", "--symbol", "XAUUSD", "--strategy", "sweep"])
    # round 2 needs reasons, and the budget still applies
    var = tmp_project / "v.json"
    var.write_text(json.dumps([{"strategy": "sweep", "params": {"pierce_atr": 0.2}, "reason": ""}]))
    with pytest.raises(SystemExit):
        BT.main(["dev", "--symbol", "XAUUSD", "--round", "2", "--variants", str(var)])


def test_m1_pseudo_ticks_order():
    m1 = {"t": np.array([0, 60_000]), "o": np.array([10.0, 10.0]), "h": np.array([12.0, 12.0]),
          "l": np.array([9.0, 9.0]), "c": np.array([11.0, 9.5]), "spread_points": np.array([20, 20])}
    t, bid, ask = BT.m1_to_pseudo_ticks(m1, 0.01)
    assert list(bid[:4]) == [10.0, 9.0, 12.0, 11.0]      # bullish: low before high
    assert list(bid[4:]) == [10.0, 12.0, 9.0, 9.5]       # bearish: high before low
    assert np.allclose(ask - bid, 0.2) and t[1] - t[0] == 15_000


def test_m1_source_loads_and_reports(tmp_project, capsys):
    t0 = ms(2026, 1, 5)
    n = 20 * 1440
    t = t0 + np.arange(n, dtype="int64") * 60_000
    keep = np.array([datetime.fromtimestamp(x / 1000, tz=timezone.utc).weekday() < 5 for x in t[::1440]])
    t = t.reshape(20, 1440)[keep].ravel()
    c = 2000 + np.cumsum(np.random.default_rng(3).normal(0, 0.3, len(t)))
    np.savez(C.DATA_DIR / "XAUUSD_m1.npz", t=t, o=c, h=c + 0.2, l=c - 0.2, c=c,
             spread_points=np.full(len(t), 15.0), tick_volume=np.full(len(t), 50.0))
    (C.DATA_DIR / "XAUUSD_spec.json").write_text(spec().to_json())
    BT.main(["info", "--symbol", "XAUUSD", "--source", "m1"])
    out = capsys.readouterr().out
    assert "source=m1" in out and "Pseudo-ticks" in out and "trading days: 15" in out


def test_tick_storage_is_memory_mapped_and_parts_merge(tmp_project):
    # three monthly parts with an overlapping border tick, written oldest-first
    parts = []
    for i, (a, b) in enumerate([(0, 10), (9, 20), (20, 25)]):
        t = np.arange(a, b, dtype="int64") * 1000
        f = C.DATA_DIR / f"p{i}.npz"
        np.savez(f, t=t, bid=2000.0 + t / 1e6, ask=2000.2 + t / 1e6)
        parts.append(f)
    n = BT.merge_parts("XAUUSD", parts)
    t, bid, ask = BT.open_ticks("XAUUSD")
    assert n == 25 and len(t) == 25 and list(t[:3]) == [0, 1000, 2000]
    assert np.all(np.diff(np.asarray(t)) > 0)                 # border duplicates removed
    assert isinstance(t, np.memmap) and bid.dtype == np.float32   # gold stored as float32
    assert BT.is_sorted(t)


def test_btc_prices_keep_float64(tmp_project):
    BT.save_ticks("BTCUSD", np.arange(5, dtype="int64"), np.full(5, 95_000.25), np.full(5, 95_010.5))
    _, bid, _ = BT.open_ticks("BTCUSD")
    assert bid.dtype == np.float64 and bid[0] == 95_000.25


def test_tick_and_m1_runs_have_separate_budgets():
    log = [{"symbol": "XAUUSD", "strategy": "sweep", "source": "ticks", "params": json.dumps({"x": i})}
           for i in range(20)]
    with pytest.raises(SystemExit):                     # ticks budget is full
        BT.check_budget(log, "XAUUSD", 2, [("sweep", {"x": 99})], "ticks")
    BT.check_budget(log, "XAUUSD", 1, [("sweep", {"x": 1})], "m1")   # m1 starts fresh
    assert len(BT.variants_tried(log, "XAUUSD", source="m1")) == 0
    assert len(BT.variants_tried(log, "XAUUSD", source="ticks")) == 20


def test_research_backtest_does_not_stop_at_kill_switch():
    cfg = cfg_for_test(slip=0.0, commission=0.0)
    cfg.risk.max_drawdown_pct = 1.0                    # tiny: the first loss would trip it
    cfg.risk.cooldown_after_losses = 99
    prices = [100.0] * 62 + [90.0] * 600 + [90.0] * 600 + [80.0] * 2000
    t, p = path_ticks(T0, prices)
    mkt = market(t, p)
    sigs = one_signal(0, T0 + MINUTE_MS, hold=5) + one_signal(15, T0 + 16 * MINUTE_MS, hold=5)
    full, _ = run(mkt, sigs, cfg)
    stopped, skips = run(mkt, sigs, cfg, kill_switch=True)
    assert len(full) == 2 and len(stopped) == 1 and skips["kill_switch"] == 1



def test_check_refuses_final_test_overlap(tmp_project, capsys):
    t, bid, ask = _random_walk_ticks()
    np.savez(C.DATA_DIR / "XAUUSD_ticks.npz", t=t, bid=bid, ask=ask)
    (C.DATA_DIR / "XAUUSD_spec.json").write_text(spec().to_json())
    BT.main(["check", "--symbol", "XAUUSD", "--strategy", "sweep", "--from", "2026-01-05",
             "--to", "2026-01-20"])
    assert "positive years" in capsys.readouterr().out
    assert (C.RESULTS_DIR / "independent_checks.csv").exists()
    assert not BT.read_log()                              # not counted as a new variant
    with pytest.raises(SystemExit, match="overlaps the final-test"):
        BT.main(["check", "--symbol", "XAUUSD", "--strategy", "sweep", "--from", "2026-01-05",
                 "--to", "2026-12-31"])
