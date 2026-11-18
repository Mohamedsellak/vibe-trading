# bot_v3: gold "swarm" scalper for MetaTrader 5 (Exness, hedging)

A Python script that trades **gold only** (XAUUSD, on Exness usually `XAUUSDm`) very fast:
many small trades at the minimum lot, each closed after a small move.
bot_v2 is untouched. bot_v3 copies its working parts (MT5 connection, orders with retries,
dashboard, logs, report) and has new trading logic.

## Read this first: the honest part
Nobody can promise this makes money. Here is the math, in plain words.

- Every trade pays the **spread** the moment it opens. On your Exness Standard demo, gold's spread
  was 0.24 (240 points). At 0.01 lot that is **$0.24 per trade**, win or lose.
- If the 5-second direction is just a guess (a coin flip), each trade loses about one spread on
  average. Choosing a different target or stop does not change that. Only a real edge does.
- So **more trades per minute does not fix a losing trade. It makes it lose faster.**
  100 trades a minute x $0.24 = $24 a minute of spread = $1,440 an hour, on a $100 account.
- **Mode A (start both ways) cannot beat mode B on average.** A BUY and a SELL opened together
  cancel out: you pay two spreads and hold no position. Cutting the loser and keeping the winner
  ends you exactly where "open only the winning side after the move" would, minus the loser's cost.
  It is built because you asked, and every trade is tagged A or B so the report can prove it either way.
- **Ten small trades opened at the same moment act like one trade ten times bigger.** The lot never
  grows, but the risk does. That is why the number of open trades is limited by your equity.
- A random-price test (`python tests/smoke_run.py sim`, 2 hours, $100) shows exactly this: 82 trades,
  win rate 54%, **−0.246 per trade after spread (the spread was 0.24)**, before spread −0.006.
  Then the daily loss limit (20%) stopped it for the day. Without that limit, the same test lost
  52% of the account in 2 hours. The bot works as designed. Without an edge, the cost is the result.

## Speed: is 100 trades a minute possible?
**No, not at your measured latency.** Your bot_v2 demo logs show gold orders take about **840 ms**
(700 to 2,250 ms). One order at a time gives at most 60,000 / 840 = **71 orders a minute**.
Most trades here close at the broker by their target or stop (1 order per trade); trades the bot
cuts need a 2nd order. So the ceiling is roughly **35 to 70 trades a minute**, before the
`MAX_ORDERS_PER_MIN = 60` cap. The screen shows the real number live ("realistic max").
Sending orders in parallel would not help much: the terminal and the broker still handle them
in turn, and Exness may answer "too many requests".

## How it decides (the same 5 lines are at the top of `strategy.py`)
1. **Direction** = the last 5 seconds of ticks, checked every second. UP only when the mid price
   rose at least 1x the trade cost AND more ticks went up than down (by 30%+). Same for DOWN. Otherwise FLAT.
2. **Start**: mode A opens 1 BUY + 1 SELL when flat; mode B waits for a direction. Default `"AB"`
   switches between A and B every 30 minutes, so one session compares both.
3. **Cut**: when the direction is clear, every trade on the other side closes at once
   ("cut wrong side" if it loses, "direction flip" if it wins).
4. **Extend**: the winning side gets up to 2 new trades per second while the direction holds,
   never while its newest trade is losing (no averaging down), up to the equity limits.
5. **Take profit fast**: each trade has its target and stop **at the broker**, set in the open order.
   The broker closes it with no bot delay. After a target, the bot reopens at once in the current direction.

## The numbers it picks, and why
Everything comes from measured cost, not fixed points or dollars:
`cost = normal spread + 2 x expected slippage` (one slippage when opening, one when closing).

| setting | value | meaning |
|---|---|---|
| `TARGET_X_COST` | 2.0 | target = the mid price moves 2x the cost our way, so the net win is about 1x the cost |
| `STOP_X_TARGET` | 1.25 | stop = the mid price moves 1.25x the target against us |

On your gold numbers (spread 0.24, slippage guessed at 0.25 x spread until 5 orders are measured):
cost 360 points ($0.36 at 0.01 lot), target 720 points (net win about +$0.36), stop 900 points
(loss about −$1.26 with spread and slippage). If measured slippage is zero: cost 240, target 480
(+$0.24), stop 600 (−$0.90).

Why the stop is a bit bigger than the target, not smaller: a trade starts one spread in the red.
A stop smaller than the target would be hit by normal noise almost every time. At 1.25x, price
noise reaches the target about 56% of the time (coin flip). Why not bigger: you asked for a stop close to
the target, and a wide stop makes each loss bigger than many wins.

**The catch:** with a win of +1 cost and a loss of about −3.5 costs, the bot needs to win about
**78% of trades** to break even, while a coin flip wins 56%. The 5-second direction must add those
22 points. The screen and the report show both numbers, so you can see if it does.

## Money rules (small account)
All in percent of **live equity**, read from MT5 every second.
- `MAX_TOTAL_STOP_RISK_PCT = 15`: the stop losses of all open trades added together stay under 15% of equity.
  The max number of open trades comes from this and is shown on screen. Example: $100 equity, one
  stop = $1.26 -> 11 trades max; all 11 stopped out at once = $13.86 = 13.9%, inside 15%.
- `BASKET_STOP_PCT = 8`: if all open bot trades together lose 8% of equity, close them all and pause 5 minutes.
- `MAX_ONE_STOP_PCT = 5`: if one trade's stop alone is more than 5% of equity, the bot does not trade
  ("stop too big for this account"). Gold at 0.01 lot needs about $25+ of equity.
- `DAILY_LOSS_PCT = 20`: if today's loss reaches 20% of today's starting balance, close all and stop until
  the next server day. (Not in your list. Added because the random-price test lost 26% an hour.)
- Free-margin check before every order (one order may use at most 50% of free margin).
  After a "no money" error from the broker: no new orders for 60 seconds.
- Lot = the symbol's minimum lot. Never more. No martingale. No averaging down.

## Filters (no NEW trades; open trades keep their broker target and stop)
- Sessions: London 08:00–16:30 London time and New York 08:00–16:00 New York time, Monday–Friday.
  Each in its own city's clock, so summer time is handled by the time zone database.
  Exness server time is UTC+0 (`SERVER_UTC_OFFSET_HOURS`); the bot warns at startup if the server clock disagrees.
- News: `news_blackout.csv` (times in UTC). The rows in it are examples: put real dates in.
- Spread spike: spread above 1.5x its 2-minute median.
- Cost check: the target must be at least 1.5x the cost measured right now.
- Too quiet: if the typical 5-second move is under half the cost, nothing can reach a target.
- Auto-pause: if the last 100 trades lost money on average after spread, a red warning shows
  (from 20 trades on) and new entries pause for 30 minutes (`AUTO_PAUSE_ON_NEGATIVE = True`).

## Speed design
- The main loop reads the newest tick every 15 ms.
- Orders go to a **second process with its own MT5 connection** (`EXECUTOR = "process"`). A slow order
  never stops price watching. If that process cannot start, the bot falls back to a worker thread with one
  lock around every MT5 call (the MetaTrader5 package is not documented as thread-safe).
- One order at a time, closes before opens. A trade with a close already queued never gets a 2nd close.
- An open that waited more than 1.5 s in the queue is dropped (its signal is old).
- Every order's send-to-fill time and queue time is measured, logged and shown.

## Setup on Windows (once)
MetaTrader 5 open, logged in to the **demo**, **Algo Trading** button on.
Use 64-bit Python 3.10, 3.11 or 3.12 from python.org. Open **cmd** in the `bot_v3` folder:

```bat
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
```
`.env` can stay empty: the bot then uses the account already logged in inside MT5.

## Tests
```bat
.venv\Scripts\python.exe -m pytest -q tests
.venv\Scripts\python.exe tests\smoke_run.py sim
.venv\Scripts\python.exe tests\smoke_run.py live
```
The tests use a fake MT5, so they also run with the market closed.

## Run
```bat
.venv\Scripts\python.exe bot.py
```
- Green **DEMO** banner, or red **REAL** banner where you must type `YES`.
- It prints the real gold name, lot, cost, target, stop, max trades and the worst case before it starts.
- **r** = report now. **Ctrl+C** = stop (asks whether to close open trades; if not, they keep their broker stop and target).
- **Kill switch:** create a file named `STOP` in the folder (`type nul > STOP`). The bot closes all its
  trades and exits. Delete the file before the next start.
- After a restart it takes over its own open trades again (by magic number). Trades of other magic numbers are never touched.

## The screen (refreshes every second)
- price, spread and normal spread, the **5-second direction** with its move and up/down tick count
- **minimum profitable target** in points and money, the target, the stop, break-even win rate vs coin flip
- equity, free margin, **open risk / cap**, max trades, basket stop level, today's realized PnL in money and %,
  floating PnL, max drawdown
- trades per minute, orders in the last minute vs the cap, queue, order latency, **realistic max trades per minute**
- a **status line**: what the bot is doing or waiting for (green = trading, yellow = waiting, red = problem)
- open BUYs and SELLs with their PnL, then an event feed. A red bar appears if the last trades lose after spread.

## Report
Press **r**, or stop the bot, or run `python report.py` (this version, all sessions; `--all` for everything).
It shows: trades per minute and hour, win rate vs break-even win rate, average win and loss,
**profit before spread, spread cost and net result per trade**, net per hour in money and % of the
starting balance, average hold time, closes by reason (target, cut wrong side, direction flip, stop, ...),
order latency and slippage, broker fill slippage, time blocked by each filter, max drawdown,
**results per mode (A vs B)** and per kind (probe / entry / extend). It says plainly when the net per trade
is negative, and whether speed would help or only multiply the cost.

Everything is saved in `logs/trades.sqlite` and `logs/bot.log.txt`. Send those two files to review a session.

## Before you ever go live (real account)
A real account is not the demo. Check each line on the real account, with `DEMO` changed to `REAL` in your head:
1. **Leverage and margin.** Real accounts often get lower leverage, and Exness can raise gold margin around news
   and before weekends. The bot reads margin from MT5 for every order, but check the free margin line on screen.
2. **Spread.** Watch the "normal spread" for an hour. If it is wider than on demo, every number above gets worse.
3. **Latency.** Real server latency is different. Look at "order latency" and "realistic max". A VPS near the
   Exness server can cut it, but it cannot remove the spread.
4. **Stop fills.** Your bot_v2 demo showed gold stops filled 0.5–0.9 worse than the stop price. Check
   "broker target/stop fills" in the report; the bot uses it to size risk.
5. **Broker rules.** Some brokers restrict very short trades on real accounts. Read Exness's terms first.
6. **`stops level` and `freeze level`** may differ (shown at startup).
7. Run the demo for **hundreds of trades** first, in mode A and B, and only consider real money if
   `report.py` shows a positive net result per trade after spread that holds up over many sessions.
