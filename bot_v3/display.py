"""Live terminal dashboard (rich): green = profit, red = loss, yellow = waiting."""
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

KIND_STYLE = {"open": "cyan", "close": "white", "warn": "yellow", "error": "bold red",
              "info": "white", "signal": "magenta"}


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


def money(x, fmt="+.2f"):
    return Text(f"{x:{fmt}}", style="green" if x > 0 else "red" if x < 0 else "white")


def _status_style(s):
    if any(w in s for w in ("error", "failed", "no price", "DISCONNECTED", "died", "auto-pause", "no money")):
        return "bold red"
    if "waiting" in s or "flat" in s:
        return "yellow"
    return "green"


def render(sw):
    sp, ms, p, a = sw.spec, sw.ms, sw.plan, sw.acct
    now = sw.now or datetime.now().timestamp()
    d = sp.digits
    pts = 1 / sp.point
    server = datetime.fromtimestamp(now + sw.cfg.SERVER_UTC_OFFSET_HOURS * 3600, tz=timezone.utc)
    head = Text.assemble(
        (f"bot_v3 {sw.cfg.VERSION}  {sw.name}  ", "bold"),
        ("REAL", "bold white on red") if sw.real else ("DEMO", "bold black on green"),
        f"  server {server:%a %H:%M:%S}   mode {sw.mode(now)} (config {sw.cfg.START_MODE})   order worker: "
        f"{sw.ex.name}   keys: r = report, Ctrl+C = stop, STOP file = close all and exit",
    )
    parts = [head]
    if not sw.connected:
        parts.append(Text(sw.status, style="bold red"))
    if sw.rolling_warning():
        r = sw.rolling
        parts.append(Text(f" WARNING: last {r.count} trades lost {r.mean():+.3f} per trade after spread. "
                          f"{'New entries pause at 100 trades.' if sw.cfg.AUTO_PAUSE_ON_NEGATIVE else ''} ",
                          style="bold white on red"))

    dcol = {"UP": "green", "DOWN": "red"}.get(sw.dir.state, "yellow")
    market = Text.assemble(
        (f"bid {ms.bid:.{d}f}  ask {ms.ask:.{d}f}   ", "bold"),
        f"spread {ms.spread * pts:.0f} pts (normal {ms.median_spread() * pts:.0f})   ",
        "5s direction ", (f"{sw.dir.state}", f"bold {dcol}"),
        f" (move {sw.dir.move * pts:+.0f} pts, ticks {sw.dir.ups} up / {sw.dir.downs} down)   ",
        f"typical 5s move {ms.vol() * pts:.0f} pts",
    )
    parts.append(market)
    if p:
        parts.append(Text.assemble(
            "min profitable target ", (f"{p.cost * pts:.0f} pts = {p.cost_money:.3f}", "bold"),
            f"   target {p.target_move * pts:.0f} pts (net {p.win_money:+.3f})   stop {p.stop_move * pts:.0f} pts "
            f"(loss {-p.risk_money:+.3f})   slippage {p.slip * pts:.0f} pts/order   "
            f"break-even win rate {p.breakeven_winrate:.0%} (coin flip {p.coinflip_winrate:.0%})"))
    if a:
        cap = sw.cfg.MAX_TOTAL_STOP_RISK_PCT / 100 * a.equity
        orisk = sw.open_risk()
        start = a.balance - sw.realized_today
        pct = 100 * sw.realized_today / start if start else 0.0
        parts.append(Text.assemble(
            f"equity {a.equity:.2f} {a.currency}   free margin {a.margin_free:.2f}   open risk ",
            (f"{orisk:.2f}", "red" if orisk > 0.8 * cap else "white"), f" / {cap:.2f} ({sw.cfg.MAX_TOTAL_STOP_RISK_PCT}%)",
            f"   max trades {sw.max_trades()}   basket stop at -{sw.cfg.BASKET_STOP_PCT / 100 * a.equity:.2f}   "
            "today ", money(sw.realized_today), " (", money(pct, "+.2f"), "%)   floating ", money(sw.floating),
            f"   max drawdown {sw.dd_money:.2f} ({sw.dd_pct:.1f}%)"))
    tpm = sw.realistic_tpm()
    parts.append(Text.assemble(
        f"trades/min: opened {sw.per_min(sw.opened_t, now)}, closed {sw.per_min(sw.closed_t, now)}   "
        f"orders last min {sw.rate.count(now)}/{sw.cfg.MAX_ORDERS_PER_MIN}   in queue {len(sw.cmds)}   "
        f"order latency {sw.latency_ms():.0f} ms   realistic max ",
        (f"{tpm:.0f} trades/min", "bold"),
        (" (100/min impossible at this latency)" if sw.order_ms and tpm < 100 else "", "yellow")))
    parts.append(Text(f"status: {sw.status}", style=_status_style(sw.status)))

    if sw.trades:
        side_sum = {}
        for t in sw.trades.values():
            pos = sw.live.get(t.ticket)
            pl = (pos.profit + pos.swap) if pos else 0.0
            n, s = side_sum.get(t.side, (0, 0.0))
            side_sum[t.side] = (n + 1, s + pl)
        line = Text("open: ")
        for side in ("BUY", "SELL"):
            n, s = side_sum.get(side, (0, 0.0))
            line.append(f"{n} {side} ", style="green" if side == "BUY" else "red")
            line.append_text(money(s))
            line.append("   ")
        parts.append(line)
        tb = Table(show_edge=False, pad_edge=False, header_style="bold")
        for col in ("ticket", "side", "mode", "kind", "open", "target", "stop", "PnL", "age"):
            tb.add_column(col, justify="left" if col in ("side", "mode", "kind") else "right")
        for t in sorted(sw.trades.values(), key=lambda t: t.open_time)[-12:]:
            pos = sw.live.get(t.ticket)
            pl = (pos.profit + pos.swap) if pos else 0.0
            tb.add_row(str(t.ticket), Text(t.side, style="green" if t.side == "BUY" else "red"), t.mode,
                       t.role + (" (closing)" if t.closing else ""), f"{t.open_price:.{d}f}",
                       f"{t.tp:.{d}f}" if t.tp else "-", f"{t.sl:.{d}f}" if t.sl else "-",
                       money(pl), f"{now - t.open_time:.1f}s")
        parts.append(tb)
    body = Panel(Group(*parts[1:]), title=f"[bold]{sw.name}[/]", border_style="blue")
    return Group(head, body, events_panel(sw.j.feed))


def events_panel(feed, n=12):
    t = Text()
    for when, kind, msg in list(feed)[-n:]:
        t.append(f"{when} ", style="dim")
        t.append(msg + "\n", style=KIND_STYLE.get(kind, "white"))
    return Panel(t or Text("no events yet", style="dim"), title="events", border_style="white")
