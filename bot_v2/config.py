"""All settings for bot_v2. Edit this file, then restart the bot.

Two yardsticks, both measured live from each symbol's own prices:
- ATR = average range of the last 14 one-minute bars (how far price usually moves).
  Stops, targets, trailing, pyramid steps and the direction threshold are in ATR,
  so they sit outside normal noise on every symbol.
- spread = the cost. It is used only for cost checks (spread filter, slippage).
Both are frozen for each trade when it opens. Money values are in your ACCOUNT currency.
See CHANGELOG.md for what changed and why.
"""

# Symbols to trade. Exness names often carry a suffix (XAUUSDm, ...);
# the bot finds the real name with symbols_get() at startup.
SYMBOLS = ["XAUUSD", "BTCUSD", "EURUSD"]

MAGIC = 26111802            # tags the bot's own orders; other trades are ignored
LOOP_MS = 25                # how often prices and trades are checked (ms)
SCREEN_REFRESH_S = 1.0      # how often the screen redraws

# Exness server time is UTC+0. Sessions below are in SERVER time;
# news_blackout.csv times are in UTC. The bot converts with this offset.
SERVER_UTC_OFFSET_HOURS = 0

# Whole-account limits
MAX_TRADES_TOTAL = 8        # open bot trades, all symbols together
MAX_TOTAL_LOTS = 0.20       # sum of open lots, all symbols together
DAILY_LOSS_LIMIT = 0        # 0 = off. If set: close everything and stop entries for the day

# Order handling
ORDER_RETRIES = 3           # retries on requote / price changed / timeout
RECONNECT_MAX_S = 60        # reconnect waits 1, 2, 4 ... up to this many seconds

# Files (relative to the bot_v2 folder)
NEWS_FILE = "news_blackout.csv"
STOP_FILE = "STOP"
LOG_DIR = "logs"
DB_FILE = "logs/trades.sqlite"

ALWAYS_OPEN = [("Mon-Sun", "00:00", "24:00")]

# Per-symbol settings. DEFAULTS apply to every symbol; SYMBOL_OVERRIDES change some.
DEFAULTS = dict(
    lot=None,                    # None = the symbol's minimum lot. Never increases.
    atr_period=14,               # ATR over the last 14 finished 1-minute bars

    # Direction: price move over the last N seconds
    dir_lookback_s=5,
    dir_min_move_atr=0.25,       # move of 0.25 ATR or more = UP / DOWN

    # Trend check: EMA fast vs EMA slow on 1-minute bars
    trend_fast=8,
    trend_slow=21,
    trend_deadband_atr=0.15,     # gap smaller than this = FLAT

    # Choppy filter on the last N 1-minute bars
    chop_bars=20,
    chop_min_straightness=0.25,  # net move / total path. Lower = zig-zag = wait

    # Exits (all in ATR, measured from the fill price, spread already included)
    stop_atr=1.0,                # broker-side stop loss on every trade, set at open
    target_atr=1.5,              # broker-side take profit, set at open (win 1.5 vs loss 1.0)
    trail_start_atr=0.8,         # once the best profit reaches +0.8 ATR ...
    trail_dist_atr=0.5,          # ... the stop follows 0.5 ATR behind the best price (locks >= +0.3)
    stall_exit_s=0,              # 0 = off. If set: close after N s ...
    stall_min_atr=0.4,           # ... if the best profit never reached +0.4 ATR (no follow-through)

    # Pyramiding: add only when every open trade on that side has its stop locked in profit
    max_adds=3,                  # adds per direction

    # Flips (opposite trade after a stop loss)
    flip_cooldown_s=15,
    max_flips_per_hour=20,       # 0 = never flip

    # Entry filters
    spread_window_s=600,         # median spread over the last 10 minutes
    spread_max_x_median=1.5,     # no entry if spread > 1.5 x its median
    min_target_x_spread=4.0,     # no entry unless the target is >= 4 x the current spread
    sessions=[("Mon-Fri", "07:00", "20:00")],   # server time

    # Per-symbol limits
    max_trades=4,                # open trades on this symbol
    basket_stop_money=5.0,       # floating loss on this symbol that closes all its trades
    basket_cooldown_s=900,       # pause after a basket stop
    entry_gap_s=1,               # min seconds between two new entries on this symbol
    deviation_spreads=1.0,       # max price slippage accepted, in spreads
)

SYMBOL_OVERRIDES = {
    "BTCUSD": dict(sessions=ALWAYS_OPEN),
}


def symbol_config(base_name):
    cfg = dict(DEFAULTS)
    cfg.update(SYMBOL_OVERRIDES.get(base_name, {}))
    return cfg
