"""Live terminal screen (rich): banner, one panel per symbol, event feed."""
from __future__ import annotations

from datetime import datetime, timezone

from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

try:
    import msvcrt          # Windows keyboard
except ImportError:
    msvcrt = None

KIND_STYLE = {"open": "cyan", "add": "cyan", "flip": "magenta", "close": "white",
              "warn": "yellow", "error": "bold red", "info": "white", "signal": "dim"}


def make_console():
    return Console()


def plain(markup):
    return Text.from_markup(markup).plain


def read_key():
    if msvcrt and msvcrt.kbhit():
        return msvcrt.getwch().lower()
    return None


def banner(console, acct, real):
    word = "REAL ACCOUNT  -  REAL MONEY" if real else "DEMO ACCOUNT"
    style = "bold white on red" if real else "bold black on green"
    big = Text(f"\n\n{word}\n\n", style=style, justify="center")
    info = (f"login {acct.login}   server {acct.server}   "
            f"balance {acct.balance:.2f} {acct.currency}   leverage 1:{acct.leverage}")
    console.print(Panel(Group(big, Align.center(info)), border_style="red" if real else "green"))


def confirm_real(console):
    console.print("[bold red]REAL account. The bot will place real orders with real money, "
                  "and you can lose it.[/]")
    try:
        return input("Type YES to start trading: ").strip() == "YES"
    except (EOFError, KeyboardInterrupt):
        return False


def live(console):
    return Live(console=console, auto_refresh=False, transient=False)


def _money(x):
    style = "green" if x > 0 else "red" if x < 0 else "white"
    return Text(f"{x:+.2f}", style=style)


def _status_style(s):
    if "error" in s or "failed" in s or "no price" in s or "DISCONNECTED" in s:
        return "bold red"
    if s.startswith("in trade"):
        return "green"
    return "yellow"


def symbol_panel(tr):
    sp, ms = tr.spec, tr.ms
    d = sp.digits
    dcol = {"UP": "green", "DOWN": "red"}.get(tr.direction, "yellow")
    tcol = {"UP": "green", "DOWN": "red"}.get(tr.trend, "yellow")
    head = Text.assemble(
        (f"bid {ms.bid:.{d}f}  ask {ms.ask:.{d}f}   ", "bold"),
        f"spread {ms.spread / sp.point:.0f} pts (normal {ms.median_spread() / sp.point:.0f})   ",
        f"ATR {tr.atr / sp.point:.0f} pts" + (f" = {tr.atr / ms.spread:.1f}x spread   " if ms.spread > 0 else "   "),
        "direction ", (tr.direction, dcol), "   trend ", (tr.trend, tcol),
    )
    money = Text.assemble("floating ", _money(tr.floating), "   today realized ", _money(tr.realized_today),
                          f"   flips this hour {tr.flips.count(tr.now)}/{tr.cfg['max_flips_per_hour']}"
                          f"   lot {tr.lot}")
    status = Text(f"status: {tr.status}", style=_status_style(tr.status))
    parts = [head, money, status]
    if tr.trades:
        t = Table(show_edge=False, pad_edge=False, header_style="bold")
        for col in ("ticket", "side", "type", "lot", "open price", "stop", "PnL", "ATR", "age"):
            t.add_column(col, justify="right" if col not in ("side", "type") else "left")
        for m in sorted(tr.trades.values(), key=lambda m: m.open_time):
            p = tr.live.get(m.ticket)
            pnl = (p.profit + p.swap) if p else 0.0
            u = (ms.bid - m.open_price if m.side == "BUY" else m.open_price - ms.ask) / m.unit if m.unit else 0.0
            t.add_row(str(m.ticket), Text(m.side, style="green" if m.side == "BUY" else "red"), m.kind,
                      f"{m.volume}", f"{m.open_price:.{d}f}", f"{m.sl:.{d}f}" if m.sl else "-",
                      _money(pnl), f"{u:+.2f}", f"{tr.now - m.open_time:.0f}s")
        parts.append(t)
    return Panel(Group(*parts), title=f"[bold]{tr.name}[/]", border_style="blue")


def events_panel(feed, n=12):
    t = Text()
    for when, sym, kind, msg in list(feed)[-n:]:
        t.append(f"{when} {sym:<9} ", style="dim")
        t.append(msg + "\n", style=KIND_STYLE.get(kind, "white"))
    return Panel(t or Text("no events yet", style="dim"), title="events", border_style="white")


def render(bot):
    now = datetime.now()
    server = datetime.fromtimestamp(now.timestamp() + bot.offset_s, tz=timezone.utc)
    acct = getattr(bot, "account", None)
    head = Text.assemble(
        ("bot_v2  ", "bold"),
        (f"{'REAL' if getattr(bot, 'real', False) else ''}", "bold white on red"),
        f"  local {now:%H:%M:%S}   server {server:%a %H:%M:%S}   ",
        f"account {acct.login} {acct.currency}   " if acct else "",
        "keys: r = report, Ctrl+C = stop, STOP file = close all and exit",
    )
    parts = [head]
    if bot.conn_status:
        parts.append(Text(bot.conn_status, style="bold red"))
    if bot.halted:
        parts.append(Text(bot.halt_reason, style="bold red"))
    parts += [symbol_panel(tr) for tr in bot.traders]
    parts.append(events_panel(bot.j.feed))
    return Group(*parts)
