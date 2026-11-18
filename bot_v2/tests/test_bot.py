"""End-to-end checks of the trading loop against the fake MT5."""
from datetime import datetime, timezone

import config
import risk
from bot import Bot, SymbolTrader
from broker import Broker
from fake_mt5 import FakeMT5
from report import Journal, build_report

SYM = "XAUUSDm"
T0 = datetime(2026, 11, 18, 10, tzinfo=timezone.utc).timestamp()   # a Wednesday
UP_BARS = [2000 + i * 1.0 for i in range(70)]
DOWN_BARS = list(reversed(UP_BARS))


class Sim:
    def __init__(self, tmp_path, max_lots=1.0, daily_loss=0, **over):
        self.fake = FakeMT5()
        self.fake.add_symbol(SYM)
        self.fake.set_bars(SYM, UP_BARS)
        self.broker = Broker(self.fake, config.MAGIC, retry_sleep=0)
        self.journal = Journal(str(tmp_path / "t.sqlite"), str(tmp_path / "logs"))
        self.cfg = config.symbol_config("XAUUSD")
        self.cfg.update(sessions=config.ALWAYS_OPEN, dir_lookback_s=5)
        self.cfg.update(over)
        self.bid, self.t = 2070.0, T0
        self.fake.set_tick(SYM, self.bid, self.bid + 0.2, self.t)
        self.max_lots, self.daily_loss = max_lots, daily_loss
        self.restart()

    def restart(self):
        self.tr = SymbolTrader("XAUUSD", SYM, self.cfg, self.broker, self.journal, risk.NewsCalendar(), 0)
        self.bot = Bot(self.broker, self.journal, [self.tr], 8, self.max_lots, self.daily_loss, 0)

    def run(self, seconds, drift=0.0, spread=0.2, dt=0.5):
        end = self.t + seconds
        while self.t < end - 1e-9:
            self.bid += drift * dt
            self.fake.set_tick(SYM, self.bid, self.bid + spread, self.t)
            self.bot.loop_once(self.t)
            self.t += dt

    def run_until(self, cond, max_s, drift=0.0, dt=0.5):
        end = self.t + max_s
        while self.t < end and not cond():
            self.run(dt, drift, dt=dt)
        assert cond(), "condition not reached"

    def positions(self):
        return self.broker.positions(SYM)

    def closed(self):
        return self.journal.closed_since(0)


def open_buy(sim):
    sim.run(12, drift=0.2)                 # warm-up, then price rises 1 spread per second
    ps = sim.positions()
    assert len(ps) == 1 and ps[0].type == 0
    return ps[0]


ATR = 1.05     # fake bars: closes 1.0 apart, range 0.1 -> true range 1.05


def test_atr_is_measured_from_bars(tmp_path):
    sim = Sim(tmp_path)
    sim.run(1)
    assert abs(sim.tr.atr - ATR) < 1e-9


def test_opens_buy_at_min_lot_with_broker_stop_and_target(tmp_path):
    sim = Sim(tmp_path)
    p = open_buy(sim)
    assert p.volume == 0.01                                    # symbol minimum
    assert abs((p.price_open - p.sl) - 1.0 * ATR) < 0.011      # stop 1 ATR, at the broker, set at open
    assert abs((p.tp - p.price_open) - 1.5 * ATR) < 0.011      # target 1.5 ATR, at the broker
    row = sim.journal.row(p.ticket)
    assert row["kind"] == "base" and row["open_latency_ms"] is not None
    assert abs(row["unit"] - ATR) < 1e-9 and row["tp"] == p.tp


def test_pyramid_adds_only_after_every_stop_locks_profit(tmp_path):
    sim = Sim(tmp_path, target_atr=10.0)               # target far away: watch the adds
    open_buy(sim)
    sim.run(1, drift=0.2)
    assert len(sim.positions()) == 1 and "add waits" in sim.tr.status   # base stop not locked yet
    sim.run_until(lambda: len(sim.positions()) == 4, 40, drift=0.2)
    trades = sorted(sim.tr.trades.values(), key=lambda m: m.open_time)
    assert [m.kind for m in trades] == ["base", "add", "add", "add"]   # max_adds = 3
    assert all(sim.tr._locked(m) for m in trades[:-1])  # every earlier trade is safe
    sim.run(3, drift=0.2)
    assert len(sim.positions()) == 4                   # base + 3 adds = max_trades 4: no 5th trade
    assert "max adds" in sim.tr.status or "max trades" in sim.tr.status


def test_add_shares_the_basket_locked_stop(tmp_path):
    sim = Sim(tmp_path, target_atr=10.0, max_adds=1)
    open_buy(sim)
    sim.run_until(lambda: len(sim.positions()) == 2, 15, drift=0.2)
    base, add = sorted(sim.tr.trades.values(), key=lambda m: m.open_time)
    assert base.kind == "base" and add.kind == "add" and sim.tr._locked(base)
    gap = add.open_price - sim.fake.open_positions[add.ticket].sl
    assert gap < 1.0 * ATR - 0.05                      # tighter than a full 1 ATR stop
    assert abs(sim.fake.open_positions[add.ticket].sl - base.sl) < 0.02   # same level as the base stop


def test_add_waits_when_price_is_too_close_to_basket_stop(tmp_path):
    sim = Sim(tmp_path, target_atr=10.0, add_min_room_atr=5.0)   # room rule impossible to meet
    open_buy(sim)
    sim.run_until(lambda: sim.tr._locked(next(iter(sim.tr.trades.values()))), 10, drift=0.2)
    sim.run(2, drift=0.2)
    assert len(sim.positions()) == 1 and "too close to the basket stop" in sim.tr.status


def test_no_entry_when_one_stop_is_too_big_for_the_account(tmp_path):
    sim = Sim(tmp_path)
    sim.fake.equity = 5.0                              # stop 1.05 x $1 = 1.05 > 10% of 5.00
    sim.run(15, drift=0.2)
    assert sim.positions() == [] and "stop too big for this account" in sim.tr.status


def test_no_entry_without_free_margin(tmp_path):
    sim = Sim(tmp_path)
    sim.fake.margin_free = 0.1                         # needs 0.20 for 0.01 lot
    sim.run(15, drift=0.2)
    assert sim.positions() == [] and "not enough free margin" in sim.tr.status
    assert not [e for e in sim.journal.feed if e[2] == "error"]   # checked before sending: no spam


def test_broker_no_money_pauses_symbol_instead_of_retrying(tmp_path):
    sim = Sim(tmp_path)
    sim.fake.fail_next = [sim.fake.TRADE_RETCODE_NO_MONEY]
    sim.run(20, drift=0.2)
    errors = [e for e in sim.journal.feed if e[2] == "error"]
    assert len(errors) == 1 and "not enough free margin" in errors[0][3]
    assert sim.positions() == [] and "paused" in sim.tr.status
    sim.run_until(lambda: sim.positions(), 60, drift=0.2)          # trades again after the pause


def test_trades_are_tagged_with_version_and_report_cli_reads_them(tmp_path, monkeypatch, capsys):
    import report
    sim = Sim(tmp_path, max_adds=0)
    p = open_buy(sim)
    assert sim.journal.row(p.ticket)["version"] == config.VERSION
    sim.bot.close_everything("manual stop", sim.t)
    monkeypatch.chdir(tmp_path)                        # main() changes folder: restore it after the test
    monkeypatch.setattr(config, "DB_FILE", str(tmp_path / "t.sqlite"))
    monkeypatch.setattr(config, "LOG_DIR", str(tmp_path / "logs"))
    assert report.main([]) == 0
    out = capsys.readouterr().out
    assert f"version {config.VERSION}, all sessions" in out and "trades 1" in out


def test_startup_shows_cost_of_one_stop_and_the_cap(tmp_path):
    from bot import stop_preview
    sim = Sim(tmp_path)
    line, ok = stop_preview(sim.tr, 1000.0)            # stop 1.05 ATR x $1 = 1.05 = 0.1% of 1000
    assert ok and "one stop now = 1.05" in line and "0.1% of equity" in line
    line, ok = stop_preview(sim.tr, 5.0)               # 21% of 5.00 > 10%
    assert not ok and "will NOT trade" in line


def test_report_cli_does_not_invent_a_drawdown(tmp_path):
    j = Journal(str(tmp_path / "r.sqlite"), str(tmp_path / "logs"))
    j.open_trade(ticket=1, symbol=SYM, side="BUY", kind="base", basket=1, volume=0.01,
                 open_time=j.session_start + 1, open_price=100.0, spread_cost=0.2, unit=1.0)
    j.close_trade(1, close_time=j.session_start + 9, close_price=100.0, close_reason="target", pnl=1.0, pnl_points=100)
    text = "\n".join(build_report(j, {}, "USD", rows=j.closed_since(0), title="REPORT"))
    assert "max floating drawdown" not in text and "trades 1" in text


def test_no_add_while_a_trade_is_losing(tmp_path):
    sim = Sim(tmp_path)
    open_buy(sim)
    t = sim.positions()[0].ticket
    for obj in (sim.fake.open_positions[t], sim.tr.trades[t]):
        obj.price_open = obj.open_price = sim.bid + 0.5   # make it a loser (still above its stop)
    sim.fake.open_positions[t].sl = sim.bid - 5
    sim.run(5, drift=0.0)
    assert len(sim.positions()) == 1


def test_broker_target_closes_winner(tmp_path):
    sim = Sim(tmp_path, max_adds=0)
    p = open_buy(sim)
    sim.run_until(lambda: sim.journal.row(p.ticket)["close_time"], 15, drift=0.2)
    row = sim.journal.row(p.ticket)
    assert row["close_reason"] == "target (broker TP)" and row["pnl"] > 0
    assert row["peak_units"] is not None


def test_stop_loss_then_flip_when_trend_agrees(tmp_path):
    sim = Sim(tmp_path, max_adds=0)
    buy = open_buy(sim)
    sim.fake.set_bars(SYM, DOWN_BARS)                  # trend turns DOWN
    sim.run_until(lambda: any(p.type == 1 for p in sim.positions()), 10, drift=-0.4)
    rows = sim.closed()
    assert [r["close_reason"] for r in rows] == ["stop loss"]
    assert rows[0]["ticket"] == buy.ticket and rows[0]["pnl"] < 0
    assert abs(rows[0]["pnl"]) < 1.5 * ATR * 0.01 * 100        # loss about 1 ATR, not 12 spreads
    ps = sim.positions()
    assert len(ps) == 1 and ps[0].type == 1 and sim.journal.row(ps[0].ticket)["kind"] == "flip"
    assert sim.tr.flips.count(sim.t) == 1


def test_no_new_trade_against_own_open_trade(tmp_path):
    sim = Sim(tmp_path, max_adds=0)
    open_buy(sim)
    sim.fake.set_bars(SYM, DOWN_BARS)
    sim.run(3.5, drift=-0.3)                           # direction and trend DOWN, BUY still open
    ps = sim.positions()
    assert len(ps) == 1 and ps[0].type == 0
    assert "opposite trades still open" in sim.tr.status


def test_no_same_side_reentry_right_after_stop_loss(tmp_path):
    sim = Sim(tmp_path, max_adds=0, stall_exit_s=999)
    p = open_buy(sim)
    sim.fake.hit_sl(p.ticket)                          # stopped out while direction still reads UP
    sim.run(2, drift=0.2)
    assert sim.positions() == [] and "fresh signal needed" in sim.tr.status
    sim.run_until(lambda: sim.positions(), 10, drift=0.2)          # after the 5 s window: a new BUY
    assert sim.t - sim.tr.last_stop[1] >= sim.cfg["dir_lookback_s"]


def test_flip_cooldown_blocks_a_quick_second_flip(tmp_path):
    sim = Sim(tmp_path, max_adds=0)
    open_buy(sim)
    sim.fake.set_bars(SYM, DOWN_BARS)
    sim.run_until(lambda: any(p.type == 1 for p in sim.positions()), 10, drift=-0.4)   # BUY -> SELL flip
    sim.fake.set_bars(SYM, UP_BARS)
    sim.run_until(lambda: not sim.positions(), 10, drift=0.4)   # SELL stopped, flip back blocked
    sim.run(1, drift=0.4)
    assert [r["close_reason"] for r in sim.closed()] == ["stop loss", "stop loss"]
    assert sim.positions() == []
    assert "flip cooldown" in sim.tr.status
    sim.run_until(lambda: sim.positions(), 20, drift=0.2)       # cooldown (15 s) over
    ps = sim.positions()
    assert len(ps) == 1 and ps[0].type == 0 and sim.journal.row(ps[0].ticket)["kind"] == "flip"


def test_no_time_exit_by_default(tmp_path):
    sim = Sim(tmp_path, max_adds=0)
    p = open_buy(sim)
    sim.run(90, drift=0.0)
    assert [x.ticket for x in sim.positions()] == [p.ticket]   # only price levels close trades


def test_no_follow_through_exit_when_switched_on(tmp_path):
    sim = Sim(tmp_path, max_adds=0, stall_exit_s=60)
    p = open_buy(sim)
    sim.run(30, drift=0.0)
    assert sim.positions()                              # still waiting
    sim.run_until(lambda: not sim.positions(), 35, drift=0.0)
    row = sim.journal.row(p.ticket)
    assert row["close_reason"] == "no follow-through"
    assert 59 <= row["close_time"] - row["open_time"] <= 62


def test_trailing_stop_moves_broker_sl_and_closes_in_profit(tmp_path):
    sim = Sim(tmp_path, max_adds=0)
    p = open_buy(sim)
    sim.run_until(lambda: sim.fake.open_positions[p.ticket].sl > p.price_open, 10, drift=0.2)
    assert sim.tr.trades[p.ticket].lock_sl                    # broker SL now locks profit
    sim.run_until(lambda: not sim.positions(), 10, drift=-0.4)
    row = sim.journal.row(p.ticket)
    assert row["close_reason"] == "trailing stop (broker SL)" and row["pnl"] > 0   # broker closed it
    assert row["close_latency_ms"] is None                                          # no bot order needed


def test_basket_stop_closes_symbol_and_pauses(tmp_path):
    sim = Sim(tmp_path, basket_stop_money=0.5)
    p = open_buy(sim)
    sim.bid = p.price_open - 0.8                       # floating about -0.8, still above the 1 ATR stop
    sim.run(0.5)
    assert sim.positions() == []
    assert [r["close_reason"] for r in sim.closed()] == ["basket stop"]
    assert sim.tr.paused_until > sim.t
    sim.run(10, drift=0.2)
    assert sim.positions() == [] and "cooldown" in sim.tr.status


def test_daily_loss_limit_closes_and_halts(tmp_path):
    sim = Sim(tmp_path, daily_loss=0.3)
    p = open_buy(sim)
    sim.bid = p.price_open - 0.8
    sim.run(0.5)
    assert sim.positions() == [] and sim.bot.halted
    sim.run(20, drift=0.2)
    assert sim.positions() == [] and "daily loss" in sim.tr.status


def test_max_total_lots_blocks_adds(tmp_path):
    sim = Sim(tmp_path, max_lots=0.01, stall_exit_s=999)
    open_buy(sim)
    sim.run(4, drift=0.2)
    assert len(sim.positions()) == 1 and "max total lots" in sim.tr.status


def test_close_of_already_closed_position_is_not_an_error(tmp_path):
    sim = Sim(tmp_path, max_adds=0)
    p = open_buy(sim)
    sim.fake.fail_next = [sim.fake.TRADE_RETCODE_POSITION_CLOSED]
    assert sim.tr._close(sim.tr.trades[p.ticket], "target", sim.t) is False
    assert not [e for e in sim.journal.feed if e[2] == "error"]


def test_frozen_position_is_retried(tmp_path):
    sim = Sim(tmp_path, max_adds=0)
    p = open_buy(sim)
    sim.fake.fail_next = [sim.fake.TRADE_RETCODE_FROZEN]
    assert sim.tr._close(sim.tr.trades[p.ticket], "target", sim.t) is True
    assert sim.journal.row(p.ticket)["close_reason"] == "target"


def test_spread_spike_blocks_entries(tmp_path):
    sim = Sim(tmp_path)
    sim.run(12)
    sim.run(0.5, spread=0.5)
    assert sim.tr.status.startswith("spread too high") and sim.positions() == []


def test_spread_too_big_for_volatility_blocks_entries(tmp_path):
    sim = Sim(tmp_path)
    sim.run(15, drift=0.2, spread=0.5)                 # target 1.575 < 4 x 0.5
    assert sim.positions() == [] and sim.tr.status.startswith("spread too high vs volatility")


def test_choppy_market_blocks_entries(tmp_path):
    sim = Sim(tmp_path)
    sim.fake.set_bars(SYM, [2000 + (3 if i % 2 else 0) for i in range(70)])
    sim.run(15, drift=0.2)
    assert sim.positions() == [] and "choppy" in sim.tr.status


def test_restart_adopts_open_trades_and_reconciles_closed_ones(tmp_path):
    sim = Sim(tmp_path)
    p = open_buy(sim)
    other = sim.fake.add_position(SYM, "SELL", 0.01, sim.bid + 0.2, magic=config.MAGIC, sl=sim.bid + 3)
    sim.fake.add_position(SYM, "BUY", 0.05, 2060.0, magic=999)         # not ours: ignored
    sim.restart()
    sim.run(0.5)
    assert set(sim.tr.trades) == {p.ticket, other.ticket}
    assert sim.tr.trades[p.ticket].kind == "base"                       # remembered from the journal
    assert sim.tr.trades[other.ticket].kind == "adopted"
    sim.fake.hit_sl(p.ticket)                                           # closes while "bot is off"
    sim.restart()
    sim.run(0.5)
    assert sim.journal.row(p.ticket)["close_reason"] == "stop loss"


def test_close_everything_for_kill_switch(tmp_path):
    sim = Sim(tmp_path)
    open_buy(sim)
    sim.run_until(lambda: len(sim.positions()) >= 2, 10, drift=0.2)
    assert sim.bot.close_everything("kill switch", sim.t) == 0
    assert {r["close_reason"] for r in sim.closed()} == {"kill switch"}


def test_order_retries_requote_and_switches_filling(tmp_path):
    sim = Sim(tmp_path)
    sim.fake.fail_next = [sim.fake.TRADE_RETCODE_REQUOTE]
    sim.fake.accepted_filling = sim.fake.ORDER_FILLING_IOC
    p = open_buy(sim)
    assert p.volume == 0.01
    fills = [r.get("type_filling") for r in sim.fake.sent]
    assert sim.fake.ORDER_FILLING_FOK in fills and fills[-1] == sim.fake.ORDER_FILLING_IOC


def test_market_closed_pauses_symbol(tmp_path):
    sim = Sim(tmp_path)
    sim.fake.fail_next = [sim.fake.TRADE_RETCODE_MARKET_CLOSED]
    sim.run(11, drift=0.2)
    assert sim.positions() == [] and sim.tr.status == "market closed"


def test_report_is_honest(tmp_path):
    j = Journal(str(tmp_path / "r.sqlite"), str(tmp_path / "logs"))
    t = j.session_start + 1
    for i, (pnl, kind, reason) in enumerate([(1.0, "base", "target"), (1.0, "add", "target"),
                                             (-3.0, "flip", "stop loss")]):
        j.open_trade(ticket=i + 1, symbol=SYM, side="BUY", kind=kind, basket=1, volume=0.01,
                     open_time=t, open_price=100.0, spread_cost=0.2, unit=0.2)
        j.close_trade(i + 1, close_time=t + 30, close_price=100.0, close_reason=reason, pnl=pnl,
                      pnl_points=pnl * 100)
    text = "\n".join(build_report(j, {SYM: -3.5}, "USD"))
    assert "average loss is BIGGER than average win" in text
    assert "flips 1 (profitable 0)" in text and "pyramid adds 1" in text
    assert "biggest losing basket -1.00" in text and "max floating drawdown -3.50" in text
    assert "stop loss 1 (avg -3.00)" in text and "target 2 (avg +1.00)" in text
    assert "before spread -0.40" in text and "avg hold: wins 30s" in text
    assert "orders: open" in text


def test_report_blames_the_spread_when_gross_is_positive(tmp_path):
    j = Journal(str(tmp_path / "r.sqlite"), str(tmp_path / "logs"))
    t = j.session_start + 1
    j.open_trade(ticket=1, symbol=SYM, side="BUY", kind="base", basket=1, volume=0.01,
                 open_time=t, open_price=100.0, spread_cost=0.5, unit=1.0)
    j.close_trade(1, close_time=t + 5, close_price=100.0, close_reason="target", pnl=-0.1, pnl_points=-10)
    text = "\n".join(build_report(j, {SYM: 0.0}, "USD"))
    assert "made money BEFORE spread but lost after it" in text


def test_report_shows_why_the_bot_waited(tmp_path):
    sim = Sim(tmp_path)
    sim.run(40, drift=0.2, spread=0.5)                 # spread too big vs ATR the whole time
    text = "\n".join(build_report(sim.journal, {SYM: 0.0}, "USD", {SYM: sim.tr.block_time}))
    assert "time spent:" in text and "spread too high vs volatility" in text
    assert "too expensive to scalp here" in text


def test_old_database_gets_new_columns(tmp_path):
    import sqlite3
    db = tmp_path / "old.sqlite"
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE trades (ticket INTEGER PRIMARY KEY, symbol TEXT)")
    con.commit()
    con.close()
    j = Journal(str(db), str(tmp_path / "logs"))
    cols = {r[1] for r in j.db.execute("PRAGMA table_info(trades)")}
    assert {"tp", "peak_units", "unit"} <= cols


def test_mt5_error_is_not_mistaken_for_closed_trades(tmp_path):
    sim = Sim(tmp_path, stall_exit_s=999)
    p = open_buy(sim)
    real_get, real_err = sim.fake.positions_get, sim.fake.last_error
    sim.fake.positions_get = lambda **kw: None            # IPC error, like a disconnect
    sim.fake.last_error = lambda: (-10004, "No IPC connection")
    sim.run(70)
    assert p.ticket in sim.tr.trades and sim.closed() == []
    sim.fake.positions_get, sim.fake.last_error = real_get, real_err
    sim.run(1)
    assert p.ticket in sim.tr.trades and sim.closed() == []
