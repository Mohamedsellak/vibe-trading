# Market Making / Maker-Biased Spread Capture for Retail (Crypto Perps: Binance, Bybit; secondary: CME Micro Futures), as of Nov 2026

Source-quality key used below: [PR] = peer-reviewed journal; [WP] = academic working paper / arXiv preprint (not peer-reviewed); [BT] = reputable open-source backtest with code; [EX] = exchange/official documentation; [PRAC] = practitioner / community anecdote; [MKT] = vendor marketing or affiliate site. "NOT FETCHED" = cited from well-known literature but the text was not retrieved in this session; the report writer should treat formula details as standard but verify before printing.

**Bottom line for the writer:** At regular-tier fees (Binance USD-M 2.0 bp maker / 5.0 bp taker; Bybit 2.0 / 5.5), we found no credible evidence that a solo developer at 20-200 ms can capture spread profitably on BTC/ETH perps. Every credible profitable crypto MM result we found assumes the best-tier maker rebate (-0.5 bp), and most authors say the rebate *is* the profit. Paying +2 bp per fill instead of earning -0.5 bp is a 2.5 bp swing per fill. That is larger than every net edge per fill reported in the sources (all under ~1.3 bp per fill).

---

## 1. Core logic: what does market making earn, and why does it persist?

### Takeaway
A market maker earns the bid-ask spread as payment for providing immediacy and carrying inventory. That spread exists to cover (a) adverse selection (losses to better-informed takers), (b) inventory/price risk, and (c) order-processing costs, including exchange fees. In competitive equilibrium the expected profit is about zero after these costs. Whatever is left goes to the fastest, lowest-fee participants (rebates, colocation), not to slow, fee-paying ones.

### Cited Findings
- Empirical decomposition for a real HFT market maker (Chi-X/Euronext, Dutch large caps): it earned about **EUR 1.55 per trade from the spread net of fees and lost EUR 0.68 per trade on positioning (inventory)**, for about EUR 0.88 gross profit per trade. It traded about 1,397 times per stock per day and took part in 64.4% of Chi-X trades (8.1% on Euronext). This is the canonical evidence that MM profit = spread minus adverse/inventory losses. — Menkveld (2013), *Journal of Financial Markets* 16(4):712-740 [PR] — [EconPapers record](https://econpapers.repec.org/RePEc:eee:finmar:v:16:y:2013:i:4:p:712-740); per-trade numbers from the working paper — [Tinbergen WP](https://repec.tinbergen.nl/tin/wpaper/11076.rdf). The figures come from the WP version via a search summary; check against the JFM version.
- HFT profitability is driven by **relative latency**. Firms that improved their latency rank (for example via colocation upgrades) saw better trading performance. Speed helps through a short-lived information channel and a risk-management channel (including market making). — Baron, Brogaard, Hagströmer & Kirilenko, "Risk and Return in High-Frequency Trading," *JFQA* 54(3) 2019:993-1024 [PR] — [IDEAS/RePEc](https://ideas.repec.org/a/cup/jfinqa/v54y2019i03p993-1024_00.html)
- The earlier CFTC-hosted draft (E-mini S&P 500 futures, two years of data) found **HFT revenue concentrated in a small number of firms**. Conference slides report that concentration does not fall over time, that firms over-invest in speed, and that profit margins are 40-60%. — [CFTC OCE draft](https://www.cftc.gov/idc/groups/public/@economicanalysis/documents/file/oce_riskandreturn0414.pdf) [WP]; [slides](https://sambuz.com/doc/risk-and-return-in-high-frequency-trading-ppt-presentation-964307) [WP slides]. These come from search snippets; the full tables were not read.
- Adverse selection theory (NOT FETCHED, canonical):
  - **Glosten & Milgrom (1985, JFE 14:71-100)**: a competitive, risk-neutral dealer sets ask = E[V | buy order] and bid = E[V | sell order]. The spread exists purely because some traders are informed, and the dealer breaks even on average by losing to informed traders and gaining from uninformed ones.
  - **Kyle (1985, Econometrica 53:1315-1335)**: price impact is linear, Δp = λ·(order flow), with λ = σ_v / (2σ_u). Market depth is 1/λ and rises with noise-trader volume.
  - For a retail MM, the implication is that your realized spread equals the quoted spread minus the price move against you after a fill (the "markout"). — [Glosten-Milgrom DOI 10.1016/0304-405X(85)90044-3](https://doi.org/10.1016/0304-405X(85)90044-3); [Kyle DOI 10.2307/1913210](https://doi.org/10.2307/1913210)
- The crypto-specific empirical confirmation: a live Binance BTC-perp experiment found **a negative correlation between maker fill likelihood and post-fill returns**. The orders most likely to fill are the most adversely selected. — Albers, Cucuringu, Howison & Shestopaloff, "The Market Maker's Dilemma," arXiv:2502.18625 (v2, Nov 2025) [WP] — [arXiv abstract](https://arxiv.org/abs/2502.18625)
- The same paper attributes the barrier to HFT profitability partly to "the persistent wealth extraction via exchange fees." — [arXiv HTML v2](https://arxiv.org/html/2502.18625v2)

### Inferences
- The premium persists because liquidity demanders (hedgers, liquidations, retail takers, arbitrageurs needing immediacy) pay for it. Competition drives it down to the marginal cost of the *lowest-cost* provider. On Binance/Bybit that provider is a colocated (AWS Tokyo/Singapore) firm with negative maker fees. A VIP0 participant's marginal cost is about 2.5 bp per fill higher, so equilibrium spreads on liquid pairs sit far below what VIP0 needs to break even.
- Menkveld's split (spread income about 2x the inventory loss) is a useful template for a retail PnL attribution: track spread capture, inventory/markout PnL, and fees separately.

### Gaps
- No 2025-2026 peer-reviewed estimate of aggregate crypto MM profits by participant tier was found.
- Makarov & Schoar (2020, JFE "Trading and arbitrage in cryptocurrency markets") and Capponi et al. were not researched in this session. They mostly concern cross-exchange arbitrage and price formation rather than perp MM profitability.

---

## 2. Codable models: exact formulas and parameters

### Takeaway
The standard codable stack is:
1. A fair price (mid, microprice, or mid plus an alpha term).
2. An inventory-skewed reservation price (Avellaneda-Stoikov or GLFT).
3. A half-spread derived from volatility, risk aversion, and fill-intensity parameters (A, k) fitted from trade data.
4. Hard caps: max position, min spread, a refresh/tolerance rule, and volatility/imbalance-based widening or pulling.

hftbacktest publishes a complete, working GLFT implementation with fitted parameters.

### Cited Findings

**Avellaneda-Stoikov (2008)**, "High-frequency trading in a limit order book," *Quantitative Finance* 8(3):217-224 [PR] (NOT FETCHED this session; formulas are the standard published ones) — [author PDF](https://www.math.nyu.edu/~avellane/HighFrequencyTrading.pdf)
- Mid price follows dS = σ dW. Inventory is q, the risk-aversion (CARA) parameter is γ, and the terminal horizon is T.
- Fill intensity at distance δ from mid: λ(δ) = A·exp(−k·δ).
- Reservation (indifference) price: **r(s,q,t) = s − q·γ·σ²·(T − t)**
- Optimal total spread: **δ_a + δ_b = γ·σ²·(T − t) + (2/γ)·ln(1 + γ/k)**
- Quotes: bid = r − (δ_a+δ_b)/2, ask = r + (δ_a+δ_b)/2.
- Units must be consistent. σ is the per-unit-time volatility of price in price units (or ticks). k is per price unit (or per tick). (T − t) is in the same time units as σ².

**Hummingbot "Avellaneda Market Making" implementation** — [Hummingbot docs](https://hummingbot.org/strategies/v1-strategies/avellaneda-market-making/) [EX/PRAC]
- `risk_factor` = γ (must be non-zero). Common values are **1-20**, and the right value depends on the asset.
- α (A) and κ (k) are **estimated automatically** by a trading-intensity indicator.
- `volatility_buffer_size` and `trading_intensity_buffer_size` default to **200 ticks**.
- `execution_timeframe` is `infinite`, `from_date_to_date`, or `daily_between_times`. The infinite-horizon equations differ from the finite-T ones.
- `inventory_target_base_pct` defaults to 50.
- `order_amount_shape_factor` η sets asymmetric order sizes to steer inventory.
- `min_spread` is a hard floor (default 0).
- `order_refresh_time` is the cancel-replace interval.
- `max_order_age` defaults to 1800 s.
- `order_refresh_tolerance_pct` defaults to 0.
- `filled_order_delay` defaults to **60 s** after a fill.
- `hanging_orders_mode` is an option.
- High γ or a wide spread can push the optimal bid to zero or below, in which case no bid is placed.
- The page says its descriptions are "approximation only"; the authoritative source is `avellaneda_market_making.pyx`.

**Guéant-Lehalle-Fernandez-Tapia (GLFT, 2013)**, "Dealing with the inventory risk: a solution to the market making problem," *Mathematics and Financial Economics* 7:477-507 [PR] (original NOT FETCHED; arXiv:1105.3115 — [arXiv](https://arxiv.org/abs/1105.3115)). The closed-form asymptotic approximation as implemented in hftbacktest (equations 4.6/4.7 of the paper) — [hftbacktest GLFT tutorial](https://hftbacktest.readthedocs.io/en/latest/tutorials/GLFT%20Market%20Making%20Model%20and%20Grid%20Trading.html) [BT]:
- **Bid depth**: δ_b = c₁ + (Δ/2)·σ·c₂ + q·σ·c₂
- **Ask depth**: δ_a = c₁ + (Δ/2)·σ·c₂ − q·σ·c₂
- **Half-spread** = c₁ + (Δ/2)·σ·c₂; **skew per unit inventory** = σ·c₂
- **c₁ = (1/(ξΔ))·ln(1 + ξΔ/k)**
- **c₂ = sqrt( γ/(2·A·Δ·k) · (1 + ξΔ/k)^(k/(ξΔ) + 1) )**
- Parameter choices in the example: Δ = 1 (order-size unit), ξ = γ, and **γ = 0.05** (described as arbitrary).
- Calibration of A, k: regress log λ on depth (in ticks), where λ is trade counts that would have hit a quote at depth δ. Counts are sampled every 100 ms over a 10-min window and divided by 600 to give counts per second. The full-range fit was A = 0.843, k = 0.0170. A refit on the first 70 ticks (the one used) gave **A = 2.986, k = 0.0424**.
- σ was measured at about 10.73 ticks/√s, and 10.69 was used.
- Result: **half-spread about 20.5 ticks, skew about 9.76 ticks per unit q**. The author estimates about 1.86% of trades per step could fill at that depth.
- The author adds adjustment factors adj1 = 1 and adj2 = 0.05 that scale the half-spread and skew. Without them the strategy loses heavily (see Section 3).
- Implementation details: fair price = mid; tick size 0.01; order qty 1; **max position 20**; a "grid" variant posts grid_num = 20 levels.
- Author caveat: the fitted intensity output is in half-tick units (a known bug that was left unfixed).

**Alpha-skewed reservation price (order-book imbalance)** — [hftbacktest OBI tutorial](https://hftbacktest.readthedocs.io/en/latest/tutorials/Market%20Making%20with%20Alpha%20-%20Order%20Book%20Imbalance.html) [BT]
- imbalance = Σ bid qty − Σ ask qty within a depth band around mid. The band is **2.5%** of mid (0.1% in the high-volume variant).
- alpha = z-score of the imbalance over a rolling **1 h window sampled every 1 s** (10 min at 500 ms in the high-volume variant).
- **fair_price = mid + c1·alpha**
- **reservation = fair_price − skew·(position/order_qty)**
- **bid = min(round(reservation − half_spread), best_bid)**; **ask = max(round(reservation + half_spread), best_ask)**. Quotes are never allowed to cross.
- BTC 2023 parameters (in ticks): c1 = 160, skew = 3.5, half_spread = 80, order qty $50k, max position 50x order qty.
- ETH 2023 parameters: c1 = 10, skew = 0.2, half_spread = 5.

**Order Flow Imbalance (OFI)** (NOT FETCHED; Cont, Kukanov & Stoikov 2014, *J. Financial Econometrics* 12(1):47-88 — [arXiv 1011.6402](https://arxiv.org/abs/1011.6402)) [PR]
- Per book event n: e_n = 1{Pᵇ_n ≥ Pᵇ_{n−1}}·qᵇ_n − 1{Pᵇ_n ≤ Pᵇ_{n−1}}·qᵇ_{n−1} − 1{Pᵃ_n ≤ Pᵃ_{n−1}}·qᵃ_n + 1{Pᵃ_n ≥ Pᵃ_{n−1}}·qᵃ_{n−1}
- OFI over an interval = Σ e_n. Short-horizon mid-price change ≈ β·OFI, with β inversely proportional to depth.
- Codable use: shift the fair price by β·OFI, or pull or widen the quote on the side OFI is moving toward.

**Contrarian imbalance finding (crypto-specific)**: viable maker strategies "often require a contrarian approach, counter-trading the prevailing order book imbalance," and the authors model "Reversals" for when quoting at the touch works. — [Albers et al. arXiv:2502.18625](https://arxiv.org/abs/2502.18625) [WP]

**Fill-probability regression** (BTC perp): fill probability falls as the near-side queue grows and rises as the opposite-side queue grows.
- About 30% fill probability with a large near queue and small far queue.
- Over 90% with a very small near queue and very large far queue.
- OLS R² = 0.946.
- — [Albers et al. HTML](https://arxiv.org/html/2502.18625v2) [WP]. The search summary notes the paper's coefficient labelling looks inconsistent; check the source.

### Inferences (codable spec the writer can adopt; these are synthesis, not a sourced recipe)
- **Fair price**: microprice = (P_b·Q_a + P_a·Q_b)/(Q_a + Q_b), or mid + c1·z(OBI).
- **Reservation**: r = fair − κ_skew·q, with κ_skew = σ·c₂ (GLFT) or γσ²τ (AS with a fixed τ, for example 1-5 min, as a finite proxy).
- **Half-spread**:
  - h = max(c₁ + ½σc₂, h_min).
  - **At VIP0, h_min must be at least the maker fee plus expected adverse markout**; see Section 4. This puts h_min at about 2-3 bp or more per side.
- **Volatility widening**: σ = EWMA of 1-s mid returns (for example a 60-s half-life). Pull all quotes if σ_short/σ_long > 2 or if |z(OBI)| > threshold on the side being hit.
- **Refresh**: cancel/replace only when the target price differs from the resting price by ≥ 1 tick (or a tolerance in bp). This saves queue position and rate limit; requoting every tick resets queue priority.
- **Inventory**: hard max |q| ≤ q_max (hftbacktest used 20 units of order size, or 50x order notional). Above 0.8·q_max, post only on the reducing side. At q_max, flatten with a taker order. A taker exit at VIP0 costs 5 bp, so budget for it.
- **Hedging**: delta-hedge net inventory in a correlated instrument (for example an alt perp against BTC perp). This adds taker costs and basis risk; retail typically just skews.

### Gaps
- No published calibrations of γ, A, k for 2025-2026 Binance/Bybit altcoin perps at retail scale were found.
- The infinite-horizon AS formula used by Hummingbot (with the ω term) was not retrieved; read it from the .pyx source.

---

## 3. Retail implementations and documented results

### Takeaway
The best documented open-source results (hftbacktest) are profitable **only with the -0.5 bp best-tier Binance maker rebate**, and the author says so explicitly. Net edge per fill shrank in 2025 and is now smaller than the rebate itself. Hummingbot evidence is anecdotal, promotional, mostly from 2021-22, and centred on liquidity-mining rewards rather than spread PnL. We found no credible, audited live retail MM PnL on Binance/Bybit perps at VIP0.

### Cited Findings

**hftbacktest GLFT tutorial** (ETHUSDT 2022-10-03 to 07; LTCUSDT 2023-07-01 to 05) — [hftbacktest GLFT](https://hftbacktest.readthedocs.io/en/latest/tutorials/GLFT%20Market%20Making%20Model%20and%20Grid%20Trading.html) [BT]
- **Fee model: `trading_value_fee_model(-0.00005, 0.0007)`**, i.e. a **maker REBATE of 0.5 bp** and a 7 bp taker fee. The page calls the rebate "the highest market maker rebate available on Binance Futures."
- Latency: interpolated from real feed/order latency data. Queue: `power_prob_queue_model(2.0)`. Fills: no partial fills.

| Variant | Period | Sharpe | Return | Max DD | Trades/day |
|---|---|---|---|---|---|
| Unadjusted GLFT | ETH, 1 day | −246 | −2.06% | — | — |
| With adj2 = 0.05 | ETH, 1 day | 1.20 | +0.036% | — | — |
| With adj2 = 0.05 | ETH, 5 days | 16.3 | +3.11% | 0.98% | about 9,464 |
| Grid | ETH, 5 days | 19.8 | +5.59% | 0.74% | about 5,879 |
| Grid | LTC, 5 days | 17.2 | +12.25% | 3.30% | about 3,426 |

- Author's statements:
  - The 1-day adjusted run "even when accounting for rebates, it can only achieve breakeven at best."
  - The 5-day profits are **attributed to rebates from high trading volume**.
  - The example is "for educational purposes only."
  - Note (from the same page's description of its model): queue position is partly ignored, and only trades that cross the quote count as fills.

**hftbacktest OBI-alpha MM** — [hftbacktest OBI tutorial](https://hftbacktest.readthedocs.io/en/latest/tutorials/Market%20Making%20with%20Alpha%20-%20Order%20Book%20Imbalance.html) [BT]
- Same fee model (−0.5 bp maker / 7 bp taker). Queue model power 2 (2023) and power 3 (2025).

| Run | Sharpe | Return | Max DD | Trades/day | Return/trade |
|---|---|---|---|---|---|
| BTCUSDT May 2023 | 10.8 | 34.2% | 3.7% | about 4,120 | 0.0139% (1.39 bp) |
| ETHUSDT May 2023 | 9.0 | 30.0% | 5.5% | about 4,113 | 1.18 bp |
| BTCUSDT Jan-Feb 2025 | 5.37 | 46.0% | 9.8% | about 4,534 | 0.86 bp |
| BTCUSDT May-Jul 2025 | 3.04 | 25.0% | 11.6% | about 3,096 | **0.44 bp** |

- Author: the decline in per-trade return "highlights the importance of rebates and the corresponding fee structure for market makers."
- For the high-volume variant (about 8,368 trades/day, 0.21 bp/trade), the author writes that "the strategy itself may not be profitable or may incur losses, it can help achieve market maker status."
- Backtest only; no live results are reported.

**Hummingbot**
- Official docs make **no profitability claims**. They warn that a low γ means more inventory-drift exposure — [Hummingbot Avellaneda docs](https://hummingbot.org/strategies/v1-strategies/avellaneda-market-making/) [EX]
- Hummingbot's own "beginner misconceptions" page lists "fees are negligible" and "it's been profitable for the past week, time to go all in" as mistakes — [Hummingbot Academy](https://docs.hummingbot.org/academy-content/top-beginner-misconceptions-about-market-making/) [PRAC]
- Hummingbot's liquidity-mining analysis of the $ONE token on Binance (Jul 1 to Sep 4, about 2 months, period year not stated; probably 2020/21):
  - 68 participants; top 10 = 88% of filled volume; 143,000+ fills, $6.4M volume, $44 average fill; about 8% of $ONE Binance volume in the final week. $ONE fell 60% during the period.
  - **No PnL or share-profitable figure was reported.** "Success" was inferred from retention (about 40% still running after one month).
  - — [Hummingbot blog](https://hummingbot.org/blog/does-community-based-market-making-work/) [MKT/PRAC]
- Interviewed liquidity miners report being "somewhat profitable, though not substantially." Stablecoin pairs did best. They stopped bots during sharp drops and used volatility/inventory kill switches. — [interview D. Salter](https://hummingbot.org/blog/interview-with-liquidity-miner-david-salter/); [interview Neohowie](https://hummingbot.org/blog/interview-with-liquidity-miner-neohowie/) [PRAC, anecdotal, rewards-subsidised]
- A Firo community campaign tester noted that 3 of 4 rapid-fire orders were losers and that the test was inconclusive — [Firo forum](https://forum.firo.org/t/2022-firo-hummingbot-campaign/2290?page=2) [PRAC]

**RL on perps (2026)**
- Čekal, "Reinforcement Learning for Perpetual Futures Market Making," FFA Working Paper 6/004 (cover date Jan 22, 2026) [WP].
- Assumes **maker fees are zero and taker fees five basis points** for the perps studied. It decomposes PnL into spread capture, adverse selection, and inventory risk, and uses an "adverse-fill penalty" in training.
- Its zero-maker-fee assumption is more favourable than VIP0 Binance/Bybit (+2 bp). — [FFA WP PDF](https://wp.ffu.vse.cz/pdfs/wps/2026/01/04.pdf)

### Inferences
- **Back-of-envelope conversion to VIP0.** The rebate is per unit of trade value and hftbacktest's "return/trade" is a per-trade return, so swapping a −0.5 bp rebate for a +2.0 bp maker fee lowers each maker fill by about 2.5 bp:
  - BTC May 2023: 1.39 → about −1.1 bp
  - BTC Jan-Feb 2025: 0.86 → about −1.6 bp
  - BTC May-Jul 2025: 0.44 → about −2.1 bp
  - Even at zero fee, the May-Jul 2025 run would be about −0.06 bp per trade.
  - This assumes "return/trade" ≈ net PnL per fill as a fraction of trade value. The exact denominator of hftbacktest's metric was not verified.
- Sharpe values in the 10-20 range over 5-day to 1-month windows are typical of short in-sample backtests. They are not evidence of live viability.
- NautilusTrader: not researched in depth. It ships Binance/Bybit adapters, including fee models (see [nautilus_binance fees.rs](https://nautilustrader.io/docs/rust-api-latest/src/nautilus_binance/common/fees.rs.html)), but we found no published MM PnL from it.

### Gaps
- No independently verified live retail MM track record (broker statements, on-chain, or audited) on Binance/Bybit perps was found.
- Hummingbot 2024-2026 community PnL data (for example from its "Botcamp" or V2 controllers) was not found.

---

## 4. Fee and queue realities, with break-even math

### Takeaway
At VIP0 a maker round trip costs **4.0 bp** (3.6 bp with Binance's BNB discount). Maker entry plus taker exit costs **7.0 bp** on Binance and **7.5 bp** on Bybit. BTCUSDT's one-tick spread is about **0.01-0.03 bp**, so **pure spread capture on BTC/ETH perps at regular-tier fees is mathematically impossible**: fees are more than 100x the spread. Wider-spread altcoins can cover fees on paper, but their spreads are wide largely because adverse selection and volatility are high. Rebate programs exist but require institutional-scale maker volume share and colocation-grade latency. MES on CME is also negative before adverse selection at typical retail commissions.

### Cited Findings
- **Binance USD-M VIP0**: **0.02% maker / 0.05% taker** — [Finder](https://www.finder.com/cryptocurrency/trading/binance-futures-fees) [MKT]; [TradersUnion](https://tradersunion.com/brokers/crypto/view/binance/futures-fees/) [MKT]
- **10% discount** when paying USD-M fees in BNB — [Binance support FAQ](https://www.binance.com/en/support/faq/360033544231) [EX]
- VIP1 needs about $15M 30-day futures volume (and/or a 25 BNB balance; sources disagree on and/or) — [Datawallet](https://www.datawallet.com/crypto/binance-vip-levels-explained) [MKT]
- Maker fee reaches 0.0000% only at VIP9, and taker falls to 0.017% at the top tier — [Datawallet](https://www.datawallet.com/crypto/binance-vip-levels-explained) [MKT; verify on Binance's official fee table]
- **Bybit non-VIP perps: 0.02% maker / 0.055% taker**. Bybit charges no liquidation fee; funding is exchanged every 8 h — [Bybit help center](https://bybit.nl/en-NL/help-center/article/Perpetual-Futures-Contract-Fees-Explained) [EX]
- Bybit VIP1 0.018%/0.040% and VIP2 0.016%/0.0375% are reported by third parties, which disagree — [coinperps](https://www.coinperps.com/learn/bybit-vip-program) [MKT]
- **Binance USD-M Liquidity Provider Program**:
  - Highest maker rebates for qualified LPs were **−0.005% on USDT-M perps** and **−0.008% on USDC-M perps** (June 2025 terms).
  - Qualification is based on a participant's **share of weekly USD-M maker volume**, including a measure that excludes BTC/ETH pairs, plus a quoting-ranking option.
  - A Nov 12, 2025 limited-time promotion boosted the BTCUSDT maker rebate. The exact figure in the search summary ("0.05 bps") is ambiguous; verify.
  - The 2024 schedule had a Tier 1 rebate of −0.003%.
  - No 2026-dated terms were found. — [Binance LP program upgrade 2024-01-03](https://www.binance.com/en/support/announcement/detail/f5d3200b65104308b8349cee59a2296e) [EX]; [Binance announcement](https://www.binance.com/en/support/announcement/a0268fbc13fd487a9ec9744a1a42480c) [EX]
- hftbacktest's summary of MM programs:
  - Binance Futures highest rebates 0.005%-0.008%, servers in **AWS Tokyo**.
  - Bybit Futures highest rebates **0.0025%-0.0125%**, servers in **AWS Singapore**.
  - Benefits: higher rate limits, low-latency connection, onboarding trial period.
  - — [hftbacktest market maker program page](https://hftbacktest.readthedocs.io/en/latest/_sources/market_maker_program.rst.txt) [BT/PRAC; the page warns it may be outdated]
- **BTCUSDT tick in bp**: the Albers et al. experiment reports a tick of about **0.03 bp** on Binance BTC perp (2024 prices) — [arXiv HTML](https://arxiv.org/html/2502.18625v2) [WP]
- Latency: the ranking of relative latency determines HFT performance — [Baron et al. JFQA 2019](https://ideas.repec.org/a/cup/jfinqa/v54y2019i03p993-1024_00.html) [PR]
- **CME MES costs and tick**:
  - Tick = 0.25 index points = **$1.25** — [TradeZero spec](https://tradezero.com/en-us/support/questions/what-are-the-contract-specifications-for-the-micro-e-mini-s-and-p-500-mes-tradezero-america) [EX/broker]
  - Exchange plus clearing about **$0.35 per side** (non-member) — [TradeStation fees](https://tradestation.com/pricing/exchange-execution-and-clearing-fees/) [broker]
  - NFA fee about $0.01 per side — [TradeStation fees](https://tradestation.com/pricing/exchange-execution-and-clearing-fees/) [broker]
  - Example broker commission **$0.39 per side** — [TradeZero](https://tradezero.com/en-us/support/questions/what-are-the-contract-specifications-for-the-micro-e-mini-s-and-p-500-mes-tradezero-america) [broker]
  - CME's 2026 fee schedule PDFs exist ([e.g. 2026-10-01](https://www.cmegroup.com/company/files/cme-fee-schedule-2026-10-01.pdf)), but the MES line was not extracted. CME fees can change without notice.

### Break-even math (computed from the fee figures above)

Notation: S = quoted spread captured per round trip (bp), AS = adverse markout per round trip (bp), F = fees per round trip (bp).

Net per round trip = S − AS − F.

| Venue / tier | Entry | Exit | Fee per round trip F |
|---|---|---|---|
| Binance VIP0, maker/maker | 2.0 | 2.0 | **4.0 bp** |
| Binance VIP0 with BNB, maker/maker | 1.8 | 1.8 | **3.6 bp** |
| Binance VIP0, maker/taker | 2.0 | 5.0 | **7.0 bp** (6.3 with BNB) |
| Binance VIP0, taker/taker | 5.0 | 5.0 | **10.0 bp** |
| Bybit non-VIP, maker/maker | 2.0 | 2.0 | **4.0 bp** |
| Bybit non-VIP, maker/taker | 2.0 | 5.5 | **7.5 bp** |
| Binance best LP rebate, maker/maker | −0.5 | −0.5 | **−1.0 bp** (you are *paid* 1 bp) |

Gap between VIP0 and best-tier LP: **5 bp per maker round trip** (2.5 bp per fill).

- **BTCUSDT perp, quoting at the touch**:
  - S is about 0.01-0.03 bp (one tick; about $0.10 on a roughly $90-100k price, an assumed 2026 level). So S − F ≈ −3.97 bp before any adverse selection.
  - To break even, the total quoted spread must be ≥ 4 bp + AS, i.e. **≥ 2 bp + AS/2 from mid on each side**. That is about 70-200 ticks away from the touch, depending on price.
  - Those orders fill only when price sweeps ≥ 2 bp through the book, which is when short-term momentum, and so AS, is highest. Quoting wide turns "market making" into a mean-reversion bet on sweeps.
- **Albers et al. at VIP0**: naive at-touch MM averaged **−0.43 bp per trade** *with* the −0.5 bp rebate. Swapping to a +2 bp fee gives about **−2.9 bp per trade** if "trade" = one fill, or about −5.4 bp if "trade" = one round trip. The paper's best reversal configuration (+1.21 bp, about 426 fills/day) becomes about **−1.3 bp** at +2 bp maker.
- **Altcoin perps**: for an alt with a 5 bp quoted spread, S − F = +1 bp per maker round trip *before* AS. Albers et al. measure BTC-perp 1-s markouts of −0.06 to −1.16 bp per fill, which is already ≥ 1 bp per round trip in most queue states. Alt markouts are plausibly larger given higher volatility and thinner books.
  - Break-even condition per fill: **half-spread captured − markout_per_fill ≥ 2 bp** (maker fee).
  - Equivalently, the quoted spread in bp must be ≥ 4 + 2·markout_per_fill.
  - With a forced taker exit on, say, 30% of round trips (inventory cap hits), add 0.3 × 3 bp = 0.9 bp per round trip (the taker-minus-maker difference at Binance).
- **CME MES**:
  - Retail all-in cost is about $0.35 + $0.01 + $0.39 ≈ **$0.75 per side, so about $1.50 per round trip ≈ 1.2 ticks**.
  - A one-tick spread capture is $1.25, so the net is about **−$0.25 per round trip before adverse selection**. Spread capture loses money unless commissions fall below about $0.27/side.
  - In bp terms: at an S&P level of about 6,500 (an assumption), one tick is about 0.38 bp of notional ($32.5k), and the round-trip cost is about 0.46 bp.
  - CME uses price-time (FIFO) priority on equity index futures (not verified this session), so queue position is won by speed and early joining, where retail is at a structural disadvantage.

### Inferences
- **Retail MM at regular-tier fees is not viable on BTC/ETH perps** on any evidence found. The only path to fee-positive maker economics is a rebate tier. That needs (a) a meaningful share of weekly exchange maker volume, plausibly hundreds of millions to billions of USD per week (threshold not confirmed; see Gaps), and (b) a colocated AWS Tokyo/Singapore setup. A 20-200 ms retail loop is 1-3 orders of magnitude slower than a colocated in-region setup, which matters most for cancelling stale quotes before being picked off.
- The volume needed for Binance VIP1 (about $15M/30 d) is achievable for a retail bot, but VIP1 maker is still positive (not a rebate). It only modestly lowers F.
- Exchange fee changes are a first-order risk. hftbacktest's own results show the edge per fill shrinking below the rebate size between 2023 and 2025.

### Gaps
- Official 2026 Binance and Bybit VIP and LP-program tables were not retrieved; values are from 2024-2025 announcements and third-party aggregators.
- The exact maker-volume-share thresholds for Binance LP tiers in 2025-2026 were not found (historically about 0.25%+ of exchange maker volume, but unverified).
- No 2026 dataset of typical quoted spreads (bp) on mid/small-cap Binance/Bybit perps was found.

---

## 5. Academic evidence on MM profitability and adverse selection in crypto and in HFT generally

### Takeaway
The best crypto-specific evidence (a live Binance BTC-perp experiment, 2024) shows naive at-touch MM is "highly unprofitable" even at the best rebate. Only a small, unscalable profit (about +0.7 to +1.2 bp per fill, a few hundred fills per day) survives, using imbalance-conditioned contrarian quoting with min-size orders and best-tier fees. General HFT literature shows MM profits are real but concentrated among the fastest firms.

### Cited Findings
- **Albers, Cucuringu, Howison & Shestopaloff (arXiv:2502.18625, v2 Nov 2025)** [WP], [arXiv HTML](https://arxiv.org/html/2502.18625v2):
  - **Setup**: live experiment on Binance linear BTC perp with minimum-size maker orders. Continuous quoting Feb 12-19, 2024: **232,897 orders, 127,051 filled**. Periodic quoting Aug 21-31, 2024: 172,800 orders, 95,998 filled; results were essentially identical.
  - **Assumptions**: best-tier fees (**taker 1.5 bp, maker −0.5 bp**), and latency treated as negligible.
  - **1-s post-fill markouts (excluding rebate), by queue position**, front (0-10%) vs back (75-100%):

    | Near-side queue | Opposite-side queue | Front | Back |
    |---|---|---|---|
    | Large | Small | −0.058 bp | −0.775 bp |
    | Large | Large | −0.296 bp | −1.157 bp |
    | Small | Large | −0.539 bp | −0.763 bp |
    | Small | Small | −0.562 bp | −0.677 bp |

  - 5-s expected return from an order's terminal time is about −0.8 bp, or −0.3 bp net of rebate. Front-of-queue fills with favourable imbalance are the only configurations with mostly positive outcomes.
  - **Strategy results (Table 2, net of fees)**:
    - Naive at-touch MM: 12,623 trades, **mean −0.4307 bp**, average hold 22.56 s, **cumulative loss of almost 60% over about 3 days 7 hours, annualised Sharpe −109**.
    - Imbalance maker without cancel: −0.4705 bp. With cancel: −0.4921 bp.
    - Imbalance taker: −1.9621 bp, despite about +1 bp gross per round trip before fees.
  - **Reversal-model "Balanced-Inventory" strategy (Table 4, logistic regression)**:

    | Threshold | Fills/day | Avg return | Sharpe | p-value |
    |---|---|---|---|---|
    | 0.24 | 654 | +0.71 bp | 11.97 | 0.016 |
    | 0.26 | 426 | +1.21 bp | 26.1 | 0.030 |
    | 0.28 | 270 | +0.90 bp | 12.3 | 0.165 (not significant) |

  - Authors' conclusions:
    - The strategy is "slightly profitable with min-sized orders and assuming low fees, albeit those profits are likely not scalable."
    - "Even minor changes to these assumptions could result in a significantly lower Sharpe ratio."
    - "Forecasting ability and ease of exploitation are anti-correlated."
    - "A key to successful market making is to avoid being adversely selected."
- **Hyperliquid adverse selection**: Barone & Lillo (arXiv:2606.15715) study market impact and adverse selection on Hyperliquid's fully on-chain perp order book. They find that hidden metaorders executed alongside already-visible same-direction TWAP flow bear higher permanent costs — [arXiv PDF](https://arxiv.org/pdf/2606.15715) [WP; search snippet only]
- **Zero-fee venues**: arXiv:2607.11888 (theoretical) argues that on zero-fee venues adverse selection becomes the binding constraint on how tight spreads can be — [arXiv PDF](https://arxiv.org/pdf/2607.11888) [WP; snippet only, not evaluated]
- **Binance short-horizon predictability**: arXiv:2602.00776 uses Binance Futures perp order-book data from 2022-2025 to test whether short-horizon return predictability has a common structure across crypto assets, linking it to order-flow imbalance and adverse selection — [arXiv PDF](https://arxiv.org/pdf/2602.00776) [WP; snippet only]
- **Funding-aware perp-DEX MM**: arXiv:2605.06405 proposes a funding-aware optimal MM model calibrated on Hyperliquid ETH/BTC/SOL — [arXiv HTML](https://arxiv.org/html/2605.06405v1) [WP; snippet only]
- **HFT generally**:
  - Menkveld 2013: spread income net of fees of EUR 1.55 vs EUR 0.68 positioning loss per trade — [EconPapers](https://econpapers.repec.org/RePEc:eee:finmar:v:16:y:2013:i:4:p:712-740) [PR]
  - Baron et al. 2019: profits concentrate in the fastest firms, and latency rank improvements raise performance — [IDEAS](https://ideas.repec.org/a/cup/jfinqa/v54y2019i03p993-1024_00.html) [PR]

### Inferences
- Albers et al. is the most directly relevant evidence. It is a live (not simulated) maker-fill dataset on the exact instrument, it shows how small the edge is, and it uses best-tier fees and negligible latency. Both assumptions are far more favourable than a VIP0 retail setup.
- Its markout table yields a practical rule: **only quote (or keep resting) when the order is near the front of the queue and the opposite queue is thin relative to the near queue (contrarian to imbalance); cancel otherwise**. Retail latency makes holding front-of-queue positions and cancelling in time much harder.

### Gaps
- No peer-reviewed (as opposed to WP) crypto perp MM profitability study was found.
- Makarov & Schoar (JFE 2020) and Capponi et al. (works on crypto/DEX liquidity and maker-taker) were not reviewed.
- No study quantified retail-vs-pro maker markouts on Binance by latency bucket.

---

## 6. Variant: maker-biased directional scalping (limit-order entries to save taker fees)

### Takeaway
Entering directional signals with passive limit orders saves 3 bp per side at VIP0 (5 bp taker vs 2 bp maker). But the trade-off is well documented: **the limit orders that fill are disproportionately the ones where price moved against the signal**. The trades you most want (strong momentum) don't fill. Taker-entered signals on BTC perp lose their about 1 bp gross edge to fees, and maker-entered signals lose it to adverse selection and non-fill.

### Cited Findings
- On Binance BTC perp: **negative correlation between maker fill likelihood and post-fill returns** — [Albers et al. arXiv](https://arxiv.org/abs/2502.18625) [WP]
- An imbalance signal traded as a **taker** earned about **+1 bp gross per round trip** but **−1.96 bp net** at 1.5 bp taker fees. Traded as a **maker**, the same signal earned **−0.47 bp (no cancel) / −0.49 bp (with cancel) net** *with* a −0.5 bp rebate. — [Albers et al. HTML](https://arxiv.org/html/2502.18625v2) [WP]
- **Undirectional reversal-signal maker orders**: at threshold 0.30, 233 orders/day, fill probability 0.85, **5-s post-fill return −0.32 bp**. At threshold 0.24, 882 orders/day, fill probability 0.87, −0.62 bp. — [Albers et al. HTML](https://arxiv.org/html/2502.18625v2) [WP]
- **Equities analogue** (Linnainmaa 2010, *Journal of Finance* 65(4):1473-1506) [PR]: trading patterns of Finnish individual investors are "explained in large part" by limit-order use, because "limit orders are price-contingent and suffer from adverse selection." — [IDEAS/RePEc](https://ideas.repec.org/a/bla/jfinan/v65y2010i4p1473-1506.html). A secondary blog cites limit orders executed in the first two minutes around earnings losing about −2.5% the same day — [dailyspeculations](https://dailyspeculations.com/wordpress/?p=394) [PRAC, unverified; check the paper].

### Inferences
- **Break-even for maker entry + taker exit at VIP0**: 7.0 bp (Binance) / 7.5 bp (Bybit) per round trip, plus adverse selection on entry, plus opportunity cost of missed fills.
- **Codable rule**: post entry at the best bid (long) only if the signal persists; cancel after N ms or if price moves ≥ 1 tick away; optionally "chase" by converting to taker after T ms.
- **Evaluation requirement**: compare signal PnL *conditional on fill* against unconditional signal PnL, and include missed trades. The fill-conditional distribution will be worse.
- **Maker-maker (entry and exit both passive)**: 4.0 bp per round trip, but exit fills are also adversely selected (your take-profit fills when price touches it, and your stop must be taker). Expect most profitable exits to be maker and most losing exits to be taker.

### Gaps
- No crypto-perp study directly measured the realised savings of maker-entry vs taker-entry for a fixed directional signal at retail latency.
- The Linnainmaa magnitudes were not verified from the primary text.

---

## 7. Failure modes

### Takeaway
The dominant failure modes are:
- Adverse selection by faster or informed flow (picked off on stale quotes).
- Inventory accumulation during trends.
- Latency races retail cannot win.
- Fee/rebate schedule changes that erase thin margins.
- Volatility and liquidation cascades where fills cluster on the wrong side.

### Cited Findings
- Naive at-touch quoting on BTC perp lost **almost 60% in about 3 days 7 hours (Sharpe −109)** even with the −0.5 bp rebate: adverse selection plus inventory drift — [Albers et al.](https://arxiv.org/html/2502.18625v2) [WP]
- An **unadjusted GLFT** model (no extra inventory skew) lost about 2.06% in one day (Sharpe −246) on ETHUSDT. Adding a skew/spread adjustment rescued it to about breakeven — [hftbacktest GLFT](https://hftbacktest.readthedocs.io/en/latest/tutorials/GLFT%20Market%20Making%20Model%20and%20Grid%20Trading.html) [BT]
- Max drawdown rose from 3.7% (May 2023) to 9.8-11.6% (2025) in hftbacktest's BTC OBI MM, while return/trade fell from 1.39 to 0.44 bp: edge decay plus higher tail risk — [hftbacktest OBI](https://hftbacktest.readthedocs.io/en/latest/tutorials/Market%20Making%20with%20Alpha%20-%20Order%20Book%20Imbalance.html) [BT]
- Inventory loss in downtrends: Hummingbot's academy describes a bot left holding inventory after a dip (for example "$1 for each BTC bought" as a temporary loss). Liquidity miners report stopping bots during sharp falls. The $ONE campaign ran through a **60% price decline** — [Hummingbot blog](https://hummingbot.org/blog/does-community-based-market-making-work/); [miner interview](https://hummingbot.org/blog/interview-with-liquidity-miner-david-salter/) [PRAC]
- Latency: relative latency rank drives HFT returns — [Baron et al.](https://ideas.repec.org/a/cup/jfinqa/v54y2019i03p993-1024_00.html) [PR]. Exchange MM programs offer low-latency connections and higher rate limits in AWS Tokyo/Singapore — [hftbacktest MM program page](https://hftbacktest.readthedocs.io/en/latest/_sources/market_maker_program.rst.txt) [BT]
- Fee and program dependence: hftbacktest attributes its profits to rebates — [GLFT page](https://hftbacktest.readthedocs.io/en/latest/tutorials/GLFT%20Market%20Making%20Model%20and%20Grid%20Trading.html). Binance's LP terms change frequently (2022, 2024, June 2025, Nov 2025 notices) — [Binance LP 2024](https://www.binance.com/en/support/announcement/detail/f5d3200b65104308b8349cee59a2296e) [EX]
- Edge does not scale: Albers et al. say profits are "likely not scalable" and fragile to "even minor changes" in assumptions — [arXiv HTML](https://arxiv.org/html/2502.18625v2) [WP]

### Inferences (risk controls to codify; synthesis, not sourced recipes)
- Kill switch if realised 1-min σ > X·(24 h median) or price moves > Y bp in Z s.
- Pull quotes on the side being swept when |OFI z| > threshold.
- Hard max inventory, with taker flatten at the cap.
- Daily loss limit.
- Disconnect handling: on websocket gap or stale book > 500 ms, cancel all (use exchange-side cancel-on-disconnect or deadman timers where available; exact Binance/Bybit endpoints not verified this session).
- Monitor funding (8-h on Bybit) for inventory carried across funding times.
- Liquidation cascades: one-directional taker flow fills resting bids repeatedly, which is the worst-case markout. Widen or pull when the open-interest drop or liquidation feed spikes.
- Crowding: many retail bots with the same Hummingbot/AS defaults cluster at the same prices, adding queue competition and correlated drawdowns. This is plausible but no source quantifies it.

### Gaps
- No source quantified retail MM losses specifically during crypto liquidation cascades (for example Oct 2025-type events).
- No source measured how much exchange fee changes affected retail bot cohorts.

---

## 8. Required data, trade frequency, and per-fill economics

### Takeaway
Credible MM research and backtesting needs:
- Tick-by-tick L2 depth (ideally full-depth diffs).
- The trade tape.
- Measured feed and order latencies.
- A queue-position model.
- Own fill/cancel logs to compute markouts.

Documented per-fill net edges at best-tier fees are roughly −0.5 to +1.4 bp, at hundreds to thousands of fills per day.

### Cited Findings
- **hftbacktest inputs**: L2 depth and trades replayed tick-by-tick; **interpolated order latency from live feed/order-latency data** (`intp_order_latency`); a probabilistic queue model (`power_prob_queue_model` with exponent 2 or 3); no-partial-fill exchange. GLFT fitting samples trades every 100 ms over 10-min windows — [hftbacktest OBI](https://hftbacktest.readthedocs.io/en/latest/tutorials/Market%20Making%20with%20Alpha%20-%20Order%20Book%20Imbalance.html); [GLFT](https://hftbacktest.readthedocs.io/en/latest/tutorials/GLFT%20Market%20Making%20Model%20and%20Grid%20Trading.html) [BT]
- **Hummingbot inputs**: volatility and trading-intensity buffers of 200 ticks (order-book snapshots), with α/κ estimated live — [Hummingbot docs](https://hummingbot.org/strategies/v1-strategies/avellaneda-market-making/) [EX]
- **Trade frequency and per-fill edge in the sources**:

| Source / strategy | Fills/day | Net edge per fill | Fee assumption |
|---|---|---|---|
| hftbacktest GLFT, ETH | about 9,500 | — | −0.5 bp rebate |
| hftbacktest Grid, ETH | about 5,900 | — | −0.5 bp rebate |
| hftbacktest OBI, BTC 2023 | about 4,100 | 1.39 bp | −0.5 bp rebate |
| hftbacktest OBI, BTC May-Jul 2025 | about 3,100 | 0.44 bp | −0.5 bp rebate |
| Albers naive at-touch | about 15,380 | −0.44 bp | −0.5 bp rebate |
| Albers best reversal | 270-654 | +0.7 to +1.2 bp | −0.5 bp rebate |
| Menkveld HFT (equities) | about 1,397 trades per stock | EUR 0.88 gross per trade | n/a |

  — [hftbacktest GLFT](https://hftbacktest.readthedocs.io/en/latest/tutorials/GLFT%20Market%20Making%20Model%20and%20Grid%20Trading.html); [hftbacktest OBI](https://hftbacktest.readthedocs.io/en/latest/tutorials/Market%20Making%20with%20Alpha%20-%20Order%20Book%20Imbalance.html); [Albers et al.](https://arxiv.org/html/2502.18625v2); [Menkveld WP](https://repec.tinbergen.nl/tin/wpaper/11076.rdf)
- Per-fill markout magnitudes on BTC perp at 1 s: **−0.06 to −1.16 bp** depending on queue position and imbalance — [Albers et al.](https://arxiv.org/html/2502.18625v2) [WP]

### Inferences
- **Minimum retail data pipeline**:
  - Binance `@depth@100ms` / Bybit orderbook.50 or 200 websocket diffs, with periodic REST snapshots for resync.
  - `@aggTrade` / public trades.
  - Own `ORDER_TRADE_UPDATE` / execution stream, with exchange timestamps stored alongside local receive timestamps to measure your own latency distribution.
  - (Stream names are standard API names, not verified this session.)
- **Per-fill KPI**: markout_k(fill) = side·(mid_{t+k} − fill_price)/fill_price, at k = 1 s, 5 s, 30 s, 60 s, in bp. Net per fill = markout − fee.
- **Go/no-go test**: run with tiny size for 1-2 weeks. Proceed only if the average 30-s markout plus half-spread captured exceeds the 2 bp maker fee by a margin, after fees, *including* taker exits forced by inventory caps.
- Because a +2 bp fee is several times larger than any net edge per fill reported above, the edge would have to come from much wider quotes on less liquid perps. That shifts the strategy from spread capture to a bet on mean reversion after the book is swept, and it should be judged as one.

### Gaps
- No public dataset of retail-latency (20-200 ms) fill markouts on Binance/Bybit was found.
- No source documented typical win/loss per round trip for retail MM bots in 2025-2026.
