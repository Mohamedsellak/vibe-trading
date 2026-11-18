# CHANGELOG

One line per change: what changed, and which market behavior it targets.
Compare session reports only between sessions run on the same version.

## v2.1 (2026-11-18): exits fixed first, plus speed and a better report

No demo session was run on v2.0, so there is no "before" report to compare against.
v2.0 had a built-in loss: one stop (−12 spreads) cost as much as 3 to 5 wins (+2.5 to +4 spreads).

**Exits and distances**
- Distances (stop, target, trailing, pyramid step, direction, trend dead-band) are now in **ATR** (average 1-minute range, 14 bars) instead of spreads. *Behavior:* noise depends on volatility, not on the spread. Gold moves about 5–10 spreads a minute and EURUSD about 2–3, so one spread multiple meant something very different on each symbol.
- Broker stop loss is now **1 ATR** (was 12 spreads), set at open. *Behavior:* a momentum scalp that moves a full normal minute range against you has failed. Holding it longer only makes the loss bigger.
- New **broker take profit at 1.5 ATR**, set at open. *Behavior:* a win (1.5) is bigger than a loss (1.0) by design, and the broker closes the trade on its server with no bot delay.
- Trailing now **follows 0.5 ATR behind the best price, from +0.8 ATR** (was "keep 50% from +5 spreads"). Target and trailing now work together, so `exit_mode` is gone. *Behavior:* it protects a profit when a burst stalls before the target.
- **Reversal exit removed.** It needed the 21-minute trend to turn, so it almost never fired, and losers ran to the −12 stop. The 1 ATR stop does that job now.
- New **"no follow-through" exit**: after 60 s, close the trade if it never got to +0.4 ATR. *Behavior:* real momentum bursts carry on within seconds. A move that stalls is usually the spike that snaps back.
- **No same-side re-entry for 20 s after a stop loss.** *Behavior:* the 20 s direction window still shows the burst that just failed. Without this the bot bought the same failed move again in the same millisecond (seen in the fake-MT5 run).
- Flips now come after a **stop loss**, because the reversal exit is gone. Flip limits are **15 s cooldown, 20 per hour** (your numbers). *Behavior:* after a stop, the turn may be real, but limits keep the bot from flipping back and forth in a range.

**Filters**
- Cost gate changed: **no entry unless the target (1.5 ATR) is at least 4× the current spread**. *Behavior:* if each trade has no edge, it loses about one spread on average. When normal moves are small compared to the spread, the spread eats any edge.
- Choppy filter keeps only the **zig-zag test** (net move ÷ path < 0.25 over 20 bars). The old "too quiet" test (range < 8 spreads) is now covered by the cost gate above.

**Speed**
- `LOOP_MS` 100 → **25 ms**. *Behavior:* the bot sees a burst up to 75 ms sooner. The broker's round trip is usually longer than that, and it is logged as latency.
- SQLite now uses WAL mode, and events are saved once per second (trades are still saved at once). The entry log line is written **after** the order is sent. *Behavior:* on Windows a disk sync per log line could block the loop for tens of milliseconds.
- 1-minute bars, ATR, trend and choppy are computed once per second, not every loop. They don't change faster than that.

**Report and screen**
- Report adds **"time spent"**: the share of time each reason kept the bot from entering. Use it to see which filter is too tight.
- Report adds **profit before spread**, **average hold time** (wins and losses), and **average PnL per close reason**.
- New honest notes: "made money before spread but lost after it", and "spread too big for this symbol's normal moves most of the time".
- Screen shows ATR, ATR as a multiple of the spread, PnL in ATR, and trade age.
