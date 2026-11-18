"""Sizing, limits and entry filters. Small pure helpers, easy to test."""
from __future__ import annotations

import csv
import math
from collections import deque
from datetime import datetime, timezone

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def lot_size(spec, wanted=None):
    """Symbol minimum by default. Rounded DOWN to the volume step, kept inside min/max."""
    lot = spec.vol_min if wanted is None else wanted
    steps = math.floor(round(lot / spec.vol_step, 6))
    lot = steps * spec.vol_step
    lot = min(max(lot, spec.vol_min), spec.vol_max)
    decimals = max(0, -int(math.floor(math.log10(spec.vol_step)))) if spec.vol_step < 1 else 0
    return round(lot, decimals)


def stop_distance(spec, dist, spread):
    """Distance (price) from the fill to a stop or target. Never closer than the broker allows."""
    broker_min = spread + (spec.stops_level + spec.freeze_level + 2) * spec.point
    return max(dist, broker_min)


def deviation_points(spec, spread, spreads):
    return max(1, int(math.ceil(spreads * spread / spec.point)))


def spread_block(cur_spread, med_spread, target_dist, cfg):
    """Reason text if the spread is too high to enter, else None. target_dist is in price."""
    if med_spread > 0 and cur_spread > cfg["spread_max_x_median"] * med_spread:
        return "spread too high"
    if target_dist < cfg["min_target_x_spread"] * cur_spread:
        return "spread too high vs volatility (target too small)"
    return None


def limit_block(symbol_open, total_open, total_lots, lot, cfg, max_total, max_lots):
    if symbol_open >= cfg["max_trades"]:
        return "max trades for this symbol"
    if total_open >= max_total:
        return "max trades overall"
    if total_lots + lot > max_lots + 1e-9:
        return "max total lots"
    return None


class FlipGuard:
    """Cooldown after each flip and a maximum number of flips per hour."""

    def __init__(self, cooldown_s, max_per_hour):
        self.cooldown_s = cooldown_s
        self.max_per_hour = max_per_hour
        self.times = deque()

    def _trim(self, now):
        while self.times and self.times[0] < now - 3600:
            self.times.popleft()

    def count(self, now):
        self._trim(now)
        return len(self.times)

    def allowed(self, now):
        self._trim(now)
        if self.times and now - self.times[-1] < self.cooldown_s:
            return False, f"flip cooldown ({self.cooldown_s - (now - self.times[-1]):.0f}s)"
        if len(self.times) >= self.max_per_hour:
            return False, "max flips this hour"
        return True, ""

    def record(self, now):
        self.times.append(now)


def _parse_days(text):
    a, _, b = text.partition("-")
    i, j = DAYS.index(a), DAYS.index(b or a)
    return set(range(i, j + 1)) if i <= j else set(range(i, 7)) | set(range(0, j + 1))


def in_session(sessions, server_epoch):
    """sessions = [("Mon-Fri", "07:00", "20:00"), ...] in SERVER time."""
    dt = datetime.fromtimestamp(server_epoch, tz=timezone.utc)   # server wall clock
    minute = dt.hour * 60 + dt.minute
    for days, start, end in sessions:
        if dt.weekday() not in _parse_days(days):
            continue
        h1, m1 = map(int, start.split(":"))
        h2, m2 = map(int, end.split(":"))
        if h1 * 60 + m1 <= minute < h2 * 60 + m2:
            return True
    return False


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
