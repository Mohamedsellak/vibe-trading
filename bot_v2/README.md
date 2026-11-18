# bot_v2: live MT5 scalping bot (Exness, hedging account)

A Python script that trades live in MetaTrader 5 while you watch it on screen.
You choose the account: log in to MT5 with a demo account to test, and with a real account only when you decide to.

**Honest warning.** Nobody can promise this makes money. It is built so the average win *can*
be bigger than the average loss after spread. Only the session report tells you whether it really is.
Run it on demo for a long time first (hundreds of trades, not a few).

## How it decides (the same 5 lines are at the top of `strategy.py`)
Two yardsticks, both measured live from each symbol's own prices:
- **ATR** = the average range of the last 14 one-minute bars, or how far price normally moves in a minute. Every distance is in ATR.
- **spread** = the cost. It is used only for cost checks.

1. **Direction:** price move over the last 5 s. +0.25 ATR or more = UP, −0.25 ATR or less = DOWN, otherwise FLAT.
2. **Trend:** on 1-minute bars, EMA(8) against EMA(21). A gap over 0.15 ATR = UP or DOWN. A trade opens only when direction and trend agree.
3. **Exits:** all at the broker. The stop is 1 ATR away and the target 1.5 ATR. From +0.8 ATR, the stop trails 0.5 ATR behind the best price.
4. **Filters:** no entry if the last 20 bars zig-zag (net move ÷ total path < 0.25), or if the target is under 4× the spread (too costly).
5. **Weak spot:** if the entries have no real edge, every trade loses about one spread on average, whatever the stop and target. Only the session report can show whether there is an edge.

See `CHANGELOG.md` for what changed in each version and why.

## What the bot does
- **Opens** a BUY when price goes up and the trend agrees, or a SELL when price goes down and the trend agrees. Lot size is always the symbol's minimum lot and never grows.
- **Sets a stop loss and a take profit at the broker** as soon as a trade opens: the stop 1 ATR away, the target 1.5 ATR away. So a win is bigger than a loss, and both work even if the bot stops.
- **Trailing stop:** once a trade has been +0.8 ATR, the bot moves the broker stop up to 0.5 ATR behind the best price. The broker closes the trade there, with no bot delay.
- **No time exit:** a trade closes only at a price level (stop, target or trailing stop), so you can see all of them on the MT5 chart. `stall_exit_s` can switch an optional time exit back on.
- **Pyramids:** adds one more trade in the same direction only when every open trade on that side has its stop locked in profit (shown green on screen). So the basket can never lose more than one trade's stop. At most 3 adds per direction. It never adds to a losing trade.
- **Flips:** after a stop loss, the next trade may be in the opposite direction, but only if the trend agrees. Protections: a 15 s cooldown after each flip, at most 20 flips per hour, and no entries while the market is choppy.
- **No re-buying a failed move:** after a stop loss, no new trade on the same side for 5 s (the direction window), so only fresh prices count.
- **Never trades against itself:** it opens no BUY while its own SELLs are open, and the other way round.
- **Basket stop:** if one symbol's floating loss reaches `basket_stop_money`, the bot closes all trades on that symbol and pauses it for 15 minutes.
- **Optional daily loss limit:** `DAILY_LOSS_LIMIT = 0` means off.
- **No new entries** (open trades are still managed) when:
  - spread is above 1.5× its 10-minute median (shown as "spread too high")
  - the target is under 4× the current spread (shown as "spread too high vs volatility")
  - the market is choppy
  - news is near (`news_blackout.csv`)
  - it is outside the session (server time: Mon–Fri 07:00–20:00 for gold and EUR, 24/7 for BTC)
  - a limit is reached
- A gap of `entry_gap_s` seconds (1 s) between new entries on a symbol stops a burst of orders in the same instant.
- The loop checks prices every 25 ms.

## Setup on Windows (once)
Have MetaTrader 5 open, logged in, and the **Algo Trading** button switched on.
Use 64-bit Python 3.10, 3.11 or 3.12 from python.org. Open **cmd** in the `bot_v2` folder:

```bat
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
.venv\Scripts\python.exe -m pytest -q tests
```
`.env` can stay empty. The bot then uses the account already logged in inside MT5.

## Run
```bat
.venv\Scripts\python.exe bot.py
```
- The bot shows a big **green DEMO** or **red REAL** banner. On REAL you must type `YES` before it trades.
- It prints the real broker name for each symbol (Exness may add a suffix such as `XAUUSDm`).
- **r** prints the session report at any time.
- **Ctrl+C** stops the bot. It asks whether to close open trades (default: no, the trades stay open with their broker stops).
- **Kill switch:** create a file named `STOP` in the folder (`type nul > STOP` in cmd). The bot closes all its trades and exits. Delete the file before the next start.
- If you restart the bot, it picks up its own open trades again (found by magic number) and keeps managing them.

## The screen
One panel per symbol shows:
- price, spread and normal spread
- ATR, and ATR as a multiple of the spread (gold is usually far above 4x; EURUSD often is not)
- direction and trend
- floating PnL, today's realized PnL, and flips this hour
- a **status line** (yellow = waiting, green = in trade, red = problem)
- a table of open trades, with PnL in ATR and the age of each trade

Below the panels, a feed shows the latest events.

## Files and logs
- `config.py`: every setting, with comments. Settings per symbol go in `SYMBOL_OVERRIDES`.
- `logs/trades.sqlite`: every trade (column `unit` = ATR at open), including:
  - kind (base, add, flip, adopted) and basket
  - requested and filled price, slippage and latency
  - spread paid
  - close reason, PnL in money and points, best profit seen
  - all events and signals
- `logs/bot.log` holds everything. `logs/<SYMBOL>.log` holds one symbol only.
- `news_blackout.csv`: the rows in it are **examples**. Check the dates in a real economic calendar.

## Session report (on exit, or press r)
Shown per symbol and in total:
- trades, win rate, average win and loss (money and points), win/loss ratio
- expectancy per trade after spread, **profit before spread**, and spread cost paid
- average hold time of wins and of losses
- flips (and how many won), pyramid adds (and their results)
- biggest losing basket, max floating drawdown
- close reasons, with the average PnL of each (target, stop loss, trailing stop ...)
- order speed: average open and close time (ms) and slippage (points)
- **time spent**: the share of time each reason kept the bot from entering

The report says plainly:
- when the average loss is bigger than the average win
- when a symbol lost money
- when the trades made money **before** spread but lost **after** it (the spread is the problem)
- when the spread was too big for the symbol's normal moves most of the time (too expensive to scalp there on a Standard account)

**How to read it:**
- If **orders** take more than about 300 ms, the PC is far from the broker. A VPS near the server helps more than any code change.
- If **time spent** is mostly "spread too high vs volatility", that symbol is too costly on a Standard account.

## Tests
`tests/` runs the real bot code against a fake MT5 module (`tests/fake_mt5.py`). The tests cover:
- risk limits, lot sizing, sessions, news, spread
- ATR, broker stop and target, trailing, optional time exit, broker-only exits, locked-stop pyramid adds
- pyramiding, flips and flip cooldown, no re-entry right after a stop
- basket stop, daily limit, kill switch, restart adoption
- requote retry, filling-mode switch, market closed
- the report, and the database upgrade from an older version

## Things to know
- The bot was built and tested on Linux against the fake MT5 only. The **first run on your Windows PC with the real MT5 is the first real test**, so do it on demo and watch the event feed and `logs/bot.log` for order errors.
- Exness server time is UTC+0 (`SERVER_UTC_OFFSET_HOURS`). At startup the bot compares this with the broker clock and warns if they don't match.
- Profit after spread on a Standard account is hard. The spread is paid on every trade, and the short-term moves the bot trades are often not much bigger than the spread.
