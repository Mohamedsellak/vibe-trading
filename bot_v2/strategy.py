"""bot_v2 strategy. Distances are in ATR = average 1-minute range (volatility). Spread is the cost.

1. DIRECTION: price move over the last 5 s: >= +0.25 ATR = UP, <= -0.25 ATR = DOWN, else FLAT.
2. TREND: 1-minute bars, EMA(8) vs EMA(21); gap > 0.15 ATR = UP/DOWN. Entries need direction == trend.
3. EXITS: all at the broker: stop 1 ATR, target 1.5 ATR, stop trails 0.5 ATR behind from +0.8 ATR.
4. FILTERS: no entry if the 20-bar path zig-zags, or the target is under 6x the spread (too costly).
5. FLAW: with no real edge every trade loses about 1 spread on average; only the report can show an edge.
"""
from __future__ import annotations

from collections import deque
from statistics import median

UP, DOWN, FLAT = "UP", "DOWN", "FLAT"
BUY, SELL = "BUY", "SELL"


def side_of(direction):
    return {UP: BUY, DOWN: SELL}.get(direction)


def dir_of(side):
    return UP if side == BUY else DOWN


def opposite(side):
    return SELL if side == BUY else BUY


class MarketState:
    """Recent mid prices (for direction) and spreads (for the median spread)."""

    def __init__(self, lookback_s, spread_window_s):
        self.lookback_s = lookback_s
        self.spread_window_s = spread_window_s
        self.mids = deque()       # (time, mid)
        self.spreads = deque()    # (time, spread), one sample per second
        self._last_spread_t = None
        self._median = None
        self.bid = self.ask = 0.0

    def update(self, t, bid, ask):
        self.bid, self.ask = bid, ask
        mid = (bid + ask) / 2
        if not self.mids or self.mids[-1][1] != mid:
            self.mids.append((t, mid))
        # keep exactly one sample at or before t - lookback (the reference point)
        while len(self.mids) >= 2 and self.mids[1][0] <= t - self.lookback_s:
            self.mids.popleft()
        if self._last_spread_t is None or t - self._last_spread_t >= 1.0:
            self.spreads.append((t, ask - bid))
            self._last_spread_t = t
            while self.spreads and self.spreads[0][0] < t - self.spread_window_s:
                self.spreads.popleft()
            self._median = median(s for _, s in self.spreads)   # once per second, not every loop

    @property
    def spread(self):
        return self.ask - self.bid

    def median_spread(self):
        return self._median if self._median is not None else self.spread

    def move(self, t):
        """Price change over the lookback, or None while warming up."""
        if not self.mids or self.mids[0][0] > t - self.lookback_s:
            return None
        return self.mids[-1][1] - self.mids[0][1]


def atr(bars, n):
    """Average true range of the last n bars. bars = [(high, low, close), ...] (finished bars only)."""
    if len(bars) < n + 1:
        return 0.0
    trs = []
    for (_, _, prev_c), (h, lo, _) in zip(bars[-n - 1:-1], bars[-n:]):
        trs.append(max(h - lo, abs(h - prev_c), abs(lo - prev_c)))
    return sum(trs) / n


def direction(move, unit, min_move_units):
    if move is None or unit <= 0:
        return FLAT
    if move >= min_move_units * unit:
        return UP
    if move <= -min_move_units * unit:
        return DOWN
    return FLAT


def ema(values, n):
    k = 2 / (n + 1)
    e = values[0]
    for v in values[1:]:
        e = v * k + e * (1 - k)
    return e


def trend(closes, unit, fast, slow, deadband_units):
    if len(closes) < slow or unit <= 0:
        return FLAT
    gap = ema(closes, fast) - ema(closes, slow)
    if gap > deadband_units * unit:
        return UP
    if gap < -deadband_units * unit:
        return DOWN
    return FLAT


def choppy(bars, n, min_straightness):
    """Zig-zag test on the last n bars: net move / total path. Returns (is_choppy, reason)."""
    if len(bars) < n:
        return True, "warming up (bars)"
    closes = [c for _, _, c in bars[-n:]]
    path = sum(abs(b - a) for a, b in zip(closes, closes[1:]))
    straight = abs(closes[-1] - closes[0]) / path if path > 0 else 0.0
    if straight < min_straightness:
        return True, f"choppy market (zig-zag {straight:.2f})"
    return False, ""


def pnl_units(side, open_price, bid, ask, unit):
    """Profit if closed now, in units of `unit` (the spread is already paid at the fill price)."""
    diff = (bid - open_price) if side == BUY else (open_price - ask)
    return diff / unit


def exit_reason(pnl_u, peak_u, age_s, cfg, broker_tp=False, broker_trail=False):
    """Bot-side exits, in ATR units. They are BACKUPS: when the broker already holds the
    target (broker_tp) or a stop locked in profit (broker_trail), the broker closes the trade
    on its server, faster and without the bot's order delay."""
    if not broker_tp and pnl_u >= cfg["target_atr"]:
        return "target"
    if not broker_trail and peak_u >= cfg["trail_start_atr"] and pnl_u <= peak_u - cfg["trail_dist_atr"]:
        return "trailing stop"
    if cfg["stall_exit_s"] > 0 and age_s >= cfg["stall_exit_s"] and peak_u < cfg["stall_min_atr"]:
        return "no follow-through"
    return None


def trail_level(peak_u, cfg):
    """Profit (ATR units) the trailing stop locks in, or None before trailing starts."""
    if peak_u < cfg["trail_start_atr"]:
        return None
    return peak_u - cfg["trail_dist_atr"]


def is_locked(side, open_price, sl):
    """True when the stop is at or beyond the entry: the trade can no longer lose."""
    if not sl:
        return False
    return sl >= open_price if side == BUY else sl <= open_price


def should_add(side_locked, adds_done, cfg):
    """Pyramid: add only while EVERY open trade on this side has its stop locked in profit,
    so the basket can never lose more than one trade's stop (the new add's)."""
    if adds_done >= cfg["max_adds"] or not side_locked:
        return False
    return all(side_locked)
