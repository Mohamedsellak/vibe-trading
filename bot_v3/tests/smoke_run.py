"""Smoke run on the fake MT5 (no real broker needed).

    python tests/smoke_run.py sim    -> 2 hours of a RANDOM price on a fake clock (takes seconds), then the report
    python tests/smoke_run.py live   -> the real loop + dashboard for 40 s, worker thread, 300 ms order delay,
                                        then the STOP file (kill switch)
A random price has no direction to find, so the honest result is: about minus one cost per trade.
"""
import os
import random
import sys
import tempfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from rich.console import Console  # noqa: E402

import bot  # noqa: E402
from broker import ThreadExecutor  # noqa: E402
from helpers import SYM, T0, Feed, make_cfg, make_swarm, warm  # noqa: E402
from report import build_report  # noqa: E402


def sim(hours=2.0, seed=7):
    rnd = random.Random(seed)
    tmp = tempfile.mkdtemp()
    sw, fake = make_swarm(tmp, make_cfg(START_MODE="AB", ALTERNATE_EVERY_MIN=30), balance=100.0)
    f = warm(sw, fake)
    f.step = 0.1
    end = f.t + hours * 3600
    while f.t < end:
        f.tick(f.mid + rnd.gauss(0, 0.07))          # random walk: typical 5-second move ~0.5
    sw.close_everything("end of simulation", f.t)
    rows = sw.j.closed_since(0)
    con = Console(width=160)
    for line in build_report(rows, hours, 100.0, "USD", sw.block_time, sw.dd_money, sw.dd_pct,
                             f"SIMULATION: {hours:.0f} h of random prices, $100 account", sw.orders_sent):
        con.print(line)


def live(seconds=40):
    tmp = tempfile.mkdtemp()
    os.chdir(tmp)
    cfg = make_cfg(START_MODE="A")
    sw, fake = make_swarm(tmp, cfg, balance=100.0)
    f = warm(sw, fake)
    fake.latency_s = 0.3
    sw.ex = ThreadExecutor(sw.b, sw.spec, 1.5)
    stop = threading.Event()

    def feed():                                     # prices move in real time, like the terminal
        rnd = random.Random(3)
        mid, t_end = f.mid, time.time() + seconds - 3
        while not stop.is_set():
            mid += rnd.gauss(0.01, 0.07)
            fake.set_tick(SYM, mid - 0.12, mid + 0.12, time.time())
            time.sleep(0.1)
            if time.time() > t_end and not os.path.exists(cfg.STOP_FILE):
                open(cfg.STOP_FILE, "w").close()     # the kill switch
    th = threading.Thread(target=feed, daemon=True)
    # the live loop uses real time: re-measure on the real clock first
    sw.ms = type(sw.ms)(cfg.DIR_WINDOW_S, cfg.SPREAD_WINDOW_S, cfg.VOL_WINDOW_S)
    sw.next_check, sw._last_t = 0.0, None
    th.start()
    how = bot.run(sw, Console(width=160), max_seconds=seconds + 10)
    stop.set()
    print(f"\nstopped by: {how}   bot trades still open: {len(fake.positions_get())}   "
          f"orders sent: {len(fake.sent)}")
    return how == "kill switch" and not fake.positions_get()


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "sim"
    if what == "sim":
        sim()
    else:
        sys.exit(0 if live() else 1)
