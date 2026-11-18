# Crypto Funding-Rate and Basis Strategies, and Short-Horizon Stat Arb / Pairs Trading, as Retail-Automatable Alternatives to Scalping (as of Nov 2026)

Source rating key: **[PR]** peer-reviewed journal; **[WP]** academic working paper or preprint (BIS, arXiv, SSRN), not yet or not verifiably peer-reviewed; **[DOC]** official exchange documentation; **[NEWS]** crypto or financial press; **[PRAC]** practitioner or vendor blog; **[MKT]** marketing. "Unverified" means I saw it only in a search snippet or secondary summary, not in the primary text.

Research note: about 20 search or fetch calls. The primary texts I read in full or in large part were He et al. (arXiv HTML) and the Hyperliquid funding docs. The other academic findings come from abstracts and secondary summaries and are flagged.

---

## 1. Funding mechanics (Binance, Bybit, OKX, Hyperliquid) and basis-trade construction

### Takeaway
Funding on Binance and Hyperliquid follows the same formula: F = average premium index + clamp(interest − premium, ±0.05%). The interest leg is fixed at 0.01% per 8h, so whenever the premium is small, funding pins to a baseline of about 11% APR paid by longs to shorts. That baseline is the main reason delta-neutral "cash-and-carry" earns money. Intervals now vary by venue and symbol: Binance and Bybit use 8h by default with some symbols on 4h or 1h, and Hyperliquid pays hourly. A bot has to normalize funding to an hourly or annual rate before comparing venues.

### Cited Findings
- **Binance formula [DOC]:** Funding Rate = Average Premium Index (P) + clamp(interest rate − P, −0.05%, +0.05%). The interest rate defaults to 0.03% per day (0.01% per 8h; 0.00125% per 1h). It is 0% for BNBUSDT and ETHBTC. For intervals other than 8h, F = [P + clamp(0.01% − P, ±0.05%)] / (8/N), where N is the interval in hours. The example given is PUMPUSDT on 4h, divided by 2. — [Binance announcement](https://www.binance.com/fr/support/announcement/detail/c00588a7e8504b3eb28d02a2da00530b)
- **Settlement times [PRAC]:** the default 8h settlements on major venues are 00:00, 08:00 and 16:00 UTC. He et al. used Binance funding at 00:00, 08:00 and 16:00 GMT. — [arXiv 2212.06888v5](https://arxiv.org/html/2212.06888v5); [search summary of bit.com/industry guides](https://www.bit.com/knowledge-hub/funding-rate)
- **Hyperliquid [DOC]:**
  - Formula: F = P + clamp(interest − P, −0.0005, 0.0005). Interest is "0.01% every 8 hours, which is 0.00125% every hour", which the docs equate to 11.6% APR paid to shorts.
  - Premium = impact_price_difference / oracle_price. It is sampled every 5 seconds and averaged over the hour.
  - Funding is paid every hour at 1/8 of the computed 8h rate and is capped at 0.5% per hour. Payment = size × oracle price × rate.
  - The docs' own worked example exceeds the cap, an internal inconsistency in the docs. — [Hyperliquid docs](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding)
- **Sampling differences [PRAC]:** Hyperliquid settles hourly and samples every 5s. Binance and Bybit settle 8-hourly and use per-minute TWAP sampling, so rates must be normalized before cross-venue comparison. — [OneKey blog](https://onekey.so/blog/ecosystem/funding-rate-divergence-dex-cex/)
- **Theory [WP]:** He, Manela, Ross & von Wachter derive the frictionless perp price F = κ/(κ − (r − r′))·S, with κ = 1095 (three 8h payments × 365 days). The deviation measure is ρ ≈ κ(f − s) − (r − r′). Their trading-cost no-arbitrage bounds are wide: about ±53% annualized for the lowest-fee tier and about ±180% for the "high-fee" tier. They also note that real funding departs from theory because of the 0.01% clamp region, weighting of recent observations and impact-margin adjustments. — [arXiv 2212.06888v5](https://arxiv.org/html/2212.06888v5)
- **Quarterly and CME basis:** the trade is long spot or spot ETF plus short a dated future. The annualized basis is (F/S − 1) × 365/days-to-expiry. Hedge funds ran it at scale as "long spot BTC ETF / short CME futures". — [The Block, Apr 2026](https://www.theblock.co/post/396722/cme-bitcoin-futures-activity-slumps-to-14-month-low-as-basis-trade-unwind-drains-institutional-demand) [NEWS]

### Inferences
- **Baseline carry:** the default is 0.01% × 3 × 365 ≈ 10.95% simple APR on short-perp notional (Hyperliquid quotes 11.6%, likely a compounded or different convention). This is the "floor" most delta-neutral bots harvest whenever the premium sits inside the ±0.05% clamp band. It is a design parameter of the exchange, not a market risk premium, and it can still go negative when the premium is strongly negative.
- **Return on capital:** because of capital tied up in both legs, return on deployed capital is lower than return on notional. Long $1 of spot plus short $1 of perp at L× margin uses about $(1 + 1/L). At L = 3, the 10.95% baseline becomes about 8.2% on capital before fees. Unified or portfolio margin (spot as perp collateral) brings this closer to the notional rate but adds liquidation coupling.
- **Bot requirements:** a bot should read the per-symbol interval from the API (for example Binance `fundingInfo`/premiumIndex endpoints, Bybit instrument info) rather than hard-coding 8h, since Binance now changes intervals per symbol.

### Gaps
- I did not fetch Bybit's or OKX's own funding documentation. Bybit's and OKX's exact clamps, caps and interest components are assumed similar to Binance's but are **unverified**.
- I did not find the exact date or rules for when Binance switches a symbol to a 4h or 1h interval (for example, when funding hits the cap).

---

## 2. Evidence on returns of delta-neutral funding capture and futures basis

### Takeaway
The best evidence is He et al. (Binance, 2020–Mar 2024). A threshold-based perp-vs-spot arbitrage earned Sharpe ratios of about 1.8 (BTC) to about 4.8 (BNB) and annual returns of about 6–23% even at the highest fee tier they modelled, with maximum drawdowns under 9%. Profits were shrinking about 11% a year. BIS reports average crypto carry above 10% p.a. with spikes to 60%, driven by retail leverage demand and scarce arbitrage capital. Live evidence from 2025–26 (Ethena, CME basis) shows the carry has compressed to roughly T-bill levels, about 4–5%, for much of the period.

### Cited Findings
- **He, Manela, Ross & von Wachter, "Fundamentals of Perpetual Futures" (arXiv 2212.06888, v6 Aug 2024) [WP, by well-regarded authors; Manela is at WashU/Reichman; publication status not confirmed]:** [arXiv HTML v5](https://arxiv.org/html/2212.06888v5), [abstract](https://arxiv.org/abs/2212.06888)
  - *Rule:* open when |ρ| exceeds the fee-tier no-arbitrage bound; close when ρ first returns to 0. They use hourly Binance data with BTC and ETH from 2020-01-08 to 2024-03-11.
  - *Fee tiers (Binance maker fees, spot/futures):* High (individual) 6.75/1.44 bps, Medium 4.5/0.72 bps, Low 2.25/0.18 bps. Indirect costs (spread plus impact) are under 0.35 bps. Note that the "High" tier still assumes VIP volumes (more than $1mn spot and $15mn futures per 30 days), so it is **not** a VIP-0 retail tier.
  - *Results, Sharpe and annual return at the High-cost tier:* BTC 1.80 / 6.38%; ETH 2.55 / 9.59%; BNB 4.84 / 18.41%; DOGE 3.58 / 23.31%; ADA 2.68 / 12.03%.
  - *Maximum drawdowns at High cost:* BTC −4.43%, ETH −3.94%, BNB −1.11%, DOGE −8.56%, ADA −4.35%.
  - *No-fee Sharpe:* BTC 3.53, ETH 4.83, BNB 12.31, DOGE 10.35, ADA 10.43.
  - *Time in market:* BTC is active only 20% of the time at High cost, and the average holding time is 135h versus 19h with no fees. Long-spot-only (no spot shorting) Sharpe is lower: BTC 1.62, ETH 2.23.
  - *BTC Sharpe by year, High cost:* 2020 2.26; 2021 2.39; 2022 0.70; 2023 1.32; 2024 (Q1 only) 11.52. Time in market fell from 28.7% (2020) to 9.2% (2022).
  - *Return decomposition (BTC, no fee):* 13.70% total = 8.64% from price convergence + 5.06% from funding. Most of the profit comes from **convergence of the perp-spot gap**, not from holding funding.
  - *Trend:* |ρ| shrinks about 11% per year, more than 44% over the sample. Past 120-day returns predict ρ (R² up to 0.33). Spot volatility does not explain it.
  - *Caveats:* the trade is not riskless because there is no fixed maturity, margin must be maintained throughout, and temporary widening can force liquidation. Results exclude taxes and operational frictions.
- **Schmeling, Schrimpf & Todorov, "Crypto carry", BIS WP 1087 (Apr 2023, revised Oct 2025; also CEPR DP 20719) [WP, central-bank research, high credibility]:** [BIS page](https://bis.org/publ/work1087.htm), [PDF](https://www.bis.org/publ/work1087.pdf)
  - Crypto futures carry averages more than 10% p.a. and can reach 60% p.a. An earlier abstract version said "sometimes exceeding 40%".
  - Interest-rate differentials explain very little. Carry is driven by convenience yield from trend-chasing retail demand for leverage and by scarce arbitrage capital.
  - Arbitrage is risky because margins and liquidations spike in drawdowns.
  - **High carry predicts future price crashes** and coincides with a higher price of crash insurance. The paper also finds evidence of market segmentation and "excess volatility" of futures relative to spot.
- **Practitioner and vendor return claims [PRAC/MKT, unverified]:**
  - "Professional funds… around 19% annualized returns in 2025 using low leverage" — vendor-blog claim with no data. — [OneKey blog](https://onekey.so/blog/ecosystem/hyperliquid-funding-rate-arbitrage/)
  - Sharpe AI claims 10–40% APY. — [Sharpe AI blog](https://sharpe.ai/blog/funding-rate-arbitrage) [MKT]
  - 1Token publishes a funding-fee arbitrage index (TWR, max drawdown), but I could not read its figures. — [1Token](https://blog.1token.tech/strategy-index-funding-fee-arbitrage-i.md)
- **Ethena USDe as live evidence [NEWS]:** Ethena's sUSDe yield is essentially pooled delta-neutral funding plus staking yield.
  - After the Oct 10, 2025 crash, sUSDe APY reportedly fell to about 3.5% from about 8% in the prior weeks.
  - Another report put the USDe rate at 5.1%, below Aave USDC borrow at 5.4%. The two figures come from different dates.
  - USDe TVL fell from a peak of more than $14.8bn (Oct 2025) to about $7bn (early Dec 2025, DeFiLlama).
  - The sUSDe looping trade turned negative-carry. Sentora estimated about $1bn of sUSDe-collateralized positions at risk.
  - Sources: [The Block](https://www.theblock.co/post/380210/yield-compression-triggers-50-tvl-drop-in-usde-despite-rising-onchain-usage); [DL News](https://www.dlnews.com/articles/defi/ethena-usde-supply-plummets-as-traders-cool-on-risky-crypto-bets); [Forklog](https://forklog.com/en/usde-stablecoins-market-cap-halved-due-to-yield-decline/)
  - Coin Metrics says funding on major venues **stayed positive** through the crash. This contradicts reports that funding "turned negative". — [Coin Metrics SOTN #335](https://coinmetrics.substack.com/p/state-of-the-network-issue-335)
- **CME and ETF basis [NEWS]:**
  - Basis dropped below about 5% annualized in Feb 2025. — [CoinDesk](https://hotfix.coindesk.com/markets/2025/02/25/u-s-bitcoin-etfs-post-year-s-2nd-biggest-outflows-as-basis-trade-drops-below-5)
  - By 2026 it was cited around 4.8%, "barely beats Treasuries". CME BTC open interest fell below $8bn in March 2026 and to $7.2bn in early April 2026 as the ETF basis trade unwound. — [The Block, Apr 2026](https://www.theblock.co/post/396722/cme-bitcoin-futures-activity-slumps-to-14-month-low-as-basis-trade-unwind-drains-institutional-demand)
  - Hedge funds cut net CME short positioning by a reported 89% from the Dec 2024 peak, and one 2026 report says they flipped net long. — [crypto.news](https://crypto.news/cme-bitcoin-futures-slump-as-basis-trade-unwinds-and-wall-street-steps-back/) (secondary, unverified)

### Inferences
- **Evidence quality:** for the simple "always long spot, short perp, collect funding" variant, quality is moderate. There is no peer-reviewed paper reporting its net returns specifically, but its gross yield is mechanically observable from funding history, and He et al. plus BIS give strong working-paper support for the broader carry/basis premium. Of everything researched here, this is the best-documented positive-expectancy crypto strategy, far better than any scalping evidence.
- **Realistic retail net return, 2025–26 (my estimate, not from a source):** BTC/ETH funding capture is roughly 3–8% APR on capital in normal regimes. It approaches the ~8–11% baseline only when funding pins at 0.01% per 8h and margin is efficient, and spikes to 15–30%+ only in euphoric phases. That is comparable to or modestly above T-bills (~4–4.5%), which is the arbitrage-capital competition the BIS paper predicts.
- **Altcoin carry:** higher-yield altcoin carry exists (He et al.: DOGE and BNB Sharpe of 3.5–4.8 at High cost), but it carries more liquidation, delisting, ADL and spot-borrow-availability risk.
- **Capacity and scaling:** capacity is large for BTC/ETH (Ethena held more than $14bn), so a retail account will not move prices. The binding constraint is yield compression from crowding, not a retail account's own capacity. It is not a strategy that scales returns with skill.

### Gaps
- I found no peer-reviewed study of the net return of naive persistent funding capture at VIP-0 retail fees.
- I found no audited multi-year track record of a retail-run funding bot.
- I did not retrieve Ethena's own transparency-dashboard history, for example the 2024 average sUSDe APY. Commonly quoted figures (around 20–30% APY in early 2024) are **unverified here**.
- The October 2025 BIS revision's updated numbers beyond the abstract were not read.

---

## 3. Drawdowns and tail risks: negative funding, Oct 10 2025 crash, ADL, depegs, exchange failure

### Takeaway
On paper, the strategy's drawdowns are small: He et al. report max drawdowns of 1–9%. In practice the risks are operational and counterparty tail events that historical backtests do not capture: auto-deleveraging closing the profitable short leg, mark-price and collateral-valuation failures, stablecoin or LST depegs, key compromises, and exchange insolvency (FTX). These risks mostly materialize in exactly the crash periods when carry was highest.

### Cited Findings
- **Scale of the Oct 10–11, 2025 crash [NEWS/PRAC]:** about $19–20bn in forced liquidations within 24h. Hyperliquid had the largest share; Bybit had $4.65bn and Binance $2.41bn. CoinShares argues the true losses could exceed $50bn. — [insights4vc](https://insights4vc.substack.com/p/inside-the-19b-flash-crash); [CoinShares](https://coinshares.com/be/insights/knowledge/billions-in-liquidations-what-happened); [Cointelegraph](https://cointelegraph.com/features/19b-crypto-market-crash-leverage-china-tariffs)
- **ADL [NEWS/PRAC]:**
  - Hyperliquid's waterfall is order-book liquidation, then the HLP vault backstop, then ADL. Oct 10 was its first ADL in more than two years.
  - ADL forcibly closes *profitable* positions, so a correctly hedged short perp can be closed at the worst moment, leaving the spot leg naked. One analysis summarized that a trader could be right on direction "and still incur losses" from risk-infrastructure failure. — [Forklog](https://forklog.com/en/whales-adl-and-the-end-of-the-bull-what-really-happened-on-cryptos-black-saturday/); [The Defiant](https://thedefiant.io/newsletter/defi-daily/the-ultimate-10-10-crash-autopsy)
- **Binance valuation and depeg [NEWS]:** Binance valued collateral such as USDe, bnSOL and wBETH from its own order book rather than oracles. It acknowledged that part of the liquidations were linked to their temporary depeg, and on Oct 13 it announced $283m in compensation. — [Forklog/insights4vc summary](https://insights4vc.substack.com/p/inside-the-19b-flash-crash)
- **Security risk [PRAC]:** a $21m Hyperliquid position was reportedly lost via key compromise in Oct 2025, and CEX accounts can be frozen. — [Buildix blog](https://www.buildix.trade/blog/crypto-funding-rate-arbitrage-delta-neutral-hyperliquid-binance) (unverified)
- **Residual risks [PRAC]:** hedging does not remove "liquidation risk, execution risk, funding reversal risk, liquidity risk, or protocol/exchange risk". — [OneKey blog](https://onekey.so/blog/ecosystem/hyperliquid-funding-rate-arbitrage/)
- **Academic framing [WP]:** BIS finds arbitrage capital is scarce because the trade suffers margin spikes and liquidations in drawdowns. — [BIS WP 1087](https://bis.org/publ/work1087.htm). He et al. say the arbitrageur must "remain solvent" through temporary widening. — [arXiv](https://arxiv.org/html/2212.06888v5)

### Inferences
- **Coupled tail risk:** a delta-neutral bot on a single CEX carries a short-volatility-like tail. Collateral can be haircut or depegged while the short is liquidated or ADL'd, and the venue itself can fail (FTX, Nov 2022, is the canonical case for venue failure; I did not research it in this session).
- **Mitigations to code:**
  - low leverage on the perp leg (≤2–3×, liquidation price ≥50–100% away);
  - BTC/ETH or USDC collateral rather than synthetic stables or LSTs;
  - ADL-rank monitoring (Binance and Bybit expose an ADL quantile in the API);
  - auto-rehedge if one leg is closed;
  - splitting capital across venues.
- **Drawdown estimate (judgment, not a measured number):** the maximum drawdown of the pure carry P&L is likely a few percent, as in He et al. Tail-event loss is bimodal: near zero most of the time, but potentially large on venue failure.

### Gaps
- I found no documented quantification of how delta-neutral funding books fared on Oct 10, 2025, such as the share hit by ADL or average loss.
- Frequency and duration of negative-funding regimes in 2022 and 2025–26 were not quantified from primary data. Coinglass or Laevitas historical funding would answer this.

---

## 4. Short-horizon funding variants: trading around funding timestamps, cross-exchange differentials, funding spikes as signals

### Takeaway
Evidence for short-horizon variants is thin and mostly from working papers. There are documented intraday patterns tied to the funding cycle: U-shaped market quality, informed trading near settlement, and cross-venue spreads peaking about 2h after settlement. I found no rigorous net-of-cost evidence that a retail bot can profit from "enter before the timestamp, exit after". The best-supported "signal" use is slow: high or extreme carry predicts crashes (BIS) and past returns predict the perp premium (He et al.). These are regime filters, not scalps.

### Cited Findings
- **AFA conference paper [WP, unverified; abstract only]:** high-frequency order-book data from 2017–2023. Spot market quality follows a **U-shaped pattern over the 8h funding cycle**, attributed to more informed trading around settlement hours and when funding fees are larger. The pattern also appears in perps. — [AFA submission](https://afajof.org/management/viewp.php?n=169764)
- **Cross-venue spreads [WP/PR?, MDPI IJFS 2026, unverified; snippet only]:** 26 exchanges and 812 symbols, Nov 2025–Jan 2026. Intraday cross-venue spread patterns are statistically significant and tied to settlement, peaking about 2 hours after standard settlement times. I could not access the full text (HTTP 403). — [MDPI 2227-7072/14/5/103](https://www.mdpi.com/2227-7072/14/5/103)
- **CEX vs DEX funding [PR, MDPI Mathematics 2026; snippet only]:** proposes normalizing funding across venue types. It reports CEXs dominate price discovery, with 61% higher integration and information flowing CEX→DEX, and says systematic cross-venue funding comparisons "have not yet been conducted". The attribution of this finding to the paper is not fully confirmed. — [MDPI Mathematics 14(2):346](https://www.mdpi.com/2227-7390/14/2/346)
- **arXiv 2601.06084 [WP, not read]:** "Who sets the range? Funding mechanics and 4h context in crypto markets" is directly relevant but was not retrieved. — [arXiv 2601.06084](https://arxiv.org/pdf/2601.06084)
- **Funding/carry as a contrarian signal [WP]:** high crypto carry predicts future crashes. — [BIS WP 1087](https://bis.org/publ/work1087.htm). Past 120-day returns predict the perp-spot deviation (R² up to 0.33). — [He et al.](https://arxiv.org/html/2212.06888v5)
- **Cost mechanics:** He et al.'s no-arbitrage band is ±53% to ±180% annualized of deviation. Short-horizon convergence trades need the perp-spot gap to exceed a large multiple of fees, and higher fees stretch average holding time from 19h to 135h. — [He et al.](https://arxiv.org/html/2212.06888v5)

### Inferences
- **"Funding-timestamp scalp"** (go short perp just before settlement to collect one payment, then close): the expected value of one 8h payment at baseline is 0.01% = 1 bp. Even maker-only round trips on both legs (4 fills) cost more than that at retail tiers, so the trade is negative-EV unless funding is extreme, and then the perp premium tends to move against the entrant around settlement. It should be treated as **not viable** absent new evidence.
- **Cross-exchange funding differential** (short perp on the high-funding venue, long perp on the low-funding venue): no spot leg is needed, so it is capital-efficient. The risks are double venue risk, mark-price divergence that can liquidate one leg, and interval mismatch (1h vs 8h). It is plausible for persistent DEX–CEX gaps such as Hyperliquid vs Binance, but **no rigorous net-of-cost evidence was found**.
- **Funding spikes:** the evidence supports using them as risk-off or regime filters (reduce directional longs, widen hedges) over days to weeks, not as minute-level mean-reversion triggers.

### Gaps
- I found no peer-reviewed or reputable backtest of pre/post-funding-timestamp price drift with explicit retail costs.
- I found no quantified net returns for cross-venue funding-differential trades.

---

## 5. Costs, capital efficiency, counterparty and regulatory constraints

### Takeaway
A full carry trade has four fills: open spot, open perp, close spot, close perp. Even the paper's "high-fee" tier assumes VIP volumes, and at VIP-0 retail taker fees the round trip can eat a month or more of baseline funding. That makes the strategy a low-turnover, maker-order, hold-for-weeks trade, the opposite of scalping. Regulation is shifting: US access to perps opened in 2025–26 via Coinbase, Deribit and Kalshi under CFTC oversight, while Binance, Bybit, OKX and Hyperliquid perps remain offshore and generally restricted for US persons.

### Cited Findings
- **Fee assumptions in the best academic test [WP]:** Binance maker fees at the "High" tier were 6.75 bps spot and 1.44 bps futures, and that tier still requires more than $1mn spot and $15mn futures in 30-day volume. — [He et al.](https://arxiv.org/html/2212.06888v5)
- **Net return sensitivity [WP]:** going from no fees to the High tier cut BTC Sharpe from 3.53 to 1.80 and return from 13.7% to 6.4%. — [He et al.](https://arxiv.org/html/2212.06888v5)
- **US regulation [NEWS]:**
  - Coinbase launched CFTC-regulated "perpetual-style" BTC/ETH futures for US users in July 2025: 10× leverage, 5-year expiry, not true perps. — [The Block](https://www.theblock.co/post/363796/coinbase-launches-perpetual-futures)
  - On about May 28–29, 2026 the CFTC granted Coinbase no-action relief to route US clients to Deribit perps as foreign futures, and approved Kalshi's BTCPERP as the first perp on a registered US exchange. The CFTC will review applications case by case and stresses leverage limits. — [CoinDesk, May 28 2026](https://www.coindesk.com/policy/2026/05/28/u-s-cftc-opens-crypto-perp-door-with-approval-of-first-regulated-firm); [Crowdfund Insider](https://www.crowdfundinsider.com/2026/05/282486-coinbase-kalshi-to-add-perpetual-crypto-futures-trading/)
- **CME basis for US retail [NEWS]:** the CME/ETF basis was about 4.8–5% annualized, close to T-bills, in 2025–26. — [The Block](https://www.theblock.co/post/396722/cme-bitcoin-futures-activity-slumps-to-14-month-low-as-basis-trade-unwind-drains-institutional-demand)

### Inferences
- **Fee arithmetic (assumed fees, not verified here):** Binance's default VIP-0 schedule is commonly published at about 0.10% spot maker/taker and about 0.02% maker / 0.05% taker on USDⓈ-M futures. A taker round trip on both legs then costs about 0.30% of notional, roughly 10 days of baseline funding (0.03% per day). Maker-only cuts this to about 0.24%, or about 0.08% with BNB/VIP discounts. Implication: hold periods must be weeks, and the bot should enter with post-only orders.
- **CME basis as a retail option:** for a US retail developer, CME basis (micro BTC futures plus spot ETF) is the cleanest regulated option. At about 5% gross minus roll and fees, it barely beats T-bills, so it is a weak "alternative".
- **Counterparty diversification:** split capital across ≥2 venues and keep idle collateral off-exchange. For FTX-style risk, the expected loss from venue failure (probability × loss) can plausibly exceed a year of carry.
- **Tax:** each funding payment is likely ordinary income and each leg a separate disposal. Holding spot can trigger capital-gains events on rehedges. This is jurisdiction-specific and **not researched**.

### Gaps
- I did not fetch exchange fee schedules for Binance, Bybit, OKX or Hyperliquid.
- I found no source on spot-borrow costs for reverse carry (short spot, long perp) when funding is negative.
- EU/MiCA treatment of retail access to perps was not found. I believe ESMA and national CFD/derivatives rules restrict retail leverage, and some offshore venues geo-restrict the EEA, but this is **unverified**.
- Tax treatment was not researched.

---

## 6. Evidence on pairs trading and short-horizon stat arb (equities to crypto)

### Takeaway
Classic daily pairs trading earned about 11% p.a. gross in 1962–2002 (Gatev et al.) but decayed to about 30 bps/month net and was largely unprofitable after 2002 (Do & Faff). Intraday pairs are much more profitable gross but extremely sensitive to costs and latency: 0.15% one-way costs halve profits, and a one-bar delay turns them negative (Bowen et al.). In crypto, intraday mean reversion is real: Fil & Kristoufek find 5-minute distance pairs far better than daily, which loses money. But most crypto pairs results are fragile to parameters and costs, and cross-venue or futures→spot lead-lag operates at milliseconds (CME leads Binance by about 55 ms), out of reach for retail REST/WebSocket bots.

### Cited Findings
- **Gatev, Goetzmann & Rouwenhorst (RFS 2006) [PR]:**
  - Rule: form pairs by minimum sum of squared deviations of normalized prices over a 12-month formation period; trade the top 20 for 6 months.
  - Open when the spread diverges by more than 2 historical SD; close at the next price crossing or at period end.
  - Average annualized excess returns were "up to 11%" for self-financing pair portfolios (10.4% for the top-20 fully invested). The strategy was profitable with reasonable frictions over 1962–1998 and in a 1999–2002 out-of-sample test. — [Alpha Architect summary](https://alphaarchitect.com/pairs-trading-kicks-butt/); [paper PDF copy](https://c.mql5.com/forextsd/forum/208/Pairs%20Trading%20-%20Performance%20of%20a%20Relative%20Value%20Arbitrage%20Rule.pdf)
- **Do & Faff (FAJ 2010; JFR 2012) [PR]:**
  - 2010: profitability declined over the long run. Worsening arbitrage risks (non-convergence) explain up to 70% of the drop. The strategy does well in prolonged turbulence such as the GFC. — [CFA Institute](https://rpc.cfainstitute.org/research/financial-analysts-journal/2010/does-simple-pairs-trading-still-work); [Bond Univ.](https://research.bond.edu.au/en/publications/does-simple-pairs-trading-still-work/)
  - 2012: after commissions, market impact and short fees, the strategy is still profitable at about 30 bps/month risk-adjusted for well-matched pairs within refined industries. Pairs trading and short-term industry reversal are "largely unprofitable after 2002". — [Strathprints](https://strathprints.strath.ac.uk/41722/)
- **Bowen, Hutchinson & O'Sullivan (J. Trading 2010) [PR, practitioner journal; secondary summary]:**
  - Setup: FTSE 100, 60-minute bars, 2007; 264h formation and 132h trading periods.
  - A 0.15% one-way cost cut net profits to less than half of gross. A one-bar (60-min) execution delay made net returns negative.
  - 75% of profits came in the first and last trading hours. Standard factors explain less than 2% of returns. — [CXO Advisory](https://www.cxoadvisory.com/technical-trading/success-factors-for-high-frequency-pairs-trading/); [UCC WP](https://www.ucc.ie/en/media/research/centreforinvestmentresearch/wp/PT2.5.pdf)
  - Follow-up, Bowen & Hutchinson (EJF 2016, UK 1980–2012): 6.2–9.5% p.a. net versus 10.9% for the FTSE All-Share. — [IDEAS](https://ideas.repec.org/a/taf/eurjfi/v22y2016i14p1363-1387.html)
- **Fil & Kristoufek (IEEE Access 2020) [PR]:**
  - Distance and cointegration pairs on 26 liquid Binance coins at 5-min, 1h and daily frequencies. The strategies underperform classical benchmarks and are "quite sensitive" to parameters, transaction costs and execution windows.
  - The daily distance method returns −0.07% per month; 5-minute returns 11.61% per month. That figure is implausibly high for live trading and suggests idealized execution.
  - The authors interpret intraday mean reversion as evidence of inefficiency. — [DOAJ record](https://doaj.org/article/8fbfa5ffeaae44a5a4c635f23f5ca05c)
- **Tadi & Kortchemski (arXiv 2109.10662) [WP]:** a dynamic cointegration pairs strategy with an optimal lookback in crypto. They note that many prior studies assume zero costs, making results unreliable. — [arXiv](https://arxiv.org/abs/2109.10662)
- **2026 crypto pairs papers [PR/WP, snippets only]:**
  - Copula pairs on 10 Binance USDT perps, hourly, Jan 2021–Dec 2023 (26,257 obs), with 0.08% round-trip costs. "Net performance depends heavily on costs and strategy design." — [AIMS QFE 2026](https://www.aimspress.com/aimspress-data/qfe/2026/2/PDF/QFE-10-02-016.pdf)
  - An arXiv thesis combines multi-pair cointegration (Hurst filter) with deep-RL execution on 1h Binance USD-M futures. — [arXiv 2606.04574](https://arxiv.org/pdf/2606.04574.pdf)
  - A Frontiers paper combines dynamic Johansen cointegration with deep-learning spread forecasts on 6 crypto pairs. — [Frontiers 2026](https://www.frontiersin.org/articles/10.3389/fams.2026.1749337/full)
- **Lead-lag [WP]:**
  - CME BTC futures lead Binance spot, with a lead-lag of 0.055 s in a March 5, 2024 event. Futures tend to lead overall, but results are mixed in high volatility. CEXs lead Uniswap v2 in ETH price discovery. — [arXiv 2506.08718](https://arxiv.org/abs/2506.08718v1)
  - Across 61 spot exchanges in 2019, price formation occurred on "more trustworthy" exchanges. — [Digital Asset Research (Medium)](https://medium.com/digitalassetresearch/an-analysis-of-price-discovery-in-bitcoin-spot-markets-7563fbf1c890) [PRAC, dated]

### Inferences
- **Evidence quality:** for crypto intraday pairs, quality is low to moderate. There is one peer-reviewed study (Fil & Kristoufek) with fragile, cost-sensitive results, plus 2026 papers that lean on ML overlays (a red flag for overfitting).
- **Cross-asset pattern:** equities show decay after publication and crowding (Do & Faff), and there is no reason crypto is immune.
- **Lead-lag:** at about 55 ms between CME and Binance, it is an HFT/co-location game. A retail bot with 50–300 ms of WebSocket latency to Binance cannot reliably harvest it, so this is not a retail strategy.

### Gaps
- I did not obtain Fil & Kristoufek's exact cost assumptions or their net-of-cost 5-min results from the full text.
- I found no robust study of BTC→altcoin lead-lag at seconds-to-minutes horizons with costs.
- I found no published live track record of a retail crypto pairs bot.
- ETF-vs-futures (IBIT vs CME) intraday arbitrage evidence was not found.

---

## 7. Exact codable rules (for a report writer to specify)

### Takeaway
Both families can be specified precisely from the literature. The funding/basis rules are simple and parameter-light. The pairs rules have many free parameters (lookback, thresholds, re-estimation cadence), which is the main overfitting risk.

### Cited Findings
- **Perp-spot convergence rule (He et al.) [WP]:**
  - Compute ρ_t = 1095·(ln F_t − ln S_t) − (r − r′) hourly, with r = Aave stablecoin borrow rate (average of USDT, USDC and DAI) and r′ = 0 for crypto.
  - If ρ > +bound: short perp, long spot. If ρ < −bound: long perp, short spot (or skip if spot cannot be shorted).
  - Close when ρ first crosses 0.
  - Bounds equal annualized round-trip costs: ±53% (low fees), ±114% (medium), ±180% (high). — [arXiv 2212.06888v5](https://arxiv.org/html/2212.06888v5)
- **Funding formula for forecasting the next payment (Binance and Hyperliquid) [DOC]:** F = P̄ + clamp(0.01% − P̄, −0.05%, +0.05%) per 8h, scaled by N/8 for N-hour intervals. Hyperliquid samples P every 5s and pays hourly at F/8, capped at 0.5% per hour. — [Binance](https://www.binance.com/fr/support/announcement/detail/c00588a7e8504b3eb28d02a2da00530b); [Hyperliquid](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding)
- **Gatev et al. distance rule [PR]:** normalize prices to cumulative total-return indices; pick the 20 pairs with the minimum SSD over 12 months. Enter at |spread| > 2σ (σ from the formation period), exit at the crossing (spread = 0), and time-stop at the end of the 6-month trading period. — [Alpha Architect](https://alphaarchitect.com/pairs-trading-kicks-butt/)
- **Intraday version (Bowen et al.) [PR]:** 60-min bars, 264-bar formation, 132-bar trading window, and immediate execution (a one-bar delay kills returns). — [CXO](https://www.cxoadvisory.com/technical-trading/success-factors-for-high-frequency-pairs-trading/)
- **Crypto intraday distance and cointegration (Fil & Kristoufek) [PR]:** applied at 5m, 1h and daily bars on Binance. Higher frequency performs better gross. — [DOAJ](https://doaj.org/article/8fbfa5ffeaae44a5a4c635f23f5ca05c)

### Inferences
These are suggested defaults synthesized by me, not empirically validated. Mark them as such in the report.

- **Persistent funding-capture bot:**
  1. *Universe:* BTC and ETH, plus top-10 perps by open interest.
  2. *Signal:* trailing 7-day average annualized funding above a hurdle of max(T-bill yield + 2%, 4 × round-trip fee / expected hold in years).
  3. *Entry:* long spot (or use spot as unified-margin collateral) and short an equal-notional perp, both post-only limit orders. Perp leverage ≤ 2–3×.
  4. *Exit:* 7-day average funding below 0 or below the hurdle for 3 consecutive days, or a basis inversion beyond −X%.
  5. *Risk controls:* rebalance the hedge when the notional mismatch exceeds 2%. Keep the liquidation buffer at ≥50% price move. Alert and auto-reduce if the ADL quantile is ≥ 3 of 5. Cap any single venue at 30–50% of capital.
- **Pairs bot (e.g. ETH/BTC or same-sector alt pairs on perps):**
  1. *Hedge ratio:* β by rolling OLS on log prices, or a Kalman filter (state = [β, α], small process noise).
  2. *Spread and z-score:* spread = ln A − β ln B. z = (spread − rolling mean)/rolling SD, with a lookback of about the spread's half-life × 3–5. Half-life comes from an AR(1) fit, θ = −ln(φ).
  3. *Pair filter:* Engle–Granger ADF p < 0.05 (or Johansen) on the formation window, and a half-life within 2–48h for intraday trading.
  4. *Thresholds:* entry at |z| ≥ 2, exit at z → 0 (or ±0.5), stop at |z| ≥ 4, and a time stop at 2–3× the half-life.
  5. *Re-estimation:* re-estimate β and the cointegration test daily to weekly, and drop the pair on test failure, which detects structural breaks.
  6. *Trade filter:* only trade if expected reversion (|z_entry| × σ_spread) exceeds about 3× the round-trip cost on 4 fills.

### Gaps
- I found no source that empirically justifies ±2 / 0 / ±4 thresholds specifically for crypto at minute horizons. Gatev's 2σ is a daily-equity convention.
- Kalman-filter parameterizations from crypto studies were not retrieved.

---

## 8. Net-of-cost viability, capacity, crowding, and comparison with scalping

### Takeaway
For a retail developer, delta-neutral funding/basis capture on BTC/ETH is the **most defensible** of the three families researched here, and more defensible than scalping. It has a structural economic source (leverage demand and scarce arbitrage capital, per BIS), a mechanically observable yield (the 0.01%/8h baseline), moderately strong working-paper evidence (Sharpe 1.8–4.8 after VIP-level fees, He et al.), and low turnover, so it is not fee-dominated. Its caveats are just as clear: net returns have compressed to roughly T-bill-plus (about 3–8% on capital in 2025–26 regimes), and the risk is concentrated in operational and counterparty tails, not in the backtest. Short-horizon variants (funding-timestamp trades, minute-level pairs, lead-lag) share scalping's problems: cost and latency sensitivity, fragile parameters, and competition with HFTs. They are not better-evidenced alternatives.

### Cited Findings
- **Funding/basis:** fees reduce but do not eliminate the edge (BTC Sharpe 3.53 → 1.80 at the High tier), and holding periods lengthen to about 135h. — [He et al.](https://arxiv.org/html/2212.06888v5)
- **Edge decay:** deviations shrink about 11% per year. — [He et al.](https://arxiv.org/html/2212.06888v5)
- **Compression in 2025–26:** sUSDe at about 3.5–5%. — [The Block](https://www.theblock.co/post/380210/yield-compression-triggers-50-tvl-drop-in-usde-despite-rising-onchain-usage). CME basis at about 4.8%. — [The Block](https://www.theblock.co/post/396722/cme-bitcoin-futures-activity-slumps-to-14-month-low-as-basis-trade-unwind-drains-institutional-demand)
- **Source of the premium:** carry is driven by convenience yield and scarce arbitrage capital, which is why it is periodically high (more than 10% average, up to 60%). — [BIS WP 1087](https://bis.org/publ/work1087.htm)
- **Intraday pairs:** 0.15% one-way costs halve profits, and a one-bar delay makes them negative. — [Bowen et al. via CXO](https://www.cxoadvisory.com/technical-trading/success-factors-for-high-frequency-pairs-trading/)
- **Equity pairs post-2002:** largely unprofitable net. — [Do & Faff 2012](https://strathprints.strath.ac.uk/41722/)
- **Crypto pairs:** "underperform classical benchmarks" and are sensitive to costs and execution windows. — [Fil & Kristoufek](https://doaj.org/article/8fbfa5ffeaae44a5a4c635f23f5ca05c)
- **Lead-lag:** CME→Binance lead of about 0.055 s. — [arXiv 2506.08718](https://arxiv.org/abs/2506.08718v1)

### Inferences
**Comparison table (synthesized judgment; ratings are mine):**

| Strategy | Economic rationale | Evidence quality | Realistic retail net (2025–26) | Turnover / fee sensitivity | Capacity for retail | Main risks |
|---|---|---|---|---|---|---|
| Persistent BTC/ETH funding capture (spot long / perp short) | Strong (leverage demand, BIS) | Moderate (WPs + observable funding history) | ~3–8% APR on capital; 10–20%+ in euphoric phases | Very low / low | Effectively unlimited | Venue failure, ADL, depeg, negative-funding stretches |
| He et al. perp-spot convergence (threshold entry, exit at 0) | Strong | Moderate (single WP, Binance, to Mar 2024) | Likely below paper's 6–10% (BTC/ETH) because retail fees exceed the paper's "High" tier and the edge decays ~11% a year | Low | High | Same as above plus long time-to-converge |
| Alt-coin funding carry | Moderate | Moderate (He et al. DOGE/BNB/ADA) | Higher gross, but tail-heavy | Low–medium | Medium | Liquidation, delisting, spot-borrow availability |
| CME / ETF cash-and-carry | Strong | Good (observable) | ~T-bills + 0–1% | Low (quarterly roll) | High | Low counterparty risk; margin calls |
| Funding-timestamp scalp | Weak | None found | Negative after fees (1 bp baseline payment vs multi-bp costs) | High | Low | Adverse price around settlement |
| Cross-venue funding differential | Moderate | Very weak | Unknown | Low–medium | Medium | Double venue risk, mark divergence |
| Intraday crypto pairs (5m–1h) | Weak–moderate (microstructure mean reversion) | Low (fragile, cost-sensitive) | Likely ≈0 or negative at VIP-0 taker fees; maybe small positive maker-only | High | Low–medium | Structural breaks, crowding, latency |
| Cross-exchange / futures→spot lead-lag | Real but ms-scale | Moderate (WP) | Not accessible to retail | Very high | Low | HFT competition |

- **Verdict for the report:** if "most defensible alternative to scalping" means positive expected value with a credible economic source and low dependence on execution speed, low-leverage BTC/ETH funding/basis capture on top-tier venues (or CME basis for US persons) qualifies, and scalping and intraday pairs do not. Frame the honest return expectation as "T-bill-plus with crypto-venue tail risk", not as a high-return trading strategy.
- **Crowding:** Ethena's growth to more than $14bn TVL and the institutional CME basis trade are the arbitrage capital that compressed the premium. Retail is a price-taker in a crowded trade whose returns rise mainly when everyone else is over-levered long.

### Gaps
- No independent, audited net-of-fees track record exists for retail funding or pairs bots.
- The retail-fee (VIP-0) version of He et al.'s backtest has not been published; I estimated it by extrapolation.
- I found no 2024–26 out-of-sample replication of He et al. after their March 2024 cutoff.
