import config
import strategy as st

CFG = config.symbol_config("XAUUSD")


def test_direction_in_atr_units():
    assert st.direction(0.51, 1.0, 0.5) == st.UP
    assert st.direction(-0.51, 1.0, 0.5) == st.DOWN
    assert st.direction(0.3, 1.0, 0.5) == st.FLAT
    assert st.direction(None, 1.0, 0.5) == st.FLAT
    assert st.direction(5.0, 0.0, 0.5) == st.FLAT          # no ATR yet: never a signal


def test_atr_uses_true_range():
    bars = [(101, 99, 100)] * 15                            # range 2 each bar
    assert abs(st.atr(bars, 14) - 2.0) < 1e-9
    gap = [(101, 99, 100)] * 14 + [(106, 105, 105.5)]        # gap up: true range = 106 - 100 = 6
    assert abs(st.atr(gap, 14) - (13 * 2 + 6) / 14) < 1e-9
    assert st.atr(bars[:10], 14) == 0.0                      # not enough bars


def test_market_state_move_and_median_spread():
    ms = st.MarketState(lookback_s=5, spread_window_s=60)
    assert ms.move(0) is None
    for i in range(11):
        ms.update(i, 100 + i * 0.1, 100.2 + i * 0.1)
    assert abs(ms.move(10) - 0.5) < 1e-9          # 5 seconds x 0.1
    assert abs(ms.median_spread() - 0.2) < 1e-9


def test_trend_and_deadband():
    up = [100 + i for i in range(40)]
    assert st.trend(up, 1.0, 8, 21, 0.15) == st.UP
    assert st.trend(list(reversed(up)), 1.0, 8, 21, 0.15) == st.DOWN
    assert st.trend([100.0] * 40, 1.0, 8, 21, 0.15) == st.FLAT
    assert st.trend(up[:10], 1.0, 8, 21, 0.15) == st.FLAT       # not enough bars
    assert st.trend(up, 0.0, 8, 21, 0.15) == st.FLAT            # no ATR yet


def test_choppy_filter():
    straight = [(c + 0.1, c - 0.1, c) for c in (100 + i * 0.5 for i in range(20))]
    assert st.choppy(straight, 20, 0.25) == (False, "")
    zigzag = [(c + 0.1, c - 0.1, c) for c in (100 + (3 if i % 2 else 0) for i in range(20))]
    ch, why = st.choppy(zigzag, 20, 0.25)
    assert ch and "zig-zag" in why
    ch, why = st.choppy(straight[:5], 20, 0.25)
    assert ch and "warming up" in why


def test_pnl_units_includes_spread():
    # buy at ask 100.2, bid still 100.0 -> -1 spread
    assert abs(st.pnl_units(st.BUY, 100.2, 100.0, 100.2, 0.2) + 1) < 1e-9
    assert abs(st.pnl_units(st.SELL, 100.0, 99.0, 99.2, 0.2) - 4) < 1e-9


# ----- exits (ATR units) -----
def test_target_exit():
    assert st.exit_reason(1.49, 1.49, 5, CFG) is None
    assert st.exit_reason(1.5, 1.5, 5, CFG) == "target"


def test_trailing_exit_follows_best_price():
    assert st.exit_reason(0.4, 0.7, 5, CFG) is None         # never reached +0.8: no trailing
    assert st.exit_reason(0.6, 1.0, 5, CFG) is None         # 0.4 below the peak, allowed 0.5
    assert st.exit_reason(0.5, 1.0, 5, CFG) == "trailing stop"
    assert st.trail_level(0.7, CFG) is None
    assert abs(st.trail_level(1.2, CFG) - 0.7) < 1e-9


def test_bot_exits_are_only_backups_for_broker_orders():
    assert st.exit_reason(1.6, 1.6, 5, CFG, broker_tp=True) is None        # broker TP will close it
    assert st.exit_reason(0.5, 1.0, 5, CFG, broker_trail=True) is None     # broker SL locked: it closes it
    assert st.exit_reason(0.5, 1.0, 5, CFG, broker_trail=False) == "trailing stop"


def test_no_follow_through_exit_is_off_by_default():
    assert CFG["stall_exit_s"] == 0
    assert st.exit_reason(0.1, 0.3, 600, CFG) is None
    cfg = dict(CFG, stall_exit_s=60)
    assert st.exit_reason(0.1, 0.3, 59, cfg) is None
    assert st.exit_reason(0.1, 0.3, 60, cfg) == "no follow-through"
    assert st.exit_reason(-0.5, 0.45, 120, cfg) is None     # it did move +0.4: the stops handle it now


def test_loss_is_smaller_than_win_by_design():
    assert CFG["stop_atr"] < CFG["target_atr"]
    assert CFG["trail_start_atr"] - CFG["trail_dist_atr"] > 0   # trailing always locks a profit


# ----- pyramiding -----
def test_locked_means_stop_at_or_beyond_entry():
    assert st.is_locked(st.BUY, 100.0, 100.0) and st.is_locked(st.BUY, 100.0, 100.3)
    assert not st.is_locked(st.BUY, 100.0, 99.0)
    assert st.is_locked(st.SELL, 100.0, 99.7) and not st.is_locked(st.SELL, 100.0, 101.0)
    assert not st.is_locked(st.SELL, 100.0, 0.0)              # no stop at all


def test_pyramid_adds_only_when_every_stop_locks_profit():
    CFG = dict(globals()["CFG"], max_adds=3)                  # pyramiding is off by default
    assert st.should_add([True], 0, CFG)
    assert st.should_add([True, True], 1, CFG)
    assert not st.should_add([True, False], 1, CFG)          # the newest trade is not safe yet
    assert not st.should_add([False], 0, CFG)
    assert not st.should_add([True] * 4, 3, CFG)              # max adds reached
    assert not st.should_add([], 0, CFG)
