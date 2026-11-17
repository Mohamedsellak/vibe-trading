from datetime import datetime, timezone

from config import RiskConfig, SymbolSpec
from risk import RiskManager, lot_size


def ms(y, mo, d, h=0, mi=0):
    return int(datetime(y, mo, d, h, mi, tzinfo=timezone.utc).timestamp() * 1000)


def gold():
    return SymbolSpec(name="XAUUSD", point=0.001, digits=3, tick_size=0.001, tick_value=0.1,
                      contract_size=100.0, volume_min=0.01, volume_max=200.0, volume_step=0.01)


def test_lot_size_risk_and_rounding():
    # risk 0.5% of 10k = $50; SL 2.00 on gold = $200/lot + $7 commission -> 0.2415 -> 0.24
    assert lot_size(10_000, 0.5, 2.0, gold(), 3.5) == 0.24
    loss = 0.24 * (2.0 * gold().value_per_price_unit + 7.0)
    assert loss <= 50.0


def test_lot_size_below_minimum_skips():
    assert lot_size(100, 0.5, 5.0, gold(), 3.5) == 0.0
    assert lot_size(10_000, 0.5, 0.0, gold(), 3.5) == 0.0


def test_daily_loss_blocks_then_resets_next_day():
    rm = RiskManager(RiskConfig(max_daily_loss_pct=2.0), 10_000)
    t = ms(2026, 3, 2, 9)
    assert rm.can_open(t, 10_000, 0) is None
    assert rm.can_open(t + 60_000, 9_790, 0) == "max_daily_loss"
    assert rm.can_open(ms(2026, 3, 3, 9), 9_790, 0) is None


def test_drawdown_kill_switch_is_permanent():
    rm = RiskManager(RiskConfig(max_drawdown_pct=10.0, max_daily_loss_pct=50.0), 10_000)
    rm.update_equity(ms(2026, 3, 2, 9), 11_000)
    assert rm.can_open(ms(2026, 3, 5, 9), 9_850, 0).startswith("kill_switch")
    assert rm.can_open(ms(2026, 3, 6, 9), 11_500, 0).startswith("kill_switch")


def test_max_trades_open_positions_and_cooldown():
    cfg = RiskConfig(max_trades_per_day=2, cooldown_after_losses=2, cooldown_minutes=30,
                     max_daily_loss_pct=50.0)
    rm = RiskManager(cfg, 10_000)
    t = ms(2026, 3, 2, 9)
    assert rm.can_open(t, 10_000, 1) == "max_open_positions"
    rm.on_open(t, 10_000); rm.on_close(t + 1, -10, 9_990)
    rm.on_open(t + 2, 9_990); rm.on_close(t + 3, -10, 9_980)
    assert rm.can_open(t + 4, 9_980, 0) == "max_trades_per_day"
    rm.state.trades_today = 0
    assert rm.can_open(t + 4, 9_980, 0) == "cooldown"
    assert rm.can_open(t + 31 * 60_000, 9_980, 0) is None


def test_win_resets_loss_streak():
    rm = RiskManager(RiskConfig(cooldown_after_losses=2), 10_000)
    t = ms(2026, 3, 2, 9)
    rm.on_close(t, -1, 9_999); rm.on_close(t, 5, 10_004); rm.on_close(t, -1, 10_003)
    assert rm.state.cooldown_until_ms == 0
