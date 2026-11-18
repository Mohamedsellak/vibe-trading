"""Shared test helpers: a config copy, a Swarm on the fake MT5, and a price feeder with a fake clock."""
import math
import os
from types import SimpleNamespace

import config
from broker import Broker, SyncExecutor
from bot import Swarm
from fake_mt5 import FakeMT5
from report import Journal

SYM = "XAUUSDm"
ALWAYS = [("All", "UTC", "Mon-Sun", "00:00", "24:00")]
T0 = 1_780_000_000.0          # a fixed start time for the fake clock


def make_cfg(**kw):
    c = SimpleNamespace(**{k: getattr(config, k) for k in dir(config) if k.isupper()})
    c.SESSIONS = ALWAYS
    for k, v in kw.items():
        setattr(c, k, v)
    return c


def make_swarm(tmp_path, cfg=None, fake=None, balance=1000.0, executor=None):
    cfg = cfg or make_cfg()
    fake = fake or FakeMT5()
    if SYM not in fake.symbols:
        fake.add_symbol(SYM)
        fake.balance = balance
        fake.set_tick(SYM, 2000.0, 2000.24)
    b = Broker(fake, cfg.MAGIC, retries=1, retry_sleep=0)
    spec = b.spec(SYM)
    ex = executor(b, spec) if executor else SyncExecutor(b, spec)
    j = Journal(os.path.join(str(tmp_path), "t.sqlite"), os.path.join(str(tmp_path), "logs"), name=f"t{id(fake)}")
    sw = Swarm(b, spec, ex, j, cfg)
    sw.adopt_existing(T0)
    return sw, fake


class Feed:
    """Moves the fake price and runs the bot loop every `step` seconds of fake time."""

    def __init__(self, sw, fake, t=T0, mid=2000.12, spread=0.24, step=0.05):
        self.sw, self.fake, self.t, self.mid, self.spread, self.step = sw, fake, t, mid, spread, step

    def tick(self, mid=None):
        if mid is not None:
            self.mid = mid
        self.fake.set_tick(SYM, self.mid - self.spread / 2, self.mid + self.spread / 2, self.t)
        self.sw.loop_once(self.t)
        self.t += self.step

    def wiggle(self, seconds, amp=0.4, period=7.0):
        """Two-way market: price swings around, so spread and 5-second moves get measured."""
        base = self.mid
        for _ in range(int(seconds / self.step)):
            self.tick(base + amp * math.sin(2 * math.pi * (self.t - T0) / period))
        self.tick(base)

    def drift(self, seconds, per_s):
        for _ in range(int(seconds / self.step)):
            self.tick(self.mid + per_s * self.step)

    def until(self, cond, per_s=0.0, max_s=10.0):
        """Drift until cond() is true. Fails the test if it never happens."""
        end = self.t + max_s
        while not cond():
            assert self.t < end, "condition never met"
            self.tick(self.mid + per_s * self.step)

    def hold(self, seconds):
        for _ in range(int(seconds / self.step)):
            self.tick()


def warm(sw, fake, seconds=20, **kw):
    """Measure spread and moves for `seconds` with entries switched off, then switch them on."""
    f = Feed(sw, fake, **kw)
    sw.halted, sw.halt_reason = True, "test warm-up"
    f.wiggle(seconds)
    f.hold(5.5)                         # a calm end: the 5-second window holds no old swings
    sw.halted, sw.halt_reason = False, ""
    return f
