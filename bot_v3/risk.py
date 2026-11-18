"""Cost, sizing, limits and filters. Small pure helpers, easy to test.

Every distance is built from the MEASURED cost of one round trip:
    cost = median spread + 2 x expected slippage           (price)
    target move = TARGET_X_COST x cost                      (mid price must move this much our way)
    stop move   = STOP_X_TARGET x target move               (mid price moved this much against us)
Every money limit is a percent of live equity.
"""
from __future__ import annotations

import csv
import math
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def lot_size(spec):
    """The symbol's minimum lot, on its volume step. Never more."""
    steps = math.ceil(round(spec.vol_min / spec.vol_step, 6))
    lot = min(steps * spec.vol_step, spec.vol_max)
    decimals = max(0, -int(math.floor(math.log10(spec.vol_step)))) if spec.vol_step < 1 else 0
    return round(lot, decimals)


class SlipStats:
    """Rolling slippage per order, in price. Positive = worse for us."""

    def __init__(self, n):
        self.xs = deque(maxlen=n)

    def add(self, adverse_price):
        self.xs.append(adverse_price)

    def expected(self, spread, prior_x_spread, min_samples=5):
        """Expected ADVERSE slippage. Good fills never lower it below zero (no free lunch assumed)."""
        if len(self.xs) < min_samples:
            return prior_x_spread * spread
        return max(0.0, sum(self.xs) / len(self.xs))

    def average(self):
        return sum(self.xs) / len(self.xs) if self.xs else 0.0


@dataclass
class Plan:
    """Distances and money for the next trade."""
    spread: float           # spread used (price)
    slip: float             # expected slippage per order (price)
    cost: float             # round-trip cost (price) = minimum profitable mid move
    target_move: float      # mid move our way that hits the target
    stop_move: float        # mid move against us that hits the stop
    tp_dist: float          # take profit distance from the fill price (what the broker gets)
    sl_dist: float          # stop loss distance from the fill price
    risk_money: float       # money lost if the stop fills (with expected stop slippage)
    win_money: float        # money won at the target, after cost
    cost_money: float       # money of one round-trip cost = minimum profitable target
    breakeven_winrate: float
    coinflip_winrate: float  # win rate if price moves at random (no edge)


def make_plan(spec, lot, spread_med, spread_now, slip, stop_slip, cfg):
    """spread_med: normal spread. spread_now: this tick. slip / stop_slip: expected slippage (price)."""
    cost = spread_med + 2 * slip
    target_move = cfg.TARGET_X_COST * cost
    stop_move = cfg.STOP_X_TARGET * target_move
    broker_min = (spec.stops_level + spec.freeze_level + 1) * spec.point
    # A BUY fills at the ask and closes at the bid: it starts one spread down.
    # Target: the bid must reach fill + (target move - spread). Stop: fill - (stop move + spread).
    tp_dist = max(target_move - spread_now, broker_min, spec.point)
    sl_dist = max(stop_move + spread_now, broker_min + spread_now)
    mpp = spec.money_per_price(lot)
    win = target_move - cost
    loss = stop_move + cost - slip + stop_slip       # open slippage + spread + stop's own slippage
    return Plan(spread=spread_med, slip=slip, cost=cost, target_move=target_move, stop_move=stop_move,
                tp_dist=tp_dist, sl_dist=sl_dist,
                risk_money=(sl_dist + slip + stop_slip) * mpp,
                win_money=win * mpp, cost_money=cost * mpp,
                breakeven_winrate=loss / (win + loss) if win + loss > 0 else 1.0,
                coinflip_winrate=stop_move / (target_move + stop_move) if target_move + stop_move else 0.0)


def cost_block(plan, spread_now, slip, cfg):
    """'Never enter unless the target is clearly bigger than spread plus expected slippage.'"""
    cost_now = spread_now + 2 * slip
    if plan.target_move < cfg.MIN_TARGET_X_COST_NOW * cost_now:
        return "cost check: target not 1.5x the cost right now"
    return None


def max_trades(equity, plan, lot, cfg):
    """How many trades the money rules allow at once (shown on screen)."""
    if equity <= 0 or plan.risk_money <= 0:
        return 0
    by_risk = int(cfg.MAX_TOTAL_STOP_RISK_PCT / 100 * equity // plan.risk_money)
    by_lots = int(cfg.MAX_TOTAL_LOTS_X_MIN)       # every trade is the minimum lot
    return max(0, min(by_risk, cfg.MAX_OPEN_TRADES, by_lots))


def free_slots(equity, open_risk, n_open, plan, lot, cfg):
    """New trades allowed right now: the sum of all stops stays under MAX_TOTAL_STOP_RISK_PCT of equity."""
    if plan.risk_money <= 0:
        return 0
    room = cfg.MAX_TOTAL_STOP_RISK_PCT / 100 * equity - open_risk
    by_risk = int(room // plan.risk_money) if room > 0 else 0
    return max(0, min(by_risk, max_trades(equity, plan, lot, cfg) - n_open))


def stop_too_big(equity, plan, cfg):
    """One trade's stop alone is too much for this account."""
    if equity <= 0:
        return "no equity"
    pct = 100 * plan.risk_money / equity
    if pct > cfg.MAX_ONE_STOP_PCT:
        return f"stop too big for this account ({plan.risk_money:.2f} = {pct:.1f}% of equity)"
    if plan.risk_money > cfg.MAX_TOTAL_STOP_RISK_PCT / 100 * equity:
        return "stop too big for this account (one stop is over the total risk cap)"
    return None


def margin_ok(need_per_order, n_orders, free_margin, cfg):
    """Free-margin check before every order. need_per_order None = MT5 could not tell: allow,
    the broker will still refuse with 'no money' and the bot then pauses."""
    if need_per_order is None:
        return True
    return need_per_order * n_orders <= cfg.MARGIN_USE_MAX_PCT / 100 * free_margin


def basket_hit(floating, equity, cfg):
    """Floating loss of all bot trades >= BASKET_STOP_PCT of the equity they started from."""
    base = equity - floating
    return floating < 0 and -floating >= cfg.BASKET_STOP_PCT / 100 * base


def deviation_points(spec, spread, x_spread):
    return max(1, int(math.ceil(x_spread * spread / spec.point)))


class RateCap:
    """At most max_per_min orders in any 60 seconds."""

    def __init__(self, max_per_min):
        self.max = max_per_min
        self.times = deque()

    def _trim(self, now):
        while self.times and self.times[0] <= now - 60:
            self.times.popleft()

    def count(self, now):
        self._trim(now)
        return len(self.times)

    def left(self, now):
        return max(0, self.max - self.count(now))

    def record(self, now):
        self.times.append(now)


def realistic_trades_per_min(latency_ms, orders_per_trade, max_orders_per_min):
    """One order at a time: orders/min = 60000 / latency. A trade needs 1 order (closed by its broker
    target or stop) or 2 (closed by the bot). Also capped by MAX_ORDERS_PER_MIN."""
    if latency_ms <= 0 or orders_per_trade <= 0:
        return 0.0
    physical = 60000.0 / latency_ms
    return min(physical, max_orders_per_min) / orders_per_trade


class RollingNet:
    """Net result per trade over the last n closed trades."""

    def __init__(self, n):
        self.xs = deque(maxlen=n)

    def add(self, pnl):
        self.xs.append(pnl)

    def reset(self):
        self.xs.clear()

    @property
    def count(self):
        return len(self.xs)

    @property
    def full(self):
        return len(self.xs) == self.xs.maxlen

    def mean(self):
        return sum(self.xs) / len(self.xs) if self.xs else 0.0


# ---------------- sessions and news ----------------
def _parse_days(text):
    a, _, b = text.partition("-")
    i, j = DAYS.index(a), DAYS.index(b or a)
    return set(range(i, j + 1)) if i <= j else set(range(i, 7)) | set(range(0, j + 1))


def active_session(sessions, utc_epoch):
    """Name of the open session, or None. Each session is in its own city's clock:
    (name, "Europe/London", "Mon-Fri", "08:00", "16:30"). Summer time comes from the tz database."""
    from zoneinfo import ZoneInfo
    for name, tz, days, start, end in sessions:
        local = datetime.fromtimestamp(utc_epoch, tz=ZoneInfo(tz))
        if local.weekday() not in _parse_days(days):
            continue
        minute = local.hour * 60 + local.minute
        h1, m1 = map(int, start.split(":"))
        h2, m2 = map(int, end.split(":"))
        if h1 * 60 + m1 <= minute < h2 * 60 + m2:
            return name
    return None


class NewsCalendar:
    """Blackout windows from a CSV. Times in UTC. Lines starting with # are ignored."""

    def __init__(self, events=None):
        self.events = events or []    # (start_utc, end_utc, currency, title)

    @classmethod
    def load(cls, path):
        events = []
        try:
            with open(path, newline="", encoding="utf-8") as f:
                rows = [ln for ln in f if ln.strip() and not ln.lstrip().startswith("#")]
        except FileNotFoundError:
            return cls([])
        for row in csv.DictReader(rows):
            t = datetime.strptime(row["utc_time"].strip(), "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            ts = t.timestamp()
            events.append((ts - 60 * float(row["minutes_before"]), ts + 60 * float(row["minutes_after"]),
                           row["currency"].strip().upper(), row["event"].strip()))
        return cls(events)

    def active(self, utc_now, currencies):
        cur = {c.upper() for c in currencies}
        for start, end, ccy, title in self.events:
            if start <= utc_now <= end and (ccy == "ALL" or ccy in cur):
                return title
        return None
