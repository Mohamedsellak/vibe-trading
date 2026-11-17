# System Architecture, Risk Management, and Testing Pipeline for a Retail Real-Time Scalping Bot (as of Nov 2026)

Scope note: notes gathered 2026-11-16. Primary sources (framework docs, SEC order, FTMO terms, academic papers) are preferred; where only practitioner blogs/vendor pages were found this is flagged as "practitioner opinion" or "secondary". Numeric defaults in the Inferences subsections are the researcher's synthesis unless a citation is attached.

---

## KQ1. Event-driven architecture patterns and how mature OSS frameworks structure a trading system

### Takeaway
The established pattern (NautilusTrader, LMAX) is a single-threaded, event-driven core where market-data handling, strategy, risk, execution and portfolio are separate components talking only through a message bus, with I/O (network, logging, persistence) pushed to background threads; the same strategy code runs in backtest and live by swapping only the venue adapter. Building your own is defensible only for the thin "glue" layer; the order-state, reconciliation and matching-engine logic is where home-grown bots fail.

### Cited Findings
- NautilusTrader's stated architectural techniques: "domain-driven design, event-driven architecture, messaging patterns (publish/subscribe, request/response, point-to-point), ports and adapters, and crash-only design." — [NautilusTrader Architecture docs](https://nautilustrader.io/docs/latest/concepts/architecture/)
- NautilusTrader core components and responsibilities: NautilusKernel ("owns the shared trading core", one lifecycle boundary, picks environment-specific clocks); MessageBus (pub/sub, request/response, command/event routing, optional Redis backing); Cache ("keeps trading state in memory": instruments, accounts, orders, positions, optional persistence); DataEngine (market data + subscriptions); ExecutionEngine (routes commands to execution clients, tracks order/position state, handles venue reports and fills); RiskEngine ("validates orders against configured checks and applies submission and modification rate limits"); Portfolio (balances, positions, margin, PnL, exposure derived from events); Trader (registers actors, strategies, execution algorithms). — [NautilusTrader Architecture docs](https://nautilustrader.io/docs/latest/concepts/architecture/)
- Threading model: "Within a node, the core consumes and dispatches messages on a single thread." Background services (network, logging, persistence) "use separate threads or the process-wide, multi-threaded Tokio runtime." — [NautilusTrader Architecture docs](https://nautilustrader.io/docs/latest/concepts/architecture/)
- Three environment contexts: Backtest (historical data + simulated execution), Sandbox (real-time data + simulated execution), Live ("Real-time data with live venue connections, including paper or real accounts"). — [NautilusTrader Architecture docs](https://nautilustrader.io/docs/latest/concepts/architecture/)
- Layering: Rust workspace crates under `crates/`; "The public package under `python/nautilus_trader/` provides Python facades and supporting utilities over the Rust implementation." PyO3 bindings collected in `nautilus_trader._libnautilus`. (The 2026 docs no longer mention Cython.) — [NautilusTrader Architecture docs](https://nautilustrader.io/docs/latest/concepts/architecture/)
- Backtest/live parity claim: "The platform has been designed to share as much common code between backtest, sandbox and live trading systems as possible"; "The common system core is used by all node environment contexts"; user actors/strategies "use the same lifecycle across these contexts." — [NautilusTrader Overview](https://nautilustrader.io/docs/latest/concepts/overview/)
- Parity caveat in the same docs: live execution still introduces venue, transport, timing, persistence, external-activity and reconciliation behaviour that simulation may not reproduce; the docs maintain a separate "Backtest and live differences" page. — [NautilusTrader Overview](https://nautilustrader.io/docs/latest/concepts/overview/)
- LMAX architecture (Martin Fowler's 2011 write-up): the business logic processor runs entirely single-threaded in memory, fed by input disruptors (ring buffers), with journaling and replication done by separate consumers. — [Martin Fowler, The LMAX Architecture](https://www.martinfowler.com/articles/lmax.html)
- Single-writer principle (Martin Thompson): "The single biggest limitation on scalability is having multiple writers contend for any item of data or resource"; the Disruptor "strives to separate the concerns so that the single writer principle can be preserved for the common cases." — [Mechanical Sympathy, Single Writer Principle (2011)](https://mechanical-sympathy.blogspot.ch/2011/09/single-writer-principle.html)
- Disruptor design goal: one core is the only writer to a memory location; multiple readers fine. — [DZone, Ring Buffer behind Disruptor](https://dzone.com/articles/ring-buffer-a-data-structure-behind-disruptor); [LMAX QCon London 2017 slides](https://qconlondon.com/london-2017/system/files/presentation-slides/lmax-architecture.pdf)
- hftbacktest: "Complete tick-by-tick simulation with a customizable time interval or based on the feed and order receipt"; "Full order book reconstruction based on Level-2 Market-By-Price and Level-3 Market-By-Order feeds"; "Order fill simulation that takes into account the order queue position, using provided models or your own custom model"; accounts for "both feed and order latencies"; live bot "currently for Binance Futures and Bybit. (Rust-only)"; Python backtests run in Numba JIT functions; same algorithm code in backtest and live. — [hftbacktest docs](https://hftbacktest.readthedocs.io/)
- Hummingbot: modular framework; core has a clock / time-iterator design (`clock.pyx`, `time_iterator.pyx`), i.e. tick-driven loop; strategy layer = scripts, V2 controllers, executors; Gateway middleware for on-chain. — [Hummingbot developer architecture](https://hummingbot.org/developers/architecture); [Hummingbot architecture blog part 1](https://hummingbot.org/blog/hummingbot-architecture---part-1/)
- Freqtrade: Python strategy runner on CCXT; decides once per candle from pandas DataFrames; includes backtesting, REST API, web UI, SQLite trade persistence, dry-run mode; REST-based data (no streaming order book). — [CCXT docs: CCXT vs Freqtrade](https://docs.ccxt.com/docs/comparisons/ccxt-vs-freqtrade) (CCXT-authored, biased); [Gainium comparison](https://gainium.io/compare/freqtrade-vs-hummingbot) (secondary)
- QuantConnect LEAN: brokerage model assigns per-security fill models; "In backtests, the pre-built fill models assume orders completely fill"; live can partially fill; market orders can be filled on stale data with a warning when data is an hour+ old (`stale_price_time_span`). — [QuantConnect Trade Fills key concepts](https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/trade-fills/key-concepts)
- Secondary (unverified) summary of the Nautilus bus: strategies publish/subscribe rather than call components directly; only the bottom venue layer swaps between simulated matching engine and real adapter. — [marketcalls.in, Introduction to NautilusTrader Part 1](https://www.marketcalls.in/python/introduction-to-nautilus-trader-part-1-architecture-backtesting-openalgo.html)

### Inferences
- Reference architecture for a retail scalper should copy the Nautilus decomposition: MarketDataHandler → (bus) → Strategy/Signal → RiskEngine (pre-trade checks, rate limits) → ExecutionEngine/venue adapter → Portfolio/Cache, with persistence/logging/dashboards as bus subscribers off the hot thread.
- Single-threaded core + async I/O is both the latency-optimal and the simplest-to-reason-about design for one developer; it also makes backtest replay deterministic (same event order every run).
- Build-vs-adopt: adopting NautilusTrader (or hftbacktest for crypto L2 HFT) buys the matching engine, order state machine, reconciliation and backtest/live parity; building your own is reasonable only when the venue has no adapter (e.g., MT5 brokers) or the strategy is simple enough to run inside MQL5/the platform. Freqtrade's once-per-candle REST model is unsuitable for tick-level scalping; Hummingbot is market-making oriented.

### Gaps
- No primary-source head-to-head comparison of frameworks' internal event-loop implementations (Hummingbot vs Freqtrade asyncio) was found; the comparisons located are vendor-authored.
- Did not fetch QuantConnect LEAN's architecture docs; only its fill-model page.

---

## KQ2. Hot path vs cold path; language choices; model inference latency

### Takeaway
Only tick ingestion, signal evaluation, pre-trade risk checks, order placement and the kill switch need to be on the low-latency path; everything else (retraining, logging, dashboards, persistence) is asynchronous. For a retail bot, Python with a single-threaded loop is adequate for the hot path, and a gradient-boosted tree model costs ~10–50 µs per prediction — negligible relative to network latency to any retail venue.

### Cited Findings
- lleaves benchmark, batch size 1, Intel i7-4770, min over 20,000 runs, NYC-taxi LightGBM model: LightGBM native 52.31 µs; ONNX Runtime 11.00 µs; Treelite 28.03 µs; lleaves 9.61 µs. — [lleaves GitHub README benchmarks](https://www.github.com/siboehm/lleaves)
- Conflicting vendor claim (Timber project README, XGBoost model, self-reported): ONNX Runtime ~80–150 µs, Treelite compiled ~10–30 µs. — [Timber (Hacker News reader mirror)](https://hn.jakechampion.name/reader/https://github.com/kossisoroyce/timber)
- Microsoft's LightGBM inferencing benchmark page exists for comparison across runtimes. — [LightGBM Inferencing Benchmark](https://microsoft.github.io/lightgbm-benchmark/results/inferencing/)
- NautilusTrader: core is single-threaded with Rust implementation and Python facades; network/logging/persistence off-thread (see KQ1). — [NautilusTrader Architecture docs](https://nautilustrader.io/docs/latest/concepts/architecture/)
- hftbacktest: live trading is Rust-only; Python backtests use Numba JIT. — [hftbacktest docs](https://hftbacktest.readthedocs.io/)
- LMAX: Java single-threaded business logic achieved high throughput by avoiding locks and queues (Disruptor). — [Martin Fowler, The LMAX Architecture](https://www.martinfowler.com/articles/lmax.html)

### Inferences
- Hot path (must be synchronous and fast): parse tick → update features → model/rule evaluation → risk checks → submit/cancel order → kill-switch evaluation. Cold path (async, separate process or thread): tick/decision/order persistence, metrics export, Telegram/Discord alerts, dashboards, model retraining, end-of-day reports.
- Tree models (LightGBM/XGBoost) compiled via ONNX Runtime, Treelite or lleaves run in 10–30 µs on commodity x86; even native LightGBM at ~50 µs is 2–4 orders of magnitude below retail venue round-trip latency (tens of ms over the internet), so model inference is not the bottleneck; feature computation in Python and GC pauses are more likely to be.
- Language guidance: Python (asyncio + numpy, or Nautilus) for strategy and glue; Rust/C++ only if you need sub-100 µs reaction or L2 book reconstruction at high message rates (hftbacktest's live path is Rust for this reason); MQL5/C# when running inside MetaTrader/NinjaTrader because the platform owns the connection and the tester.

### Gaps
- No measured end-to-end latency figures for Python asyncio tick loops vs Rust were found in this research; the above is inference from component benchmarks.
- No source quantifying typical retail broker/exchange round-trip order latency was fetched.

---

## KQ3. State management and persistence: order state machine, idempotency, reconciliation, clocks, data storage

### Takeaway
The consensus pattern is: deterministic client order IDs as idempotency keys, write intent to local durable storage before sending to the venue, never auto-resubmit with a new ID while prior state is unknown, deduplicate fills by execution ID, and run a startup + periodic reconciliation loop that adopts unknown venue orders and holds strategy start until reconciliation completes. Every tick, decision and order should be persisted off the hot thread for post-mortems.

### Cited Findings
- Deterministic client IDs: "If your strategy emits the same signal again after a restart, it should produce the same clientOrderId. That gives your bot a natural deduplication key both internally and at the exchange." — [dev.to, Building an idempotent crypto order pipeline](https://dev.to/cvchelles/building-an-idempotent-crypto-order-pipeline-in-nodejs-9ip) (practitioner)
- Write-intent-first: "If a worker dies after placing an order but before storing the response, the next reconciliation pass can attach the exchange order ID." — [dev.to, idempotent crypto order pipeline](https://dev.to/cvchelles/building-an-idempotent-crypto-order-pipeline-in-nodejs-9ip)
- Separate local vs venue keys: "idempotency_key controls local deduplication; client_oid controls the ID sent to the exchange." — [NexusTrader docs, Reliable WS Order Flow](https://nexustrader.readthedocs.io/en/latest/quickstart/reliable_orders.html)
- FIX-style rules: "no auto-resubmit with new ClOrdID while prior state is unknown"; deduplicate fills by ExecID since "position/PnL updates must be idempotent." — [Order Idempotency & Duplicate-Order Prevention Playbook](https://velobot-wiki.pages.dev/article/finance/order-idempotency-duplicate-prevention-playbook/) (practitioner wiki)
- Reconnect handling: a REST snapshot on WebSocket reconnect "adopts orders the bot doesn't recognize", typically those created while disconnected. — [dev.to, WebSocket reconnection for trading bots](https://dev.to/matrixtrak/websocket-reconnection-that-actually-works-auto-reconnect-guide-for-trading-bots-3fe0)
- NautilusTrader execution policies: recovery "means restoring available cached state, reconciling available venue reports, and holding the strategy-start barrier until startup reconciliation finishes"; the live engine generates external order events for unrecognized client order IDs. — [NautilusTrader Execution Policies](https://nautilustrader.io/docs/latest/concepts/execution/policies/)
- NautilusTrader Cache holds orders/positions in memory with optional persistence; MessageBus can be externally backed by Redis. — [NautilusTrader Architecture docs](https://nautilustrader.io/docs/latest/concepts/architecture/)
- Periodic reconciliation on a fixed interval, flagging orders missing on either side. — [Polytraders Dev Guide, Order Lifecycle Manager](https://polytraders-library.pages.dev/bots/exec/orderlifecyclemanager) (practitioner)
- Monitoring guide: reconcile positions and orders with the broker "every few minutes" as a distinct monitoring level. — [NexusFi, Trading bot monitoring](https://nexusfi.com/a/automation/trading-bot-monitoring)
- Broker-side idempotency guidance from a broker API: tastytrade documents idempotency and retry semantics for its order API. — [tastytrade developer docs, Idempotency and retries](https://developer.tastytrade.com/docs/guides/idempotency-and-retries/)
- Databento supplies "up to four timestamps per event, each in nanosecond resolution" (exchange vs receive timestamps). — [Databento tick data](https://databento.com/tick-data)
- Post-trade analysis store: QuestDB cookbook uses `ASOF JOIN` to pair each fill with latest mid/book snapshot; notes QuestDB has native Parquet support. — [QuestDB cookbook, Slippage per fill](https://questdb.com/docs/cookbook/sql/finance/slippage/)
- Decision-time logging: "a live system should use the mid at decision time instead, with the drift from decision to first fill counted as delay cost." — [QuestDB cookbook, Order-level implementation shortfall](https://questdb.com/docs/cookbook/sql/finance/implementation-shortfall-order/)
- Kill-switch trip persistence: write the trip to a dated file the bot checks at startup so an automatic restart cannot silently re-enable trading; clearing is manual. — [NexusFi, Automated trading emergency protocols](https://nexusfi.com/a/automation/automated-trading-emergency-protocols)

### Inferences
- Order state machine minimum: INTENT → SUBMITTED → ACKED → (PARTIALLY_FILLED)* → FILLED | CANCELLED | REJECTED | EXPIRED, with UNKNOWN as an explicit state after timeouts; transitions only from venue events keyed by exchange order id + exec id.
- Persist (append-only, off hot thread): raw ticks/book snapshots with both exchange and local receive timestamps; every signal/decision with the feature vector and model version; every order command and venue event; periodic account/position snapshots. Parquet files per day (cheap, Polars/DuckDB-queryable) or QuestDB/ClickHouse if you want SQL `ASOF JOIN` for TCA.
- Restart mid-position: on boot, load cache, pull open orders/positions from venue, adopt unknowns, compare to local intents, and only then release the strategy; if any discrepancy cannot be resolved automatically, default to flatten-and-halt.

### Gaps
- No primary source on NTP vs PTP clock sync requirements for retail bots was fetched; the practical point (store both exchange and local timestamps, measure skew) is inference.
- Exchange-specific client-order-id uniqueness scopes/lookup-by-client-id support were not verified per venue.

---

## KQ4. Monitoring, logging, alerting, deployment, restarts

### Takeaway
Practitioner consensus: layer the monitoring (process alive → connected → data fresh → positions reconciled → PnL within limits), run an independent watchdog/dead-man's-switch outside the bot process that flattens via the broker API when heartbeats stop, and persist the kill-switch state so restarts cannot silently resume trading.

### Cited Findings
- Layered monitoring: level 1 is "whether the bot is alive, checked by an outside service"; another level is "whether it agrees with the broker on positions and orders, reconciled every few minutes"; the bot "pings an outside service every minute, and that service alerts you when the pings stop. This is called a heartbeat, or a dead man's switch." — [NexusFi, Trading bot monitoring](https://nexusfi.com/a/automation/trading-bot-monitoring)
- Heartbeat rule example: if more than 30 seconds pass since the last heartbeat, an independent watchdog process kills and flattens; kill action = "flatten all positions immediately, cancel all orders, disable all automated trading" with no discretion or delay. — [NexusFi, Automated trading emergency protocols](https://nexusfi.com/a/automation/automated-trading-emergency-protocols)
- Defense in depth: an in-process dead-man switch with a 300-second timeout plus a standalone systemd watchdog that polls telemetry and flattens through the API. — [qgtm-docs, DMS independence audit](https://qgtm-docs.pages.dev/audit/DMS_INDEPENDENCE/) (single project's docs)
- Flatten cost warning: flattening in thin overnight liquidity "can cost several ticks of slippage", so flatten logic should consider session liquidity. — [NexusFi, Automated trading emergency protocols](https://nexusfi.com/a/automation/automated-trading-emergency-protocols)
- Hummingbot kill switch: config `kill_switch_enabled` / `kill_switch_rate` ("At what profit/loss rate would you like the bot to stop? (e.g. -5 equals 5 percent loss)"); when triggered the log shows "Kill switch threshold reached" and "Stopping the bot..."; the docs do not state whether open orders are cancelled or positions closed; the page's own unit examples conflict (-5 vs -0.3). — [Hummingbot Kill Switch docs](https://hummingbot.org/client/global-configs/kill-switch/)
- Real-time monitoring article (QuantInsti) covers monitoring a trading bot in real time. — [QuantInsti, Monitor trading bot real time](https://www.quantinsti.com/articles/monitor-trading-bot-real-time/) (not fetched in full)
- Knight Capital precedent: Knight's PMON "relied entirely on human monitoring and did not generate automated alerts regarding the firm's financial exposure"; 97 automated "BNET reject" e-mails referencing "Power Peg disabled" went to personnel at ~8:01 a.m. ET before the open and were not acted on. — [SEC Order, In re Knight Capital Americas LLC, Release 34-70694 (Oct 16, 2013)](https://www.sec.gov/files/litigation/admin/2013/34-70694.pdf)

### Inferences
- Metrics worth exporting (Prometheus-style counters/histograms; dashboards in Grafana): tick-to-decision latency, decision-to-ack latency, order reject rate, fill rate for limit orders, realized slippage vs decision mid (bps), open exposure, daily PnL vs limit, heartbeat age, data-feed age. Alerts (Telegram/Discord) should fire on: kill switch tripped, reconciliation mismatch, feed stale, reject burst, daily-loss threshold at 50%/80%/100%.
- Deployment for retail: one VPS in the broker/exchange region, bot as a systemd service (Restart=on-failure) or Docker container, secrets in environment files with 0600 permissions or a secrets manager — but the restart policy must be paired with the persisted kill-switch latch so a crash loop never re-enters the market. Redundancy for a solo developer is better spent on an independent watchdog with its own API key able only to cancel/flatten than on a second trading instance (which risks duplicate orders).

### Gaps
- No authoritative source found on specific Prometheus/Grafana setups for trading bots; the metric list above is inference.
- Stale-data detection thresholds: an operational-controls guide lists "don't trade on old prices" as a core control but none of the sources gives a concrete threshold; no dedicated source found.
- VPS placement, Docker/systemd specifics and secrets management were not researched with sources.

---

## KQ5. Position sizing: fixed fractional, volatility targeting, Kelly/fractional Kelly, caps

### Takeaway
Fixed-fractional risk per trade (sub-1%) with hard exposure caps is the baseline; Kelly gives the theoretical upper bound on fraction but, because the edge is estimated and the penalty for over-betting is asymmetric, practitioners use half- or quarter-Kelly at most and still cap the position.

### Cited Findings
- Thorp's chapter "The Kelly Criterion in Blackjack, Sports Betting, and the Stock Market" (ch. 9 of MacLean, Thorp & Ziemba, *The Kelly Capital Growth Investment Criterion*, World Scientific 2011) includes a section "The case for 'fractional Kelly'" (sec. 7.3). — [World Scientific / RePEc chapter listing](https://ideas.repec.org/h/wsi/wschap/9789814293501_0054.html); full text [Thorp 2006 PDF (gwern mirror)](https://www.Gwern.net/doc/statistics/decision/2006-thorp.pdf)
- "Thus long term growth maximizing investors should bet Kelly or less. We call betting less than Kelly 'fractional Kelly,' which is simply a blend of Kelly and cash"; "growth is traded off for security when using fractional Kelly strategies." — [MacLean, Thorp, Ziemba, "Good and bad properties of the Kelly criterion" (Berkeley stat mirror)](https://www.stat.berkeley.edu/~aldous/157/Papers/Good_Bad_Kelly.pdf)
- Estimation error is the core danger: full Kelly "amplifies estimation error"; overestimating the edge pushes sizing past the optimum into a regime that destroys capital; the growth penalty for betting above the true optimum is severe while the penalty for betting below is mild. — [Philipp Dubach, Bet Sizing at the Frontier](https://philippdubach.com/posts/bet-sizing-at-the-frontier/) (essay); [StockAlarm, Kelly position sizing guide](https://pro.stockalarm.io/blog/kelly-criterion-position-sizing-guide) (practitioner)
- Kelly assumptions that fail in trading: independence (correlated positions raise ruin risk) and zero transaction costs (fees/slippage lower effective edge); edges decay across regimes, so estimates should be recomputed regularly. — [LuxAlgo, Kelly criterion](https://www.luxalgo.com/library/concept/kelly-criterion/) (secondary)
- Common practice cited: half or quarter Kelly plus a hard cap per position (one source quotes 2–5% of portfolio caps; not a standard). — [StockAlarm, Kelly position sizing guide](https://pro.stockalarm.io/blog/kelly-criterion-position-sizing-guide)
- FTMO (a widely copied risk template) caps daily loss at 3–5% and total loss at 10% of initial capital (details in KQ7), which bounds the feasible per-trade risk. — [FTMO Trading Objectives (updated 2026-11-02)](https://ftmo.com/en/trading-objectives/)

### Inferences
- For a scalper taking many trades/day, per-trade risk must be small enough that a plausible losing streak (e.g., 10–15 consecutive losses at a ~50% win rate) stays inside the daily loss limit: with a 3% daily limit and 10 consecutive losses, per-trade risk ≤ 0.3%. A 0.1–0.5% per-trade default is consistent with the prop-firm constraints above.
- Volatility targeting (ATR-scaled stop distance, size = risk$/stop distance) keeps dollar risk constant as spread/volatility changes; this is a standard formulation but no primary source was fetched for it in this research.
- Fractional Kelly should be computed from out-of-sample/live trade statistics only, re-estimated on a rolling window, and used as a ceiling, never a target.

### Gaps
- Did not retrieve the body of Thorp's sec. 7.3 or Ed Seykota's writings; the "2x Kelly guarantees ruin" attribution to Thorp was seen only in a secondary source and is unverified.
- No academic source on ATR-based volatility sizing was fetched.

---

## KQ6. Stop-loss logic for scalps

### Takeaway
Hard broker-side stops guarantee an exit on disconnect but are visible to the broker and subject to minimum stop distances and slippage in fast markets; software stops are flexible but die with the bot — practitioner guidance is to use both (soft stop as primary, hard stop as a wider catastrophe backstop) and to add time stops for scalps.

### Cited Findings
- Fast-market slippage on stops: NexusFi warns flattening in thin liquidity can cost "several ticks of slippage". — [NexusFi, Automated trading emergency protocols](https://nexusfi.com/a/automation/automated-trading-emergency-protocols)
- Backtest fill realism for stops/limits: OHLC bars don't show the order in which high and low traded, so a stop and a target inside the same bar can't be ordered from the data alone. — [ABC Trading Group, 8 Backtesting Pitfalls](https://www.abctradinggroup.com/backtesting-pitfalls/) (practitioner)
- NautilusTrader L1 fill model: `prob_slippage` models "a one-tick adverse move on each fill"; a successful draw "moves the fill one tick against the order"; a limit order filled at its limit price never slips. — [NautilusTrader Fill Models](https://nautilustrader.io/docs/latest/concepts/backtesting/fill-models/)
- Independent watchdog flattening as the disconnect backstop (see KQ4). — [NexusFi, Automated trading emergency protocols](https://nexusfi.com/a/automation/automated-trading-emergency-protocols)

### Inferences
- Recommended stop stack for a scalper: (1) software stop evaluated on every tick with market-order exit; (2) broker-side hard stop placed wider (e.g., 1.5–2x the soft stop) solely as a disconnect/crash backstop; (3) time stop (close if neither target nor stop hit within N bars/seconds — scalps that stall have lost their edge); (4) volatility stop sized from ATR/spread so stop distance exceeds typical noise plus spread; (5) break-even/trailing only after move ≥ 1R to avoid being stopped by spread.
- Stops placed exactly at obvious levels in news periods are vulnerable to spread widening; the fix is to pause trading around scheduled high-impact news rather than widen stops.

### Gaps
- No source fetched documenting broker minimum stop distance (e.g., MT5 `SYMBOL_TRADE_STOPS_LEVEL`) or quantifying stop slippage during news; treat these as known-but-unsourced constraints to verify per broker.
- No empirical source on "stop hunting" was found; this remains folklore/opinion.

---

## KQ7. Drawdown limits, cool-off periods, prop-firm templates

### Takeaway
FTMO's published objectives (daily loss 3–5% of initial capital measured on equity including floating PnL, reset at 00:00 CE(S)T; 10% maximum loss, static or trailing by account type) are a concrete, widely-copied template for a retail bot's drawdown shutoffs.

### Cited Findings
- FTMO 2-Step: Maximum Daily Loss 5%; Maximum Loss 10% static ("Initial Simulated Capital minus 10%", does not trail); profit targets 10% (Challenge) / 5% (Verification); minimum 4 trading days in evaluation phases. — [FTMO Trading Objectives (published 2025-12-07, modified 2026-11-02)](https://ftmo.com/en/trading-objectives/)
- FTMO 1-Step: Maximum Daily Loss 3%; Maximum Loss 10% end-of-day trailing, recalculated at 00:00 CE(S)T from the highest balance reached, "The limit can only increase, but never decrease." — [FTMO Trading Objectives](https://ftmo.com/en/trading-objectives/)
- FTMO Instant: Daily Loss 3%; Maximum Loss 10% intraday trailing ("updates the moment a trade closes at a new balance high"); Best-Day consistency ≤ 30% of total profit. — [FTMO Trading Objectives](https://ftmo.com/en/trading-objectives/)
- Daily loss measured on equity: "Balance + Open Positions P/L ± Swaps – Commissions", recalculated at 00:00 CE(S)T from the prior day's balance. — [FTMO Trading Objectives](https://ftmo.com/en/trading-objectives/)
- Third-party summaries conflict on whether the limit is balance- or equity-based and on 1-step trailing type; the official page settles both (equity; EOD trailing for 1-Step). — [LuxAlgo FTMO page](https://www.luxalgo.com/prop-firms/ftmo/); [Backtrex, prop firm daily loss and max drawdown](https://backtrex.com/en/blog/prop-firm-rules-daily-loss-limit-max-drawdown) (secondary)
- Hummingbot's kill switch is a PnL-rate-based stop (see KQ4). — [Hummingbot Kill Switch docs](https://hummingbot.org/client/global-configs/kill-switch/)

### Inferences
- Bot defaults modelled on FTMO but tighter (because a bot can be stopped automatically, use an internal limit with margin before the external one): soft daily loss limit 2% (halt new entries), hard 3% (flatten + lock until next session); weekly 5%; max drawdown from equity peak 8% (halt, require manual review); max consecutive losses 6–8 → cool-off of 30–60 minutes; equity-curve throttle: halve size when rolling 20-trade PnL < 0, restore after 20 trades of positive expectancy.
- Count floating PnL in the daily figure (as FTMO does) so that an open loser cannot mask a breach.

### Gaps
- No academic or primary source on equity-curve trading / throttling effectiveness was found; it is practitioner opinion.
- Minimum stop/max-consecutive-loss defaults above are researcher synthesis, not cited.

---

## KQ8. Transaction cost modelling and break-even math for scalps

### Takeaway
Break-even win rate = 1/(1+R) before costs and (1+c)/(1+R) with cost c expressed in R units; for scalps where the target is a few spreads wide, spread and commission move the break-even by several percentage points, so a scalping edge must be measured against arrival-price slippage with decision-time timestamps, not against mid or last.

### Cited Findings
- Break-even formula: win rate = 1 ÷ (1 + R); 1:1 → 50%, 2:1 → 33.3%, 3:1 → 25%; with per-trade cost c in R units: (1 + c) ÷ (1 + R). — [MQL5 blog, Risk/Reward vs Win Rate: The Breakeven Line](https://www.mql5.com/en/blogs/post/779062)
- Alternative: break-even = (average loss + costs) ÷ (average win + average loss); example: $200 win, $100 loss, $5 cost → 35% vs 33%. — [NexusFi, Expectancy](https://nexusfi.com/articles/trading/Expectancy)
- Spread effect on scalps: required break-even win rate increases by 100×(spread/stop)%; a 10-pip target with a 1-pip spread is effectively a 9-pip reward. — [TradingView note, Winrates required to breakeven](https://my.tradingview.com/chart/ZC1%21/aJvJwYQK-Winrates-required-to-breakeven-relative-to-stop-target-sizes) (practitioner)
- Arrival-price benchmark: "slippage from arrival as the difference between the arrival price and the execution price in bps"; "in systematic trading (where bots execute trades based on signals), the arrival price is commonly used as a benchmark"; use a short-window mid-quote as a stable arrival price. — [Talos, Execution insights through TCA](https://www.talos.com/insights/execution-insights-through-transaction-cost-analysis-tca-benchmarks-and-slippage)
- Expected slippage for a spread-crossing strategy ≈ "the average half-spread, plus whatever the market drifted against us." — [QuestDB, TCA with QuestDB and Polars](https://questdb.com/blog/transaction-cost-analysis-questdb-polars/)
- Decision-time vs first-fill: delay cost "would be the drift from decision to first fill"; sign convention "positive IS always means you paid more than the arrival benchmark." — [QuestDB cookbook, Order-level implementation shortfall](https://questdb.com/docs/cookbook/sql/finance/implementation-shortfall-order/)
- Markout measurement: record mid at execution and at later offsets (`HORIZON JOIN`). — [QuestDB cookbook, Post-trade overview](https://questdb.com/docs/cookbook/sql/finance/post-trade-overview/)
- Fixed-tick slippage models may understate real costs by 40–60% (unverified practitioner claim); a scalping backtest with 60% win rate / ~$400/day was profitable only with zero slippage once realistic costs were added. — [LuxAlgo, Backtesting limitations: slippage and liquidity](https://www.luxalgo.com/blog/backtesting-limitations-slippage-and-liquidity-explained/); [dev.to, 5 backtesting mistakes](https://dev.to/qcautomation/5-backtesting-mistakes-that-make-your-algo-look-like-a-money-printer-until-it-isnt-2kf1)
- NautilusTrader models one-tick adverse slippage probabilistically on L1 (`prob_slippage`), none on L2/L3 where the book is walked. — [NautilusTrader Fill Models](https://nautilustrader.io/docs/latest/concepts/backtesting/fill-models/)

### Inferences
- Cost model for backtests: round-trip cost = full spread (taker) or expected adverse selection (maker) + commission + modelled slippage as a function of volatility and order size relative to top-of-book depth + funding/swap if held across the funding/rollover time. Require expected net edge per trade ≥ 1.5–2× round-trip cost before the strategy is considered viable (margin for cost under-estimation).
- Measure realized slippage live as fill price minus mid at decision timestamp (bps), split into delay (decision→ack) and impact (ack→fill); compare its distribution to the backtest's assumed distribution as a scaling gate.

### Gaps
- No source on modelling swap/funding for scalps or on measured retail market impact in thin crypto books.
- The 40–60% understatement figure is unverified.

---

## KQ9. Kill switches, runaway protection, pre-trade controls (Rule 15c3-5, Knight Capital)

### Takeaway
SEC Rule 15c3-5 requires automated, pre-trade controls that reject orders exceeding pre-set capital/credit thresholds and prevent erroneous (fat-finger, duplicate, runaway) orders; Knight Capital's 2012 loss of >$460M in ~45 minutes, caused by dead code on one of eight servers and the absence of automated capital-threshold rejects, is the canonical reason a retail bot should have independent order-rate, exposure and heartbeat kill switches.

### Cited Findings
- Knight facts (SEC order, Oct 16 2013): on August 1, 2012 SMARS processed "212 small retail orders" through defective code, producing "4 million executions in 154 stocks for more than 397 million shares in approximately 45 minutes"; Knight "assumed an approximately $3.5 billion net long position in 80 stocks and an approximately $3.15 billion net short position in 74 stocks"; "Knight lost over $460 million from these unwanted positions." — [SEC Order 34-70694](https://www.sec.gov/files/litigation/admin/2013/34-70694.pdf)
- Root cause: new RLP code repurposed a flag previously used by discontinued "Power Peg" functionality (unused since 2003); the deployment was missed on "the eighth server"; "Knight did not retest the Power Peg code after moving the cumulative quantity function"; orders sent to the eighth server "triggered the defective Power Peg code" which sent child orders without tracking fills; "Knight had no written procedures" requiring deployment verification. — [SEC Order 34-70694](https://www.sec.gov/files/litigation/admin/2013/34-70694.pdf)
- Missed warning: at ~8:01 a.m. ET the system sent 97 "BNET reject" e-mails referencing "Power Peg disabled" to a group of personnel; not acted on. — [SEC Order 34-70694](https://www.sec.gov/files/litigation/admin/2013/34-70694.pdf)
- Control failures cited: no controls to reject orders exceeding "pre-set capital thresholds for the firm, in the aggregate, as required under Rule 15c3-5(c)(1)(i)" ("Knight failed to link accounts to firm-wide capital thresholds"); failure to prevent erroneous orders "at a point immediately prior to the submission of orders" (15c3-5(c)(1)(ii)); PMON "relied entirely on human monitoring and did not generate automated alerts"; annual review did not evaluate controls for "orders that exceed pre-set capital thresholds ... or that indicate duplicative orders." — [SEC Order 34-70694](https://www.sec.gov/files/litigation/admin/2013/34-70694.pdf)
- Penalty: $12 million settlement; independent consultant required. — [WilmerHale, Knight Capital settles Rule 15c3-5 violations](https://www.wilmerhale.com/en/insights/client-alerts/knight-capital-settles-rule-15c3-5-violations-with-sec-agrees-to-pay-12-million)
- Rule 15c3-5 core: controls must be "implemented on a pre-trade, automated basis"; must "systematically limit the financial exposure", including "pre-set capital and credit thresholds"; must prevent erroneous orders and orders that violate regulatory requirements; controls under the broker-dealer's "direct and exclusive control"; CEO annual certification (secondary claim). — [FINRA Market Access Rule (2026 Oversight Report)](https://finra.org/rules-guidance/guidance/reports/2026-finra-annual-regulatory-oversight-report/market-access-rule); [SEC Final Rule 34-63241 (2010)](https://www.SEC.gov/rules/final/2010/34-63241.pdf); [Nasdaq 15c3-5 FAQ](https://m.nasdaqtrader.com/content/productsservices/trading/ften/marketaccessrulefaq.pdf)
- Independent watchdog + flatten semantics, heartbeat 30 s, persisted trip file (see KQ4). — [NexusFi, Automated trading emergency protocols](https://nexusfi.com/a/automation/automated-trading-emergency-protocols)
- NautilusTrader RiskEngine "applies submission and modification rate limits" as a built-in control. — [NautilusTrader Architecture docs](https://nautilustrader.io/docs/latest/concepts/architecture/)
- Hummingbot kill switch stops the bot at a configured PnL rate. — [Hummingbot Kill Switch docs](https://hummingbot.org/client/global-configs/kill-switch/)

### Inferences
- Translate 15c3-5(c)(1) into retail-bot pre-trade checks executed synchronously before every order: (i) aggregate exposure cap (notional and per-instrument), (ii) max order size / max notional per order (fat-finger), (iii) price collar vs current mid (reject if > X bps away), (iv) duplicate detection by client order id and by (symbol, side, qty, 1-s window), (v) max orders per second and per minute (runaway guard — Knight's failure mode was exactly unbounded child orders), (vi) max open positions, (vii) daily-loss/drawdown gates (KQ7), (viii) stale-data gate (no entries if last tick older than T), (ix) connectivity gate (no entries while disconnected; flatten after a reconnect timeout), (x) kill-switch latch checked at startup.
- Knight-specific lessons for solo deployments: verify deployed version hash on every host/instance at startup; remove dead code paths rather than leaving them behind flags; never repurpose a config flag; treat reject/error bursts as an automatic halt trigger rather than an e-mail.

### Gaps
- Specific numeric thresholds (orders/sec, price-collar bps) are researcher defaults; no source prescribes retail values.

---

## KQ10. Overfitting protection: walk-forward, CPCV, DSR/PBO, parameter stability, Monte Carlo

### Takeaway
Bailey & López de Prado show that with enough trials a researcher "will always find a misleadingly profitable strategy"; the remedies with primary-source backing are tracking the number of trials and deflating the Sharpe ratio (DSR), estimating the probability of backtest overfitting via CSCV, and using purged/embargoed combinatorial cross-validation; walk-forward with a pre-fixed protocol is the practitioner standard.

### Cited Findings
- DSR abstract: "analysts can backtest millions (if not billions) of alternative investment strategies. Backtest optimizers search for combinations of parameters that maximize the simulated historical performance of a strategy, leading to backtest overfitting"; "Selecting the one 'significant' result from a multiplicity of parallel tests poses a grave risk of an incorrect conclusion"; with enough "number of trials, it is guaranteed that a researcher will always find a misleadingly profitable strategy, a false positive." — [Bailey & López de Prado, The Deflated Sharpe Ratio (2014), author PDF](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf); [SSRN 2460551](https://papers.ssrn.com/abstract=2460551)
- DSR inputs: "non-Normality of the returns (skewness, kurtosis), the length of the returns series (T), the variance of the SRs tested (V[{SR}]), as well as the number of independent trials involved in the selection of the investment strategy (N)"; the "expected maximum is greater than zero, even if the true SR is zero." Keywords: Probabilistic Sharpe ratio, Minimum Track Record Length, Minimum Backtest Length. Published J. Portfolio Management 40(5), 2014. — [Bailey & López de Prado, DSR PDF](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf)
- PBO: Bailey, Borwein, López de Prado & Zhu, "The Probability of Backtest Overfitting", estimated "through a numerical method that we call combinatorially symmetric cross-validation (CSCV)"; J. Computational Finance 20(4), 2017. — [SSRN 2326253](https://papers.ssrn.com/abstract=2326253)
- "Pseudo-Mathematics and Financial Charlatanism" (Bailey, Borwein, López de Prado, Zhu, Notices of the AMS 2014) — the companion paper arguing backtest overfitting is routine. — [Backtest overfitting paper PDF (ioandc mirror)](https://ioandc.com/wp-content/uploads/2021/08/backtestfail.pdf)
- Secondary commentary on DSR: even with true SR = 0, "the likelihood of getting a Sharpe ratio of 3 or more is pretty high" after many trials. — [Klement on Investing, The big risk of big data](https://klementoninvesting.substack.com/p/the-big-risk-of-big-data) (secondary)
- CPCV (López de Prado, *Advances in Financial Machine Learning*, 2018): "systematically constructing multiple train-test splits, purging overlapping samples, and enforcing an embargo period to prevent information leakage"; produces "multiple backtest paths instead of one and thereby a distribution of performance"; embargo applies only after the test set. — [Wikipedia, Purged cross-validation](https://en.wikipedia.org/wiki/Purged_cross-validation); implementation [skfolio CombinatorialPurgedCV](https://skfolio.org/generated/skfolio.model_selection.CombinatorialPurgedCV.html)
- Walk-forward: Pardo (1992/2008) formalised it; anchored window keeps the start fixed (in-sample grows), rolling keeps constant length; "neither is uniformly better"; secondary sources attribute to Pardo a 3:1 IS/OOS ratio and a minimum of 5 OOS periods; walk-forward efficiency (OOS/IS performance) > 0.5 suggests robustness; choosing anchored vs rolling ex post "is a form of meta-overfitting" — fix the protocol before fitting. — [LuxAlgo, Walk-forward analysis](https://www.luxalgo.com/library/concept/walk-forward-analysis/); [Backtrex, Walk Forward Analysis guide](https://backtrex.com/en/blog/walk-forward-analysis-guide-backtesting) (secondary; book not checked)
- Minimum trades rule of thumb: scalping needs 200–500+ trades (not a standard). — [ABC Trading Group, 8 Backtesting Pitfalls](https://www.abctradinggroup.com/backtesting-pitfalls/)
- Secondary: PBO and DSR are complementary — PBO checks rank stability across subsamples without distributional assumptions; DSR checks the SR clears a luck hurdle; "PBO also has no universal threshold." — [LuxAlgo, Probability of backtest overfitting](https://www.luxalgo.com/library/concept/probability-of-backtest-overfitting.md) (secondary)

### Inferences
- Minimum protocol for a solo developer: log every backtest run (parameters, result) so N is known; keep an untouched final holdout; use walk-forward with the window/step fixed in advance; run CPCV for ML models; compute DSR with the logged N and reject if DSR < 0.95; run PBO/CSCV on the parameter grid and reject if PBO > ~0.1–0.2 (threshold is a judgement call, none is canonical); check parameter plateaus (neighbouring parameters should perform similarly); Monte Carlo resample trade sequences to get drawdown distributions.
- Limit degrees of freedom: fewer than ~5 free parameters for a rule-based scalper; every additional parameter must be justified with a mechanism, not a backtest improvement.

### Gaps
- Could not read the DSR formula cleanly from the PDF (equation symbols lost in extraction); the paper's Eq. (1) gives E[max SR] as a function of V[SR] and N.
- Pardo's own numeric recommendations were not verified against the book.
- No primary source on Monte Carlo trade resampling or parameter-stability (plateau) tests was fetched.

---

## KQ11. Historical tick data sources and known quality issues

### Takeaway
For crypto, Tardis.dev (reconstructed L2 from exchange WebSocket feeds, 50+ exchanges) is the documented standard; for US futures/equities, Databento (MBO/MBP-10, nanosecond multi-timestamp); for FX, Dukascopy's SWFX ticks are widely used but quality evidence is anecdotal; MT5 broker tick history is convenient but gaps are filled with synthetic ticks and the "modelling quality %" measures tick density, not data quality.

### Cited Findings
- Tardis.dev: "tick-level historical and real-time cryptocurrency market data from 50+ exchanges"; order books are "tick-level order book snapshots reconstructed from exchanges' real-time WebSocket order book L2 data feeds"; normalization mappings are open source. — [Tardis.dev docs, order books FAQ](https://docs.tardis.dev/faq/order-books); [Tardis.dev](https://tardis.dev/)
- Databento: tick data across futures, options, equities, "70+ global trading venues"; L3 MBO and L2 MBP-10; "up to four timestamps per event, each in nanosecond resolution"; a flags field indicating data quality; a published guide on data integrity and cleaning for high-frequency data. — [Databento tick data](https://databento.com/tick-data); [Databento blog, Data integrity and cleaning](https://databento.com/blog/data-cleaning)
- Dukascopy: data source is "quotes in SWFX Marketplace (the ECN run by Dukascopy)"; one user calls it "quite high quality", others advise caution and filtering ticks where price does not change. — [EliteTrader thread, Interpreting Dukascopy Tick Data](https://elitetrader.com/et/threads/interpreting-dukascopy-tick-data.352792/) (anecdotal)
- MT5 real ticks: "the tester downloads real ticks from a broker's trade server"; "In case real ticks are absent for some time intervals, the tester simulates the price just like in the 'Every tick' mode"; real-tick test used 34,099,141 ticks vs 18,983,485 generated ticks; EURUSD H1 2016 example net profit −97.24 (real ticks) vs −466.81 (generated) with similar trade counts (156 vs 158); test time 74 s vs 36.7 s vs 1.6 s (1-minute OHLC). — [MQL5 article 2612, Testing on real ticks](https://www.mql5.com/en/articles/2612)
- Modelling quality caveat: the percentage "describes how densely the tester filled the intervals with ticks, not how good the underlying data is"; a 99% score "can sit on poor data". — [MQL5 blog 762517, Not all 99% backtests are equal](https://www.mql5.com/en/blogs/post/762517)
- Known MT5 tester errors with real ticks: "Real Ticks Discarded", "Price Mismatch", "Minutes Bars Absent". — [MQL5 forum thread 447280](https://www.mql5.com/en/forum/447280); [energyexch thread](https://www.energyexch.com/thread/676516-real-ticks-discarded-price-mismatch-minutes-bars-absent)
- Skeptical view (Dec 2025): tester ticks are algorithmic fill-ins, so even real-tick mode is not a perfect replay. — [MQL5 blog 765944, The truth about tick data in MT5 backtests](https://www.mql5.com/es/blogs/post/765944) (opinion)
- Imported third-party ticks (Tickstory) show 0% quality unless "every tick based on real ticks" mode is used and dates fall inside the exported range. — [Tickstory support thread](https://support.tickstory.com/viewtopic.php?p=7101)
- A competitor's comparison claims Tardis has 6+ years of tick history (competitor claim). — [CryptoHFTData vs Tardis](https://www.cryptohftdata.com/cryptohftdata-vs-competitors)

### Inferences
- Validate any tick source before use: check gap distribution (seconds between ticks per session), weekend/holiday boundaries, DST transitions in the vendor's timezone convention, spread distribution vs your live broker's spread, outlier ticks (price jumps > k × rolling std), and that bid/ask (not mid or last) are present.
- The live broker's own feed is the only feed that matches live spreads; backtesting on a different broker's/vendor's ticks is a known source of backtest-live divergence (see KQ14).

### Gaps
- No sourced information on TrueFX, Kibot, Tick Data LLC, Polygon, Binance/Bybit public historical dumps, or on DST/weekend/survivorship issues specific to each vendor.
- No head-to-head data-quality comparison exists in the sources found.

---

## KQ12. Backtesting frameworks and suitability for tick-level scalping

### Takeaway
Only hftbacktest (queue position + feed/order latency on L2/L3) and NautilusTrader (event-driven, L1/L2/L3 matching with probabilistic limit-fill/slippage models) model the execution details scalps depend on; vectorized tools (vectorbt) and bar-based engines are fine for idea screening but systematically overstate limit-order fills; MT5's real-tick mode is the right choice inside MetaTrader.

### Cited Findings
- hftbacktest features: queue-position-aware fills, feed and order latency models (`IntpOrderLatency`), queue models (`ProbQueueModel`, `PowerProbQueueModel3`, `RiskAverseQueueModel`, L3 FIFO), L2/L3 book reconstruction, tick-by-tick simulation; Python (Numba) backtest, Rust live for Binance Futures/Bybit. — [hftbacktest docs](https://hftbacktest.readthedocs.io/); [hftbacktest Rust crate models](https://docs.rs/crate/hftbacktest/0.9.4/source/src/backtest/models/mod.rs)
- NautilusTrader FillModel: `prob_fill_on_limit` (default 1.0) "controls whether a limit order fills when the market touches, but does not cross, its price"; `prob_slippage` (default 0.0) one-tick adverse move on L1; with L2/L3 "the recorded book supplies price levels and sizes" and the engine walks levels; `random_seed` for reproducibility; "Historical data cannot show how a simulated order would have interacted with other market participants"; with `liquidity_consumption=False` the same displayed size can fill multiple simulated orders; queue-volume tracking is a separate feature. — [NautilusTrader Fill Models](https://nautilustrader.io/docs/latest/concepts/backtesting/fill-models/)
- NautilusTrader backtest docs split execution realism into Fill Models, Fill Prices and Matching, Trade-Based Execution ("trade ticks, aggressor sides, and queues"), Bar-Based Execution ("OHLC sequencing, and bar timing"), Data and Venues (match data granularity with venue `book_type`). — [NautilusTrader Backtesting overview](https://nautilustrader.io/docs/latest/concepts/backtesting/)
- QuantConnect LEAN: full fills assumed in backtests; partial fills require a custom fill model (volume-share example caps each fill at 30% of previous second-bar volume); market orders can fill on stale data with warning. — [QuantConnect Trade Fills](https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/trade-fills/key-concepts)
- MT5 tester: "Every tick based on real ticks" recommended "for scalping, arbitrage, or strategies built on indices"; workflow: screen with "1 minute OHLC", debug with "Every tick", optimise on real ticks; "The faster the test, the lower the trading simulation accuracy." — [MQL5 article 2612](https://www.mql5.com/en/articles/2612)
- Backtrader: development "mostly stalled" (2026 comparison) / "doesn't seem very active" (Wilmott forum); broad features, live-trading support. — [tradesight blog, Python backtesting libraries 2026](https://rmbell09-lang.github.io/tradesight/blog/python-backtesting-libraries-2026.html); [Wilmott forum thread](https://forum.wilmott.com/viewtopic.php?p=876767) (secondary)
- vectorbt: open-source is "a work of a single developer, who puts his energy mainly into the Pro (paid) version"; vectorbt PRO self-describes as "high-performance, production-grade Python engine for backtesting"; speed claims unverified. — [Wilmott forum thread](https://forum.wilmott.com/viewtopic.php?p=876767); [vectorbt.pro getting started](https://vectorbt.pro/getting-started)
- backtesting.py: lightweight, beginner-friendly, no live broker connection, limited features. — [dev.to, Python backtesting frameworks compared](https://dev.to/pickuma/python-backtesting-frameworks-compared-backtrader-vectorbt-and-zipline-reloaded-41l8) (secondary)
- Freqtrade: once-per-candle decisions on DataFrames (unsuitable for tick scalping). — [CCXT docs, CCXT vs Freqtrade](https://docs.ccxt.com/docs/comparisons/ccxt-vs-freqtrade)
- Twenty-framework comparison (secondary, not fetched). — [AutoTradeLab, Nautilus vs vectorbt vs Freqtrade](https://hn.jakechampion.name/reader/https://autotradelab.com/blog/nautilus-vs-vectorbt-vs-freqtrade-20-python-quant-trading-frameworks-compared)

### Inferences
- Suitability matrix for scalping: hftbacktest — best for crypto L2 maker strategies (queue + latency), Rust live only; NautilusTrader — best general-purpose event-driven engine with same-code live adapters, set `prob_fill_on_limit` < 1 and `prob_slippage` > 0 on L1 data, or use L2 data with liquidity consumption; MT5 real-ticks — only option inside MT5, remember gaps are synthetically filled; vectorbt — research/screening only; Backtrader/backtesting.py/Zipline — bar-based, avoid for tick scalps; LEAN — good infrastructure, write a custom partial-fill model; Jesse/Freqtrade — candle-based, not for tick scalps.

### Gaps
- Jesse and Zipline-reloaded were not researched; Backtrader's actual commit status in 2026 was not verified against GitHub.
- NautilusTrader LatencyModel details were not found on the fetched pages.

---

## KQ13. Walk-forward → paper → live-minimum-size → scaling pipeline

### Takeaway
Practitioner guidance: paper-trading fills are systematically optimistic (first-touch limit fills, no partials, no latency, no rejects), so the demo phase is for validating plumbing and signal-vs-fill logging, not performance; go live at 10–20% of intended size and scale only when live slippage, fill rate and expectancy match backtest within tolerance over a meaningful trade count.

### Cited Findings
- Optimistic simulator fills: "Optimistic fill models fill your limit orders on first touch, and this is the default on many retail platforms and it systematically inflates your results"; pessimistic alternative requires price to trade one tick through the level; live, "your limit order fills when every order ahead of you in the queue has been filled AND an aggressive counter-order matches yours." — [NexusFi, Paper trading futures simulators](https://nexusfi.com/a/brokers/paper-trading-futures-simulators)
- Paper vs live: paper orders "always fill completely at the intended price"; live large orders "may fill partially across multiple price levels"; "network latency, broker processing times, and other factors are typically not present in simulated trading"; "there is no guarantee a live order will fill." — [TradersPost, Paper trading vs live results](https://blog.traderspost.io/article/paper-trading-vs-live-results); [dev.to, Paper vs live trading](https://dev.to/reyazk08/paper-trading-vs-live-trading-why-your-results-will-always-differ-4jei)
- Haircut and sizing: "if your paper strategy returns 10% annualised, plan for live performance to be lower"; start with "10-20% of your intended trading capital and scaling up based on consistent profitability." — [DayTradingToolkit, Paper-to-live transition](https://daytradingtoolkit.com/beginners-guide/paper-to-live-trading-transition) (practitioner)
- Use paper to verify "which account, symbol, size, and exit orders the app sends", logging paper and live executions separately. — [TradersPost, Paper trading strategy development guide](https://blog.traderspost.io/article/paper-trading-strategy-development-guide)
- Walk-forward protocol fixed in advance; WFE > 0.5; ≥ 5 OOS windows (secondary attribution to Pardo). — [LuxAlgo, Walk-forward analysis](https://www.luxalgo.com/library/concept/walk-forward-analysis/)
- NautilusTrader Sandbox context = real-time data with simulated execution, i.e., a built-in shadow mode. — [NautilusTrader Architecture docs](https://nautilustrader.io/docs/latest/concepts/architecture/)
- Minimum trades for scalping stats: 200–500+ (rule of thumb). — [ABC Trading Group, 8 Backtesting Pitfalls](https://www.abctradinggroup.com/backtesting-pitfalls/)
- NautilusTrader docs warn live introduces venue/transport/timing/reconciliation behaviour a simulation may not reproduce. — [NautilusTrader Overview](https://nautilustrader.io/docs/latest/concepts/overview/)

### Inferences
- Stage sequence with exit criteria (researcher synthesis, anchored to the above):
  1. Data validation → exit when gap/outlier/DST audits pass and backtest spread distribution matches live broker's.
  2. In-sample research with trial logging → exit when a candidate has ≥ 300 trades, parameter plateau, net edge ≥ 1.5× round-trip cost.
  3. Walk-forward (rolling, protocol fixed, ≥ 5 OOS windows) → exit when WFE ≥ 0.5 and every OOS window is not catastrophically negative.
  4. DSR/PBO/Monte Carlo → exit when DSR ≥ 0.95 given logged N, PBO low, Monte-Carlo 95th-percentile drawdown < max-drawdown limit.
  5. Shadow mode (real-time data, no orders; Nautilus "sandbox") ≥ 2 weeks → exit when signal timing/latency and would-be fills are logged with no plumbing bugs.
  6. Paper/demo ≥ 2–4 weeks → exit when order lifecycle, reconciliation, restarts and kill switches have been exercised (including a forced disconnect test).
  7. Live minimum size (10–20% of target, or exchange minimum lot) ≥ 100–200 trades → exit when realized slippage ≤ modelled slippage + tolerance, fill rate within 10–15% of backtest, expectancy sign matches.
  8. Scale in steps (e.g., double) only after each step repeats criterion 7; any kill-switch trip or metric breach resets to the previous step.

### Gaps
- No empirical study quantifying demo-vs-live fill differences for retail FX/CFD brokers was found; only practitioner claims.
- Durations/trade counts in the stage list are researcher defaults, not cited standards.

---

## KQ14. Common mistakes that make backtests misleading ("backtest lies")

### Takeaway
The sourced failure modes cluster into: information leakage (look-ahead, repainting, bar-close signals used intrabar), execution optimism (first-touch limit fills, full fills, no latency, no spread/slippage), data defects (synthetic ticks, gaps, wrong feed), and statistical abuse (multiple testing, too few trades, ex-post protocol choice).

### Cited Findings
- Look-ahead bias "can enter through data preparation, indicator calculations, portfolio selection, or order timing"; repainting indicators change output on closed bars. — [LuxAlgo, Backtesting traps](https://www.luxalgo.com/blog/backtesting-traps-common-errors-to-avoid/); [TradersPost, Pine Script backtesting limitations](https://blog.traderspost.io/article/pine-script-backtesting-limitations-and-validation)
- Limit fills assumed on touch vs needing to trade through; "if you place a limit order at 1.1050, you're behind every order already sitting at that level"; even a print at your price may not fill you. — [NexusFi, Backtest-to-live performance gap](https://nexusfi.com/a/automation/backtest-to-live-performance-gap); [NexusFi, Paper trading simulators](https://nexusfi.com/a/brokers/paper-trading-futures-simulators)
- OHLC bars hide intrabar path: "A 15-minute bar tells you four numbers"; stop and target inside one bar cannot be ordered. — [ABC Trading Group, 8 Backtesting Pitfalls](https://www.abctradinggroup.com/backtesting-pitfalls/)
- NautilusTrader defaults: `prob_fill_on_limit` = 1.0 and `prob_slippage` = 0.0, i.e., optimistic unless changed; historical data cannot show interaction with other participants. — [NautilusTrader Fill Models](https://nautilustrader.io/docs/latest/concepts/backtesting/fill-models/)
- LEAN: full fills assumed; stale-data market fills. — [QuantConnect Trade Fills](https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/trade-fills/key-concepts)
- MT5: generated "Every tick" uses virtual ticks from M1 bars; real-tick mode fills gaps synthetically; modelling-quality % ≠ data quality; discarded ticks / price mismatch / missing M1 bars errors. — [MQL5 article 2612](https://www.mql5.com/en/articles/2612); [MQL5 blog 762517](https://www.mql5.com/en/blogs/post/762517); [MQL5 forum 441266](https://www.mql5.com/en/forum/441266)
- Scalping backtest profitable only with zero slippage; fixed-tick slippage may understate costs. — [dev.to, 5 backtesting mistakes](https://dev.to/qcautomation/5-backtesting-mistakes-that-make-your-algo-look-like-a-money-printer-until-it-isnt-2kf1); [LuxAlgo, slippage and liquidity](https://www.luxalgo.com/blog/backtesting-limitations-slippage-and-liquidity-explained/)
- Multiple testing guarantees false positives; selection bias from unreported trials. — [Bailey & López de Prado, DSR](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf)
- Ex-post choice of walk-forward variant is meta-overfitting. — [LuxAlgo, Walk-forward analysis](https://www.luxalgo.com/library/concept/walk-forward-analysis/)
- Sample size: scalping needs 200–500+ trades. — [ABC Trading Group](https://www.abctradinggroup.com/backtesting-pitfalls/)
- Forex-specific pitfalls article (spread, session, data issues). — [FXReplay, Common pitfalls in forex backtesting](https://www.fxreplay.com/learn/common-pitfalls-in-forex-backtesting-and-how-to-avoid-them?aff=blog) (not fetched in full)

### Inferences
- "Backtest lies" checklist (sourced items marked S; unsourced-but-standard items marked U):
  - S Look-ahead: any feature using the current bar's close/high/low before the bar closes; repainting indicators; future-shifted joins.
  - S Signal at bar close but entry assumed at bar open/close of the same bar.
  - S Mid or last price used for fills instead of bid for sells / ask for buys (ignores spread).
  - S Limit orders filled on touch (set prob_fill_on_limit < 1 or require trade-through); no queue position.
  - S Full fills always (no partials), no rejects, no latency between signal and order.
  - S Stop and target in the same bar resolved optimistically.
  - S Zero or fixed-tick slippage; no volatility/size-dependent slippage.
  - S Synthetic ticks (MT4/MT5 "Every tick"), gaps filled synthetically; trusting modelling-quality %.
  - S Backtest feed ≠ live broker feed (different spreads/ticks).
  - S Too few trades (< 200–500 for scalps); parameters chosen by grid without logging trial count; DSR/PBO not computed.
  - S Walk-forward protocol or window chosen after seeing results.
  - U Ignoring swap/funding/rollover, session gaps, holiday/weekend boundaries, DST shifts.
  - U Tick volume treated as real volume in FX.
  - U Ignoring broker minimum stop distance, margin/PDT constraints, and market impact in thin crypto books.
  - U Survivorship bias in instrument selection (less relevant to a single-pair scalper, relevant to crypto pair universes).

### Gaps
- Survivorship, DST/timezone, FX tick-volume, swap/funding, PDT/margin and market-impact items were not supported by sources found in this research (listed as U above).

---

## Deliverable A. Reference architecture component list (responsibilities + suggested tech)

### Takeaway
Component layout mirrors NautilusTrader's kernel; a solo developer should implement at most the strategy, feature and venue-adapter layers and reuse a framework for the rest.

### Cited Findings
- Component responsibilities taken from NautilusTrader (DataEngine, ExecutionEngine, RiskEngine, Cache, MessageBus, Portfolio, Trader, Kernel) and its single-thread core / async I/O model. — [NautilusTrader Architecture docs](https://nautilustrader.io/docs/latest/concepts/architecture/)
- LMAX single-threaded business logic with journaling/replication as separate consumers. — [Martin Fowler, The LMAX Architecture](https://www.martinfowler.com/articles/lmax.html)
- Inference runtime benchmarks (ONNX Runtime ~11 µs, lleaves ~10 µs, LightGBM ~52 µs single-row). — [lleaves benchmarks](https://www.github.com/siboehm/lleaves)
- Post-trade store with ASOF joins / Parquet. — [QuestDB cookbook, slippage](https://questdb.com/docs/cookbook/sql/finance/slippage/)
- Independent watchdog via systemd + API flatten. — [qgtm-docs DMS independence](https://qgtm-docs.pages.dages.dev/audit/DMS_INDEPENDENCE/)

### Inferences
| Component | Responsibility | Hot/cold | Suggested tech (retail) |
|---|---|---|---|
| Market data adapter | WebSocket/FIX/MT5 feed → normalized tick/book events with exchange + local timestamps; gap/stale detection | Hot | Python asyncio websockets / ccxt.pro, Nautilus adapter, MT5 Python API; Rust only if L2 at high rates |
| Message bus | Pub/sub between components, deterministic ordering, replayable | Hot | In-process queue (Nautilus msgbus), asyncio.Queue; Redis only for cross-process |
| Feature/signal engine | Rolling features (microstructure, volatility, spread), model inference, signal events | Hot | numpy/numba; LightGBM via ONNX Runtime/lleaves; rules in plain Python |
| Risk engine | Synchronous pre-trade checks (KQ9 list), rate limits, daily/drawdown gates, kill-switch latch | Hot | Pure Python module with unit tests; Nautilus RiskEngine config |
| Execution engine / venue adapter | Order state machine, client order ids, submit/cancel/modify, fill handling, reconciliation | Hot | Nautilus ExecutionEngine + adapter, or hand-written with idempotent ids |
| Portfolio/cache | Positions, balances, exposure, PnL from events | Hot (in-memory) | In-memory dict/dataclasses; snapshot to SQLite/Redis |
| Persistence | Append-only ticks, decisions, orders, fills, snapshots | Cold | Parquet per day (Polars/DuckDB), or QuestDB/ClickHouse/TimescaleDB |
| Monitoring/alerting | Metrics, heartbeat, dashboards, alerts | Cold | Prometheus client + Grafana; Telegram/Discord bot; healthchecks-style dead-man's switch |
| Watchdog | Independent process; cancels/flattens if heartbeat stale; separate API key limited to cancel/close | Separate process | systemd service, small Python script |
| Research/backtest | Same strategy code on historical ticks; fill/latency models; WFA, CPCV, DSR | Offline | NautilusTrader backtest node / hftbacktest; MT5 tester real ticks |
| Deployment | Service management, restart policy, secrets, version pinning | — | VPS near venue, systemd or Docker, env-file secrets, version hash logged at start |

### Gaps
- Tech suggestions are researcher judgement; no source ranks retail deployment stacks.

---

## Deliverable B. Risk-rule checklist with example numeric defaults

### Takeaway
Defaults below are derived from FTMO limits (sourced), 15c3-5 control categories (sourced) and practitioner heartbeat/kill-switch rules (sourced); the numbers themselves are researcher proposals to be tuned to the strategy's trade frequency.

### Cited Findings
- FTMO: 3–5% daily loss on equity incl. floating PnL, 10% max loss, midnight CE(S)T reset. — [FTMO Trading Objectives](https://ftmo.com/en/trading-objectives/)
- 15c3-5: pre-trade automated capital/credit thresholds, erroneous/duplicate order prevention. — [SEC Order 34-70694](https://www.sec.gov/files/litigation/admin/2013/34-70694.pdf); [FINRA Market Access Rule](https://finra.org/rules-guidance/guidance/reports/2026-finra-annual-regulatory-oversight-report/market-access-rule)
- Heartbeat 30 s → flatten; 300 s in-process DMS + external systemd watchdog; persisted trip file. — [NexusFi emergency protocols](https://nexusfi.com/a/automation/automated-trading-emergency-protocols); [qgtm-docs](https://qgtm-docs.pages.dev/audit/DMS_INDEPENDENCE/)
- Fractional Kelly as ceiling; hard per-position cap. — [MacLean/Thorp/Ziemba, Good and bad properties of Kelly](https://www.stat.berkeley.edu/~aldous/157/Papers/Good_Bad_Kelly.pdf)
- Break-even with costs (1+c)/(1+R). — [MQL5 blog 779062](https://www.mql5.com/en/blogs/post/779062)

### Inferences
- Position sizing: risk per trade 0.1–0.5% of equity (default 0.25%); size = risk$ / (stop distance incl. spread); cap ≤ min(¼ Kelly from live stats, 2% of equity notional-risk); max net exposure per instrument and total (e.g., 3× and 5× one standard position).
- Stops: soft stop on every tick; hard broker stop at 1.5–2× soft; time stop (e.g., 5–15 min for a scalp); no trailing until ≥ 1R.
- Loss limits: daily soft 2% (no new entries), hard 3% (flatten + lock to next session); weekly 5%; peak-to-trough 8% (halt, manual review); max consecutive losses 6–8 → 30–60 min cool-off; equity-curve throttle halves size after a losing 20-trade window.
- Pre-trade checks (all synchronous, reject on failure): max order qty; max notional/order; price collar (e.g., ±25 bps from mid for a liquid FX/crypto major); duplicate id/signature in 1 s; max 5 orders/s and 60/min; max open positions (e.g., 1–3); margin check; stale data (no entries if last tick > 2–5 s old for liquid instruments, flatten if > 30–60 s); connectivity (no entries while reconnecting; flatten via watchdog after heartbeat > 30–60 s).
- Kill switch: trip on any hard limit, reject burst (e.g., > 5 rejects/min), reconciliation mismatch, feed stale, version mismatch; action = cancel all, flatten, disable entries, write latch file, alert; manual reset only.
- Cost gate: strategy enabled only if measured live expectancy ≥ 1.5× measured round-trip cost over the last N trades.

### Gaps
- All specific numbers above beyond the FTMO percentages and the 30 s/300 s heartbeat examples are unsourced proposals.

---

## Deliverable C. Testing pipeline sequence with exit criteria

### Takeaway
See KQ13 Inferences for the eight-stage sequence (data validation → in-sample with trial logging → walk-forward → DSR/PBO/Monte Carlo → shadow mode → paper → live minimum size → stepwise scaling), each with a stated exit criterion; the sourced anchors are Pardo's walk-forward conventions (secondary), DSR/PBO (primary), paper-fill optimism (practitioner) and the 10–20% initial live sizing (practitioner).

### Cited Findings
- (Consolidated from KQ10 and KQ13.) — [Bailey & López de Prado, DSR](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf); [SSRN 2326253 PBO](https://papers.ssrn.com/abstract=2326253); [LuxAlgo, Walk-forward analysis](https://www.luxalgo.com/library/concept/walk-forward-analysis/); [NexusFi, Paper trading simulators](https://nexusfi.com/a/brokers/paper-trading-futures-simulators); [DayTradingToolkit, Paper-to-live](https://daytradingtoolkit.com/beginners-guide/paper-to-live-trading-transition); [MQL5 article 2612 (screen→debug→real-tick workflow)](https://www.mql5.com/en/articles/2612)

### Inferences
- Add a chaos-test gate before live: kill the process mid-position, drop the network, send a duplicate fill, replay a stale snapshot, and confirm the watchdog flattens and the restart reconciles without placing new orders.

### Gaps
- No source prescribes stage durations; defaults are researcher proposals.

---

## Deliverable D. "Backtest lies" checklist

### Takeaway
See KQ14 Inferences for the consolidated checklist (items marked S are sourced, U are standard practice without a source found in this research).

### Cited Findings
- (Consolidated in KQ14.)

### Inferences
- Treat any backtest that has not been re-run with pessimistic fill settings (limit fills on trade-through only, ≥ 1-tick adverse slippage, latency ≥ measured live round-trip) as an upper bound, not an estimate.

### Gaps
- As listed in KQ14.
