# bot_v3 changelog

Each line: what was decided, and the market behavior it targets.

## 3.0 (2026-11-18) - first version (new logic; infrastructure copied from bot_v2 2.5)
- **Gold only, minimum lot, never more.** Targets: a small account, where one bigger lot would break the risk caps.
- **Direction from the last 5 s of ticks, checked every 1 s:** the mid move must be >= 1x the round-trip
  cost AND (up ticks − down ticks) / all >= 0.3 the same way. Targets: short bursts of one-way order flow.
  A move smaller than the cost cannot pay for a trade, and a move made of one jump plus many opposite ticks is noise.
  Known side effect (seen in tests): after a 5 s rise, the direction needs about 3.3 s of mostly falling ticks
  to turn DOWN, so late trades on the old side are usually cut at a loss.
- **Start modes A / B / AB (default AB, 30 min each), every trade tagged.** Targets: the user's question
  "does probing both sides help?". Expected answer: A pays 2 spreads for no position, so A ≤ B. The report will tell.
- **Cut the wrong side at once; close winners on a flip.** Targets: reversals inside 5-second bursts.
  Reason "cut wrong side" = closed losing, "direction flip" = closed winning.
- **Extend the winning side by up to 2 trades per check, only while its newest trade is not under water.**
  Targets: bursts that continue. Never adds to a losing side (no averaging down).
- **Target and stop at the broker, in the open order.** Targets: fast moves where the bot's 0.5–1 s order delay
  would miss the price. Also halves the order count: a trade closed by its target or stop needs no bot order.
- **Reopen at once after a target** (the bot does not wait for the next 1 s check). Targets: a burst still going.
- **Target = 2x cost (net win ~1x cost); stop = 1.25x target.** Targets: a trade starts one spread down; a stop
  smaller than the target would be hit by noise almost every time. Cost = median spread + 2 x measured slippage
  (only adverse slippage counts; prior 0.25 x spread until 5 orders are measured). Break-even win rate ~78%,
  coin flip ~56%: shown on screen.
- **Cost check against the spread right now** (target >= 1.5x current cost) and **spread spike filter** (> 1.5x
  the 2-minute median). Targets: spread jumps at session opens and news.
- **"Too quiet" filter: typical 5-second move >= 0.5x cost.** Targets: dead markets where no target can be reached.
- **Equity-based swarm size:** sum of all stops < 15% of equity, basket stop at 8%, one stop > 5% = no trading.
  Max open trades derived and shown. Targets: a small account that 10 same-moment trades could wipe out.
- **Daily loss limit 20% (added, not in the brief).** Targets: the random-price simulation lost 26% an hour;
  the 100-trade auto-pause alone reacts too late on a small account.
- **Auto-warning from 20 trades, auto-pause for 30 min at 100 trades with a negative net per trade.**
  The 100-trade window restarts from zero after a pause; it is reloaded from the database after a restart.
- **Sessions in each city's own clock** (London 08:00–16:30, New York 08:00–16:00, zoneinfo). Targets:
  gold's liquid hours; summer-time shifts no longer need manual edits.
- **Orders through a 2nd process with its own MT5 connection; closes before opens; one at a time; stale opens
  (> 1.5 s in queue) dropped; max 2 opens queued; 60 orders a minute cap.** Targets: order latency of
  0.5–2 s (bot_v2 demo: median 840 ms) that must not freeze price watching, and broker "too many requests".
- **Realistic max trades per minute shown live** (60,000 / latency / orders per trade). At 840 ms: ~71 orders a
  minute, so 100 trades a minute is not possible on this setup.
