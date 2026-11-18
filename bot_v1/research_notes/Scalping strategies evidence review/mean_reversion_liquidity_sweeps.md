# Short-Horizon Mean-Reversion Scalping and Liquidity-Sweep / Stop-Hunt Reversals: Evidence Review (crypto perps, MES/ES, major FX), as of Nov 2026

Source rating key used throughout: **[PR]** peer-reviewed journal; **[WP]** working paper / preprint (SSRN, arXiv, central-bank staff report), not yet peer-reviewed; **[RB]** reputable independent backtest with stated rules and costs; **[PRAC]** practitioner / vendor blog; **[MKT]** marketing or unverifiable claim. "UNVERIFIED" marks numbers I could not confirm from a primary source in this session.

Research budget note: about 20 tool calls. Several primary papers were only accessible as abstracts, so effect sizes are given only where I saw them. Where I rely on background knowledge rather than a fetched source, I say so and put it under Inferences or Gaps, not Cited Findings.

---

## Q1. Short-horizon reversal evidence: bid-ask bounce vs genuine reversal; equities, crypto, FX

### Takeaway
At minute to half-hour horizons, reversal in last-trade prices is real but largely **mechanical** (bid-ask bounce, lack of resiliency), and that part cannot be captured by a taker. The **genuine, compensated** part is a liquidity-provision premium. It is time-varying and largest when volatility spikes and liquidity evaporates (Nagel 2012). In crypto, peer-reviewed work finds intraday reversal **conditional on large jumps/overreaction**, alongside intraday momentum. No peer-reviewed paper I found shows that fading crypto liquidation cascades is profitable net of costs. In FX, the best-documented intraday reversal is tied to **benchmark fixes**, not generic session ranges.

### Cited Findings
- **Heston, Korajczyk & Sadka (2010), J. Finance 65(4):1369–1407 [PR].** Splits the US trading day into 13 half-hour intervals. A stock's return over an interval is negatively related to its returns over recent intervals, "consistent with the negative autocorrelation induced by bid-ask bounce and lack of resiliency." They also find continuation at lags that are exact multiples of a trading day (the same half-hour on prior days), lasting up to 40 trading days, strongest in the first and last half-hours. Volume, order imbalance, volatility and spreads do not explain the patterns. — [arXiv version](https://arxiv.org/pdf/1005.3535.pdf); [RePEc JF record](https://econpapers.repec.org/RePEc:bla:jfinan:v:65:y:2010:i:4:p:1369-1407); [UH working paper](https://www.bauer.uh.edu/departments/finance/documents/Heston_Korajczyk_Sadka_paper_UH.pdf)
- **Nagel (2012), "Evaporating Liquidity," RFS 25(7):2005–2039 [PR].** Uses short-term reversal strategy returns as a proxy for returns to liquidity provision. Expected returns are "strongly time-varying and highly predictable with the VIX." Expected returns and conditional Sharpe ratios "increase enormously" with VIX in turmoil, e.g., 2007–09. Even industry-portfolio reversal, weak on average, earns high returns and Sharpe ratios when VIX is high. Mechanism: liquidity suppliers withdraw. — [NBER w17653](https://nber.org/papers/w17653); [RePEc RFS](https://econpapers.repec.org/RePEc:oup:rfinst:v:25:y:2012:i:7:p:2005-2039)
- **Wen, Bouri, Xu & Zhao (2022), N. Am. J. Econ. & Finance [PR].** Bitcoin high-frequency data 2013–2020. Finds **both** intraday momentum and intraday reversal. Predictability shifts around **large intraday price jumps**, FOMC announcements, liquidity changes and COVID-19. The same patterns appear in ETH, LTC and XRP. Reversal is attributed to overreaction/overconfidence, and "information-based large price changes experience reversals". Momentum is attributed to late-informed investors. — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1062940822000833); [SSRN 4080253](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4080253)
- **"On the Intraday Behavior of Bitcoin" [WP/PR, venue not confirmed].** Bigger moves produce stronger percentage reversals. The no-jump null is rejected at every intraday scale up to 2 hours. — [ResearchGate](https://www.researchgate.net/publication/353205654_On_the_Intraday_Behavior_of_Bitcoin)
- **"On the intraday return curves of Bitcoin" [PR, venue not confirmed].** Average returns concentrate at the turn of 15-minute candles, other minutes are negative, and the effect persists out of sample. This is a microstructure/timing effect, not a reversal rule. — [ResearchGate](https://www.researchgate.net/publication/351147995_On_the_intraday_return_curves_of_Bitcoin_Predictability_and_trading_opportunities)
- **JRFM (2026) 19(9):692 [PR, MDPI].** Bitcoin shows **conditional reversal** in both daytime and overnight sessions. Ethereum shows positive overnight drift with daytime reversal. — [doi:10.3390/jrfm19090692](https://doi.org/10.3390/jrfm19090692)
- **Open-Alpha-Lab study notes [PRAC, secondary].** The notes say the authors' own earlier studies (#251 crypto-reversal, #210 crypto-trend) found short-horizon crypto reversal "weak-to-absent net of costs," with trend persisting at some horizons. They call "buy-the-blood after liquidation spikes" desk/Twitter folklore with no canonical paper. — [GitHub references.md](https://github.com/Guillain-RDCDE/Open-Alpha-Lab/blob/main/studies/586-liquidation-cascade/docs/references.md)
- **The finance literature supports the liquidation-overshoot mechanism (forced sales give temporary price pressure that reverses).** Coval & Stafford (2007, JFE) show that forced mutual-fund sales cause temporary price pressure that later reverses. Brunnermeier & Pedersen (2009, RFS) model margin/funding spirals. (Both are cited in the lab notes. I did not fetch them separately.) — [GitHub references.md](https://github.com/Guillain-RDCDE/Open-Alpha-Lab/blob/main/studies/586-liquidation-cascade/docs/references.md)
- **FX (Krohn, Mueller & Whelan) [WP; BoC staff WP 2021-48; BIS workshop].** In regular Asian hours the USD is roughly flat on average but "displays two V-shaped return reversals with turning points marked by the reference fixes". Dealers hedging pre-fix demand drive intraday reversals in OTC and exchange-traded FX. The "W"-shape is prevalent across FX segments and is "not driven by stale/indicative quotes." The authors say arbitrageurs can exploit it after costs. A companion version is more cautious: exploitable by those with "lower than average transaction costs." — [BoC SWP 2021-48](https://www.bankofcanada.ca/wp-content/uploads/2021/10/swp2021-48.pdf); [WU Vienna VSFX 2022 paper](https://www.wu.ac.at/fileadmin/wu/d/ri/isk/VSFX_2022/Paper/Session_III_1a_Krohn__foreign_Exchange_Fixings_Returns_Around_The_Clock_0712.pdf); [BIS slides](https://www.bis.org/events/221213_bis_bdi_ecb_exchange_rates/mueller.pdf)
- **1-minute EURUSD [PR, small regional journal].** Finds mean reversion (ADF rejects a unit root) but does not test a trading rule after costs. — [Folia Oeconomica Stetinensia 2014](https://bazhum.muzhp.pl/media/texts/folia-oeconomica-stetinensia/2014-tom-1422-numer-2/folia_oeconomica_stetinensia-r2014-t1422-n2-s152-162.pdf)

### Inferences
- **Separate the bounce component from the real reversal.** The negative lag-1 autocorrelation of last-trade returns is mostly bounce. Roll (1984) gives cov(Δp_t, Δp_{t-1}) = −s²/4 (background knowledge, not fetched). A taker crosses the spread on entry and exit and pays it back. Only a passive (maker) trader, or a trader fading moves much larger than the spread, can harvest reversal. The test: re-run any reversal backtest on **mid-quote** or bid/ask-side prices (buy at ask, sell at bid). If the edge disappears, it was bounce.
- **Nagel's result is the key regime fact, and it cuts against a common filter.** Reversal/liquidity-provision payoffs are **highest when volatility is high**. Many retail mean-reversion systems filter out high volatility. These conflict: the high-vol state is where the premium lives, and also where fat-tail losses live. The likely reconciliation: fade **after** a dislocation (a liquidity shock that has already happened), but not during a sustained, information-driven trend. This is untested inference.
- **Crypto evidence is conditional.** The unconditional minute-level reversal premium in BTC/ETH looks small or negative after costs (Open-Alpha-Lab; also Q2 backtests). The peer-reviewed reversal signal is conditional on **large jumps**, which points to event-driven fades rather than continuous band-trading.

### Gaps
- Effect sizes (bps per trade, t-stats) for Wen et al. 2022 and the JRFM paper: only abstracts were seen.
- No peer-reviewed study found on **post-liquidation-cascade forward returns** on Binance/Bybit perps (see Q3).
- No peer-reviewed minute-level ES/MES reversal study with realistic costs was found in this session.

---

## Q2. Indicator strategies (RSI(2), Bollinger(20,2), VWAP ± kσ, IBS) at minute horizons, and the technical-analysis data-snooping literature

### Takeaway
No credible source shows that minute-bar Bollinger/RSI/VWAP-band rules survive realistic costs on BTC/ETH. The independent and vendor backtests I found, at 15m–1h, mostly **lose after costs** despite 55–68% win rates. That is the classic high-win-rate, negative-expectancy profile. The academic technical-analysis literature (Brock-Lakonishok-LeBaron → Sullivan-Timmermann-White → Hsu-Taylor-Wang) shows that apparent profits shrink sharply once data snooping is corrected and in later subsamples. FX rule predictability is largely gone in 2006–2015.

### Cited Findings
- **WhatDoesntWork replication [RB].** Rules: BB(20,2) on 1h bars. Long when the 1h close < lower band, short when > upper band. Fill at next bar open. Filters: 4h RSI > 55 for longs, < 45 for shorts; ADX(1h) > 20 and ADX(4h) > 25. Stop 4.5 ATR. Exit at the opposite band. 240-bar time stop. Costs 10 bps round trip (5 bps/side). Period 2025-06-17 to 2026-06-13, nine perps. **Average strategy return −20.6%** (buy & hold −38.3%). Only BTC was positive: +4.9%, 38 trades, 60.5% win rate, +15.0 bps/trade, PF 1.17, max DD −12.5%. NEAR: 63.2% win rate but −67.6 bps/trade, PF 0.70, −27.4%. A YouTube claim of +179% on NEAR (optimized params, 8m IS / 4m OOS) was **not reproduced**. — [whatdoesntwork.com](https://whatdoesntwork.com/research/bollinger-rsi-adx-crypto-mean-reversion/)
- **Coinquant "78 backtests" [PRAC/vendor].** Naked long-only rules on Binance spot BTC/ETH, at 15m/1h/4h/1d, across 2022 bear, 2023 sideways and late-2023/24 bull windows. Rules: BB(20, k=2.0/2.5), with entry on a close below the lower band and exit on a cross above the SMA20; RSI(2) < 10 entry, > 70 exit; and distance from SMA20 (5% daily, scaled to 2.5%/1.25%/0.6% for 4h/1h/15m). Average return by timeframe: **15m −14.4%, 1h −8.1%, 4h −9.5%, 1d −4.0%**. By regime: bull +16.3%, sideways −2.2%, bear −40.6%. **14 of 78 cells won ≥65% of trades yet lost money**, e.g., BB k=2 BTC 1h sideways: 68% wins, −12.5%; RSI-2 BTC 1h bear: 67% wins, −21.9%. BB on 15m made 693 trades and paid more than $2,300 in fees on a $10k account. Fee/slippage rates are not stated. Regimes were labeled in hindsight. — [coinquant.ai](https://www.coinquant.ai/blog/building-a-mean-reversion-strategy-in-cryptocurrency-markets-evidence-from-78-backtests)
- **Edgoro default-indicator test [PRAC].** RSI 30/70, BB reversion and Stochastic 20/80 at default settings beat buy-and-hold in **0 of 42** crypto backtests and lost money in 26 (daily and 4h, not minute). On 4h bars the median run had about 240 trades and costs took **51.3%** of gross. — [edgoro.com](https://edgoro.com/blog/default-indicator-settings-crypto-backtest)
- **Parameter-tuning inflation [PRAC].** Fine-tuning, e.g., RSI(2) < 7 instead of < 10 or BB width 1.8σ instead of 2.0σ, "typically add[s] 30 to 50 percent to backtest Sharpe Ratios". This is an unverified practitioner rule of thumb. — [backtestme.com via search](https://backtestme.com/guides/mean-reversion-strategies)
- **Sullivan, Timmermann & White (1999), J. Finance 54:1647–1691 [PR].** Expands BLL's 26 rules to a large universe on about 100 years of DJIA daily data and applies White's Reality Check bootstrap to adjust for data snooping. They also test BLL's rules on the following 10 years (1987–1996). A review summarizes the broader finding that technical rules "lose their predictive power for major U.S. stock indices after the mid 80's." — [RePEc](https://econpapers.repec.org/RePEc:bla:jfinan:v:54:y:1999:i:5:p:1647-1691); [working paper](https://www.fmg.ac.uk/sites/default/files/2020-11/dp303.pdf); [Park & Irwin review](https://ageconsearch.umn.edu/record/19039/files/cp05pa01.pdf)
- **Hsu, Taylor & Wang (2016), J. Int'l Econ. 102:188–208 [PR].** Daily data, 45 years, 30 currencies, more than 21,000 rules, stepwise SPA test against data snooping. Finds substantial predictability in developed and emerging FX, cross-validated out of sample, with time-series and cross-sectional variation consistent with "temporarily irrational behavior and market immaturity." — [WUSTL profile](https://profiles.wustl.edu/en/publications/technical-trading-is-it-still-beating-the-foreign-exchange-market/); [RePEc](https://econpapers.repec.org/RePEc:eee:inecon:v:102:y:2016:i:c:p:188-208)
- **The recent FX subperiod is weak [PR].** A related stepwise-test study reports "virtually no traditional rule is significant in the 2006-2015 sub-sample." Hsu & Taylor (2013) and Coakley et al. (2016) also find little after correction. — [Essex repository](https://repository.essex.ac.uk/18805/1/1-s2.0-S1057521916301958-main.pdf); [Springer FMPM 2023](https://link.springer.com/content/pdf/10.1007/s11408-023-00433-2.pdf)

### Inferences
- **RSI(2) Connors-style (background knowledge, not fetched this session).** Canonical daily rule: long when close > SMA(200) and RSI(2) < 5–10; exit when close > SMA(5) or RSI(2) > 70; no stop. It was designed for daily equity indices, where it historically showed about 70%+ win rates with small average gains. Its intraday transplant has no credible cost-inclusive evidence. The Coinquant data show RSI-2 losing in bear regimes even at 1h.
- **IBS, Internal Bar Strength = (C − L)/(H − L) (background knowledge).** Documented on daily equity-index ETFs/futures (long when IBS < 0.2, exit next close). I found no minute-bar evidence. Treat it as unproven intraday.
- **VWAP ± k·σ bands.** I found no independent, cost-inclusive minute-level backtest on ES/MES or BTC. Practitioner claims exist but are unverified (Gap).
- The pattern across all sources is consistent: **win rate is not the metric.** At 55–68% win rates, payoffs were negative because average losses exceeded average wins plus costs. Minute bars multiply trade count and therefore the cost drag (Edgoro: costs about half of gross at 4h; the 15m BB results were the worst cell).
- The FX technical-rule literature is daily-horizon trend-following, not scalping. Its relevance here is methodological: correct for testing many parameterizations (SPA/Reality Check/Romano-Wolf) and expect decay.

### Gaps
- No QuantConnect or Robot Wealth minute-bar replication with costs was retrieved this session. Robot Wealth/QuantConnect pages were not fetched.
- Brock, Lakonishok & LeBaron (1992) and STW (1999) exact Reality-Check p-values and 1987–96 OOS numbers were not retrieved.
- No cost-inclusive VWAP-band study for MES/ES was found.

---

## Q3. Liquidity sweep / stop-hunt reversals: stop clustering, round numbers, cascades, and "ICT/SMC"

### Takeaway
There is solid **peer-reviewed microstructure evidence** that stop-loss orders cluster just beyond round numbers and that crossing them **accelerates** moves (cascades). Take-profit clusters at exact round numbers produce **slightly more frequent reversals**. The tradable implication is weaker than retail "sweep-and-reverse" lore. The magnitudes are tiny (sub-basis-point differences over 15 minutes in 1996–98 FX), and the **continuation** after a stop run is the more robust effect, not the reversal. For crypto liquidation cascades, the evidence describes mechanics (mark-price undershoot, open-interest collapse, slow liquidity recovery), but **no peer-reviewed study shows that fading cascades is profitable net of costs**. ICT/"smart money concepts" have **no independent statistical evidence** and should be rated marketing.

### Cited Findings
- **Osler (2003), "Currency Orders and Exchange Rate Dynamics," J. Finance 58(5):1791–1819 [PR].** Uses the first individual stop-loss/take-profit order data to explain two technical-analysis predictions: trends reverse at support/resistance, and trends accelerate after crossing them. — [RePEc JF](https://econpapers.repec.org/RePEc:bla:jfinan:v:58:y:2003:i:5:p:1791-1819); [NY Fed SR 125](https://econpapers.repec.org/RePEc:fip:fednsr:125)
- **Osler (2005), "Stop-Loss Orders and Price Cascades in Currency Markets" (NY Fed Staff Report 150; J. Int'l Money & Finance 2005) [PR/WP].** Figures from the staff-report text:
  - **Order data:** more than $55bn of orders in USD/JPY, GBP/USD and EUR/USD; stop-losses are 43% of orders by volume and 45% by value.
  - **Clustering:** almost **10%** of all orders sit at rates ending in **00**; about 3% at each other rate ending in 0; about 2% at other rates.
  - **Asymmetric placement:** executed stop-loss **buys cluster just above** round numbers (00 or 50), and stop-loss **sells just below**. For example, 14.3% of executed stop-loss buys have requested rates ending in [01,10] vs 6.9% in the range just below. Take-profits cluster **at** the exact round number (about 9.9%), with no above/below skew.
  - **Price tests:** minute-by-minute quotes for DEM, JPY and GBP vs USD, NY hours, Jan 1996–Apr 1998. "Reaching" a level means coming within 0.01%.
  - **Speed after crossing:** example result, USD/DEM moves on average **0.061% in the 15 minutes after crossing a round number vs 0.054% after an arbitrary number**, significant via bootstrap.
  - **Reversal frequency:** **59.3% at round numbers vs 54.8% at arbitrary numbers** (significance < 0.001%).
  - **Duration and caveats:** the stop-loss response is larger and longer-lasting than the take-profit response, and is "statistically significant for hours, although not for days." Osler says statistics cannot prove causality. The paper quotes "running the stops" as a known dealer practice and gives the Deutsche Bank USD/JPY 2002 example: below ¥129.80 the pair "fell within seconds to ¥129.40." — [NY Fed SR150 PDF](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf); [SR150 page](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.html)
- **Crypto round-number clustering [PR].** Urquhart (2017, Economics Letters 159:145–148) finds significant clustering of BTC prices at whole numbers, linked to the negotiation hypothesis. Another study reports more than 10% of BTC prices ending in 00 but **no significant pattern in returns after the round number**. Clustering fell after BTC futures were introduced. Traders place limit orders at round numbers in crypto LOBs. — [IDEAS Urquhart 2017](https://ideas.repec.org/a/eee/ecolet/v159y2017icp145-148.html); [Applied Econ Letters 2019](https://ideas.repec.org/a/taf/apeclt/v26y2019i10p807-811.html); [Finance Research Letters 2019](https://ideas.repec.org/a/eee/finlet/v28y2019icp337-342.html)
- **Seuma (2026), arXiv 2607.27070 [WP].** Covers seven BTCUSDT (Binance USD-M) cascades: May 2022 LUNA, Nov 2022 FTX, Aug 2024 yen-carry, Dec 2024, Feb 2025 tariffs, Apr 2025 "Liberation Day," and **10 Oct 2025** (more than $19B liquidated, about 1.6M accounts, intraday **OI −24.6%**, onset 20:50 UTC).
  - No early-warning variable is consistent across events.
  - The one placebo-tested regularity: **taker order-flow variance compresses** before six of seven cascades (Fisher p ≈ 5×10⁻⁶). The authors call it a population-level precursor, not a per-event alarm.
  - Data notes: Binance per-event liquidation snapshots are discontinued. Data come from 1m klines and 5m OI/taker metrics.
  - **Post-cascade returns are not studied.** — [arXiv HTML](https://arxiv.org/html/2607.27070v1)
- **Lim (2026), "Anatomy of a Crypto Cascade: Minute-Level Evidence from the October 2025 Crash" [WP, SSRN].** On Binance/Bybit, the **mark price used for liquidation triggers undershot both spot and futures**, creating a reflexive feedback loop. This is from a search snippet; the SSRN page returned 403. — [SSRN 6579278](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6579278)
- **Lim, "Two-Regime Liquidity Recovery…" (Hyperliquid, 10 Oct 2025) [WP].** Market-maker pricing (spreads) recovers within weeks, but inventory commitment (depth) contracts persistently. — [SSRN 6636998](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6636998)
- **Coinglass [PRAC/data vendor].** Large liquidation events are often read as a washout before a rebound, but "do not directly guarantee an immediate trend reversal." In strong trends they may be mid-trend corrections. — [Coinglass BTC liquidations](https://www.coinglass.com/liquidations/BTC)
- **Open-Alpha-Lab [PRAC].** The bounce sign after liquidation spikes is treated as unknown ("bounce or falling knife"). Free liquidation-USD history is unavailable, so the study is synthetic-only and capped at WEAK evidence. — [GitHub](https://github.com/Guillain-RDCDE/Open-Alpha-Lab/blob/main/studies/586-liquidation-cascade/docs/references.md)
- **ICT/SMC evidence = none independent [MKT].**
  - The TradingView "Sweep & Reverse" script defines a sweep as a wick through a prior swing high/low followed by a close back inside. Its author warns that "in strongly trending markets, sweeps frequently continue rather than reverse," that results are sensitive to pivot length, stop distance and filters, and that a high win rate on few trades is not meaningful. — [TradingView script](https://www.tradingview.com/script/GoeqO1ev-Sweep-Reverse-Liquidity-Sweep-Reversal-Strategy/)
  - The Backtrex vendor claims 1,247 trades on EURUSD + XAUUSD over 5 years, PF 1.68 and 53.2% win rate with an "ICT kill zone" filter. There is no published OOS split, cost model or audit. **Rate: MKT/UNVERIFIED.** — [backtrex.com](https://backtrex.com/en/blog/liquidity-sweep-strategy-backtest-results)

### Inferences
- **Osler's results imply two distinct, opposite trades:**
  - **(a) Fade at take-profit clusters** (the exact 00/50 level, *before* it is breached): a reversal-frequency edge of about 4.5 percentage points (59.3% vs 54.8%).
  - **(b) Go with the break** once price trades through the stop cluster just beyond the round number: an acceleration edge.

  The retail "liquidity sweep reversal" (fade *after* the stops are run) is **not** what Osler documents. Her stop-cluster response is continuation that lasts hours. A sweep-reversal trade has to show that the cascade overshoots and then reverts. That is a separate empirical claim, untested in the peer-reviewed FX literature I found.
- **The edges are microscopic relative to costs.** 0.061% vs 0.054% is **0.7 bp** of excess move over 15 minutes, on 1996–98 data. That is smaller than an all-in retail FX round trip (about 0.5–1.0 bp on EURUSD at ECN, UNVERIFIED) and has likely decayed with algorithmic market making. The reversal-frequency difference is a probability edge without a stated payoff size.
- **For crypto cascades, the mechanism supports a temporary overshoot.** Forced selling plus mark-price undershoot plus withdrawn depth all point to price pressure, the Coval-Stafford/Nagel logic. But the overshoot can extend for hours (FTX and LUNA were information events, not pure liquidity events). The Oct 2025 recovery of *depth* was slow, which raises slippage for anyone fading.
- **Most defensible sub-variant:** fading cascades that are **leverage-driven** (large OI drop, extreme liquidation notional, no fundamental news) rather than **information-driven** (exchange failure, depeg, regulatory). The classification has to be made in real time, which is hard.

### Gaps
- No peer-reviewed or reputable independent study of **forward returns after Binance/Bybit liquidation spikes** (e.g., 5/15/60-min returns conditional on liquidation-notional percentile) was found. **This is the critical gap, and the user will need their own event study.** Data sources: Binance `forceOrder` stream (my background knowledge, UNVERIFIED: it reports at most one liquidation per symbol per 1000 ms, so it understates volume), Coinglass/Amberdata/Kaiko paid history.
- Kaiko, Glassnode and Amberdata reports on Oct 10, 2025 were not retrieved.
- Osler's evidence is from 1996–98 FX. No modern replication on FX, ES or crypto stop clustering was found.

---

## Q4. Regime filters (ranging vs trending, sessions, news)

### Takeaway
Evidence for specific filter thresholds such as ADX > 25 or Hurst < 0.5 at minute horizons is **practitioner-only**. Filters chosen in hindsight overstate results (Coinquant labeled regimes ex post). The best-supported conditioning variables from peer-reviewed work are: **volatility/liquidity stress** (Nagel: reversal pays more when VIX is high), **large jumps** (Wen et al.: reversal after information-based large moves), **scheduled events** (FOMC changes the pattern; Wen et al.), and **benchmark fix times** in FX (Krohn et al.).

### Cited Findings
- Reversal returns rise with VIX, and the Sharpe ratio is higher in turmoil. — [Nagel, NBER](https://nber.org/papers/w17653)
- Crypto intraday predictability changes around large jumps, FOMC and liquidity changes. — [Wen et al. 2022](https://www.sciencedirect.com/science/article/abs/pii/S1062940822000833)
- Mean reversion performs very differently by regime: average bull +16.3%, sideways −2.2%, bear −40.6%. Regimes were labeled in hindsight, so this is not a usable filter as tested. — [Coinquant](https://www.coinquant.ai/blog/building-a-mean-reversion-strategy-in-cryptocurrency-markets-evidence-from-78-backtests)
- ADX filters (1h > 20, 4h > 25) plus a 4h RSI trend filter did not rescue BB mean reversion on 8 of 9 perps. — [WhatDoesntWork](https://whatdoesntwork.com/research/bollinger-rsi-adx-crypto-mean-reversion/)
- In FX the Asian session has V-shaped reversals at the Tokyo-area fixes. This is a fix-time effect, not a generic "Asian range" effect. — [BoC SWP 2021-48](https://www.bankofcanada.ca/wp-content/uploads/2021/10/swp2021-48.pdf)
- Taker order-flow variance compression preceded 6 of 7 BTC cascades. It is a possible "stand aside / widen stops" flag, at population level only. — [arXiv 2607.27070](https://arxiv.org/html/2607.27070v1)

### Inferences
- **Codable regime set, to be validated walk-forward:**
  - **Trend-strength veto:** |variance ratio VR(q)| test on 1m returns over a trailing window. Lo-MacKinlay VR(q) > 1 significantly means trending, so veto fades. Alternatives: ADX(14) on 5m > 30, or a rolling Hurst exponent (R/S or DFA on 1m log-returns, 2–6h window) > 0.55. All thresholds are untested here.
  - **Vol percentile:** use realized-vol percentile (e.g., 1h RV vs trailing 30 days) as a **sizing** input rather than a binary veto, given Nagel. Fade only after a vol spike that is decaying (RV over the last 15m < RV over the prior 15m), not one that is rising.
  - **News blackout:** ±15–30 min around FOMC, CPI, NFP and other high-impact releases. For MES, avoid 08:30 ET and 10:00 ET releases and 14:00 ET FOMC. For crypto, the same US macro times plus exchange-incident headlines.
  - **Session windows:** MES RTH after the opening range (e.g., after 10:00 ET) through 15:30 ET. FX major pairs in the low-volatility Asian hours, with fix-aware timing.
- Do not use a regime filter that is computed with information from the trade's own future window, e.g., labeling a "range day" from the day's full high-low.

### Gaps
- No peer-reviewed study validating ADX/Hurst/VR thresholds for minute-level mean reversion in BTC, MES or FX was found.
- The direction and size of the fix-time FX reversal were not extracted from the full paper.

---

## Q5. Costs, trade frequency, win rate, break-even math

### Takeaway
Short-horizon reversal scalps have small gross edges per trade, so **execution type (maker vs taker) decides viability.** At taker fees on crypto perps, a 60–70% win-rate system with a typical asymmetric payoff needs an unrealistic win rate to break even. Maker execution roughly halves the cost but introduces adverse selection and fill uncertainty.

### Cited Findings
- Costs consumed 51.3% of gross on 4h-bar indicator strategies with about 240 trades. — [Edgoro](https://edgoro.com/blog/default-indicator-settings-crypto-backtest)
- A 15m BB strategy: 693 trades, more than $2,300 in fees on $10,000 (more than 23% of capital in fees). — [Coinquant](https://www.coinquant.ai/blog/building-a-mean-reversion-strategy-in-cryptocurrency-markets-evidence-from-78-backtests)
- High win rate with negative expectancy is common: 14 of 78 cells won ≥65% and lost money; NEAR won 63.2% at −67.6 bps/trade. — [Coinquant](https://www.coinquant.ai/blog/building-a-mean-reversion-strategy-in-cryptocurrency-markets-evidence-from-78-backtests); [WhatDoesntWork](https://whatdoesntwork.com/research/bollinger-rsi-adx-crypto-mean-reversion/)
- Practitioner guides suggest 0.3–0.5% all-in for "high-frequency" retail crypto modeling. This is likely too high for VIP or maker execution, and it is UNVERIFIED. — [search summary of backtesting guides](https://backtestme.com/guides/mean-reversion-strategies)

### Inferences (math; fee levels are UNVERIFIED background knowledge, so check current schedules)
- **Assumed cost levels (verify):**
  - **Binance USD-M perps, VIP0:** about 2 bp maker / 5 bp taker per side. **Bybit:** about 2 / 5.5 bp.
  - **MES:** tick 0.25 pt = $1.25. All-in commission plus exchange fees about $0.50–1.25 per side. At an index level near 6,000–7,000, one tick is about 0.36–0.42 bp of notional.
  - **EURUSD ECN:** raw spread about 0.1–0.3 pip plus about $3–3.5 per side per 100k, so about 0.6–1.0 bp round trip.
- **Break-even formula.** Gross average win W, gross average loss L, round-trip cost C (all in bp). Expectancy is E = p(W − C) − (1−p)(L + C) = pW − (1−p)L − C. The break-even win rate is **p\* = (L + C)/(W + L)**.
- **BTC perp scenarios:**
  - Scalp W = 20 bp, L = 40 bp (typical mean-reversion asymmetry: tight target, wider stop).
    - Taker both legs, C = 10 bp + 2 bp slippage = 12 → p\* = 52/60 = **86.7%**.
    - Maker entry + taker exit, C ≈ 7 + 1 = 8 → p\* = 48/60 = **80%**.
    - Maker both legs, C = 4 → p\* = 44/60 = **73.3%**.
    - So a "70% win-rate" scalp is **negative EV even at maker-maker** with this payoff shape.
  - Cascade fade W = 150 bp, L = 150 bp, C = 12 → p\* = 162/300 = **54%**. At C = 4, p\* = 51.3%. Larger target moves make costs proportionally small, which is why event-driven fades of multi-σ moves are structurally more viable than continuous band scalps.
- **MES:** a 4-tick target / 6-tick stop scalp. Assume 1 tick slippage on the stop, a passive entry, and commission about 0.6 tick round trip (1.5 ticks combined on the losing side in this rough figure). Then p\* ≈ (6 + 1.5)/(4 + 6) = **75%**. A VWAP ±2σ fade targeting VWAP (often 10–20 ticks) with a 10-tick stop needs p\* ≈ 11.5/25 ≈ **46%** for a 15-tick target.
- **Trade frequency vs cost:** at 20 trades/day × 250 days × 8 bp = **400% of notional per year in costs at 1× leverage**. The gross edge must exceed that, which is the core reason continuous minute-bar indicator systems fail.
- **Win-rate profile:** mean-reversion systems commonly show 60–75% win rates with a left-skewed P&L (many small wins, occasional large losses on trend days). This is consistent with the cited backtests (55–68% wins, negative expectancy).

### Gaps
- Current 2026 fee schedules for Binance, Bybit, CME/MES and major FX ECNs were not fetched. All figures above need verification.
- No empirical slippage distribution during liquidation cascades was found. Slippage is likely many times normal, given the depth contraction documented by Lim.

---

## Q6. Failure modes and backtest pitfalls

### Takeaway
The dominant failure modes:
- trend days and information-driven moves, where fades become falling knives;
- fat left tails;
- cost underestimation;
- **backtest artifacts**: bid-ask bounce in last-trade data, same-bar fills, look-ahead in VWAP/bands, optimistic limit-order fills, and hindsight regime labels;
- data snooping across many parameter sets.

### Cited Findings
- Reversal in last-trade returns is "consistent with the negative autocorrelation induced by bid-ask bounce." Backtests on last-trade closes overstate tradable reversal. — [HKS 2010](https://arxiv.org/pdf/1005.3535.pdf)
- "In strongly trending markets, sweeps frequently continue rather than reverse — no combination of filters here eliminates that risk." — [TradingView Sweep & Reverse](https://www.tradingview.com/script/GoeqO1ev-Sweep-Reverse-Liquidity-Sweep-Reversal-Strategy/)
- Stop-loss cascades propagate trends for hours, so fading them early fights a documented continuation. — [Osler SR150](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf)
- Optimized results did not replicate: NEAR's claimed +179% became −27.4% under the stated rules. — [WhatDoesntWork](https://whatdoesntwork.com/research/bollinger-rsi-adx-crypto-mean-reversion/)
- Data-snooping correction removes much of the apparent technical-rule profitability; FX rules are mostly insignificant in 2006–2015. — [STW 1999](https://econpapers.repec.org/RePEc:bla:jfinan:v:54:y:1999:i:5:p:1647-1691); [Essex repository](https://repository.essex.ac.uk/18805/1/1-s2.0-S1057521916301958-main.pdf)
- Post-cascade depth stays depressed for weeks (Hyperliquid, Oct 2025), so fills are worse than normal-period models assume. — [Lim SSRN 6636998](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6636998)
- The Oct 2025 cascade was news-shock driven: price showed no critical-slowing-down signature, so there was no warning. — [arXiv 2607.27070](https://arxiv.org/html/2607.27070v1)

### Inferences (backtest hygiene checklist for the implementer)
1. **Prices:** use bid/ask (or mid plus half-spread) for fills, never last-trade closes, to strip bounce.
2. **Signal timing:** compute signals on bar t's close and fill at bar t+1's open, or at a limit price only if price **trades through** the limit by at least 1 tick. Do not fill on a touch. Model queue position where possible.
3. **VWAP look-ahead:** session VWAP at bar t must use only bars ≤ t. The σ for the bands must be the running volume-weighted std up to t. Do not use full-day VWAP or a centered rolling std. Anchor sessions consistently (UTC 00:00 for crypto, or a rolling 24h; RTH 09:30 ET for MES).
4. **Bands:** BB(20,2) on bar t uses closes t−19..t. Entering on "close below band" and filling at that same close is a look-ahead if the band uses that close. That is borderline acceptable only with next-bar fills.
5. **Regimes:** no ex-post regime labels. Filters must be computable in real time.
6. **Multiple testing:** report the number of parameter combinations tried and apply White's Reality Check, Hansen SPA or Romano-Wolf stepdown (STW, HTW).
7. **Stress:** include FTX (Nov 2022), LUNA (May 2022), Aug 2024 and Oct 10, 2025 in the test window. Model 3–10× normal slippage and possible exchange API outages during cascades (cascade slippage multipliers are UNVERIFIED assumptions).
8. **Funding** on perps for holds that span funding timestamps (8h on Binance/Bybit for most symbols, UNVERIFIED for 2026), and **crowding**: popular sweep levels (prior day high/low, round numbers) are where many retail stops and fade orders sit.

### Gaps
- No quantified study on crowding decay of retail-popular mean-reversion levels was found.

---

## Q7. Most defensible codable variants (proposed rules) and ranking

### Takeaway
Ranked by evidence quality × net-of-cost plausibility:
1. **Event-driven fade of liquidity shocks** (BTC/ETH perp liquidation-cascade overshoots), using passive limit entries, a VWAP/retracement exit and a time stop. The mechanism is supported (Nagel, Coval-Stafford, Wen et al. jump reversals, mark-price undershoot), the edge per trade is large relative to costs, but there is **no direct net-of-cost evidence yet**.
2. **FX fix-time reversal** (peer-reviewed-adjacent WP evidence, authors claim tradable after costs). Low frequency, institutional execution needed.
3. **MES VWAP ±kσ fade in balanced sessions.** Plausible but unverified; needs a news and trend-day veto.
4. **Continuous minute-bar BB/RSI(2)/IBS scalps.** Cost-inclusive evidence is negative; rank last.
5. **ICT/SMC "liquidity sweep" reversals.** No independent evidence; marketing.

### Cited Findings
- Reversal after information-based large jumps in BTC/ETH/LTC/XRP. — [Wen et al. 2022](https://www.sciencedirect.com/science/article/abs/pii/S1062940822000833)
- Liquidity-provision returns spike with volatility stress. — [Nagel 2012](https://nber.org/papers/w17653)
- Forced-sale price pressure reverses. — [Coval & Stafford 2007 via lab notes](https://github.com/Guillain-RDCDE/Open-Alpha-Lab/blob/main/studies/586-liquidation-cascade/docs/references.md)
- Liquidation-trigger mark price undershot spot/futures in Oct 2025. — [Lim SSRN 6579278](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6579278)
- OI fell 24.6% intraday on 10 Oct 2025, and 5m OI/taker data are available from Binance. — [arXiv 2607.27070](https://arxiv.org/html/2607.27070v1)
- FX fix reversals are claimed exploitable after costs. — [BoC SWP 2021-48](https://www.bankofcanada.ca/wp-content/uploads/2021/10/swp2021-48.pdf)
- Minute/hour indicator scalps lose after costs. — [WhatDoesntWork](https://whatdoesntwork.com/research/bollinger-rsi-adx-crypto-mean-reversion/); [Coinquant](https://www.coinquant.ai/blog/building-a-mean-reversion-strategy-in-cryptocurrency-markets-evidence-from-78-backtests)

### Inferences: concrete rule specs (all parameters are starting points for walk-forward testing, not validated values)

**Strategy A: BTC/ETH perp liquidation-cascade fade (Binance/Bybit USD-M)**
- **Data:**
  - 1m bid/ask or trades plus L2 top-of-book;
  - 5m open interest; liquidation feed (Binance `!forceOrder@arr` websocket, Bybit `liquidation` topic, or Coinglass/Amberdata history for backtests);
  - funding rate;
  - macro calendar.
- **Volatility baseline:** σ5 = std of 5m log-returns over the trailing 7 days, excluding the current hour.
- **Trigger (long fade; mirror the rules for a short squeeze). All must hold at 1m close t:**
  1. The 15m return ending at t ≤ −4·σ5·√3 (about a 4σ 15-minute drop).
  2. Long-liquidation notional over the last 15m ≥ 99th percentile of the trailing 30-day distribution of 15m windows.
  3. OI change over the last 15m ≤ −3% (forced deleveraging, not new shorts).
  4. No scheduled high-impact macro release in the window [t−30m, t+15m], and no known exchange-solvency or stablecoin-depeg headline. The headline veto is manual or a news-feed flag. Without it the strategy fades FTX/LUNA-type information events.
  5. Optional precursor flag: taker order-flow variance compression in the prior 6h. Use it to raise caution or cut size, not as an entry condition (Seuma).
- **Entry:** post-only limit ladder at P_t − {0.5, 1.0, 1.5}·σ5·√3 below the trigger close, 1/3 size each, live for 10 minutes. Cancel unfilled orders at 10 min.
  - Alternative variant to test: a confirmation entry on the first 1m close above the prior 1m high, taker.
  - Backtest fills only on trade-through.
- **Exits, whichever comes first:**
  1. **Target:** 50% retracement of the move from the 60-minute pre-trigger high to the post-trigger low, or the anchored VWAP from cascade start, whichever is nearer.
  2. **Time stop:** 60 minutes after the first fill; exit with a passive limit at mid for 2 min, then taker.
  3. **Hard stop:** the cascade low − 1.0 × (cascade range), or 6·ATR(1m, 60), as a stop-market order. Assume 3–5× normal slippage.
- **Risk:** 0.25–0.5% of equity at risk per event; one position per asset; BTC and ETH correlated, so a combined cap; daily loss kill-switch of 1.5R; avoid holding across a funding timestamp unless the funding sign favors the position.
- **Expected profile (untested):** low frequency, perhaps tens of events per year per asset at these thresholds (UNVERIFIED), with larger per-trade moves (100–300 bp). Cost ratio is small (C ≈ 4–12 bp vs W ≈ 150 bp, p\* ≈ 51–54% at W = L).
- **Validation:** an event study first, then the strategy test.
  - **Event study:** forward 5/15/60/240-min mid-quote returns after triggers vs a matched placebo (random times with the same 15m return magnitude but no liquidation spike).
  - **Strategy test:** a permutation test, a walk-forward split by year, and an explicit Oct 10 2025, FTX and LUNA stress test.

**Strategy B: MES VWAP ±2σ fade, balanced-session only**
- **Universe and session:** MES front month, RTH. Trade only between 10:00 and 15:30 ET. Flat by 15:45.
- **Indicators:**
  - VWAP_t = Σ(p·v)/Σv from 09:30 ET using 1m bars ≤ t;
  - σ_t = sqrt(Σv·(p − VWAP_t)²/Σv);
  - 30-minute opening range (OR).
- **Trend-day veto:** skip the session if any of these hold at 10:00 ET:
  - (i) price is beyond the OR by more than 1×OR width;
  - (ii) |VWAP slope over the last 30 min| > a threshold set to the 80th percentile of history;
  - (iii) the 1m variance ratio VR(10) over 09:30–10:00 > 1.3.
- **Entry:** short when the 1m close > VWAP + 2σ, long when the 1m close < VWAP − 2σ. Use a limit at the close price; it fills only if traded through by 1 tick within 3 bars.
- **Exit:** target VWAP, stop at entry ± 1σ beyond the band (VWAP ± 3σ), time stop 45 min.
- **News blackout:** ±15 min around 08:30/10:00 ET releases and 14:00 ET FOMC (entire FOMC afternoon).
- **Max trades:** 2–3 per day.
- **Cost math:** a 12–20 tick target vs a ~1.5 tick round-trip cost makes it viable if p is above about 45–50%. Evidence status: unverified.

**Strategy C: FX fix-time reversal (EURUSD, USDJPY)**
- Trade the documented V-shaped reversal around the Tokyo fix (09:55 JST) and the WM/Reuters London 4pm fix.
  - Direction is set by the pre-fix drift: fade the move from t−30m to the fix over t to t+30m.
  - Exit by time.
- Requires ECN costs below about 1 bp round trip. Exact direction and size must be taken from Krohn-Mueller-Whelan before coding.

**Strategy D (benchmark/control): BB(20,2) or RSI(2) < 10 on 5m with next-bar fills and maker execution**
- Keep it as a null-hypothesis control. Cost-inclusive evidence says it is likely negative.

**ICT/SMC "liquidity sweep" (prior-day high/low wick plus close back inside):**
- Codable for testing: high_t > PDH and close_t < PDH, then short at the next open, stop above high_t, target the session VWAP.
- Treat it as a hypothesis with no independent evidence. Osler's data imply that runs through stop clusters tend to *continue* for hours.

### Gaps
- Event counts, forward-return distributions and hit rates for Strategy A are unknown and must come from the user's own data. This is the main open question for ranking.
- No independent minute-level evidence for Strategy B was found.
- The exact sign and magnitude of fix-time FX reversals were not extracted.
- Whether the 2024–2026 growth of crypto market-making and ADL (auto-deleveraging) mechanics has shrunk cascade overshoots is unknown.
