# Hybrid "rule-based trigger + ML meta-label filter": evidence, NautilusTrader implementation, and validation/go-live criteria (as of Nov 2026)

Source rating legend used below: [A] primary/peer-reviewed or official source code/docs; [B] working paper or practitioner write-up with data; [C] vendor/blog/forum or search-snippet only (opinion). COI = conflict of interest.

Research method note: NautilusTrader API names below were checked directly against the source files on GitHub (branch `develop_v1`, whose `pyproject.toml` reads `version = "1.231.0"`) and against `MIGRATION_V2.md` on `develop`. They were not executed. Meta-labeling papers in the Journal of Financial Data Science (JFDS) are paywalled. Their findings come from abstracts or repository summaries unless a figure is quoted.

---

## 1. Evidence for meta-labeling (López de Prado; Joubert; Meyer/Barziy/Joubert; Hudson & Thames; independent tests)

### Takeaway
The published evidence that meta-labeling improves out-of-sample results comes almost entirely from Hudson & Thames-affiliated authors, who sell mlfinlab and so have a COI. It is mostly synthetic data or daily/bar-level E-mini tests reporting small precision gains: +0.03 to +0.06 OOS precision in the one study with numbers. Independent practitioner tests are anecdotal and mixed to negative. I found no rigorous, independent, minute-horizon study that quantifies a Sharpe improvement. Overall rating: **weak to moderate, unproven at intraday horizons, plausible mechanism.**

### Cited Findings
- **Definition and origin.** Meta-labeling comes from López de Prado, *Advances in Financial Machine Learning* (Wiley, 2018), ch. 3: §3.6 "Meta-labeling" and §3.4 "The triple-barrier method". Bet sizing is ch. 10: 10.3 "Bet Sizing from Predicted Probabilities" (p.142), 10.4 "Averaging Active Bets" (p.144), 10.5 "Size Discretization" (p.144). — [AFML table of contents](https://toc.uni.li/FLMF049641.pdf) [A]
- **How it works.** A primary model (here, a rule) sets the **side**. A secondary binary classifier learns whether that side will hit the profit barrier (label 1) or not (label 0), and its probability sets **whether to trade and how much**. Singh & Joubert put it this way for the SMA strategy: "The meta-labeling function decides on the size (to trade or not to trade)." — [Singh & Joubert, "Does Meta-Labeling Add to Signal Efficacy?" (Hudson & Thames PDF)](https://hudsonthames.org/wp-content/uploads/2022/04/Does-Meta-Labeling-Add-to-Signal-Efficacy.pdf) [B, COI]
- **Singh & Joubert, data and design.**
  - Data: S&P 500 E-mini tick data from Tick Data LLC (about $750), 1 Jul 2011 to 13 Feb 2019.
  - Bars and events: information-driven bars, CUSUM-filter events, triple-barrier labels with horizontal barriers from daily standard deviation.
  - Model: Random Forest, with up-sampling because "meta-labeling often resulted in unbalanced classes".
  - Primary models: a Bollinger-band mean-reversion rule and a 20/50-bar SMA cross.
  - Features (trend strategy): 50/31/15-bar rolling volatility, 1–5-day autocorrelation, 1–5-day momentum.
  - Data splits: train, validation, and a separate OOS set "never used in the training".
  - Leakage risk: the authors "manually tuned a few parameters", including the CUSUM threshold. — [same PDF](https://hudsonthames.org/wp-content/uploads/2022/04/Does-Meta-Labeling-Add-to-Signal-Efficacy.pdf) [B, COI]
- **Singh & Joubert, numbers.**

  | Strategy | Validation | Out of sample |
  |---|---|---|
  | Mean reversion | precision 0.21 → 0.39; accuracy 20% → 77% | precision **0.17 → 0.20**; accuracy 17% → 63% |
  | Trend following | precision 0.37 → 0.42; accuracy 37% → 56% | precision **0.48 → 0.54**; accuracy 48% → 55% |

  The authors say trend following "doesn't outperform on all the metrics however it does outperform on a risk adjusted basis". The Sharpe and drawdown tables for 2018-01 to 2019-01 are images that did not survive text extraction. The authors note there is no bet-sizing component and that the primary signals "don't provide the best signals". — [same PDF](https://hudsonthames.org/wp-content/uploads/2022/04/Does-Meta-Labeling-Add-to-Signal-Efficacy.pdf) [B, COI]
- **Joubert (2022), "Meta-Labeling: Theory and Framework".** JFDS 4(3): 31–44, DOI 10.3905/jfds.2022.1.043. It consolidates earlier work, "links binary classification metrics to strategy performance", and splits meta-labeling into three components. A controlled experiment, reported to be on synthetic data, shows how each component improves strategy metrics. No effect sizes were retrievable. — [hudson-and-thames/meta-labeling repo](https://github.com/hudson-and-thames/meta-labeling) [A-abstract, COI]; bibliographic details from [Wikipedia draft mirror](https://wikiless.lunar.icu/wiki/Draft:Meta-Labeling?lang=en) [C]
- **Meyer, Joubert & Alfeus (2022), "Meta-Labeling Architectures".** JFDS, Fall 2022. Proposes heterogeneous architectures, compares feature-driven and strategy-driven designs, and introduces "inverse meta-labeling" to improve the quantity and quality of side forecasts. — [repo](https://github.com/hudson-and-thames/meta-labeling) [A-abstract, COI]
- **Meyer, Barziy & Joubert (2023), "Meta-Labeling: Calibration and Position Sizing".** JFDS 5(2): 23–40. Compares six position-sizing algorithms, including the new "sigmoid optimal position sizing", using calibrated and uncalibrated probabilities. Calibration significantly improves **fixed** sizing functions. Methods that **estimate** their sizing function from training data gain nothing significant from calibration. Metrics are Sharpe and maximum drawdown; no numbers were retrievable. — [repo](https://github.com/hudson-and-thames/meta-labeling) [A-abstract, COI]
- **Thumm, Barucca & Joubert (2022), "Ensemble Meta-Labeling".** JFDS, Winter 2022. Quote: "ensembles are especially beneficial when the underlying data consist of multiple regimes." — [repo](https://github.com/hudson-and-thames/meta-labeling) [A-abstract, COI]
- **Vendor claim about overfitting.** Hudson & Thames argue overfitting effects are limited "because ML will not decide the side of your bet, only the size". Their toy example uses MNIST, not market data. — [Hudson & Thames, "Meta Labeling (A Toy Example)"](https://hudsonthames.org/meta-labeling-a-toy-example/) [C, COI]
- **Independent, skeptical test 1.** Francesco Baldisserri on QuantConnect ran a grid over `use_meta` ∈ {0,1} across seeds. The performance range widened but the **average Sharpe was lower with the meta-model**. His point is that a meta-model trained on the same features as an ML primary "cannot squeeze the same orange twice". He concludes it is useful mainly for sizing existing discretionary or rule-based strategies. — [QuantConnect forum, "why meta labeling is not a silver bullet"](https://www.quantconnect.com/forum/discussion/14706/why-meta-labeling-is-not-a-silver-bullet/) [C]
- **Independent, skeptical test 2.** In the same thread:
  - Lars Klawitter: meta-labeling on an ExtraTrees strategy performed "significantly worse" (no numbers).
  - Adam W: "limited success" at high compute cost.
  - Michael Meyer (a JFDS co-author, so COI) advised using a different model class for the meta-model, applying it to **high-recall** primaries, adding regime features, and sizing with calibrated probabilities. — [same thread](https://www.quantconnect.com/forum/discussion/14706/why-meta-labeling-is-not-a-silver-bullet/) [C]
- **Academic, 2025.** Isufaj, Mollá & Prendinger (arXiv:2510.26353, XAIFIN'25) use a reliability estimator, "Corrective AI" in the meta-labeling sense, on a Time-LLM primary for equity and crypto data. The abstract claims it "reduces false positives and supports selective execution" but gives no numbers. — [arXiv 2510.26353](https://arxiv.org/abs/2510.26353) [B]
- **Crypto and intraday.** Searches found:
  - crypto papers using triple-barrier labels plus deep learning (best OOS Sharpe about 2.0 and 1.9), but they do **not** isolate a meta-labeling layer — [ResearchGate: information-driven bars, triple-barrier, DL](https://www.researchgate.net/publication/398702027_Algorithmic_crypto_trading_using_information-driven_bars_triple_barrier_labeling_and_deep_learning) [B, from search snippet];
  - a 16-asset study in which triple-barrier labeling as a baseline averaged a Sharpe of −0.03 — [MDPI Applied Sciences 15(24):13204](https://www.mdpi.com/2076-3417/15/24/13204) [B, from search snippet];
  - Medium and MQL5 blog posts with informal claims — [Medium crypto meta-labeling](https://medium.com/@liangnguyen612/meta-labeling-in-cryptocurrencies-market-95f761410fac) [C]; [MQL5 "Meta-Labeling the Classics (Part 1)"](https://www.mql5.com/en/articles/22274) [C].

### Inferences
- **Size of the effect.** The only quantified OOS gains are small precision improvements (+3 to +6 points), and accuracy jumps mostly reflect the filter predicting "no trade" for a minority-positive class. The report should treat meta-labeling as a **false-positive filter and sizing layer**, not a source of alpha. It needs a primary trigger with real but noisy edge (high recall, modest precision).
- **Why accuracy misleads.** Accuracy rising from 17% to 63% while precision moves only 0.17 → 0.20 means most of the "improvement" is correctly skipping losing trades. That is valuable only if precision × payoff after costs clears break-even. At minute horizons, fees and spread dominate, so judge the filter on **net expectancy per trade and profit factor after costs**, not on accuracy or F1.
- **Evidence rating for the report.** Mechanism: plausible and well defined. Peer-reviewed evidence: exists, but COI-heavy, mostly synthetic or daily-bar, with effect sizes not public. Independent replication: none rigorous; anecdotes are mixed to negative. Intraday or minute evidence: essentially none found.
- **Where it is most likely to help.** Rule-based (non-ML) primaries, which is exactly the hybrid design. Features should carry information the rule does not use (volatility regime, spread, order-flow imbalance, time of day), consistent with the Baldisserri and Meyer remarks.

### Gaps
- Effect sizes (Sharpe or drawdown deltas) from Joubert (2022), Meyer et al. (2023) and Thumm et al. (2022) are behind the JFDS paywall and could not be retrieved.
- The Singh & Joubert Sharpe and drawdown tables are images and did not extract.
- No independent peer-reviewed minute-bar meta-labeling study was found. No Robot Wealth or QuantConnect study with numeric minute-horizon results was found.

---

## 2. Best-practice design of the meta-label model at minute horizons (labels, features, CV, weights, calibration, bet sizing)

### Takeaway
The standard recipe has six parts:
- triple-barrier labels with volatility-scaled profit-take and stop-loss barriers and a vertical (time) barrier, applied only at trigger events;
- features that are orthogonal to the trigger;
- purged and embargoed (or combinatorial purged) CV;
- sample-uniqueness weights;
- isotonic or Platt calibration;
- probability-to-size mapping m = 2Φ(z) − 1, with averaging and discretization.

Most of this is from AFML. Minute-specific feature evidence is practitioner-level.

### Cited Findings
- **Triple-barrier labeling.** Horizontal barriers are scaled to recent volatility; Singh & Joubert used daily standard deviation. Events are sampled with a CUSUM filter so labels are not generated on every bar; Singh & Joubert say the filter "prevents multiple events from getting generated". — [Singh & Joubert PDF](https://hudsonthames.org/wp-content/uploads/2022/04/Does-Meta-Labeling-Add-to-Signal-Efficacy.pdf) [B]
- **Bet sizing from probability (AFML Snippet 10.1).**
  - Clip p to [1e-6, 1 − 1e-6].
  - z = (p − 1/n) / √(p(1−p)), with n = 2 for binary.
  - size m = 2·Φ(z) − 1, multiplied by side.
  - Then average across active bets and discretize: `signal1 = (signal0 / step_size).round() * step_size`.

  One MQL5 article uses a simpler linear map, clip((p − 0.5)/0.5, 0, 1), so check which one is intended. — [MQL5 "ML Blueprint Part 10: Bet Sizing"](https://www.mql5.com/en/articles/21824) [C, reproduces AFML ch.10]; [AFML TOC](https://toc.uni.li/FLMF049641.pdf) [A]
- **Why discretize.** Continuous resizing of an averaged signal produces micro-adjustments whose transaction cost exceeds their expected P&L. — [MQL5 Part 10](https://www.mql5.com/en/articles/21824) [C]
- **Calibration.** It matters for fixed sizing functions such as Φ-based or linear maps. Learned sizing functions do not benefit significantly. — [hudson-and-thames/meta-labeling](https://github.com/hudson-and-thames/meta-labeling) [A-abstract, COI]
- **Model diversity and regimes.** Use a different model class for the meta-model than for the primary, include regime features, and target high-recall primaries. — [QuantConnect thread, M. Meyer reply](https://www.quantconnect.com/forum/discussion/14706/why-meta-labeling-is-not-a-silver-bullet/) [C, COI]. Ensembles help in multi-regime data. — [repo](https://github.com/hudson-and-thames/meta-labeling) [A-abstract]
- **Class imbalance.** Label 0 dominates. Singh & Joubert up-sampled; class weights are the alternative. — [Singh & Joubert PDF](https://hudsonthames.org/wp-content/uploads/2022/04/Does-Meta-Labeling-Add-to-Signal-Efficacy.pdf) [B]
- **Purged and embargoed CV, uniqueness weights, CPCV.** These are AFML ch. 4 (sample weights / average uniqueness), ch. 7 (purged k-fold with embargo) and ch. 12 (CPCV). Chapter structure is per [AFML TOC](https://toc.uni.li/FLMF049641.pdf) [A]. The definitions below are from the book as I know it, not re-fetched this session:
  - **Purging** removes training samples whose label interval [t0, t1] overlaps any test sample's label interval.
  - **Embargo** additionally drops training samples within h bars after each test block; AFML suggests h ≈ 0.01·T.
  - **Average uniqueness** of a label is the mean over its life of 1 / (number of concurrent labels). Use it as a sample weight and in sequential bootstrap.
  - **CPCV** splits data into N groups and tests on k at a time, giving C(N, k) splits and φ = (k/N)·C(N, k) full backtest paths. Example: N=6, k=2 gives 15 splits and 5 paths.

### Inferences
Minute-bar recipe for the report (synthesis, not sourced as tested):
- **Events.** One label per rule trigger. Vertical barrier at 15–60 bars. Profit-take and stop-loss at k·σ, where σ is an EWMA of 1-minute returns (for example span 60–100) scaled by √holding-period, k ≈ 1–2. Include round-trip fees and half-spread in the barrier P&L so label 1 means "net profitable".
- **Features**, all known at t0:
  - realized-volatility ratios (short/long);
  - ATR/price;
  - bid-ask spread in ticks;
  - L1 order-book imbalance and trade-flow OFI over 1–5 minutes;
  - signed volume / VPIN-like toxicity;
  - time-of-day and day-of-week dummies (sin/cos encoded), with session flags for CME RTH/ETH or crypto Asia/EU/US;
  - funding rate and basis for perpetuals;
  - distance to VWAP;
  - trend regime (ADX or efficiency ratio);
  - rolling hit-rate and P&L of the last N triggers (lagged, so no leakage of open trades);
  - the trigger's own strength.
- **Model.** Gradient-boosted trees or Random Forest with monotone-constraints sanity checks. Calibrate with isotonic regression on a purged hold-out fold inside each training window.
- **Decision rule.** Trade only if calibrated p > p* where p*·avg_win − (1−p*)·avg_loss − costs > 0. Size with m = 2Φ(z) − 1, capped by the risk-per-trade cap.

### Gaps
- No sourced minute-horizon feature-importance study specific to meta-labeling was found.
- The exact AFML equations for uniqueness, embargo and CPCV were not re-verified from a primary text this session; the report writer should cite AFML ch. 4/7/12 directly.

---

## 3. NautilusTrader implementation: version, Strategy API, indicators, orders, events, timers, official example patterns

### Takeaway
As of Nov 2026 there are two parallel lines:
- **Stable v1 (Cython): `nautilus_trader==1.231.0`**, the latest non-prerelease on PyPI, published 2026-08-02. Code lives on branch `develop_v1`.
- **v2 (Rust core + PyO3): `2.0.0rc9`**, a pre-release from 2026-11-10, on `develop`. It renames many Strategy methods.

Write the skeleton against **1.231.0** and provide a v2 rename table. All API names below were verified in the v1 source.

### Cited Findings
**Versions and the v1/v2 split**
- PyPI timeline: 1.224.0 (2026-03-03) … 1.230.0 (2026-06-29), 1.231.0 (2026-08-02), then 2.0.0rc3 (2026-08-21) through rc9 (2026-11-10). `pip install nautilus_trader` resolves to 1.231.0; v2 needs `--pre`. — [PyPI nautilus_trader](https://pypi.org/project/nautilus_trader/) [A]
- `MIGRATION_V2.md` says:
  - v1 lives on `develop_v1` and "receives only critical security backports for approximately three months after the v2 cutover";
  - "Both versions install and import as `nautilus_trader`. Use separate virtual environments";
  - v2 installs with `uv pip install --pre nautilus_trader` (Python 3.14 shown). — [MIGRATION_V2.md](https://github.com/nautechsystems/nautilus_trader/blob/develop/MIGRATION_V2.md) [A]
- **v2 renames.**
  - Handlers and subscriptions: `on_quote_tick`→`on_quote`, `on_trade_tick`→`on_trade`, `on_order_book_deltas`→`on_book_deltas`, `subscribe_quote_ticks`→`subscribe_quotes`, `subscribe_trade_ticks`→`subscribe_trades`, `subscribe_order_book_deltas`→`subscribe_book_deltas`, `request_quote_ticks`→`request_quotes`, `cache.quote_tick`→`cache.quote`.
  - Imports: `nautilus_trader.backtest.engine.BacktestEngine`→`nautilus_trader.backtest.BacktestEngine`, `nautilus_trader.live.node.TradingNode`→`nautilus_trader.live.LiveNode`, `nautilus_trader.model.enums.OrderSide`→`nautilus_trader.model.OrderSide`.
  - Backtest models: v2 drops the `Importable*ModelConfig` wrappers; construct `ProbabilisticFillModel`, `FixedFeeModel`, `StaticLatencyModel` directly.
  - Leverage: an omitted backtest `default_leverage` now gives 10x for margin accounts. Set `Decimal(1)` to keep v1 behavior. — [MIGRATION_V2.md](https://github.com/nautechsystems/nautilus_trader/blob/develop/MIGRATION_V2.md) [A]
- **v2 rc breaking changes.**
  - rc5: `TradingState` values changed (ACTIVE=1, REDUCING=2, HALTED=3), and REDUCING "allows only eligible reduce-only submissions, cancels, and queries".
  - rc6: instrument `maker_fee`/`taker_fee` removed; set rates on the venue `fee_model`.
  - rc7: `BacktestNode` batches book deltas by default (`batch_deltas=False` to opt out).
  - rc8: `add_venue()` argument order changed, so pass models by keyword; "HALTED denies stops; use REDUCING for eligible exits".
  - rc9: Binance REST blocks on HTTP 418; Bybit `modify_order` takes `trigger_price`. — [GitHub releases](https://github.com/nautechsystems/nautilus_trader/releases) [A]

**Strategy structure (v1.231.0)**
- **Config fields.** `StrategyConfig` (frozen msgspec) has: `strategy_id`, `order_id_tag`, `oms_type`, `external_order_claims`, `manage_contingent_orders: bool = False`, `manage_gtd_expiry: bool = False`, `manage_stop: bool = False`, `market_exit_interval_ms = 100`, `market_exit_max_attempts = 100`, `market_exit_time_in_force = GTC`, `market_exit_reduce_only = True`, `log_events`, `log_commands`. — [trading/config.py (develop_v1)](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/trading/config.py) [A]
- **Lifecycle and event hooks** (`cdef class Strategy(Actor)`):
  - lifecycle: `on_start`, `on_stop`, `on_resume`, `on_reset`;
  - order events: `on_order_event`, `on_order_denied`, `on_order_rejected`, `on_order_accepted`, `on_order_canceled`, `on_order_expired`, `on_order_triggered`, `on_order_filled`, `on_order_modify_rejected`, `on_order_cancel_rejected`;
  - position events: `on_position_opened`, `on_position_changed`, `on_position_closed`;
  - market exit: `on_market_exit`, `post_market_exit`.
- **Commands:**
  - `submit_order(order, position_id=None, client_id=None, params=None)`
  - `submit_order_list(...)`
  - `modify_order`, `cancel_order`, `cancel_orders`, `cancel_all_orders`
  - `close_position(position, client_id=None, tags=None, time_in_force=GTC, reduce_only=True, quote_quantity=False, params=None)`
  - `close_all_positions(instrument_id, position_side=NO_POSITION_SIDE, ..., reduce_only=True)`
  - `market_exit()`, `is_exiting()`, `query_account`, `query_order`, `cancel_gtd_expiry`

  `market_exit()` "will cancel all open orders and close all open positions, and wait for all in-flight orders to resolve… The strategy remains running." — [trading/strategy.pyx (develop_v1)](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/trading/strategy.pyx) [A]
- **Bracket orders.** `order_factory.bracket(instrument_id, order_side, quantity, quote_quantity=False, emulation_trigger=TriggerType.NO_TRIGGER, trigger_instrument_id=None, contingency_type=ContingencyType.OUO, ...)` returns an `OrderList`. Its keyword groups are:
  - entry: `entry_order_type=OrderType.MARKET`, `entry_price`, `entry_trigger_price`, `expire_time`, `time_in_force=GTC`, `entry_post_only=False`, `entry_tags`;
  - take-profit: `tp_order_type=OrderType.LIMIT`, `tp_price`, `tp_trigger_price`, `tp_trigger_type`, trailing options, `tp_time_in_force=GTC`, `tp_post_only=True`, `tp_tags`;
  - stop-loss: `sl_order_type=OrderType.STOP_MARKET`, `sl_trigger_price`, `sl_trigger_type`, trailing options, `sl_time_in_force=GTC`.

  The TP/SL pair is OUO (one-updates-other), which behaves like OCO, and is OTO-linked to the entry. — [common/factories.pyx (develop_v1)](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/common/factories.pyx) [A]
- **Timers.**
  - `clock.set_timer(name, interval: timedelta, start_time=None, stop_time=None, callback=None, allow_past=True, fire_immediately=False)`
  - `clock.set_time_alert(name, alert_time: datetime, callback=None, override=False, allow_past=True)`
  - `set_time_alert_ns(...)`

  These are what time stops and session-flat logic use. — [common/component.pyx (develop_v1)](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/common/component.pyx) [A]
- **Portfolio queries.** `account`, `balances_locked`, `equity`, `is_flat`, `is_completely_flat`, `is_net_long`, `is_net_short`, `net_position`, `net_exposure(s)`, `realized_pnl(s)`, `unrealized_pnl(s)`, `total_pnl(s)`, `margins_init`, `margins_maint`, `mark_values`. — [portfolio/portfolio.pyx (develop_v1)](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/portfolio/portfolio.pyx) [A]
- **Position sizer.** `FixedRiskSizer(instrument).calculate(entry: Price, stop_loss: Price, equity: Money, risk: Decimal, commission_rate=Decimal(0), exchange_rate=Decimal(1), hard_limit=None, ...)` returns a `Quantity`. — [risk/sizing.pyx (develop_v1)](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/risk/sizing.pyx) [A]
- **Indicators** (`from nautilus_trader.indicators import ...`): `ExponentialMovingAverage`, `SimpleMovingAverage`, `AverageTrueRange`, `BollingerBands`, `VolumeWeightedAveragePrice`, `RelativeStrengthIndex`, `MovingAverageConvergenceDivergence`, `KeltnerChannel`, `DonchianChannel`, `EfficiencyRatio`, `VolatilityRatio`, `SpreadAnalyzer`, `Pressure`, `RateOfChange`, `LinearRegression`, `Stochastics`, `HullMovingAverage`, `OnBalanceVolume`, `DirectionalMovement`, and more. — [indicators/\_\_init\_\_.py (develop_v1)](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/indicators/__init__.py) [A]

**Official example 1: `ema_cross_bracket.py`** — [source (develop_v1)](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/examples/strategies/ema_cross_bracket.py) [A]
- Config: `class EMACrossBracketConfig(StrategyConfig, frozen=True)` with `instrument_id`, `bar_type`, `trade_size: Decimal`, `atr_period=20`, `fast_ema_period=10`, `slow_ema_period=20`, `bracket_distance_atr: PositiveFloat = 3.0`, `emulation_trigger: str = "NO_TRIGGER"`.
- `on_start`:
  - `self.instrument = self.cache.instrument(...)`
  - `self.register_indicator_for_bars(bar_type, self.atr)` (and the EMAs)
  - `self.request_bars(bar_type, start=self._clock.utc_now() - timedelta(days=1), callback=lambda _: self.subscribe_bars(bar_type))`
  - `self.subscribe_quote_ticks(instrument_id)`
- `on_bar`:
  - `if not self.indicators_initialized(): return`
  - `if bar.is_single_price(): return`
  - Uses `self.portfolio.is_flat(...)` and `is_net_short`/`is_net_long`, then `close_all_positions` and `cancel_all_orders`, before entering.
- Entry:
  ```python
  order_list = self.order_factory.bracket(
      instrument_id=..., order_side=OrderSide.BUY,
      quantity=self.instrument.make_qty(self.config.trade_size),
      time_in_force=TimeInForce.GTD, expire_time=self.clock.utc_now() + timedelta(seconds=30),
      entry_price=self.instrument.make_price(last_bar.close),
      entry_trigger_price=self.instrument.make_price(last_bar.close),
      sl_trigger_price=self.instrument.make_price(last_bar.close - bracket_distance),
      tp_price=self.instrument.make_price(last_bar.close + bracket_distance),
      entry_order_type=OrderType.LIMIT_IF_TOUCHED,
      emulation_trigger=TriggerType[self.config.emulation_trigger],
  )
  self.submit_order_list(order_list)
  ```
- `on_stop`: `cancel_all_orders`, `close_all_positions`, `unsubscribe_bars`, `unsubscribe_quote_ticks`.
- `on_reset`: resets the indicators.

**Official example 2: `orderbook_imbalance.py`** — [source (develop_v1)](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/examples/strategies/orderbook_imbalance.py) [A]
- Config: `max_trade_size`, `trigger_min_size=100.0`, `trigger_imbalance_ratio=0.20`, `min_seconds_between_triggers=1.0`, `book_type="L2_MBP"`, `use_quote_ticks=False`, `dry_run=False`.
- Data: `subscribe_order_book_deltas(instrument.id, book_type)`, or, for an L1 book, `subscribe_quote_ticks` plus a local `OrderBook(instrument.id, BookType.L1_MBP)` updated with `book.update_quote_tick(tick)`.
- Trigger logic:
  - `book = self._book or self.cache.order_book(instrument_id)`, then reads `book.best_bid_size()`, `best_ask_size()`, `spread()`;
  - ratio = smaller/larger;
  - guards: cooldown and `if self.cache.orders_inflight(strategy_id=self.id): return`;
  - order: `order_factory.limit(..., price=..., post_only=False, time_in_force=TimeInForce.FOK)` then `submit_order`.
- `on_stop`: cancel all orders and close all positions.

**Official example 3: backtest `examples/backtest/crypto_orderbook_imbalance.py`** — [source (develop_v1)](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/examples/backtest/crypto_orderbook_imbalance.py) [A]
- Engine: `BacktestEngine(config=BacktestEngineConfig(trader_id=TraderId("BACKTESTER-001")))`.
- Venue: `engine.add_venue(venue=BINANCE_VENUE, oms_type=OmsType.NETTING, account_type=AccountType.CASH, base_currency=None, starting_balances=[Money(1_000_000.0, USDT), Money(100.0, BTC)], book_type=BookType.L2_MBP)`.
- Instrument: `TestInstrumentProvider.btcusdt_binance()`.
- Data: Binance depth CSVs via `BinanceOrderBookDeltaDataLoader.load(path)`, wrangled with `OrderBookDeltaDataWrangler(instrument).process(df)`, then `engine.add_data(deltas)`.
- Run and report: `engine.run()`, `engine.trader.generate_account_report(BINANCE_VENUE)`, `generate_order_fills_report()`, `generate_positions_report()`, `engine.reset()`, `engine.dispose()`.
- The v2 `develop` examples directory also contains `examples/backtest/crypto_ema_cross_with_binance_provider.py`, `crypto_ema_cross_ethusdt_trade_ticks.py`, `fx_market_maker_gbpusd_bars.py`, and per-venue live `data_tester.py`/`exec_tester.py` (Binance, Bybit, OKX, Hyperliquid, Databento, IB). — [repo tree (develop)](https://github.com/nautechsystems/nautilus_trader/tree/develop/examples) [A]

### Inferences
**Skeleton for 1.231.0.** Synthesized from the verified API names above; not executed. The report writer should present it as "untested reference code".

```python
from datetime import timedelta
from decimal import Decimal
import numpy as np
from scipy.stats import norm
from nautilus_trader.config import StrategyConfig, PositiveInt, PositiveFloat
from nautilus_trader.indicators import ExponentialMovingAverage, AverageTrueRange
from nautilus_trader.model.data import Bar, BarType, QuoteTick
from nautilus_trader.model.enums import OrderSide, OrderType, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.events import OrderFilled, PositionClosed
from nautilus_trader.risk.sizing import FixedRiskSizer
from nautilus_trader.trading.strategy import Strategy

class MetaFilterConfig(StrategyConfig, frozen=True):
    instrument_id: InstrumentId
    bar_type: BarType                  # e.g. "BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL"
    model_path: str                    # pickled calibrated classifier (trained offline, walk-forward)
    fast: PositiveInt = 10
    slow: PositiveInt = 30
    atr_period: PositiveInt = 20
    pt_atr: PositiveFloat = 1.5        # take-profit = 1.5 * ATR
    sl_atr: PositiveFloat = 1.0        # stop = 1.0 * ATR
    time_stop_bars: PositiveInt = 30   # vertical barrier, must match training labels
    p_min: PositiveFloat = 0.55        # meta-probability threshold
    risk_per_trade: Decimal = Decimal("0.0025")   # 0.25% equity at stop
    max_daily_loss: Decimal = Decimal("0.02")     # 2% of day-start equity
    max_qty: Decimal = Decimal("0.05")

class MetaFilterStrategy(Strategy):
    def __init__(self, config: MetaFilterConfig):
        super().__init__(config)
        self.fast = ExponentialMovingAverage(config.fast)
        self.slow = ExponentialMovingAverage(config.slow)
        self.atr = AverageTrueRange(config.atr_period)
        self.halted = False
        self.day_start_equity = None

    def on_start(self):
        self.instrument = self.cache.instrument(self.config.instrument_id)
        if self.instrument is None:
            self.log.error("instrument not found"); self.stop(); return
        self.sizer = FixedRiskSizer(self.instrument)
        self.model = load_model(self.config.model_path)            # user function
        for ind in (self.fast, self.slow, self.atr):
            self.register_indicator_for_bars(self.config.bar_type, ind)
        self.request_bars(self.config.bar_type,
                          start=self.clock.utc_now() - timedelta(days=2),
                          callback=lambda _: self.subscribe_bars(self.config.bar_type))
        self.subscribe_quote_ticks(self.config.instrument_id)       # v2: subscribe_quotes
        self._reset_day(None)
        # daily roll at 00:00 UTC (crypto); use exchange session time for CME
        self.clock.set_timer("day_roll", timedelta(days=1),
                             start_time=next_midnight_utc(self.clock.utc_now()),
                             callback=self._reset_day)

    def _equity(self):
        acct = self.portfolio.account(self.instrument.id.venue)
        return acct.balance_total(self.instrument.quote_currency)   # USDT for linear perps

    def _reset_day(self, _event):
        self.day_start_equity = self._equity()
        self.halted = False

    def _check_kill_switch(self) -> bool:
        eq = self._equity().as_decimal() + (
            self.portfolio.unrealized_pnl(self.instrument.id) or 0).as_decimal()
        if eq <= self.day_start_equity.as_decimal() * (1 - self.config.max_daily_loss):
            if not self.halted:
                self.log.warning("Daily loss limit hit: flattening and halting")
                self.halted = True
                self.market_exit()          # cancels all orders + closes positions, reduce-only
            return True
        return self.halted

    def on_bar(self, bar: Bar):
        if not self.indicators_initialized() or bar.is_single_price():
            return
        if self._check_kill_switch():
            return
        if not self.portfolio.is_flat(self.instrument.id) or self.cache.orders_open(
                instrument_id=self.instrument.id, strategy_id=self.id):
            return
        side = self._trigger()                                       # rule: EMA cross
        if side is None:
            return
        x = self._features(bar, side)                                # spread, vol ratio, OFI, ToD...
        p = float(self.model.predict_proba(x.reshape(1, -1))[0, 1])  # calibrated P(win)
        if p < self.config.p_min:
            return
        z = (p - 0.5) / np.sqrt(p * (1 - p)); m = 2 * norm.cdf(z) - 1   # AFML ch.10 bet size
        self._enter(side, bar, m)

    def _enter(self, side, bar, m):
        atr = self.atr.value; px = bar.close.as_double()
        sl = px - self.config.sl_atr * atr if side == OrderSide.BUY else px + self.config.sl_atr * atr
        tp = px + self.config.pt_atr * atr if side == OrderSide.BUY else px - self.config.pt_atr * atr
        qty = self.sizer.calculate(entry=bar.close, stop_loss=self.instrument.make_price(sl),
                                   equity=self._equity(), risk=self.config.risk_per_trade,
                                   commission_rate=Decimal("0.0005"))
        qty = min(qty.as_decimal() * Decimal(str(round(m, 2))), self.config.max_qty)
        if qty <= 0:
            return
        ol = self.order_factory.bracket(
            instrument_id=self.instrument.id, order_side=side,
            quantity=self.instrument.make_qty(qty),
            entry_order_type=OrderType.MARKET,                 # or LIMIT + entry_post_only=True
            sl_trigger_price=self.instrument.make_price(sl),
            tp_price=self.instrument.make_price(tp),
            tp_post_only=True)
        self.submit_order_list(ol)
        self.clock.set_time_alert(f"tstop-{ol.first.client_order_id}",
                                  self.clock.utc_now() + self.config.time_stop_bars * timedelta(minutes=1),
                                  callback=self._time_stop)

    def _time_stop(self, _event):                       # vertical barrier
        self.cancel_all_orders(self.instrument.id)
        self.close_all_positions(self.instrument.id)    # reduce_only=True default

    def on_position_closed(self, event: PositionClosed):
        self.cancel_all_orders(self.instrument.id)     # belt-and-braces for orphaned bracket legs
        # log realized_pnl for live-vs-backtest drift monitoring / feature "recent trigger performance"

    def on_stop(self):
        self.cancel_all_orders(self.instrument.id)
        self.close_all_positions(self.instrument.id)
        self.unsubscribe_bars(self.config.bar_type)
```

Notes on the skeleton:
- **`cache.orders_open` and `PositionClosed` timer cleanup.** `orders_open` is a v1 Cache method I recall but did not verify in this session; the verified alternative is `cache.orders_inflight`. On a timer callback the stale time alert should be cancelled with `clock.cancel_timer(name)`; that is also unverified.
- **Bracket emulation.** On Binance or Bybit, use native contingent orders where the adapter supports them, or set `emulation_trigger=TriggerType.BID_ASK` so the local `OrderEmulator` manages SL/TP. Under v2 rc8+, emulated releases pass through risk checks.
- **CME micro futures** (MES/MNQ) run through the Interactive Brokers or Databento adapters, not Binance or Bybit. Use `PerContractFeeModel` (for example $0.62/side as a placeholder; verify the broker's actual micro fees) and session-close flat timers.

### Gaps
- `OrderList.first`, `cache.orders_open`, `clock.cancel_timer`, and `Account.balance_total(currency)` were not verified line by line this session. They are in v1 as I know it, but should be checked against the docs at https://nautilustrader.io/docs/latest/ before publishing.
- Whether Binance USDT-M and Bybit linear accept native OTO/OCO brackets in the 1.231 adapters (or require emulation) was not verified.
- The official docs pages on nautilustrader.io were not fetched; the source code was used instead.

---

## 4. Risk engine, trading states, and a daily-loss kill switch

### Takeaway
v1 `RiskEngineConfig` offers only `bypass`, order submit and modify rate limits, and per-instrument max notional. There is **no built-in daily-loss limit**. Implement the kill switch in the strategy (or a dedicated Actor) by:
- (a) calling `market_exit()` or `close_all_positions`;
- (b) blocking new entries;
- (c) optionally setting the engine's `TradingState` to **REDUCING**, not HALTED, because HALTED denies exits too.

### Cited Findings
- **`RiskEngineConfig` fields (v1):**
  - `bypass: bool = False` ("bypass all pre-trade risk checks and rate limits (will still check for duplicate IDs)")
  - `max_order_submit_rate: str = "100/00:00:01"`
  - `max_order_modify_rate: str = "100/00:00:01"`
  - `max_notional_per_order: dict[str, int] = {}` (per instrument ID)
  - `debug: bool = False`

  The live variant `LiveRiskEngineConfig(RiskEngineConfig)` is used as `TradingNodeConfig.risk_engine`. — [risk/config.py](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/risk/config.py) [A]; [live/config.py](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/live/config.py) [A]
- **Trading-state behavior.**
  - `RiskEngine.trading_state` starts as `TradingState.ACTIVE`.
  - Methods: `set_trading_state(TradingState state)` and `set_max_notional_per_order(instrument_id, new_value)`.
  - In order checks, HALTED denies with reason "TradingState.HALTED". REDUCING denies "BUY when TradingState.REDUCING and LONG", and the mirror case, including inside OrderLists. — [risk/engine.pyx (develop_v1), lines ~132–279, 1137–1177](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/risk/engine.pyx) [A]
- **v2 changes.** rc5: "REDUCING now allows only eligible reduce-only submissions, cancels, and queries". rc8: "HALTED denies stops… use REDUCING for eligible exits". — [releases](https://github.com/nautechsystems/nautilus_trader/releases) [A]
- **Strategy-level flatten** uses `market_exit()` with `market_exit_interval_ms`, `market_exit_max_attempts`, `market_exit_reduce_only=True`. The `on_market_exit` and `post_market_exit` hooks are available. — [strategy.pyx](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/trading/strategy.pyx); [trading/config.py](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/trading/config.py) [A]

### Inferences
Recommended layered limits for the report:
1. **Venue-side:** exchange position limits, isolated margin, low leverage (1–3x).
2. **`RiskEngineConfig`:** `max_notional_per_order={"BTCUSDT-PERP.BINANCE": 5000}` and `max_order_submit_rate="10/00:00:01"`, well under Binance and Bybit API limits.
3. **Strategy kill switch:** daily loss ≥ 2% of day-start equity, or N consecutive losses, or trade-count cap leads to `market_exit()` and a `halted` flag until the next day roll.
4. **Engine-level:** an Actor holding a reference to the risk engine (in backtest, `engine.kernel.risk_engine`) can call `set_trading_state(TradingState.REDUCING)`. This path is unverified as a public API; prefer the strategy flag.

### Gaps
- No official example of a daily-loss kill switch was found in the repo examples.
- How a v1 strategy can legitimately obtain the RiskEngine reference (public API vs. internal) was not verified.

---

## 5. Backtest setup (engine/node, venue, fees, fill and latency models, book type, catalog, data) and live TradingNode for Binance/Bybit

### Takeaway
v1 offers two entry points:
- the low-level **`BacktestEngine.add_venue(...)`**, which takes model objects directly;
- the high-level **`BacktestNode`** with `BacktestRunConfig(venues=[BacktestVenueConfig], data=[BacktestDataConfig])` over a `ParquetDataCatalog`, which takes models through `Importable*ModelConfig`.

Fees in v1 come from instrument `maker_fee`/`taker_fee` via `MakerTakerFeeModel`; v2 rc6 moved them to the fee model. Live trading uses `TradingNode` with Binance or Bybit factories.

### Cited Findings
- **`BacktestEngine.add_venue` signature (v1):**
  - `venue`, `oms_type`, `account_type`, `starting_balances: list[Money]`, `base_currency=None`, `default_leverage=None`, `leverages=None`, `margin_model=None`, `modules=None`;
  - models: `fill_model: FillModel | None`, `fee_model: FeeModel | None`, `latency_model: LatencyModel | None`;
  - `book_type=BookType.L1_MBP`, `routing=False`, `reject_stop_orders=True`, `support_gtd_orders=True`, `support_contingent_orders=True`, `oto_trigger_mode=PARTIAL`, `use_position_ids=True`, `use_random_ids=False`, `use_reduce_only=True`, `use_message_queue=True`, `use_market_order_acks=False`;
  - execution realism: `bar_execution=True`, `bar_adaptive_high_low_ordering=False`, `trade_execution=True`, `liquidity_consumption=False`, `queue_position=False`, `allow_cash_borrowing=False`. — [backtest/engine.pyx (develop_v1) L502–532](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/backtest/engine.pyx) [A]
- **`BacktestVenueConfig` fields:** `name`, `oms_type`, `account_type`, `starting_balances: list[str]`, `base_currency`, `default_leverage=1.0`, `leverages`, `margin_model: MarginModelConfig`, `modules`, `fill_model: ImportableFillModelConfig`, `latency_model: ImportableLatencyModelConfig`, `fee_model: ImportableFeeModelConfig`, `book_type="L1_MBP"`, `routing`, `reject_stop_orders`, `support_gtd_orders`, `support_contingent_orders`, `oto_trigger_mode`, `use_position_ids`, `use_random_ids`, `use_reduce_only`, `use_market_order_acks`, and more. — [backtest/config.py (develop_v1)](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/backtest/config.py) [A]
- **Data and run configs.**
  - `BacktestDataConfig`: `catalog_path`, `data_cls`, `catalog_fs_protocol`, `instrument_id`/`instrument_ids`, `start_time`, `end_time`, `filter_expr`, `client_id`, `bar_spec`, `bar_types`, `optimize_file_loading`.
  - `BacktestRunConfig`: `venues`, `data`, `engine`, `chunk_size`, `raise_exception`, `dispose_on_completion`, `start`, `end`, `data_clients`.
  - Model configs: `FillModelConfig(prob_fill_on_limit=1.0, prob_slippage=0.0, random_seed=None)`; `LatencyModelConfig(base_latency_nanos=1_000_000_000, insert_latency_nanos=0, update_latency_nanos=0, cancel_latency_nanos=0)` (note the **1 s default** in the config class versus 1 ms in the Cython class); `MakerTakerFeeModelConfig`; `FixedFeeModelConfig(commission: str)`. — [backtest/config.py](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/backtest/config.py) [A]
- **Fill model.** `FillModel(prob_fill_on_limit=1.0, prob_slippage=0.0, random_seed=None)`. `prob_fill_on_limit` is "the probability of limit order filling if the market rests on its price"; `prob_slippage` is "the probability of order fill prices slipping by one tick".
  - Other available models: `BestPriceFillModel`, `CompetitionAwareFillModel`, `LimitOrderPartialFillModel`, `MarketHoursFillModel`, `OneTickSlippageFillModel`, `ProbabilisticFillModel`, `SizeAwareFillModel`, `ThreeTierFillModel`, `TwoTierFillModel`, `VolumeSensitiveFillModel`.
  - Fee models: `FixedFeeModel`, `MakerTakerFeeModel`, `PerContractFeeModel`. Margin models: `StandardMarginModel`, `LeveragedMarginModel`.
  - `LatencyModel(base_latency_nanos=1ms default, insert_latency_nanos=0, update_latency_nanos=0, cancel_latency_nanos=0)`. — [backtest/models/\_\_init\_\_.py](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/backtest/models/__init__.py); [fill.pyx](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/backtest/models/fill.pyx); [latency.pyx](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/backtest/models/latency.pyx) [A]
- **Maker/taker fees in v1.** `MakerTakerFeeModel.get_commission` computes `notional * instrument.maker_fee` (MAKER) or `* instrument.taker_fee` (TAKER), so set the instrument fees to the account's VIP tier. v2 rc6 removed instrument fees in favor of rates on the venue `fee_model`, with per-instrument overrides. — [fee.pyx (develop_v1)](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/backtest/models/fee.pyx); [releases](https://github.com/nautechsystems/nautilus_trader/releases) [A]
- **Catalog.** `ParquetDataCatalog` has `from_env()`, `from_uri()`, `write_data()`, `query()`, `consolidate_catalog()`/`consolidate_data_by_period()`, `delete_data_range()`. — [persistence/catalog/parquet.py (develop_v1)](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/persistence/catalog/parquet.py) [A]
- **v2 catalog limits.** `BacktestNode` does not support data-client factories, on-the-fly downloads, custom data or data frames; use `BacktestEngine` directly for custom statistics. — [MIGRATION_V2.md](https://github.com/nautechsystems/nautilus_trader/blob/develop/MIGRATION_V2.md) [A]
- **Binance adapter exports (v1):** `BINANCE`, `BINANCE_VENUE`, `BinanceAccountType` (SPOT, MARGIN, ISOLATED_MARGIN, **USDT_FUTURES**, COIN_FUTURES), `BinanceEnvironment` (LIVE, TESTNET, DEMO), `BinanceDataClientConfig`, `BinanceExecClientConfig`, `BinanceLiveDataClientFactory`, `BinanceLiveExecClientFactory`, `BinanceOrderBookDeltaDataLoader`, `BinanceFuturesMarkPriceUpdate`.
  - Data config fields: `api_key`, `api_secret`, `key_type=HMAC`, `account_type=SPOT`, `environment`, `base_url_*`, `proxy_url`, `us=False`, `update_instruments_interval_mins=60`, `use_agg_trade_ticks=False`.
  - Exec config adds `use_position_ids`, `use_trade_lite`, and more. — [adapters/binance/\_\_init\_\_.py](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/adapters/binance/__init__.py); [binance/config.py](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/adapters/binance/config.py); [binance/common/enums.py](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/adapters/binance/common/enums.py) [A]
- **Bybit adapter exports (v1):** `BYBIT`, `BYBIT_VENUE`, `BybitDataClientConfig`, `BybitExecClientConfig`, `BybitEnvironment`, `BybitProductType`, `BybitLiveDataClientFactory`, `BybitLiveExecClientFactory`, `BybitOrderBookDeltaDataLoader`.
  - Config fields: `api_key`, `api_secret`, `product_types: tuple[BybitProductType, ...]`, `environment`, `recv_window_ms=5000`, `bars_timestamp_on_close=True`, `max_retries`.
  - Exec config adds `use_gtd=False` ("Not supported on Bybit"), `use_ws_execution_fast`, `use_http_batch_api`. — [adapters/bybit/\_\_init\_\_.py](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/adapters/bybit/__init__.py); [bybit/config.py](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/adapters/bybit/config.py) [A]
- **`TradingNodeConfig` fields:** `environment=LIVE`, `trader_id`, `data_engine`, `risk_engine: LiveRiskEngineConfig`, `exec_engine`, `data_clients: dict`, `exec_clients: dict`. — [live/config.py](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/live/config.py) [A]
- **Adapter gotchas (v2 rc).** Binance futures book subscriptions reject depth changes until unsubscribed. `close_position` orders require `reduce_only=true`. Binance REST blocks on HTTP 418 (IP ban), so "confirm the ban has ended before restarting". — [releases](https://github.com/nautechsystems/nautilus_trader/releases) [A]

### Inferences
**Backtest snippet (v1, synthesis):**
```python
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.models import FillModel, LatencyModel, MakerTakerFeeModel
engine.add_venue(
    venue=Venue("BINANCE"), oms_type=OmsType.NETTING, account_type=AccountType.MARGIN,
    starting_balances=[Money(10_000, USDT)], base_currency=USDT, default_leverage=Decimal(2),
    fill_model=FillModel(prob_fill_on_limit=0.3, prob_slippage=0.5, random_seed=42),
    fee_model=MakerTakerFeeModel(),          # instrument maker_fee/taker_fee e.g. 0.0002/0.0005
    latency_model=LatencyModel(base_latency_nanos=50_000_000),  # 50 ms
    book_type=BookType.L1_MBP,               # L2_MBP if feeding Tardis/Binance depth deltas
    bar_adaptive_high_low_ordering=True)
```
- **Pessimistic settings for scalping:**
  - taker fees on all market entries and stop exits;
  - `prob_fill_on_limit` ≤ 0.3–0.5 for post-only TPs;
  - `prob_slippage` ≥ 0.5 or `OneTickSlippageFillModel`;
  - 20–100 ms latency;
  - run with quote or trade ticks rather than bars where available;
  - re-run at 2× fees as a stress test.
- **Live (v1):**
  ```python
  TradingNodeConfig(
      data_clients={BINANCE: BinanceDataClientConfig(account_type=BinanceAccountType.USDT_FUTURES,
                                                     environment=BinanceEnvironment.TESTNET)},
      exec_clients={BINANCE: BinanceExecClientConfig(...)},
      risk_engine=LiveRiskEngineConfig(...),
  )
  node.add_data_client_factory(BINANCE, BinanceLiveDataClientFactory)
  node.add_exec_client_factory(BINANCE, BinanceLiveExecClientFactory)
  node.build()
  node.run()
  ```
  `add_*_client_factory` and `build` follow the v1 pattern I know but were not verified this session. Bybit is analogous with `product_types=(BybitProductType.LINEAR,)`.
- **Data:** use Tardis or Binance public data dumps for depth and trades, wrangled into the catalog.

### Gaps
- Tardis loader class names (`TardisCSVDataLoader`), the Tardis Machine replay config, and exact fee-tier numbers were not verified.
- The official docs pages for backtesting fill realism (bar execution ordering, `liquidity_consumption`) were not fetched.

---

## 6. Validation methodology: walk-forward, CPCV, Deflated Sharpe, PBO, MinTRL, trade counts, Monte Carlo, parameter stability

### Takeaway
Use three layers:
- anchored or rolling walk-forward with purge and embargo around every train/test boundary;
- CPCV or CSCV over the full configuration set to estimate PBO, rejecting if PBO > 0.05 per Bailey et al.;
- DSR computed with the **true number of trials N**, plus MinTRL to size the live paper-trading period.

### Cited Findings
- **Expected maximum Sharpe under N independent zero-skill trials:**
  E[max SR] ≈ √V[{SR_n}] · ((1−γ)·Z⁻¹[1 − 1/N] + γ·Z⁻¹[1 − 1/(N·e)])
  where γ ≈ 0.5772 (Euler–Mascheroni constant), Z⁻¹ is the inverse standard-normal CDF, and e is Euler's number. — [Bailey & López de Prado (2014), "The Deflated Sharpe Ratio", JPM 40(5)](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf) [A]
- **Deflated Sharpe Ratio:**
  DSR = Z[ (SR̂ − SR̂₀)·√(T−1) / √(1 − γ̂₃·SR̂ + ((γ̂₄−1)/4)·SR̂²) ]
  with SR̂₀ = E[max SR] above, T = sample length, γ̂₃ = skewness, γ̂₄ = kurtosis (not excess). In the paper's words, "DSR is a PSR where the rejection threshold is adjusted to reflect the multiplicity of trials." — [same](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf) [A]
- **DSR worked example.** A treasury-auction strategy has annualized SR̂ = 2.5 on 5 years of daily data (T = 1250); many configurations give SR ≈ 2. The investor declines because DSR ≈ 0.90, "only a 90% chance that the true SR… is greater than zero". With N = 46 trials, DSR would have been 0.9505; with Normal returns the cutoff moves to N = 88.
  - The exact N, V and skew/kurtosis inputs were lost in PDF extraction. My recollection of the paper is N = 100, V = 1/2, γ̂₃ = −3, γ̂₄ = 10; verify before quoting. — [same](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf) [A]
- **PBO via CSCV** (Bailey, Borwein, López de Prado & Zhu, revised Feb 2015):
  1. Form the T×N matrix of per-period performance for N configurations.
  2. Split its rows into an even number S of blocks.
  3. Form all C(S, S/2) train/test combinations (S = 16 gives 12,780).
  4. In each combination, pick the in-sample-best configuration n\* and compute its OOS relative rank ω̄ = r̄/(N+1).
  5. Compute the logit λ = ln(ω̄/(1−ω̄)).
  6. PBO φ = ∫₋∞⁰ f(λ)dλ, the share of combinations where the IS-best underperforms the OOS median.

  Complementary outputs are performance degradation, probability of loss and stochastic dominance. "A customary approach would be to reject models for which PBO is estimated to be greater than 0.05." — [Bailey et al., "The Probability of Backtest Overfitting"](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf) [A]
- **MinTRL** (Minimum Track Record Length) is listed as a keyword of the DSR paper, and its inputs (SR, skew, kurtosis, confidence) are described in López de Prado's slides. The requirement grows as the observed SR approaches the threshold and as skew becomes more negative or tails fatter. — [DSR paper](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf) [A]; [López de Prado slides (QWAFAFEW)](https://newyork.qwafafew.org/wp-content/uploads/sites/4/2017/01/Lopez_de_Prado_Sharpe.pdf) [A, formula garbled in extraction]. Standard form (Bailey & López de Prado 2012, SSRN 1821643), reproduced from my knowledge, verify:
  MinTRL = 1 + [1 − γ̂₃·SR̂ + ((γ̂₄−1)/4)·SR̂²] · (Z_α / (SR̂ − SR*))²
  Here SR is per-period (not annualized) and the result counts observations.
- **N must count every tested configuration**, and DSR should be computed on data not used for selection. — [search summary of DSR secondary sources](https://www.quantt.co.uk/resources/deflated-sharpe-ratio) [C]

### Inferences
**Walk-forward design** for 1-minute crypto perpetuals:
- rolling 6-month train / 1-month test, stepped monthly, giving 24–36 OOS months from 2–3+ years of data;
- inside each train window, purged k-fold (k = 5) with embargo ≈ 1% of the window (≈ 1,800 one-minute bars ≈ 1.25 days), at least the vertical-barrier length, for meta-model hyperparameters and calibration;
- freeze primary-rule parameters before the meta-model walk-forward, or include them in N.

For CME micro futures, use RTH-only or ETH-segmented windows and roll-adjusted continuous contracts.

**Trade-count significance** (my arithmetic, not sourced):
- To reject "mean net trade P&L ≤ 0" at about 95% one-sided, n ≥ (1.645·σ_trade/μ_trade)².
- Typical scalping values, μ/σ ≈ 0.05–0.10 per trade, imply n ≈ 270–1,080 trades. This supports the ≥ 300–500 OOS trade practitioner rule.
- Bootstrap the trade sequence (≥ 10,000 resamples, block bootstrap to keep serial dependence) to get distributions of max drawdown and the 5th-percentile terminal P&L.

**Parameter stability:**
- heatmap OOS net Sharpe or profit factor over the (p_min, pt_atr, sl_atr) grid;
- require a plateau, meaning neighbors within about 20–30% of the chosen cell, rather than an isolated peak;
- compute PBO across that grid with CSCV, S = 16.

**Meta-label-specific ablations** to report on the same OOS periods:
- primary-only;
- primary + random filter at the same trade rate (the placebo);
- primary + meta filter;
- primary + meta filter + bet sizing.

The meta filter must beat the random filter at equal trade rate, and beat primary-only on net Sharpe and on DSR.

### Gaps
- CPCV details were not re-verified from AFML ch. 12 this session.
- No source was found for a specific recommended walk-forward window ratio for minute bars; 6m/1m is convention, not evidence.

---

## 7. Practitioner go-live thresholds (profit factor, Sharpe, drawdown, trade counts, live-vs-backtest slippage)

### Takeaway
There is no authoritative standard. Thresholds come from blogs, vendors and forums and are opinion. The academically grounded criteria are DSR > 0.95 and PBO < 0.05 (Bailey et al.). Everything else (profit factor > 1.2–1.5, ≥ 100–1000 trades, paper performance within 20% of OOS, +1 tick slippage stress) is rule-of-thumb.

### Cited Findings
- **Academic criteria.** Reject if PBO > 0.05 — [Bailey et al.](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf) [A]. The DSR example uses a 95% confidence cutoff — [Bailey & López de Prado 2014](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf) [A].
- **Profit factor (opinion).**
  - "Minimum Profit Factor: > 1.3 (some sources use 1.5)" — [cli-trader-site backtesting-validation](https://cli-trader-site.pages.dev/trading-skills/backtesting-validation/) [C]
  - "Below 1.2, real costs usually eliminate the edge" and 1.3–1.8 "realistic for a day trading strategy"; PF > 2.5 in a backtest "almost certainly indicates overfitting" — [LuxAlgo stress-test guide](https://www.luxalgo.com/blog/stress-test-your-algorithmic-trading-strategy-guide-to-avoiding-overfitting/) and [AlgoChef validate-before-live](https://algochef-10n68b26c-statoasis.vercel.app/learn/validate-trading-strategy-before-live) [C, search snippets; attribution between these two is uncertain]
- **Trade counts (opinion).** "At least 100 trades across varied market conditions"; another guide asks for "> 200 per rule and > 1000 total". — [cli-trader-site](https://cli-trader-site.pages.dev/trading-skills/backtesting-validation/); [tradingwyckoff validate guide](https://tradingwyckoff.com/en/algorithmic-trading/validate-trading-strategy-guide/) [C, snippets]
- **Out-of-sample share and expected degradation (opinion).** Reserve at least 30% of data for OOS. A practitioner expects backtest and OOS "to be off by about 20%". — [tradingwyckoff](https://tradingwyckoff.com/en/algorithmic-trading/validate-trading-strategy-guide/); [huntersalgo backtesting vs live](https://huntersalgo.pages.dev/blog/backtesting-vs-live-performance) [C, snippets]
- **Paper-trading phase (opinion).** For daily strategies with 200+ trades/year: 4–6 weeks and 30–50 trades, passing if "paper performance within 20% of validated OOS performance across key metrics". Another source says "minimum 30 trades or 3 months (whichever is longer)". — [AlgoChef](https://algochef-10n68b26c-statoasis.vercel.app/learn/validate-trading-strategy-before-live); [AlgoChef why strategies fail](https://algochef-10n68b26c-statoasis.vercel.app/docs/why-strategies-fail) [C, snippets]
- **Slippage stress (opinion).** Add at least 1 tick of slippage per trade. One ES futures trader requires a minimum average trade of $50 after 2 ticks of slippage plus commission. — [NexusFi thread](https://nexusfi.com/showthread.php?p=304291); [NexusFi profit factor thread](https://nexusfi.com/psychology-money-management/26039-what-good-profit-factor-2.html) [C, snippets]
- **No sourced threshold found** for "Sharpe > 1.5 for intraday". It is common folklore; I found no primary source.

### Inferences
Proposed numeric acceptance gates for the report. Label them as the author's synthesis: the academic ones (DSR, PBO) are sourced, the rest are opinion calibrated to scalping costs.

| Gate | Threshold | Basis |
|---|---|---|
| OOS walk-forward trades (meta-filtered) | ≥ 500 (absolute floor 300) | t-stat arithmetic above; practitioner 200–1000 |
| Net profit factor, OOS, with taker fees + 1-tick slippage | ≥ 1.25; and ≥ 1.10 at 2× costs | practitioner 1.2–1.5 |
| Net annualized Sharpe (daily P&L), OOS | ≥ 1.5; DSR ≥ 0.95 with honest N | DSR paper; Sharpe floor is opinion |
| PBO (CSCV, S = 16, over the full grid) | ≤ 0.05 strict, ≤ 0.20 relaxed | Bailey et al. (0.05); relaxed is opinion |
| Max drawdown, OOS | ≤ 10% of equity; Monte Carlo 95th-percentile DD ≤ 15% | opinion |
| Meta filter vs. random filter at the same trade rate | net Sharpe uplift > 0 in ≥ 70% of WF folds | ablation design |
| Profitable WF months | ≥ 60% | opinion |
| Paper/testnet phase | ≥ 4 weeks and ≥ 100 trades, or MinTRL, whichever is longer | MinTRL; practitioner 30–50 trades |
| Live vs. backtest slippage | median realized slippage ≤ 1 tick and ≤ 1.5× modeled; live expectancy within 25% of OOS | practitioner "within 20%" |
| Small-capital live | 3–6 months at ≤ 10–25% of target size before scaling | opinion |
| Kill / rollback triggers | daily loss ≥ 2% equity; live DD > 1.5× backtest 95th-percentile DD; rolling 100-trade PF < 1.0; feature/probability drift (PSI > 0.2 on meta-probabilities) leads to retraining or halt | opinion |

### Gaps
- No peer-reviewed or regulator-published go-live thresholds for retail or prop intraday strategies were found.
- Several of the threshold sources are low-quality blog or vendor pages read only through search snippets. Their exact wording and attribution should be treated as approximate.
