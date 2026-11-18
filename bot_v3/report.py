"""Journal (SQLite + text log + on-screen event feed) and the report.

    python report.py         -> every closed trade of this version, all sessions
    python report.py --all   -> every closed trade ever saved
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import statistics
import time
from collections import deque
from datetime import datetime

TRADE_COLS = """ticket INTEGER PRIMARY KEY, symbol TEXT, side TEXT, mode TEXT, role TEXT, session INTEGER,
    open_time REAL, open_price REAL, entry_mid REAL, req_open_price REAL, open_slip_pts REAL,
    open_latency_ms REAL, open_queue_ms REAL, spread_open REAL, spread_cost REAL, cost_pts REAL,
    cost_money REAL, target_pts REAL, stop_pts REAL, risk_money REAL, breakeven_wr REAL, sl REAL, tp REAL,
    volume REAL, close_time REAL, close_price REAL, close_reason TEXT, close_slip_pts REAL,
    close_latency_ms REAL, pnl REAL, pnl_points REAL, version TEXT"""
# spread_cost = money paid to the spread at open. pnl = money from MT5 deals (after spread).
# close_slip_pts: bot close = slippage of the close order; broker target/stop = fill vs the level.

SESSION_COLS = """id INTEGER PRIMARY KEY, version TEXT, start REAL, end REAL, executor TEXT,
    start_balance REAL, start_equity REAL, max_dd_money REAL, max_dd_pct REAL, blocks TEXT,
    orders INTEGER, order_ms REAL"""


class Journal:
    def __init__(self, db_path, log_dir, name="bot_v3"):
        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=NORMAL")
        for table, cols in (("trades", TRADE_COLS), ("sessions", SESSION_COLS)):
            self.db.execute(f"CREATE TABLE IF NOT EXISTS {table} ({cols})")
            have = {r[1] for r in self.db.execute(f"PRAGMA table_info({table})")}
            for col in cols.split(","):
                cname, typ = col.split()[:2]
                if cname not in have:
                    self.db.execute(f"ALTER TABLE {table} ADD COLUMN {cname} {typ}")
        self.db.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, time REAL,"
                        " kind TEXT, msg TEXT)")
        self.db.commit()
        self.session_start = time.time()
        self.session_id = None
        self._dirty, self._commit_t = False, 0.0
        self.feed = deque(maxlen=200)
        self.log = logging.getLogger(name)
        self.log.setLevel(logging.INFO)
        path = os.path.abspath(os.path.join(log_dir, "bot.log.txt"))
        if not any(getattr(h, "baseFilename", None) == path for h in self.log.handlers):
            h = logging.FileHandler(path, encoding="utf-8")
            h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            self.log.addHandler(h)

    # ---------- sessions ----------
    def start_session(self, version, executor, balance, equity):
        cur = self.db.execute("INSERT INTO sessions (version, start, executor, start_balance, start_equity)"
                              " VALUES (?,?,?,?,?)", (version, self.session_start, executor, balance, equity))
        self.session_id = cur.lastrowid
        self.db.commit()

    def update_session(self, **row):
        if self.session_id is None:
            return
        if "blocks" in row:
            row["blocks"] = json.dumps(row["blocks"])
        sets = ",".join(f"{k}=?" for k in row)
        self.db.execute(f"UPDATE sessions SET {sets} WHERE id=?", (*row.values(), self.session_id))
        self._dirty = True

    def sessions(self, version=None):
        if version is None:
            return self.db.execute("SELECT * FROM sessions ORDER BY start").fetchall()
        return self.db.execute("SELECT * FROM sessions WHERE version=? ORDER BY start", (version,)).fetchall()

    # ---------- events ----------
    def event(self, kind, msg, show=True):
        level = logging.ERROR if kind == "error" else logging.WARNING if kind == "warn" else logging.INFO
        self.log.log(level, f"{kind}: {msg}")
        self.db.execute("INSERT INTO events (time, kind, msg) VALUES (?,?,?)", (time.time(), kind, msg))
        self._dirty = True
        if show:
            self.feed.append((datetime.now().strftime("%H:%M:%S"), kind, msg))

    def flush(self, force=False):
        now = time.time()
        if self._dirty and (force or now - self._commit_t >= 1.0):
            self.db.commit()
            self._dirty, self._commit_t = False, now

    # ---------- trades ----------
    def open_trade(self, **row):
        keys = ",".join(row)
        self.db.execute(f"INSERT OR REPLACE INTO trades ({keys}) VALUES ({','.join('?' * len(row))})",
                        tuple(row.values()))
        self._dirty = True

    def close_trade(self, ticket, **row):
        sets = ",".join(f"{k}=?" for k in row)
        self.db.execute(f"UPDATE trades SET {sets} WHERE ticket=?", (*row.values(), ticket))
        self._dirty = True

    def row(self, ticket):
        return self.db.execute("SELECT * FROM trades WHERE ticket=?", (ticket,)).fetchone()

    def open_rows(self, symbol):
        return self.db.execute("SELECT * FROM trades WHERE symbol=? AND close_time IS NULL", (symbol,)).fetchall()

    def realized_since(self, since):
        r = self.db.execute("SELECT SUM(pnl) FROM trades WHERE close_time>=?", (since,)).fetchone()[0]
        return r or 0.0

    def closed_since(self, since):
        return self.db.execute("SELECT * FROM trades WHERE close_time>=? ORDER BY close_time", (since,)).fetchall()

    def last_closed(self, n, version):
        rows = self.db.execute("SELECT pnl FROM trades WHERE close_time IS NOT NULL AND version=? "
                               "ORDER BY close_time DESC LIMIT ?", (version, n)).fetchall()
        return [r["pnl"] or 0.0 for r in reversed(rows)]

    def version_rows(self, version=None):
        if version is None:
            return self.db.execute("SELECT * FROM trades WHERE close_time IS NOT NULL ORDER BY close_time").fetchall()
        return self.db.execute("SELECT * FROM trades WHERE close_time IS NOT NULL AND version=? "
                               "ORDER BY close_time", (version,)).fetchall()


# ---------------- report ----------------
def _avg(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else 0.0


def _med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else 0.0


def stats(rows):
    pnl = [r["pnl"] or 0.0 for r in rows]
    n = len(rows)
    spread = sum(r["spread_cost"] or 0.0 for r in rows)
    wins = [p for p in pnl if p > 0]
    losses = [p for p in pnl if p <= 0]
    reasons = {}
    for r in rows:
        reasons.setdefault(r["close_reason"] or "?", []).append(r["pnl"] or 0.0)
    eq, peak, dd = 0.0, 0.0, 0.0                 # drawdown of the closed-trade curve
    for p in pnl:
        eq += p
        peak = max(peak, eq)
        dd = max(dd, peak - eq)
    return dict(
        n=n, total=sum(pnl), wins=len(wins), win_rate=len(wins) / n if n else 0.0,
        avg_win=_avg(wins), avg_loss=_avg(losses),
        net=_avg(pnl), spread=spread / n if n else 0.0, gross=(sum(pnl) + spread) / n if n else 0.0,
        hold=_avg([r["close_time"] - r["open_time"] for r in rows if r["close_time"] and r["open_time"]]),
        reasons=reasons, closed_dd=dd,
        lat_open=_avg([r["open_latency_ms"] for r in rows]), lat_open_med=_med([r["open_latency_ms"] for r in rows]),
        lat_close=_avg([r["close_latency_ms"] for r in rows]),
        queue=_avg([r["open_queue_ms"] for r in rows]),
        slip_open=_avg([r["open_slip_pts"] for r in rows]),
        slip_close=_avg([r["close_slip_pts"] for r in rows if r["close_latency_ms"] is not None]),
        slip_fill=_avg([r["close_slip_pts"] for r in rows if r["close_latency_ms"] is None]),
        bot_closes=sum(1 for r in rows if r["close_latency_ms"] is not None),
        cost_pts=_avg([r["cost_pts"] for r in rows]), cost_money=_avg([r["cost_money"] for r in rows]),
        target_pts=_avg([r["target_pts"] for r in rows]), stop_pts=_avg([r["stop_pts"] for r in rows]),
        be_wr=_avg([r["breakeven_wr"] for r in rows]),
    )


def _money(x, fmt="+.2f"):
    c = "green" if x > 0 else "red" if x < 0 else "white"
    return f"[{c}]{x:{fmt}}[/]"


def build_report(rows, hours, start_balance, currency="", blocks=None, dd_money=None, dd_pct=None,
                 title="SESSION REPORT", orders=None):
    """Rich-markup lines. rows = closed trades. hours = time the bot ran. blocks = {reason: seconds}.
    dd_money / dd_pct = max equity drawdown seen live (None if unknown). orders = orders sent."""
    st = stats(rows)
    cur = currency or "account money"
    lines = [f"[bold]{title}[/]  (money in {cur})"]
    if not rows:
        lines.append("[yellow]No closed trades.[/]")
    else:
        per_min = st["n"] / (hours * 60) if hours > 0 else 0.0
        net_h = st["total"] / hours if hours > 0 else 0.0
        pct_h = 100 * net_h / start_balance if start_balance else 0.0
        lines += [
            f"trades {st['n']}   per minute {per_min:.2f}   per hour {per_min * 60:.0f}   "
            f"(bot ran {hours * 60:.0f} min)",
            f"win rate {st['win_rate']:.0%}   (needed to break even: {st['be_wr']:.0%})   "
            f"avg win {_money(st['avg_win'])}   avg loss {_money(st['avg_loss'])}   avg hold {st['hold']:.1f}s",
            f"per trade: before spread {_money(st['gross'], '+.3f')}   spread cost {st['spread']:.3f}   "
            f"[bold]net after spread {_money(st['net'], '+.3f')}[/]",
            f"total {_money(st['total'])}   net per hour {_money(net_h)} = {_money(pct_h, '+.2f')}% "
            f"of the starting balance {start_balance:.2f}",
            f"minimum profitable target (one round-trip cost): {st['cost_pts']:.0f} points = "
            f"{st['cost_money']:.3f} per trade   target {st['target_pts']:.0f} pts, stop {st['stop_pts']:.0f} pts",
            "closed by: " + ", ".join(f"{k} {len(v)} (avg {v and sum(v) / len(v):+.3f})"
                                      for k, v in sorted(st["reasons"].items(), key=lambda kv: -len(kv[1]))),
            f"orders: open {st['lat_open']:.0f} ms avg ({st['lat_open_med']:.0f} median) + "
            f"{st['queue']:.0f} ms in queue   bot closes {st['bot_closes']} at {st['lat_close']:.0f} ms avg"
            + (f"   orders sent {orders} = {orders / st['n']:.2f} per trade" if orders else ""),
            f"slippage: open {st['slip_open']:+.1f} pts   bot close {st['slip_close']:+.1f} pts   "
            f"broker target/stop fills {st['slip_fill']:+.1f} pts from the level (+ = worse for us)",
        ]
        if dd_money is not None:
            lines.append(f"max drawdown (equity, live): {dd_money:.2f} = {dd_pct:.1f}%   "
                         f"closed-trade drawdown {st['closed_dd']:.2f}")
        else:
            pct = 100 * st["closed_dd"] / start_balance if start_balance else 0.0
            lines.append(f"max drawdown (closed trades): {st['closed_dd']:.2f} = {pct:.1f}% of the starting balance")
        # per mode and per role
        for key, label in (("mode", "mode"), ("role", "kind")):
            groups = {}
            for r in rows:
                groups.setdefault(r[key] or "?", []).append(r)
            lines.append(f"by {label}: " + "   ".join(
                f"{g}: {s['n']} trades, win {s['win_rate']:.0%}, net/trade {_money(s['net'], '+.3f')}, "
                f"before spread {_money(s['gross'], '+.3f')}, total {_money(s['total'])}"
                for g, s in ((g, stats(rs)) for g, rs in sorted(groups.items()))))
    if blocks:
        total = sum(blocks.values())
        if total > 0:
            top = sorted(blocks.items(), key=lambda kv: -kv[1])[:10]
            lines.append("time spent: " + ", ".join(f"{k} {v / total:.0%}" for k, v in top))
    lines += honest_notes(st, orders)
    return lines


def honest_notes(st, orders=None):
    if not st["n"]:
        return []
    out = []
    if st["n"] < 300:
        out.append(f"[yellow]Only {st['n']} trades. With results this noisy, a few hundred trades are "
                   f"needed before the averages mean much.[/]")
    if st["net"] < 0:
        out.append(f"[bold red]HONEST NOTE: the net result per trade after spread is NEGATIVE "
                   f"({st['net']:+.3f}). Each trade loses on average.[/]")
        if st["gross"] > 0:
            out.append("[bold yellow]Before spread the trades made money, so the direction call has a small "
                       "edge, but it is smaller than the cost. More speed would NOT help: it only multiplies "
                       "the cost. A bigger target, fewer trades or a cheaper account (Raw Spread) could.[/]")
        else:
            out.append("[bold red]Even before spread the trades lost. There is no edge to speed up: "
                       "more trades per minute would only lose faster.[/]")
    else:
        out.append("[green]Net result per trade after spread is positive in this sample. "
                   "More speed would help only if it keeps the same net per trade - check that with more trades.[/]")
    return out


def main(argv=None):
    import sys
    import config
    from rich.console import Console
    argv = sys.argv[1:] if argv is None else argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.exists(config.DB_FILE):
        print(f"No trade database yet ({config.DB_FILE}). Run the bot first.")
        return 1
    j = Journal(config.DB_FILE, config.LOG_DIR)
    version = None if "--all" in argv else config.VERSION
    rows = j.version_rows(version)
    sess = j.sessions(version)
    hours = sum(((s["end"] or s["start"]) - s["start"]) for s in sess) / 3600
    start_balance = sess[0]["start_balance"] if sess else 0.0
    blocks = {}
    for s in sess:
        for k, v in json.loads(s["blocks"] or "{}").items():
            blocks[k] = blocks.get(k, 0.0) + v
    dds = [(s["max_dd_money"], s["max_dd_pct"]) for s in sess if s["max_dd_money"] is not None]
    dd_money, dd_pct = max(dds) if dds else (None, None)
    orders = sum(s["orders"] or 0 for s in sess) or None
    title = "REPORT  all versions" if version is None else f"REPORT  version {version}, {len(sess)} sessions"
    con = Console()
    for line in build_report(rows, hours, start_balance, "", blocks, dd_money, dd_pct, title, orders):
        con.print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
