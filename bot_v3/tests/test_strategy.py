"""Direction logic and the swarm decisions (pure functions)."""
from helpers import make_cfg
import strategy as st
from strategy import Pos, decide, direction

CFG = make_cfg(EXTEND_PER_CHECK=2, PROBE_PER_SIDE=1)
COST = 0.30


def rising(n=8, step=0.1):
    return [2000 + i * step for i in range(n)]


# ---------- direction: last 5 seconds ----------
def test_direction_up_when_move_beats_cost_and_ticks_agree():
    d = direction(rising(), COST, 1.0, 0.3, 4)
    assert d.state == st.UP and d.ups == 7 and d.downs == 0


def test_direction_down_is_symmetric():
    d = direction([2000 - i * 0.1 for i in range(8)], COST, 1.0, 0.3, 4)
    assert d.state == st.DOWN


def test_direction_flat_when_move_smaller_than_cost():
    d = direction(rising(n=4, step=0.05), COST, 1.0, 0.3, 2)     # move 0.15 < cost 0.30
    assert d.state == st.FLAT


def test_direction_flat_when_ticks_disagree():
    # one big jump up, then more small down-ticks: the net move is up but most ticks go down
    mids = [2000, 2000.8, 2000.75, 2000.7, 2000.65, 2000.6, 2000.55]
    d = direction(mids, COST, 1.0, 0.3, 4)
    assert d.move > COST and d.imbalance < 0 and d.state == st.FLAT


def test_direction_flat_when_market_asleep():
    d = direction([2000, 2000.5], COST, 1.0, 0.3, 4)            # 1 tick only
    assert d.state == st.FLAT


def test_market_state_window_needs_5_seconds_and_measures_spread():
    ms = st.MarketState(5, 120, 300)
    for i in range(40):                                        # 4 s of ticks
        ms.update(100 + i * 0.1, 2000 + i * 0.01, 2000.24 + i * 0.01)
    assert ms.move(103.9) is None
    for i in range(40, 80):
        ms.update(100 + i * 0.1, 2000 + i * 0.01, 2000.24 + i * 0.01)
    assert abs(ms.move(107.9) - 0.5) < 0.02                    # 5 s x 0.1 per s
    assert abs(ms.median_spread() - 0.24) < 1e-9


# ---------- cut the wrong side / close winners on a flip ----------
def test_cut_wrong_side_closes_losers_and_flip_closes_winners():
    trades = [Pos(1, st.SELL, -0.10, 2000, 1), Pos(2, st.SELL, +0.20, 2000, 2), Pos(3, st.BUY, 0.05, 2000, 3)]
    acts, _ = decide(st.UP, trades, 2000.5, "B", 5, True, False, CFG)
    closes = {a.ticket: a.reason for a in acts if a.kind == "close"}
    assert closes == {1: "cut wrong side", 2: "direction flip"}


def test_closes_happen_even_when_entries_are_blocked():
    trades = [Pos(1, st.BUY, -0.10, 2000, 1)]
    acts, _ = decide(st.DOWN, trades, 1999, "B", 5, False, False, CFG)
    assert [(a.kind, a.ticket) for a in acts] == [("close", 1)]


# ---------- extend the right side ----------
def test_extend_right_side_up_to_extend_per_check():
    trades = [Pos(1, st.BUY, 0.1, 2000.0, 1)]
    acts, note = decide(st.UP, trades, 2000.5, "B", 10, True, False, CFG)
    opens = [a for a in acts if a.kind == "open"]
    assert len(opens) == 2 and all(a.side == st.BUY and a.role == "extend" for a in opens)


def test_extend_limited_by_money_slots():
    acts, note = decide(st.UP, [Pos(1, st.BUY, 0.1, 2000.0, 1)], 2000.5, "B", 1, True, False, CFG)
    assert sum(a.kind == "open" for a in acts) == 1
    acts, note = decide(st.UP, [Pos(1, st.BUY, 0.1, 2000.0, 1)], 2000.5, "B", 0, True, False, CFG)
    assert not acts and "full" in note


def test_no_averaging_down():
    trades = [Pos(1, st.BUY, -0.2, 2000.6, 1)]                  # newest BUY decided at 2000.6, now 2000.4
    acts, note = decide(st.UP, trades, 2000.4, "B", 10, True, False, CFG)
    assert not acts and "under water" in note


def test_no_new_trade_on_a_side_just_stopped_out():
    acts, note = decide(st.UP, [], 2000, "B", 10, True, False, CFG, blocked_sides={st.BUY})
    assert not acts


# ---------- start modes ----------
def test_mode_a_probes_both_sides_when_flat():
    acts, _ = decide(st.FLAT, [], 2000, "A", 10, True, True, CFG)
    assert sorted(a.side for a in acts) == [st.BUY, st.SELL] and all(a.role == "probe" for a in acts)


def test_mode_a_waits_for_probe_cooldown_and_slots():
    assert decide(st.FLAT, [], 2000, "A", 10, True, False, CFG)[0] == []
    assert decide(st.FLAT, [], 2000, "A", 1, True, True, CFG)[0] == []       # needs 2 slots


def test_mode_b_never_probes():
    acts, note = decide(st.FLAT, [], 2000, "B", 10, True, True, CFG)
    assert not acts and "direction" in note


def test_flat_with_open_trades_holds():
    acts, note = decide(st.FLAT, [Pos(1, st.BUY, 0.1, 2000, 1)], 2000, "A", 10, True, True, CFG)
    assert not acts and "holding" in note
