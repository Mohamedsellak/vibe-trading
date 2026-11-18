"""Journal (SQLite + text logs + on-screen event feed) and the session report."""
from __future__ import annotations

import logging
import os
import sqlite3
import time
from collections import deque
from datetime import datetime

TRADE_COLS = """ticket INTEGER PRIMARY KEY, symbol TEXT, side TEXT, kind TEXT, basket INTEGER,
    volume REAL, open_time REAL, open_price REAL, req_open_price REAL, open_slip_pts REAL,
    open_latency_ms REAL, spread_open REAL, spread_cost REAL, unit REAL, sl REAL,
    close_time REAL, close_price REAL, close_reason TEXT, close_slip_pts REAL,
    close_latency_ms REAL, pnl REAL, pnl_points REAL, peak_units REAL, tp REAL"""
# unit = ATR (price) frozen at open. peak_units = best profit seen, in ATR.

STYLE = {"open": "cyan", "add": "cyan", "flip": "magenta", "close": "white",
         "signal": "dim", "warn": "yellow", "error": "red", "info": "white"}


class Journal:
    def __init__(self, db_path, log_dir, symbols=()):
        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")       # fast writes, no full disk sync per row
        self.db.execute("PRAGMA synchronous=NORMAL")
        self.db.execute(f"CREATE TABLE IF NOT EXISTS trades ({TRADE_COLS})")
        have = {r[1] for r in self.db.execute("PRAGMA table_info(trades)")}
        for col in TRADE_COLS.split(","):                   # add columns new in this version
            name, typ = col.split()[:2]
            if name not in have:
                self.db.execute(f"ALTER TABLE trades ADD COLUMN {name} {typ}")
        self.db.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, time REAL,"
                        " symbol TEXT, kind TEXT, msg TEXT)")
        self.db.commit()
        self.session_start = time.time()
        self._dirty, self._commit_t = False, 0.0
        self.feed = deque(maxlen=200)
        self.log = logging.getLogger("bot_v2")
        self.log.setLevel(logging.INFO)
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        self._add_file(self.log, os.path.join(log_dir, "bot.log"), fmt)
        self.sym_logs = {}
        for s in symbols:
            self.add_symbol(s, log_dir)
        self._log_dir = log_dir
        self._fmt = fmt

    @staticmethod
    def _add_file(logger, path, fmt):
        if not any(getattr(h, "baseFilename", None) == os.path.abspath(path) for h in logger.handlers):
            h = logging.FileHandler(path, encoding="utf-8")
            h.setFormatter(fmt)
            logger.addHandler(h)

    def add_symbol(self, symbol, log_dir=None):
        lg = logging.getLogger(f"bot_v2.{symbol}")   # also goes to bot.log (propagates)
        self._add_file(lg, os.path.join(log_dir or self._log_dir, f"{symbol}.log"),
                       logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        self.sym_logs[symbol] = lg

    # ---------- events ----------
    def event(self, symbol, kind, msg, show=True):
        now = time.time()
        lg = self.sym_logs.get(symbol, self.log)
        lg.log(logging.ERROR if kind == "error" else logging.WARNING if kind == "warn" else logging.INFO,
               f"[{symbol or '-'}] {kind}: {msg}")
        self.db.execute("INSERT INTO events (time, symbol, kind, msg) VALUES (?,?,?,?)",
                        (now, symbol, kind, msg))
        self._dirty = True            # events are saved by flush() at most once per second
        if show:
            self.feed.append((datetime.now().strftime("%H:%M:%S"), symbol or "-", kind, msg))

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
        self.flush(force=True)

    def close_trade(self, ticket, **row):
        sets = ",".join(f"{k}=?" for k in row)
        self.db.execute(f"UPDATE trades SET {sets} WHERE ticket=?", (*row.values(), ticket))
        self.flush(force=True)

    def open_rows(self, symbol):
        return self.db.execute("SELECT * FROM trades WHERE symbol=? AND close_time IS NULL",
                               (symbol,)).fetchall()

    def row(self, ticket):
        return self.db.execute("SELECT * FROM trades WHERE ticket=?", (ticket,)).fetchone()

    def next_basket(self):
        r = self.db.execute("SELECT MAX(basket) FROM trades").fetchone()[0]
        return (r or 0) + 1

    def realized_since(self, symbol, since):
        r = self.db.execute("SELECT SUM(pnl) FROM trades WHERE symbol=? AND close_time>=?",
                            (symbol, since)).fetchone()[0]
        return r or 0.0

    def closed_since(self, since):
        return self.db.execute("SELECT * FROM trades WHERE close_time>=? ORDER BY close_time",
                               (since,)).fetchall()


# ---------- session report ----------
def _avg(xs):
    return sum(xs) / len(xs) if xs else 0.0


def stats(rows):
    pnl = [r["pnl"] or 0.0 for r in rows]
    pts = [r["pnl_points"] or 0.0 for r in rows]
    wins = [(m, p) for m, p in zip(pnl, pts) if m > 0]
    losses = [(m, p) for m, p in zip(pnl, pts) if m < 0]
    flips = [r for r in rows if r["kind"] == "flip"]
    adds = [r["pnl"] or 0.0 for r in rows if r["kind"] == "add"]
    hold = [(r["close_time"] - r["open_time"], r["pnl"] or 0.0) for r in rows
            if r["close_time"] and r["open_time"]]
    baskets = {}
    for r in rows:
        baskets[r["basket"]] = baskets.get(r["basket"], 0.0) + (r["pnl"] or 0.0)
    reasons = {}
    for r in rows:
        reasons.setdefault(r["close_reason"], []).append(r["pnl"] or 0.0)
    avg_win = _avg([m for m, _ in wins])
    avg_loss = _avg([m for m, _ in losses])
    spread_cost = sum(r["spread_cost"] or 0.0 for r in rows)
    return dict(
        n=len(rows), wins=len(wins), losses=len(losses),
        win_rate=len(wins) / len(rows) if rows else 0.0,
        avg_win=avg_win, avg_loss=avg_loss,
        avg_win_pts=_avg([p for _, p in wins]), avg_loss_pts=_avg([p for _, p in losses]),
        ratio=(avg_win / abs(avg_loss)) if avg_loss else float("inf") if avg_win else 0.0,
        expectancy=_avg(pnl), expectancy_pts=_avg(pts), total=sum(pnl),
        flips=len(flips), flips_won=sum(1 for r in flips if (r["pnl"] or 0) > 0),
        spread_cost=spread_cost, gross=sum(pnl) + spread_cost,
        adds=len(adds), adds_total=sum(adds), adds_avg=_avg(adds),
        hold_win=_avg([h for h, p in hold if p > 0]), hold_loss=_avg([h for h, p in hold if p <= 0]),
        worst_basket=min(baskets.values()) if baskets else 0.0,
        reasons=reasons,
    )


def _block_lines(blocks):
    """blocks = {reason: seconds}. Share of time each reason kept the bot from entering."""
    total = sum(blocks.values())
    if total <= 0:
        return [], {}
    share = {k: v / total for k, v in blocks.items()}
    top = sorted(share.items(), key=lambda kv: -kv[1])[:6]
    return ["  time spent: " + ", ".join(f"{k} {v:.0%}" for k, v in top)], share


def build_report(journal, worst_floating, currency="", blocks=None):
    """Rich-markup text lines. worst_floating = {symbol: most negative floating PnL seen}.
    blocks = {symbol: {state: seconds}} from the traders (why the bot was not entering)."""
    blocks = blocks or {}
    rows = journal.closed_since(journal.session_start)
    by_sym = {}
    for r in rows:
        by_sym.setdefault(r["symbol"], []).append(r)
    lines = [f"[bold]SESSION REPORT[/]  since {datetime.fromtimestamp(journal.session_start):%Y-%m-%d %H:%M:%S}"
             f"  (money in {currency or 'account currency'}, after spread)"]
    if not rows:
        lines.append("[yellow]No closed trades this session.[/]")
    groups = [(s, by_sym.get(s, [])) for s in sorted(set(by_sym) | set(worst_floating))]
    if len(by_sym) > 1:
        groups.append(("ALL", rows))
    for sym, rs in groups:
        st = stats(rs)
        dd = (min(worst_floating.values()) if worst_floating else 0.0) if sym == "ALL" \
            else worst_floating.get(sym, 0.0)
        blines, share = _block_lines(blocks.get(sym, {}))
        if not st["n"]:
            lines.append(f"\n[bold underline]{sym}[/]  no closed trades   max floating drawdown {dd:+.2f}")
            lines += blines
        else:
            c = "green" if st["total"] > 0 else "red" if st["total"] < 0 else "white"
            lines += [
                f"\n[bold underline]{sym}[/]",
                f"  trades {st['n']}   wins {st['wins']}   losses {st['losses']}   win rate {st['win_rate']:.0%}",
                f"  avg win  {st['avg_win']:+.2f} ({st['avg_win_pts']:+.0f} pts)   "
                f"avg loss {st['avg_loss']:+.2f} ({st['avg_loss_pts']:+.0f} pts)   win/loss ratio {st['ratio']:.2f}",
                f"  expectancy per trade [{c}]{st['expectancy']:+.2f}[/] ({st['expectancy_pts']:+.0f} pts)   "
                f"total [{c}]{st['total']:+.2f}[/]",
                f"  before spread {st['gross']:+.2f}   spread cost paid {st['spread_cost']:.2f}   "
                f"avg hold: wins {st['hold_win']:.0f}s, losses {st['hold_loss']:.0f}s",
                f"  flips {st['flips']} (profitable {st['flips_won']})   pyramid adds {st['adds']} "
                f"(total {st['adds_total']:+.2f}, avg {st['adds_avg']:+.2f})",
                f"  biggest losing basket {min(st['worst_basket'], 0.0):+.2f}   max floating drawdown {dd:+.2f}",
                "  closed by: " + (", ".join(f"{k} {len(v)} (avg {_avg(v):+.2f})"
                                             for k, v in sorted(st["reasons"].items())) or "-"),
            ] + blines
            if st["losses"] and abs(st["avg_loss"]) > st["avg_win"]:
                lines.append("  [bold red]HONEST NOTE: average loss is BIGGER than average win.[/]")
            if st["expectancy"] <= 0:
                lines.append("  [bold red]HONEST NOTE: this symbol lost money per trade this session.[/]")
            if st["total"] <= 0 < st["gross"]:
                lines.append("  [bold yellow]HONEST NOTE: the trades made money BEFORE spread but lost after it. "
                             "The spread is the problem: a Raw Spread account or longer trades would change this.[/]")
            if st["n"] < 30:
                lines.append("  [yellow]Fewer than 30 trades: too few to judge the strategy.[/]")
        if share.get("spread too high vs volatility", 0) > 0.5:
            lines.append("  [bold yellow]HONEST NOTE: most of the time the spread was too big for this symbol's "
                         "normal moves. On a Standard account it is too expensive to scalp here.[/]")
    return lines
