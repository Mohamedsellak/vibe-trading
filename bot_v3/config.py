"""All settings for bot_v3 (gold swarm scalper). Edit this file, then restart the bot.

Nothing here is a price, a lot size or a dollar amount:
- distances come from the MEASURED cost of one trade (spread + slippage) and the symbol's own info;
- money limits are a PERCENT of live equity, read from MT5 every second.
See CHANGELOG.md for why each value was picked.
"""

VERSION = "3.0"             # saved with every trade, so reports never mix versions
SYMBOL = "XAUUSD"           # base name. The real Exness name (e.g. XAUUSDm) is found with symbols_get()
MAGIC = 26111903            # tags the bot's own orders. Other trades are never touched

# ---------------- experiment: how the bot starts when it has no trades ----------------
# "A"  = both sides: open PROBE_PER_SIDE BUY + SELL at once, then cut the side that is wrong
# "B"  = directional only: wait for a clear 5-second direction, then open on that side only
# "AB" = alternate A and B every ALTERNATE_EVERY_MIN minutes (one session compares both)
START_MODE = "AB"
ALTERNATE_EVERY_MIN = 30

# ---------------- speed ----------------
LOOP_MS = 15                # main loop: read the newest tick every 15 ms
SCREEN_REFRESH_S = 1.0
EXECUTOR = "process"        # "process": orders go through a 2nd process with its own MT5 connection,
                            #            so a slow order never freezes price watching (recommended)
                            # "thread":  one worker thread + one lock around every MT5 call (fallback)
MAX_ORDERS_PER_MIN = 60     # hard cap on orders sent (opens + closes). Closes are never blocked by it
MAX_PENDING_OPENS = 2       # open orders waiting in the queue at once
OPEN_MAX_AGE_MS = 1500      # an open that waited longer than this in the queue is dropped (stale signal)

# ---------------- direction: last 5 seconds of ticks, checked every 1 second ----------------
DIR_WINDOW_S = 5
DIR_CHECK_S = 1
DIR_MOVE_X_COST = 1.0       # the mid price must move at least 1x the round-trip cost in the window ...
DIR_MIN_IMBALANCE = 0.3     # ... and (up ticks - down ticks) / (up + down) must be >= 0.3 the same way
DIR_MIN_TICKS = 4           # fewer price changes than this in the window = FLAT (market asleep)

# ---------------- swarm ----------------
PROBE_PER_SIDE = 1          # mode A: trades per side in a probe
PROBE_COOLDOWN_S = 5        # mode A: at most one probe every 5 s
EXTEND_PER_CHECK = 2        # max new trades on the winning side per direction check (and after a target)
SAME_SIDE_PAUSE_AFTER_STOP_S = DIR_WINDOW_S   # after a stop loss, no new trade on that side for 5 s
MAX_OPEN_TRADES = 20        # hard cap, even if equity would allow more
MAX_TOTAL_LOTS_X_MIN = 20   # total open lots <= 20 x the symbol's minimum lot

# ---------------- target and stop, in units of the measured round-trip cost ----------------
# cost = median spread + 2 x expected slippage (one slippage at open, one at close)
TARGET_X_COST = 2.0         # take profit when the mid price moved 2x cost our way -> net win ~ 1x cost
STOP_X_TARGET = 1.25        # stop when the mid price moved 1.25x the target against us
MIN_TARGET_X_COST_NOW = 1.5 # entry gate: target must be >= 1.5x the cost measured RIGHT NOW
SLIP_PRIOR_X_SPREAD = 0.25  # expected slippage before 5 orders are measured: 0.25 x spread
SLIP_SAMPLES = 50           # slippage = average of the last 50 orders
DEVIATION_X_SPREAD = 1.0    # max price slippage accepted on an order, in spreads

# ---------------- small-account money rules (percent of live equity) ----------------
MAX_TOTAL_STOP_RISK_PCT = 15   # sum of the stop losses of all open trades (money) < 15% of equity
BASKET_STOP_PCT = 8            # floating loss of all open bot trades >= 8% of equity: close all ...
BASKET_COOLDOWN_S = 300        # ... and pause 5 minutes
MAX_ONE_STOP_PCT = 5           # one trade's stop > 5% of equity = "stop too big for this account"
MARGIN_USE_MAX_PCT = 50        # one new order may use at most 50% of the free margin
NO_MONEY_PAUSE_S = 60          # after a "no money" error, no new orders for 60 s
DAILY_LOSS_PCT = 20            # today's realized + floating loss >= 20% of today's starting balance:
                               # close all, no new entries until the next server day. 0 = off

# ---------------- filters ----------------
SPREAD_WINDOW_S = 120          # "normal spread" = median of the last 2 minutes
SPREAD_SPIKE_X_MEDIAN = 1.5    # spread above 1.5x normal = spike, no entries
VOL_WINDOW_S = 300             # volatility = median 5-second move over the last 5 minutes
MIN_VOL_X_COST = 0.5           # if the typical 5-second move is under 0.5x cost: "too quiet", no entries
# Sessions in each city's OWN clock (summer time handled by the time zone database).
# (name, time zone, days, start, end)
SESSIONS = [
    ("London", "Europe/London", "Mon-Fri", "08:00", "16:30"),
    ("New York", "America/New_York", "Mon-Fri", "08:00", "16:00"),
]
# Exness server time is UTC+0 all year. Used for "today" in the PnL line and to check the server clock.
SERVER_UTC_OFFSET_HOURS = 0
NEWS_FILE = "news_blackout.csv"     # times in UTC

# ---------------- auto-warning ----------------
ROLLING_TRADES = 100           # net result per trade over the last 100 closed trades
WARN_MIN_TRADES = 20           # show the warning from 20 trades on (judged on fewer than 100)
AUTO_PAUSE_ON_NEGATIVE = True  # with 100 trades and a negative average: pause new entries ...
AUTO_PAUSE_MIN = 30            # ... for 30 minutes, then judge the next 100 trades from zero

# ---------------- orders and connection ----------------
ORDER_RETRIES = 2              # retries on requote / price changed / timeout
RECONNECT_MAX_S = 60           # reconnect waits 1, 2, 4 ... up to 60 s

# ---------------- files (inside the bot_v3 folder) ----------------
STOP_FILE = "STOP"
LOG_DIR = "logs"
DB_FILE = "logs/trades.sqlite"
