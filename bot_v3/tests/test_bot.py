"""The bot on a fake MT5: probe, cut, extend, target + reopen, flip, stops, money checks, safety."""
import os

import pytest

import strategy as st
from bot import Swarm
from broker import Broker, SyncExecutor, ThreadExecutor, new_cmd
from fake_mt5 import FakeMT5
from helpers import SYM, T0, Feed, make_cfg, make_swarm, warm


def sides(sw):
    out = {"BUY": 0, "SELL": 0}
    for t in sw.trades.values():
        out[t.side] += 1
    return out


def reasons(sw):
    return [r["close_reason"] for r in sw.j.db.execute("SELECT close_reason FROM trades WHERE close_time IS NOT NULL")]


def test_every_order_has_broker_stop_and_target(tmp_path):
    sw, fake = make_swarm(tmp_path, make_cfg(START_MODE="B"))
    f = warm(sw, fake)
    f.drift(3, 0.4)
    opens = [r for r in fake.sent if "position" not in r]
    assert opens and all(r["sl"] > 0 and r["tp"] > 0 for r in opens)
    for r in opens:                                  # stop below / target above for a BUY
        assert r["sl"] < r["price"] < r["tp"]
    assert all(r["volume"] == 0.01 for r in opens)   # minimum lot, never more


def test_mode_a_probes_then_cuts_wrong_side_and_extends_right_side(tmp_path):
    sw, fake = make_swarm(tmp_path, make_cfg(START_MODE="A", PROBE_PER_SIDE=1))
    f = warm(sw, fake)
    f.wiggle(2, amp=0.03, period=0.5)                # two-way ticks, no direction -> probe
    assert sides(sw) == {"BUY": 1, "SELL": 1}
    assert all(t.role == "probe" and t.mode == "A" for t in sw.trades.values())
    f.until(lambda: sw.dir.state == st.UP, per_s=0.3, max_s=5)
    f.tick()
    assert "cut wrong side" in reasons(sw)           # the SELL probe was cut at a loss
    assert sides(sw)["SELL"] == 0 and sides(sw)["BUY"] >= 2
    assert {t.role for t in sw.trades.values()} >= {"probe", "extend"}


def test_mode_b_waits_for_direction_then_opens_one_side(tmp_path):
    sw, fake = make_swarm(tmp_path, make_cfg(START_MODE="B"))
    f = warm(sw, fake)
    f.hold(3)
    assert not sw.trades and not [r for r in fake.sent if "position" not in r]
    f.drift(3, -0.3)
    assert sides(sw)["BUY"] == 0 and sides(sw)["SELL"] >= 2
    assert all(t.mode == "B" and t.role in ("entry", "extend") for t in sw.trades.values())


def test_target_closes_at_broker_then_reopens_at_once(tmp_path):
    sw, fake = make_swarm(tmp_path, make_cfg(START_MODE="B", EXTEND_PER_CHECK=1, MAX_OPEN_TRADES=1))
    f = warm(sw, fake)
    f.until(lambda: sw.trades, per_s=0.3, max_s=5)
    first = list(sw.trades)
    f.until(lambda: "target" in reasons(sw), per_s=0.6, max_s=5)     # target reached at the broker
    row = sw.j.db.execute("SELECT * FROM trades WHERE close_reason='target'").fetchone()
    assert row["pnl"] > 0 and row["close_latency_ms"] is None        # no bot order was needed
    t_close = sw.closed_t[-1]
    f.until(lambda: sw.trades, per_s=0.6, max_s=0.3)                 # reopened within a few loops,
    assert list(sw.trades) != first                                  # not at the next 1 s check
    assert max(t.open_time for t in sw.trades.values()) - t_close < 0.2


def test_direction_flip_closes_winners_too(tmp_path):
    sw, fake = make_swarm(tmp_path, make_cfg(START_MODE="B", TARGET_X_COST=8.0, STOP_X_TARGET=1.0))
    f = warm(sw, fake)
    f.until(lambda: sides(sw)["BUY"] >= 1, per_s=0.3, max_s=5)
    f.drift(8, 0.3)                                  # a long rise: the first BUYs are far in profit
    f.until(lambda: sides(sw)["BUY"] == 0, per_s=-0.15, max_s=8)
    rs = reasons(sw)
    assert "direction flip" in rs                    # winners closed because the direction turned
    assert "cut wrong side" in rs                    # the late BUYs were losing
    assert sides(sw)["SELL"] >= 1                    # and the bot reopened on the new side


def test_broker_stop_then_same_side_pause(tmp_path):
    sw, fake = make_swarm(tmp_path, make_cfg(START_MODE="B", EXTEND_PER_CHECK=1, MAX_OPEN_TRADES=1))
    f = warm(sw, fake)
    f.until(lambda: sw.trades, per_s=0.3, max_s=5)
    t = next(iter(sw.trades.values()))
    f.tick(t.sl - 0.5)                               # crash through the broker stop
    f.tick()
    assert "stop" in reasons(sw) and sw.now - sw.last_stop["BUY"] < 1
    sw.dir = st.Direction(st.UP, 1.0, 10, 0)         # even if the direction still says UP ...
    sw.decide_now = True
    f.tick()
    assert sides(sw)["BUY"] == 0                     # ... no new BUY right after its stop


def test_no_duplicate_close_while_one_is_queued(tmp_path):
    class Held(SyncExecutor):                        # keeps commands until released
        def submit(self, cmd):
            self.inflight[cmd["id"]] = cmd
            self.held = getattr(self, "held", []) + [cmd]
    sw, fake = make_swarm(tmp_path, make_cfg(START_MODE="B"))
    p = fake.add_position(SYM, "SELL", 0.01, 2000.0, sw.cfg.MAGIC, sl=2010.0, tp=1990.0)
    sw.adopt_existing(T0)
    sw.ex = Held(sw.b, sw.spec)
    f = warm(sw, fake)
    sw.halted = True                                 # no opens, closes only
    f.drift(3, 0.3)
    closes = [c for c in sw.ex.held if c["kind"] == "close"]
    assert len(closes) == 1 and closes[0]["ticket"] == p.ticket


def test_free_margin_blocks_entries(tmp_path):
    sw, fake = make_swarm(tmp_path, make_cfg(START_MODE="B"))
    f = warm(sw, fake)
    fake.margin_free_override = 5.0                  # 0.01 lot needs 4.0 > 50% of 5.0
    f.drift(3, 0.3)
    assert not sw.trades and "margin" in sw.block


def test_no_money_error_pauses_60_seconds(tmp_path):
    sw, fake = make_swarm(tmp_path, make_cfg(START_MODE="B"))
    f = warm(sw, fake)
    fake.fail_next = [fake.TRADE_RETCODE_NO_MONEY] * 2     # the first batch of 2 opens is refused
    f.drift(2.5, 0.3)
    assert sw.no_money_until > f.t
    n = len(fake.sent)
    f.drift(5, 0.3)
    assert len(fake.sent) == n and "no money" in sw.block
    f.wiggle(sw.no_money_until - f.t + 1)          # the pause runs out with the market still moving
    f.hold(5.5)
    f.until(lambda: sw.trades, per_s=0.3, max_s=5)


def test_order_rate_cap_limits_orders(tmp_path):
    sw, fake = make_swarm(tmp_path, make_cfg(START_MODE="B", MAX_ORDERS_PER_MIN=3, EXTEND_PER_CHECK=2))
    f = warm(sw, fake)
    f.drift(8, 0.2)
    assert len(fake.sent) <= 3 and sw.rate.left(f.t) == 0


def test_equity_based_sizing_keeps_total_stop_risk_under_cap(tmp_path):
    sw, fake = make_swarm(tmp_path, make_cfg(START_MODE="B", TARGET_X_COST=4.0), balance=80.0)
    f = warm(sw, fake)
    most = 0
    for _ in range(300):                             # 15 s of a steady rise
        f.tick(f.mid + 0.01)
        cap = sw.cfg.MAX_TOTAL_STOP_RISK_PCT / 100 * sw.acct.equity
        assert sw.open_risk() <= cap + 1e-9
        assert len(sw.trades) <= sw.max_trades()
        most = max(most, len(sw.trades))
    assert 2 <= most <= sw.max_trades() < sw.cfg.MAX_OPEN_TRADES


def test_stop_too_big_for_tiny_account(tmp_path):
    sw, fake = make_swarm(tmp_path, make_cfg(START_MODE="B"), balance=10.0)
    f = warm(sw, fake)
    f.drift(3, 0.3)
    assert not sw.trades and "stop too big" in sw.block


def test_spread_spike_blocks(tmp_path):
    sw, fake = make_swarm(tmp_path, make_cfg(START_MODE="B"))
    f = warm(sw, fake)
    f.spread = 0.6
    f.drift(3, 0.3)
    assert not sw.trades and sw.block in ("spread spike",) or "cost" in sw.block


def test_basket_stop_closes_all_and_pauses(tmp_path):
    sw, fake = make_swarm(tmp_path, make_cfg(START_MODE="B", BASKET_STOP_PCT=0.1))
    f = warm(sw, fake)
    f.drift(3, 0.3)
    assert sw.trades
    f.tick(f.mid - 0.5)
    f.tick()
    f.tick()
    assert not sw.trades and "basket stop" in reasons(sw) and sw.basket_until > f.t


def test_daily_loss_limit_closes_all_and_stops_for_the_day(tmp_path):
    sw, fake = make_swarm(tmp_path, make_cfg(START_MODE="B", DAILY_LOSS_PCT=0.2))
    f = warm(sw, fake)
    f.until(lambda: sw.trades, per_s=0.3, max_s=5)
    f.drift(0.6, -2.0)                               # 0.2% of 1000 = 2.0 lost
    f.tick()
    assert sw.halted and "daily loss" in sw.block and not [t for t in sw.trades.values() if not t.closing]
    f.t = sw.day_start(f.t) + 86400 + 1              # next server day
    f.tick()
    assert not sw.halted


def test_auto_pause_on_negative_rolling_result(tmp_path):
    sw, fake = make_swarm(tmp_path, make_cfg(START_MODE="B", ROLLING_TRADES=5))
    for _ in range(5):
        sw.rolling.add(-0.1)
    sw._check_auto_pause(T0)
    assert sw.auto_pause_until > T0 and sw.rolling_warning() is False      # warning needs 20 trades
    f = warm(sw, fake)
    f.drift(3, 0.3)
    assert not sw.trades and "auto-pause" in sw.block


def test_adopts_own_positions_after_restart_and_ignores_others(tmp_path):
    fake = FakeMT5()
    fake.add_symbol(SYM)
    fake.set_tick(SYM, 2000.0, 2000.24)
    cfg = make_cfg(START_MODE="B")
    mine = fake.add_position(SYM, "BUY", 0.01, 2000.24, cfg.MAGIC, sl=1999.0, tp=2001.0)
    fake.add_position(SYM, "SELL", 0.01, 2000.0, 999)
    sw, _ = make_swarm(tmp_path, cfg, fake=fake)
    assert list(sw.trades) == [mine.ticket] and sw.trades[mine.ticket].role == "adopted"
    assert sw.trades[mine.ticket].risk_money == pytest.approx(1.24)


def test_kill_switch_closes_everything(tmp_path):
    sw, fake = make_swarm(tmp_path, make_cfg(START_MODE="B"))
    f = warm(sw, fake)
    f.drift(3, 0.3)
    assert sw.trades
    other = fake.add_position(SYM, "SELL", 0.01, 2000.0, 999)
    left = sw.close_everything("kill switch", f.t)
    assert left == 0 and not sw.trades
    assert other.ticket in fake.open_positions       # never touches trades of other magic numbers
    assert "kill switch" in reasons(sw)


def test_thread_executor_sends_closes_before_opens():
    fake = FakeMT5()
    fake.add_symbol(SYM)
    fake.set_tick(SYM, 2000.0, 2000.24)
    p = fake.add_position(SYM, "BUY", 0.01, 2000.24, 1)
    b = Broker(fake, 1, retries=0)
    spec = b.spec(SYM)
    fake.latency_s = 0.05
    ex = ThreadExecutor(b, spec, max_age_s=10)
    ex.submit(new_cmd("open", side="BUY", volume=0.01, sl_dist=1, tp_dist=1, deviation=10, comment="a"))
    ex.submit(new_cmd("open", side="BUY", volume=0.01, sl_dist=1, tp_dist=1, deviation=10, comment="b"))
    ex.submit(new_cmd("close", ticket=p.ticket, pos_type=0, volume=0.01, deviation=10, comment="c"))
    import time
    end = time.time() + 2
    got = []
    while time.time() < end and len(got) < 3:
        got += ex.results()
        time.sleep(0.01)
    ex.stop()
    assert len(got) == 3 and all(r["ok"] for r in got)
    assert [r["kind"] for r in got].index("close") <= 1          # the close jumped the queue
    assert all(r["latency_ms"] >= 40 for r in got)


def test_stale_open_is_dropped():
    fake = FakeMT5()
    fake.add_symbol(SYM)
    fake.set_tick(SYM, 2000.0, 2000.24)
    b = Broker(fake, 1, retries=0)
    ex = SyncExecutor(b, b.spec(SYM), max_age_s=0.5)
    cmd = new_cmd("open", side="BUY", volume=0.01, sl_dist=1, tp_dist=1, deviation=10, comment="a")
    cmd["created"] -= 1.0
    ex.submit(cmd)
    r = ex.results()[0]
    assert r["stale"] and not fake.sent


def test_requote_is_retried(tmp_path):
    fake = FakeMT5()
    fake.add_symbol(SYM)
    fake.set_tick(SYM, 2000.0, 2000.24)
    b = Broker(fake, 1, retries=2, retry_sleep=0)
    fake.fail_next = [fake.TRADE_RETCODE_REQUOTE]
    res = b.market_order(b.spec(SYM), "BUY", 0.01, 1.0, 0.5, 10, "x")
    assert res.ok and len(fake.sent) == 2


def test_report_runs_and_is_honest(tmp_path):
    from report import build_report, stats
    sw, fake = make_swarm(tmp_path, make_cfg(START_MODE="AB"))
    f = warm(sw, fake)
    for k in range(4):
        f.drift(3, 0.3 if k % 2 else -0.3)
    sw.close_everything("manual stop", f.t)
    rows = sw.j.closed_since(0)
    assert rows
    lines = build_report(rows, 0.1, 1000.0, "USD", sw.block_time, sw.dd_money, sw.dd_pct, "T", sw.orders_sent)
    text = "\n".join(lines)
    for word in ("per minute", "before spread", "net after spread", "minimum profitable target",
                 "closed by", "slippage", "drawdown", "by mode", "time spent"):
        assert word in text
    if stats(rows)["net"] < 0:
        assert "NEGATIVE" in text


def test_process_executor_plumbing():
    """The default order worker: a spawned process with its own MT5 connection (here: the fake)."""
    import time
    from broker import ProcessExecutor
    ex = ProcessExecutor({}, SYM, 7, 1, 10.0, module="fake_mt5_proc")
    try:
        assert ex.wait_ready(20)
        ex.submit(new_cmd("open", side="BUY", volume=0.01, sl_dist=1.0, tp_dist=0.5, deviation=10, comment="p"))
        got, end = [], time.time() + 10
        while time.time() < end and not got:
            got += ex.results()
            time.sleep(0.01)
        assert got and got[0]["ok"] and got[0]["ticket"] and got[0]["sl"] and got[0]["tp"]
        ex.submit(new_cmd("close", ticket=got[0]["ticket"], pos_type=0, volume=0.01, deviation=10, comment="c"))
        got2, end = [], time.time() + 10
        while time.time() < end and not got2:
            got2 += ex.results()
            time.sleep(0.01)
        assert got2 and got2[0]["ok"] and got2[0]["kind"] == "close"
    finally:
        ex.stop()
    assert not ex.alive()


def test_report_cli_reads_all_sessions(tmp_path, monkeypatch, capsys):
    import config
    import report
    sw, fake = make_swarm(tmp_path, make_cfg(START_MODE="B"))
    sw.j.start_session(config.VERSION, "sync", 1000.0, 1000.0)
    f = warm(sw, fake)
    f.until(lambda: sw.trades, per_s=0.3, max_s=5)
    sw.close_everything("manual stop", f.t)
    sw.save_session(f.t)
    sw.j.flush(force=True)
    monkeypatch.setattr(config, "DB_FILE", os.path.join(str(tmp_path), "t.sqlite"))
    monkeypatch.setattr(config, "LOG_DIR", os.path.join(str(tmp_path), "logs"))
    assert report.main([]) == 0
    out = capsys.readouterr().out
    assert "REPORT  version" in out and "net after spread" in out and "manual stop" in out
