# CHANGELOG

One line per change: what changed, and which market behavior it targets.
Compare session reports only between sessions run on the same version.
Since v2.3 every trade is saved with its version, and `python report.py` shows one version's trades from all sessions together.

## v2.5 (2026-11-18): pyramiding off, measure stops better

Based on the v2.4 demo ($100, 21 trades, about 85 minutes): −12.58 in total. Gold made −14.10, with 0 targets hit in 13 trades. BTC made +1.52. EURUSD stayed out, as v2.4 intended.
Across all demo sessions so far (v2.1 to v2.4, 91 trades): **first trades (base + flip) 49, +0.07; adds 42, −10.82.** So the adds made almost all of the loss.

- **Pyramiding switched off** (`max_adds = 0`). Turn it back on with `max_adds = 3`. *Behavior:* an add can open only after the earlier trades are about 0.8–1.0 ATR in profit. Gold's moves mostly stopped around +0.8 to +1.0 ATR (12 of 34 gold trades peaked there, and only 6 went past +1.3). So adds opened right where the move usually ends, and lost in every version except one session.
- **Worst point of each trade is saved** (`trough_units`, in ATR), and the report shows the average best and worst point for winners and losers. *Behavior:* 15 of 34 gold trades never got even +0.3 ATR in profit, then lost a full stop. With the worst point saved, the next report can show whether a tighter early stop would cut those without cutting the winners. Today the data can't answer that.
- **Broker stop and target fills are measured:** the report shows how far from the stop or target level the broker filled, on average. *Behavior:* several gold stops filled 0.5–0.9 USD (2–4 spreads) worse than the stop level. That cost is hidden in "stop loss" today.

## v2.4 (2026-11-18): stricter cost gate, clearer startup

Based on the v2.3 demo (22 trades, about 25 minutes, on a $10 balance): +1.65 in total. BTC made +1.84, mostly in one 10-minute selloff. EURUSD made −0.19, and +0.21 before spread. Gold made no trades: the 10% risk cap blocked it correctly. This is too little data to change the entry or exit rules, so this version changes none of them.

- **Cost gate 4× → 6×:** no entry unless the target is at least 6× the spread, which means the normal one-minute move (ATR) must be at least 4 spreads. *Behavior:* EURUSD on a Standard account moves only about 2–3.5 spreads a minute. In v2.2 and v2.3 its 9 trades made +0.24 before spread and −0.48 after it. Its wins (+7 points) were smaller than one spread (8 points). Gold (11–15×) and BTC (6–26×) still pass.
- **Startup line per symbol:** how much one stop costs right now, as a % of equity, and whether the risk cap will let that symbol trade. *Behavior:* on a $10 account one gold stop is about $3.50 (35%), so gold sat idle without a clear reason on screen.
- `report.py` no longer prints "max floating drawdown +0.00", because it can't know the drawdown outside a live session.

## v2.3 (2026-11-18): smaller loss on the last add, money checks

Based on v2.2 demo sessions (29 trades, all sessions together: +2.56). Gold: 21 trades, +3.40 total, +8.44 before spread. Still too few to prove anything.

**Pyramiding**
- **An add now shares the basket's locked stop** instead of getting its own full 1 ATR stop. Its stop sits at the best locked stop of that side (never farther than 1 ATR). *Behavior:* the last add of a basket is opened near the top of the move. In v2.2 the five last adds lost −18.47 together, each with a full stop of $3–4.5 on gold. When the move ends, the whole basket should now leave at the same price, and the last add loses about half as much.
- **No add when the price is within 0.3 ATR of that shared stop** (`add_min_room_atr`). *Behavior:* with less room than that, normal noise would hit the stop right away, and the add would only pay the spread.

**Money safety**
- **Free margin is checked before each order** (MT5's own `order_calc_margin`). If the broker still answers "no money" (10019), that symbol pauses entries for 60 s (`NO_MONEY_PAUSE_S`). *Behavior:* v2.2 sent the same order again every few seconds and logged 47 "no money" errors while the account had no free margin.
- **No entry if one trade's stop would lose more than 10% of equity** (`MAX_RISK_PCT`). *Behavior:* gold's ATR rose to about $3–3.8, so one stop was half of a $7 account. A scalper must survive a run of losses.

**Report**
- Every trade is saved with `VERSION` (now "2.3"). **`python report.py`** prints one report for all trades of this version, across every restart. `python report.py --all` covers every version.

## v2.2 (2026-11-18): exits only at price levels, safer adds, faster direction

Based on the first demo session (19 trades, about 50 minutes: too few to prove anything, but enough to see the problems).
Gold made +1.84 before spread and −1.76 after it. Adds lost −2.32, almost the whole session loss.

**Exits**
- **"No follow-through" exit switched off** (`stall_exit_s = 0`). *Behavior:* it closed 9 of 19 trades (−4.49) at exactly 60 s, wherever the price happened to be. Winners needed 64–324 s, so 60 s cut trades that were still normal noise. Now every exit is a price level you can see on the MT5 chart: stop, target or trailing stop.
- **Trailing stop and target are now closed only by the broker.** The bot-side checks are backups, used only when the broker does not hold that order. *Behavior:* bot-side closes took 500–760 ms and slipped up to about 1 spread on gold. Two times the bot raced the broker's stop and got errors 10029 and 10036.
- Errors **10029 (position frozen near its stop)** are retried. **10036 (position already closed)** is no longer an error: the broker's real close reason is logged on the next loop.

**Pyramiding**
- **An add opens only when every open trade on that side has its stop at or beyond its entry** (locked in profit). The old rule was "all in profit, newest +0.5 ATR". Max adds 2 → **3**. *Behavior:* every losing add opened while the earlier trade could still lose. Now the whole basket can lose at most one trade's stop, and adds come only in moves that are already working.

**Entries**
- **Direction window 20 s → 5 s, threshold 0.5 → 0.25 ATR.** It is about as hard to trigger by noise as before, but it fires after half the price move. *Behavior:* the bot entered after the burst had already gone 0.5 ATR, so it bought late. Now it enters earlier in the move. Expect more signals, and more spread paid.
- The pause on the same side after a stop loss follows the window: 20 s → 5 s.

**Report and screen**
- Report adds **order speed and slippage**: average open and close time in ms, and average slippage in points.
- On screen, a trade's stop shows **green** when it is locked in profit.

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
