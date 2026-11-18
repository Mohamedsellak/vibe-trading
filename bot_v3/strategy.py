"""The trading logic of bot_v3, as small pure functions (easy to test).

In 5 lines:
1. Direction = the last 5 seconds of ticks: the mid price must move at least 1x the trade cost,
   and most price changes must go the same way. Checked every second. Otherwise FLAT.
2. Start: mode A opens 1 BUY + 1 SELL when flat; mode B waits for a direction.
3. When the direction is clear, every trade on the other side is closed at once
   ("cut wrong side" if it loses, "direction flip" if it wins).
4. The winning side grows by up to 2 trades per check, never while its newest trade is losing.
5. Each trade has its target and stop AT THE BROKER, so most trades close with no bot order.
"""
from __future__ import annotations

import statistics
from collections import deque
from dataclasses import dataclass

BUY, SELL = "BUY", "SELL"
UP, DOWN, FLAT = "UP", "DOWN", "FLAT"


def side_of(direction):
    return BUY if direction == UP else SELL if direction == DOWN else None


def other(side):
    return SELL if side == BUY else BUY


class MarketState:
    """Recent ticks, spread samples and 5-second moves, all measured live."""

    def __init__(self, dir_window_s, spread_window_s, vol_window_s):
        self.dir_window_s = dir_window_s
        self.spread_window_s = spread_window_s
        self.vol_window_s = vol_window_s
        self.ticks = deque()                 # (time, mid) of each new tick, last few windows
        self.spreads = deque()               # (time, spread) once per second
        self.moves = deque()                 # (time, |5-second move|) once per second
        self.bid = self.ask = self.spread = 0.0
        self._last_key = None
        self._sample_t = -1e18

    @property
    def mid(self):
        return (self.bid + self.ask) / 2

    def update(self, now, bid, ask, tick_key=None):
        self.bid, self.ask, self.spread = bid, ask, ask - bid
        key = tick_key if tick_key is not None else (bid, ask)
        if key != self._last_key:            # a new tick
            self._last_key = key
            self.ticks.append((now, (bid + ask) / 2))
        keep = max(3 * self.dir_window_s, 10)
        while self.ticks and self.ticks[0][0] < now - keep:
            self.ticks.popleft()
        if now - self._sample_t >= 1.0:
            self._sample_t = now
            self.spreads.append((now, self.spread))
            while self.spreads and self.spreads[0][0] < now - self.spread_window_s:
                self.spreads.popleft()
            mv = self.move(now)
            if mv is not None:
                self.moves.append((now, abs(mv)))
            while self.moves and self.moves[0][0] < now - self.vol_window_s:
                self.moves.popleft()

    def window(self, now):
        """Mid prices inside the direction window, starting with the last one before it."""
        start = now - self.dir_window_s
        pts = [m for t, m in self.ticks if t >= start]
        before = [m for t, m in self.ticks if t < start]
        if before:
            pts.insert(0, before[-1])
        return pts, bool(before)

    def move(self, now):
        pts, full = self.window(now)
        if not full or not pts:
            return None                      # not 5 seconds of history yet
        return pts[-1] - pts[0]

    def median_spread(self):
        return statistics.median(s for _, s in self.spreads) if self.spreads else self.spread

    def vol(self):
        """Median size of a 5-second move over the last minutes (price)."""
        return statistics.median(m for _, m in self.moves) if self.moves else 0.0


@dataclass
class Direction:
    state: str = FLAT
    move: float = 0.0       # mid price change over the window
    ups: int = 0
    downs: int = 0

    @property
    def imbalance(self):
        n = self.ups + self.downs
        return (self.ups - self.downs) / n if n else 0.0


def direction(mids, cost, move_x_cost, min_imbalance, min_ticks):
    """mids = mid prices over the last 5 s (oldest first). UP / DOWN only when the move is at least
    move_x_cost x the cost AND the up/down tick count agrees. Small or two-way moves = FLAT."""
    d = Direction()
    if len(mids) < 2:
        return d
    d.move = mids[-1] - mids[0]
    for a, b in zip(mids, mids[1:]):
        if b > a:
            d.ups += 1
        elif b < a:
            d.downs += 1
    if cost <= 0 or d.ups + d.downs < min_ticks:
        return d
    if d.move >= move_x_cost * cost and d.imbalance >= min_imbalance:
        d.state = UP
    elif d.move <= -move_x_cost * cost and d.imbalance <= -min_imbalance:
        d.state = DOWN
    return d


@dataclass
class Pos:
    """What decide() needs to know about one open trade."""
    ticket: int
    side: str
    pnl: float              # live result in price: bid - open (BUY) or open - ask (SELL)
    entry_mid: float        # mid price when the bot decided to open it
    opened: float           # time
    role: str = ""


@dataclass
class Action:
    kind: str               # "open" or "close"
    side: str
    role: str = ""          # open: probe / entry / extend
    reason: str = ""        # close: cut wrong side / direction flip
    ticket: int = 0


def decide(dir_state, trades, mid, mode, slots, can_open, probe_ready, cfg, blocked_sides=()):
    """One decision. Returns (actions, note).
    dir_state  : UP / DOWN / FLAT (from the last 5 s)
    trades     : list of Pos (open trades, not counting ones already being closed)
    slots      : how many new trades the money limits allow right now
    can_open   : False when a filter blocks new entries (closes still happen)
    probe_ready: mode A only - the probe cooldown has passed and the market is moving
    """
    actions, note = [], ""
    want = side_of(dir_state)
    if want:
        # 3. cut the wrong side / 6. close even winners on a flip
        for t in trades:
            if t.side != want:
                reason = "cut wrong side" if t.pnl < 0 else "direction flip"
                actions.append(Action("close", t.side, reason=reason, ticket=t.ticket))
        if not can_open:
            return actions, note
        if want in blocked_sides:
            return actions, f"no new {want}: a {want} was just stopped out"
        mine = sorted((t for t in trades if t.side == want), key=lambda t: t.opened)
        if mine:
            newest = mine[-1]
            against = (mid < newest.entry_mid) if want == BUY else (mid > newest.entry_mid)
            if against:   # no averaging down: only add while the side is going our way
                return actions, f"no add: newest {want} is under water"
        n = min(cfg.EXTEND_PER_CHECK, slots)
        if n <= 0:
            return actions, "swarm full (money limits)"
        role = "extend" if mine else "entry"
        actions += [Action("open", want, role=role) for _ in range(n)]
        note = f"riding {dir_state}: +{n} {want}"
        return actions, note
    # FLAT: keep what is open (its broker target and stop still work)
    if trades:
        return actions, "direction unclear: holding, no new trades"
    if mode == "A" and can_open:
        if not probe_ready:
            return actions, "mode A: waiting to probe"
        k = min(cfg.PROBE_PER_SIDE, slots // 2)
        if k <= 0:
            return actions, "probe needs 2 free slots"
        for _ in range(k):
            actions += [Action("open", BUY, role="probe"), Action("open", SELL, role="probe")]
        return actions, f"probing both sides ({k} BUY + {k} SELL)"
    return actions, "waiting for a clear 5-second direction"
