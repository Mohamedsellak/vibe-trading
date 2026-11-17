"""Position sizing and account-level risk limits, shared by backtest and bot."""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import numpy as np

from config import RiskConfig, SymbolSpec
from strategy import MINUTE_MS, local_minutes


def lot_size(equity: float, risk_pct: float, sl_dist: float, spec: SymbolSpec,
             commission_per_lot_side: float) -> float:
    """Lots so that a stop-out loses `risk_pct` of equity, commission included.

    Rounded DOWN to the volume step. Returns 0.0 when even the minimum volume
    would risk more than allowed (the trade must then be skipped).
    """
    if sl_dist <= 0 or equity <= 0:
        return 0.0
    risk_amount = equity * risk_pct / 100.0
    loss_per_lot = sl_dist * spec.value_per_price_unit + 2.0 * commission_per_lot_side
    if loss_per_lot <= 0:
        return 0.0
    raw = risk_amount / loss_per_lot
    step = spec.volume_step
    lots = math.floor(raw / step + 1e-9) * step
    decimals = max(0, -int(math.floor(math.log10(step)))) if step < 1 else 0
    lots = round(min(lots, spec.volume_max), decimals)
    if lots < spec.volume_min - 1e-12:
        return 0.0
    return lots


@dataclass
class RiskState:
    day_key: int = -1
    day_start_equity: float = 0.0
    peak_equity: float = 0.0
    halted: bool = False
    halt_reason: str = ""
    trades_today: int = 0
    consec_losses: int = 0
    cooldown_until_ms: int = 0


class RiskManager:
    """Daily loss, drawdown kill switch, trade count, cooldown, open positions.

    The drawdown kill switch is permanent: once tripped, trading stays off until
    a human resets the persisted state (see README).
    """

    def __init__(self, cfg: RiskConfig, equity: float, server_tz: str = "UTC",
                 state: RiskState | None = None):
        self.cfg = cfg
        self.server_tz = server_tz
        self.state = state or RiskState(peak_equity=equity, day_start_equity=equity)
        if self.state.peak_equity <= 0:
            self.state.peak_equity = equity

    def _day(self, now_ms: int) -> int:
        return int(local_minutes(np.array([now_ms]), self.server_tz)[1][0])

    def update_equity(self, now_ms: int, equity: float) -> None:
        s = self.state
        d = self._day(now_ms)
        if d != s.day_key:
            s.day_key, s.day_start_equity, s.trades_today = d, equity, 0
        s.peak_equity = max(s.peak_equity, equity)
        if not s.halted and s.peak_equity > 0:
            dd = (s.peak_equity - equity) / s.peak_equity * 100.0
            if dd >= self.cfg.max_drawdown_pct:
                s.halted = True
                s.halt_reason = f"max drawdown {dd:.2f}% >= {self.cfg.max_drawdown_pct}%"

    def daily_loss_hit(self, equity: float) -> bool:
        s = self.state
        if s.day_start_equity <= 0:
            return False
        loss = (s.day_start_equity - equity) / s.day_start_equity * 100.0
        return loss >= self.cfg.max_daily_loss_pct

    def can_open(self, now_ms: int, equity: float, n_open: int) -> str | None:
        """None if a new trade is allowed, otherwise the reason it is blocked."""
        self.update_equity(now_ms, equity)
        s = self.state
        if s.halted:
            return "kill_switch:" + s.halt_reason
        if self.daily_loss_hit(equity):
            return "max_daily_loss"
        if n_open >= self.cfg.max_open_positions:
            return "max_open_positions"
        if s.trades_today >= self.cfg.max_trades_per_day:
            return "max_trades_per_day"
        if now_ms < s.cooldown_until_ms:
            return "cooldown"
        return None

    def on_open(self, now_ms: int, equity: float) -> None:
        self.update_equity(now_ms, equity)
        self.state.trades_today += 1

    def on_close(self, now_ms: int, pnl: float, equity: float) -> None:
        s = self.state
        if pnl < 0:
            s.consec_losses += 1
            if s.consec_losses >= self.cfg.cooldown_after_losses:
                s.cooldown_until_ms = now_ms + self.cfg.cooldown_minutes * MINUTE_MS
                s.consec_losses = 0
        else:
            s.consec_losses = 0
        self.update_equity(now_ms, equity)

    def to_dict(self) -> dict:
        return asdict(self.state)
