# Order-Flow Imbalance (OFI), Order-Book Imbalance (OBI), Trade-Flow Imbalance and Microprice as 1–5 Minute Directional Scalping Signals (crypto perps and CME index futures, as of Nov 2026)

Source-rating legend: **[PR]** peer-reviewed journal; **[WP]** working paper or arXiv preprint (not peer reviewed); **[RB]** reputable open-source backtest with code; **[PRAC]** practitioner or blog; **[DOC]** official exchange or vendor documentation; **[BK]** background knowledge from the researcher's training. A [BK] item was not re-fetched this session and should be checked before publication.

Summary: OFI-type signals are strong at explaining price changes in the same interval (R² of 65–87%). They are weak or useless at predicting the next minute's return (out-of-sample R² below zero at 1 minute in Cont et al.). Their predictive power mostly sits between sub-second and a few seconds, or about "two price changes" ahead. The only live Binance BTC-perp test found (Albers et al. 2025) shows an imbalance taker strategy earning about +1 bp gross per round trip. Even at the best fee tier (1.5 bp taker), fees wipe that out entirely. At retail taker cost (~10 bp round trip) a standalone OFI or OBI taker scalp at 1–5 minutes has no supporting evidence. Its most defensible uses are as an execution-timing or adverse-selection filter for maker orders, or as one feature in a meta-labelling model on top of a slower primary signal.

---

## Q1. Exact definitions and formulas (codable)

### Takeaway
All core signals have precise, codable definitions. Normalization matters: divide by average depth, then take a rolling z-score. Use multi-level or integrated OFI rather than best-level only. The definitions below are implementation-ready. Formulas marked [BK] should be checked against the original paper.

### Cited Findings
**A. Best-level OFI (Cont, Kukanov & Stoikov 2014, J. Financial Econometrics) [PR]**
- Event-level contribution, for a book update n with best bid/ask prices P^B, P^A and sizes q^B, q^A:
  `e_n = 1{P^B_n >= P^B_{n-1}}·q^B_n − 1{P^B_n <= P^B_{n-1}}·q^B_{n-1} − 1{P^A_n <= P^A_{n-1}}·q^A_n + 1{P^A_n >= P^A_{n-1}}·q^A_{n-1}`.
  Then `OFI_k = Σ_{n in interval k} e_n`.
- Equivalently, OFI = L^b − C^b − M^b − L^a + C^a + M^a: limit arrivals minus cancels minus market orders at the best bid, minus the same at the best ask. — restated in [Cont, Cucuringu & Zhang, arXiv 2112.13213, footnote 4](https://arxiv.org/abs/2112.13213)
- Price-impact model: `ΔP_k = β·OFI_k + ε_k`, with β roughly inversely proportional to average market depth. Estimated on 50 US stocks at 10-second intervals; average R² was about 65%, and the relationship is contemporaneous, not predictive. — [BK] [Cont, Kukanov & Stoikov, arXiv 1011.6402](https://arxiv.org/abs/1011.6402) (not re-fetched)

**B. Multi-level and integrated OFI**
- Level-m OFI over window h is `OF^{m}_{t} = Σ_n (OF^{m,b}_n − OF^{m,a}_n)`. Scale it by average depth across the first M levels: `ofi^{m,h}_t = OF^{m,h}_t / Q^{M,h}_t`, where `Q^{M,h}_t = (1/M)·Σ_{m=1..M} (1/(2ΔN))·Σ_n (q^{m,b}_n + q^{m,a}_n)` and ΔN is the number of events in the window. The paper uses M = 10 levels. — [Cont, Cucuringu & Zhang (CCZ), arXiv 2112.13213 v4, Eqs. 2–3](https://arxiv.org/abs/2112.13213) [WP; later versions are reported as published in Quantitative Finance 2023, unverified]
- Integrated OFI: the first principal component of the 10-level OFI vector explains "over 89%" of its variance. `ofi^I_t = w1ᵀ·ofi_t / ||w1||_1`, where w1 is estimated from historical data (e.g., the previous day). — [CCZ](https://arxiv.org/abs/2112.13213)
- Xu, Gould & Howison, "Multi-level order-flow imbalance in a limit order book" (Market Microstructure and Liquidity, 2018/19): the MLOFI vector across the top ~10 levels is regressed with OLS or ridge on mid-price change. It improves out-of-sample contemporaneous fit over best-level OFI, with larger gains for some stocks. — [BK] [arXiv 1907.06230](https://arxiv.org/abs/1907.06230) (exact R² gains not verified this session)
- Kolm, Turiel & Westray, "Deep order flow imbalance" (Mathematical Finance 33(4):1044–1081, 2023) [PR]. They feed per-level OFI series (bid and ask separately, top 10 levels) into LSTM and MLP models. These models "significantly outperform most models trained directly on order books." The effective forecast horizon is "approximately two average price changes." Data: 115 Nasdaq stocks, LOBSTER, Jan 2019–Jan 2020. — [RePEc record](https://econpapers.repec.org/RePEc:bla:mathfi:v:33:y:2023:i:4:p:1044-1081); [SSRN 3900141](https://papers.ssrn.com/abstract=3900141); [Quantpedia summary [PRAC]](https://quantpedia.com/how-to-use-deep-order-flow-imbalance/)

**C. Queue imbalance and microprice**
- Queue imbalance: `I = (Q_bid − Q_ask)/(Q_bid + Q_ask)` using top-of-book sizes, so I ∈ [−1, 1]. Gould & Bonart (2016, Market Microstructure and Liquidity) use logistic regression of I to predict the direction of the next mid-price move. Predictive power is much stronger for large-tick stocks than small-tick stocks. — [BK] [arXiv 1512.03492](https://arxiv.org/abs/1512.03492) (exact accuracy numbers not verified)
- The same imbalance, with threshold |imb| > 0.5, is used in a live Binance BTC-perp study (defined as `(B_t − A_t)/(B_t + A_t)` on top-of-book quantities). — [Albers, Cucuringu, Howison & Shestopaloff 2025, arXiv 2502.18625](https://arxiv.org/html/2502.18625v2) [WP]
- Weighted mid: `P_w = I_b·P_ask + (1−I_b)·P_bid`, with `I_b = Q_b/(Q_b+Q_a)`. Stoikov's (2018, Quantitative Finance) microprice is `P_micro = mid + g(I, S)`. g is the expected long-run mid adjustment given discretized imbalance I and spread S, estimated from a Markov chain of (I, S, mid moves). It is a martingale-like fair price that predicts the next mids better than mid or weighted mid. A practical code feature is `micro_dev = (P_micro − mid)/tick` or `/mid` in bps. — [BK] [Stoikov, "The micro-price", SSRN 2970694](https://papers.ssrn.com/abstract=2970694) (not re-fetched)

**D. Trade-flow imbalance, CVD, VPIN**
- Trade-flow imbalance (TFI) over window W: `TFI_W = Σ buy-initiated qty − Σ sell-initiated qty`. Normalized form: `TFI_W / Σ qty`, which lies in [−1, 1]. On Binance aggTrade data the aggressor side comes from field `m` ("Is the buyer the market maker?"); m = true means a seller-initiated trade. — [Binance spot WebSocket docs [DOC]](https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md)
- Cumulative volume delta (CVD) is the running sum of signed taker volume, i.e. the cumulative TFI. [BK] practitioner convention, with no formal source.
- Silantyev (2019, Digital Finance 1:191–218) [PR] studied BitMEX XBTUSD perps. TFI explained contemporaneous price changes better than OFI, contrary to his prior hypothesis. Crypto differs from established markets through "lack of depth and low update arrival rates." — [Springer DOI 10.1007/s42521-019-00007-w](https://link.springer.com/doi/10.1007/s42521-019-00007-w); [RePEc](https://ideas.repec.org/a/spr/digfin/v1y2019i1d10.1007_s42521-019-00007-w.html)
- VPIN as implemented on Binance 1-minute bars: `VPIN_t = (1/W)·Σ_{i=t−W+1..t} |V^S_i − V^B_i| / V_i`, with bulk-volume classification `V^B_i = V_i·Z(Δp_i/σ_Δp)` and `V^S_i = V_i − V^B_i`. Lookback W = 50 or 100 bars. Related measures in the same paper: Roll measure `2·sqrt(|cov(ΔP_t, ΔP_{t−1})|)`, Kyle λ `(p_t − p_{t−W})/Σ b_i V_i` with `b_i = sign(p_i − p_{i−1})`, and Amihud `(1/W)·Σ |r_i|/(p_i V_i)`. — [Easley, O'Hara, Yang & Zhang 2024, SSRN 4814346](https://stoye.economics.cornell.edu/docs/Easley_ssrn-4814346.pdf) [WP]
- VPIN is unsigned: it measures toxicity or intensity, not direction. The original version uses volume buckets of ~ADV/50 and a 50-bucket window. — [BK] Easley, López de Prado & O'Hara, "Flow toxicity and liquidity in a high-frequency world," RFS 2012 (not re-fetched).

**E. Depth-band imbalance and normalization used by practitioners**
- hftbacktest's Binance-futures example uses `alpha = zscore(Σ Q_bid − Σ Q_ask)`, summing depth within 2.5% of mid (`depth = 0.025`). The z-score is rolling over 1 hour (3,600 one-second samples). Fair price is `mid + c1·alpha`, with c1 = 160 for BTC and 10 for ETH. A "volume" variant uses depth within 0.1% and a 10-minute window. — [hftbacktest tutorial [RB]](https://hftbacktest.readthedocs.io/en/latest/tutorials/Market%20Making%20with%20Alpha%20-%20Order%20Book%20Imbalance.html)
- Bieganowski & Ślepaczuk (2026) [WP] use raw, unnormalized features at 1-second frequency on Binance perps: top-of-book spread, L1 volumes and imbalance, net or signed order flow, and buy/sell VWAP-to-mid deviations. The exact OFI formula and windows are not published in the paper. — [arXiv 2602.00776](https://arxiv.org/html/2602.00776v1)

### Inferences
- Recommended feature set for code: best-level OFI and integrated 10-level OFI, both depth-normalized; L1 queue imbalance; microprice deviation in ticks; TFI normalized by volume; depth-band imbalance (±0.1% and ±0.5% of mid); VPIN as a regime/toxicity filter. Aggregate into 1-second buckets, then take rolling sums over 10 s, 30 s and 60 s. Z-score over 30–60 minutes.
- For BTC/ETH perps on Binance, L1 queue imbalance and Stoikov microprice degenerate because the tick is tiny (~0.03 bp, see Q3). The spread is almost always 1 tick, so I mostly reflects queue sizes at the touch. Depth-band and multi-level measures are more informative there. For MES and ES, the large tick of 0.25 index points makes queue imbalance and microprice textbook-relevant (Gould & Bonart's large-tick result).

### Gaps
- I did not re-fetch the original Cont–Kukanov–Stoikov, Xu–Gould–Howison, Gould–Bonart or Stoikov papers, so their exact R² and accuracy numbers are unverified (marked [BK]).
- Kolm et al.'s per-horizon out-of-sample R² tables were not retrieved.

---

## Q2. Evidence of predictive power by horizon (seconds vs minutes), decay, and crypto evidence

### Takeaway
Contemporaneous explanatory power is very high (R² 65–87%). Forward predictability exists at sub-second to few-second horizons (≤500 ms for deep learning on stocks; ~2 price changes; a 3-second horizon on Binance perps). It is close to zero at 1 minute: Cont et al. find negative out-of-sample R² for 1-minute-ahead returns using OFI. Crypto-specific evidence covers horizons of ≤3 seconds, contemporaneous effects, or volatility and liquidity regimes, not 1–5 minute direction.

### Cited Findings
- **Contemporaneous fit (US equities, 1-minute bins, 2017–2019, ~100 large caps).** Best-level OFI price-impact model: in-sample R² 71.16%. Integrated OFI: 87.14%. Out-of-sample on the next 30 minutes: 64.64% (best-level), 66.03% (with cross-impact), 83.83% (integrated). — [CCZ, arXiv 2112.13213, Tables 3 & 5](https://arxiv.org/abs/2112.13213) [WP]
- **One-minute-ahead forecast.** Using lagged OFIs at lags {1, 2, 3, 5, 10, 20, 30} minutes with a rolling 30-minute estimation window, out-of-sample R² was: FPI best-level −0.37%, FCI cross-asset −0.10%, integrated FPI −0.36%, integrated FCI −0.10%. A pure return AR model got −0.36%. OFI forecasts were no better than an AR model on lagged returns. — [CCZ Table 8](https://arxiv.org/abs/2112.13213)
- In the same paper, a forecast-implied portfolio traded only when |forecast| > relative spread. It earned annualized PnL of 0.21 (FPI), 0.43 (FCI), 0.23 (AR) and 0.40 (CAR) with costs explicitly ignored ("the strategy ignores trading costs"). Lagged cross-impact "decays rapidly in time." — [CCZ §4.2–4.3](https://arxiv.org/abs/2112.13213)
- **Sub-second horizon.** Lucchese, Pakkanen & Veraart (IJF 40(4):1587–1621, 2024) [PR] find predictability of mid-price returns "ubiquitous" at high frequency, with high accuracy "up to 500ms ahead" using a deepVOL CNN on a volume representation of the book. — [arXiv 2211.13777](https://arxiv.org/abs/2211.13777v3); [summary page](https://alphatrade.readthedocs.io/en/latest/_shortterm_predictability.html)
- **About two price changes.** The effective horizon of deep-OFI forecasts is "approximately two average price changes," and accuracy declines beyond that. — [Kolm, Turiel & Westray 2023 [PR]](https://papers.ssrn.com/abstract=3900141)
- **Crypto, 3 seconds.** Bieganowski & Ślepaczuk (Jan 2026) [WP] use Binance Futures perps (BTC, LTC, ETC, ENJ, ROSE), 1-second data, Jan 2022–Oct 12 2025, with a CatBoost target of 3-second mid log return. OFI shows a "mostly monotone" effect with diminishing returns at the extremes. OFI, spread and VWAP-to-mid dominate SHAP importance and are stable across assets. No R², AUC or IC values are reported. — [arXiv 2602.00776](https://arxiv.org/html/2602.00776v1)
- **Crypto, contemporaneous.** On BitMEX XBTUSD, OFI shows a strong linear relationship with price change "over large enough time intervals," and TFI explains more than OFI. — [Silantyev 2019 [PR]](https://link.springer.com/doi/10.1007/s42521-019-00007-w)
- **Crypto, 1-minute bars, volatility and regime rather than direction.** Easley, O'Hara, Yang & Zhang (2024) [WP] use Binance 1-minute bars for five major coins, Jan 2021–Jul 2023. Targets are signs of changes in realized volatility, autocorrelation, Jarque–Bera, kurtosis and skew over a 1,500-bar look-ahead. Average accuracy is 0.53–0.54. AUC ranges 0.54–0.61 by label, except skewness (0.50). Predictability is driven mainly by the Roll measure and VPIN, with strong BTC/ETH cross effects. — [SSRN 4814346](https://stoye.economics.cornell.edu/docs/Easley_ssrn-4814346.pdf)
- **Crypto, liquidity state at 1 and 5 minutes.** Jeon (Jul 2026) [WP] uses Binance BTCUSDT/ETHUSDT perps, 2023–mid-2026, with top-20 L2 levels sampled once per minute. Pre-event trade-flow adds a small but significant improvement in predicting calm, mixed or stressed liquidity states after macro releases: pooled +0.010 at 1 m and 5 m, ETH +0.020/+0.016, BTC +0.001/+0.003 (no established BTC effect). The ETH increment rises in stressed regimes. The paper studies liquidity states, not price direction, and makes no profit claims. — [arXiv 2607.09230](https://arxiv.org/html/2607.09230v1)
- **Crypto, longer horizon.** "The Quarter-Hour Effect" (2026) [WP] reports that ordinary order imbalance has "little predictive content." Imbalance measured at 15-minute clock boundaries predicts returns over ~4–12 hours. — [arXiv 2607.09426](https://arxiv.org/html/2607.09426v1). This comes from a search snippet; the full paper was not read.
- **Simple models compete with deep ones.** On Bybit BTC/USDT book snapshots, logistic regression and XGBoost match or beat DeepLOB and Conv1D+LSTM once preprocessing is done (Kalman or Savitzky–Golay filters). — [Wang 2025, arXiv 2506.05764 [WP]](https://arxiv.org/abs/2506.05764v1). Horizon and accuracy numbers were not retrieved.

### Inferences
- The decay profile is consistent across studies. Contemporaneous R² is very high (OFI largely is the price move). Forward R² is meaningful only out to sub-seconds or seconds, and is ≤0 out-of-sample at 1 minute (equities). No study found reports positive, cost-relevant out-of-sample directional R² for OFI or OBI at 1–5 minutes on crypto.
- **Back-of-envelope (researcher's calculation, not from a source).** With BTC annualized vol of ~50%, 1-minute σ ≈ 0.5/√525,600 ≈ 6.9 bp and 5-minute σ ≈ 15 bp. A linear signal with forecast correlation ρ gives `E[r | z] ≈ ρ·σ_h·z`. Even an optimistic ρ = 0.05 (R² = 0.25%) at z = 2 yields ≈0.7 bp (1 min) or ≈1.5 bp (5 min). That is an order of magnitude below a 10 bp taker round trip. To clear 10 bp at 5 minutes at z = 2 you would need ρ ≈ 0.33 (R² ≈ 11%), which no study supports.
- Because OFI is mostly contemporaneous, a 60-second aggregated OFI z-score > 2 mostly tells you that price has already moved. At 1–5 minutes, any residual effect could be continuation (momentum or herding) or reversal (temporary impact decays). The sign must be tested empirically per asset and regime, not assumed.

### Gaps
- No peer-reviewed study was found that reports out-of-sample hit rates or R² for OFI/OBI at 1–5 minute horizons on Binance or Bybit perps.
- No CME ES/MES-specific OFI horizon study was retrieved this session.
- The Kolm et al. and Lucchese et al. accuracy-by-horizon tables were not extracted.

---

## Q3. Profitability after costs: what survives?

### Takeaway
In the only live Binance BTC-perp experiment found, an imbalance-following taker strategy earned about +1 bp gross per round trip with ~15-second holds. Net of the best-tier fee of 1.5 bp per side it lost −1.96 bp per trade. Imbalance-following maker variants also lost about −0.4 to −0.5 bp per trade, even with a 0.5 bp rebate. Effectively none of the gross edge survives retail costs. The only near-viable variants rely on top-tier maker rebates, minimum size, or contrarian quoting. At 1–5 minutes no study shows aggregated OFI predicting moves larger than about 10 bp.

### Cited Findings
- **Albers, Cucuringu, Howison & Shestopaloff, "The Market Maker's Dilemma" (arXiv 2502.18625, v2 Nov 2025) [WP, live trading data]**
  - Setup: Binance USDT-margined BTC perp. Live quoting Feb 12–19, 2024 placed 232,897 minimum-sized maker orders (127,051 filled). A second run in Aug 2024 placed 172,800 orders.
  - Assumed best-tier fees: taker 1.5 bp, maker rebate −0.5 bp. Tick ≈ 0.03 bp. — [arXiv html](https://arxiv.org/html/2502.18625v2)
  - Net results of "commonly-cited strategies" (Table 2):

    | Strategy | Trades | Mean net (bp) | Avg hold |
    |---|---|---|---|
    | Imbalance taker | 18,927 | −1.96 | 15.0 s |
    | Naive maker | 12,623 | −0.43 | 22.6 s |
    | Imbalance maker, no cancel | 8,851 | −0.47 | 32.2 s |
    | Imbalance maker, with cancel | 7,333 | −0.49 | 38.8 s |

    The naive market maker lost ~60% in about 3.3 days (annualized Sharpe −109). — [arXiv html](https://arxiv.org/html/2502.18625v2)
  - Quote: "challenging to overcome the taker fee with taker strategies, even when the signal provides a robust pre-fee edge." Pre-fee, the imbalance taker made about +1 bp per round trip; fees "erode its profitability completely." — same
  - Adverse selection: maker fill probability is negatively correlated with post-fill returns. One-second markouts range from −0.06 bp (front of queue, favourable queues) to −1.16 bp (back of queue). The average 5-second post-fill return is about −0.8 bp, or −0.3 bp after rebate. — same
  - Contrarian "balanced-inventory/reversal" maker with a logistic or random-forest fill model at threshold 0.24–0.34 earns +0.31 to +1.21 bp per fill. Holding times were ~194–409 (units likely seconds). Sharpe +12 to +26 on minimum size. The authors call it "slightly profitable with min-sized orders and assuming low fees, albeit those profits are likely not scalable," and "a proof-of-concept." — [arXiv html, Table 4 & conclusion](https://arxiv.org/html/2502.18625v2)
- **Bieganowski & Ślepaczuk 2026 [WP]** (3-second horizon, Binance perps). The taker backtest reports annualized return/vol ratio IR* of 8.97 (ETC), 6.58 (ENJ), 5.28 (ROSE), but only 0.25 for BTC and 0.07 for LTC. Maker IR* was 5.47 on BTC but negative on ETC and ENJ. Only ETC, ENJ and ROSE taker results were significant at 5%. The ROSE result is "largely due to the extreme event on 2025-10-10." The fee rate and fee-adjusted figures are not stated, and latency is not modelled, so the authors describe results as an upper bound. **Credibility: low to medium for live tradability.** — [arXiv 2602.00776](https://arxiv.org/html/2602.00776v1)
- **Briola, Bartolucci & Aste, "Deep limit order book forecasting: a microstructural guide" (Quantitative Finance 25(7):1101–1131, 2025) [PR].** On Nasdaq stocks, "high forecasting power does not necessarily correspond to actionable trading signals." Standard ML metrics are inadequate; the authors propose scoring the probability of correctly forecasting complete transactions. They release LOBFrame. — [arXiv 2403.09267](https://arxiv.org/html/2403.09267v3); [RePEc](https://econpapers.repec.org/RePEc:taf:quantf:v:25:y:2025:i:7:p:1101-1131)
- **LOBCAST, Prata et al. (Artificial Intelligence Review 57:116, 2024) [PR].** 15 deep LOB models perform markedly worse on new data than on FI-2010, and most overfit FI-2010. The authors raise doubts about real-market applicability. — [arXiv 2308.01915](https://arxiv.org/abs/2308.01915v2)
- **CCZ 2023 [WP].** Positive 1-minute PnL only with "the strategy ignores trading costs." — [arXiv 2112.13213](https://arxiv.org/abs/2112.13213)
- **hftbacktest OBI market making [RB].** Profitable in backtest (BTC May 2023: SR 10.83, 0.0139% per trade; BTC Jan–Feb 2025: SR 5.37, 0.0086% per trade; BTC May–Jul 2025: SR 3.04, 0.0044% per trade). This assumes a −0.005% maker rebate, "the highest market maker rebate available on Binance Futures," and a 0.07% taker fee. Per-trade return (0.44–1.39 bp) is of the same order as the 0.5 bp rebate. Results without the rebate are not shown, and the author stresses the importance of rebates. — [hftbacktest tutorial](https://hftbacktest.readthedocs.io/en/latest/tutorials/Market%20Making%20with%20Alpha%20-%20Order%20Book%20Imbalance.html)
- **Retail fee reference [BK, verify on exchange fee pages].** Binance USDⓈ-M futures regular (VIP0) is about 0.02% maker and 0.05% taker, with roughly 10% off when paying in BNB. Bybit non-VIP perps are about 0.02% maker and 0.055% taker. The brief's "~1 bp maker" assumption is lower than Binance VIP0's ~2 bp maker. — [Binance fee schedule](https://www.binance.com/en/fee/futureFee); [Bybit fee page](https://www.bybit.com/en/help-center/article/Trading-Fee-Structure) (not fetched this session)

### Inferences
- **Fraction of gross edge surviving.** In Albers et al., the imbalance taker's gross ~+1 bp per round trip became −1.96 bp net at 3 bp round-trip fees. At retail 10 bp round trip the same signal would lose about −9 bp per trade. Surviving fraction is 0%.
- **Crypto break-even.** A retail taker round trip on Binance is ~10 bp; spread is negligible on BTC (1 tick ≈ 0.01–0.03 bp), plus slippage. A maker–maker round trip is ~2–4 bp (VIP0) but incurs adverse selection of ~0.3–1.2 bp per fill (Albers markouts) plus non-fill opportunity cost. A maker-entry, taker-exit hybrid is ~7 bp.
- **MES break-even (researcher's arithmetic).** MES = $5 × S&P index and tick = 0.25 pt = $1.25. At an illustrative index of 6,000, notional ≈ $30,000. One tick ≈ 0.42 bp. With ~$1–2 per side all-in commission, a round trip costs ~$2.5–4 (~0.8–1.3 bp) plus one tick of spread crossing (~0.42 bp), about **1.2–1.8 bp round trip**. That is roughly 6–8 times cheaper than a Binance retail taker round trip. With S&P 1-minute σ ≈ 1%/√390 ≈ 5 bp and 5-minute σ ≈ 11 bp, the required ρ·z at 5 minutes is about 0.15. That is still above any documented 1–5 minute OFI forecast correlation, but within an order of magnitude. If any OFI-based taker scalp is viable for retail, MES is the more plausible venue on cost grounds. ES, however, is among the most HFT-contested books, so its sub-second alpha is competed away fastest.
- No study found demonstrates aggregated OFI at 1–5 minutes predicting a conditional mean move ≥10 bp out-of-sample. The answer to "is there a horizon where it exceeds ~10 bp?" is no evidence, and theory (Q2 arithmetic) argues against it.

### Gaps
- Bilokon & Qiu (2023, transformers vs LSTMs on LOB) and Briola et al. (2021, deep RL for active HFT) were not retrieved this session. My recollection is that both report results that are fragile or only profitable under favourable assumptions, but this is [BK] and unverified.
- There is no MES/ES OFI scalping study net of realistic costs.
- The exact Binance and Bybit 2026 fee schedules were not verified this session.

---

## Q4. OFI/OBI as a filter (entry timing, adverse-selection avoidance, meta-labelling)

### Takeaway
The strongest evidence of value is in execution and maker-side decisions: which side to quote, when to cancel, and where you stand in the queue. The evidence is not about standalone directional taker bets. Imbalance-aware maker strategies still lose at the top fee tier unless they go contrarian or use fill-probability models. That makes OFI/OBI a defensible filter or feature, not a standalone edge.

### Cited Findings
- Queue position and opposite-queue size drive post-fill markouts. Being at the back of a large near-side queue against a large opposite queue gives −1.16 bp at 1 second, versus −0.30 bp at the front. — [Albers et al. 2025, Table 1](https://arxiv.org/html/2502.18625v2)
- Imbalance-following maker logic (quote with the imbalance, cancel when it flips) did not improve outcomes: −0.47 and −0.49 bp versus −0.43 bp for naive. The improvement came from modelling "reversals." In those cases imbalance falsely predicts the next move, giving high fill probability and favourable subsequent returns. A contrarian maker with LR/RF fill models reached +0.3 to +1.2 bp per fill. — [Albers et al. 2025](https://arxiv.org/html/2502.18625v2)
- hftbacktest uses OBI as a fair-value skew for a quoting market maker rather than as a taker trigger. It reports positive backtest returns with rebates, plus a statement that the imbalance "continues to work consistently" in 2025. Per-trade edge shrank from 1.39 bp (2023) to 0.86 bp (Jan–Feb 2025) to ~0.44 bp (May–Jul 2025). — [hftbacktest [RB]](https://hftbacktest.readthedocs.io/en/latest/tutorials/Market%20Making%20with%20Alpha%20-%20Order%20Book%20Imbalance.html)
- For regime filtering, microstructure measures (Roll, VPIN) predict the sign of future changes in volatility and autocorrelation on Binance 1-minute data, with AUC 0.54–0.61. That is usable as a regime filter (e.g., avoid mean-reversion entries when volatility is predicted to rise). — [Easley et al. 2024](https://stoye.economics.cornell.edu/docs/Easley_ssrn-4814346.pdf)
- Trade-flow features add more information about liquidity-state transitions in stressed regimes, at least for ETH. — [Jeon 2026](https://arxiv.org/html/2607.09230v1)

### Inferences
- **Practical filter design.** Take a slower primary signal (e.g., 15-minute to 1-hour trend or mean-reversion). Enter with a passive limit only when the 10–30 s OFI z-score and the microprice deviation are not adverse to your side. Cancel or reprice when they turn adverse beyond a threshold. Use a meta-label classifier (gradient-boosted trees, triple-barrier labels) with OFI, TFI, depth imbalance, VPIN, spread and realized vol as features to decide whether to take or skip the primary signal.
- The value of such a filter shows up as reduced adverse selection on maker fills, about 0.3–1 bp per fill based on Albers markout dispersion. That is meaningful for maker-maker round trips (2–4 bp cost) but cannot rescue a 10 bp taker round trip.

### Gaps
- No published study was found that quantifies the improvement from OFI-based meta-labelling of a slower crypto signal net of costs.

---

## Q5. Practitioner reports and credibility

### Takeaway
The only high-quality reproducible practitioner work found is hftbacktest's OBI market-making tutorial. It is credible as a backtest because it uses queue and latency models and real data, but it is rebate-dependent and only shown for market making. No credible public practitioner result shows a profitable 1–5 minute OBI taker scalp on crypto after retail fees.

### Cited Findings
- **hftbacktest (nkaz001) [RB, credible].** Uses Binance Futures data, interpolated live order latency, a power-probability queue model (exponent 2–3) and no partial fills. Results are in Q3. The author states it is "for educational purposes only." The volume-generation variant "may not be profitable or may incur losses" but can help reach market-maker status. — [hftbacktest tutorial](https://hftbacktest.readthedocs.io/en/latest/tutorials/Market%20Making%20with%20Alpha%20-%20Order%20Book%20Imbalance.html)
- **Silantyev's Medium and Towards Data Science posts [PRAC, moderate].** Blog versions of his Digital Finance paper on OBI and OFI price impact in crypto. They describe contemporaneous impact, not tradable alpha. — [Medium](https://medium.com/@eliquinox/order-flow-analysis-of-cryptocurrency-markets-b479a0216ad8); [TDS](https://towardsdatascience.com/price-impact-of-order-book-imbalance-in-cryptocurrency-markets-bf39695246f6)
- **Forum commentary [PRAC, anecdotal].** At high frequency, backtest PnL overstates live results because of queue position, fill-rate degradation and impact. — [NexusFi thread](https://nexusfi.com/showthread.php?p=911892)
- **General cost-stress advice [PRAC, low].** Add the taker fee plus 0.1–0.2% slippage per side. — [HackerNoon](https://hackernoon.com/your-backtest-left-out-the-two-costs-that-kill-it). This is generic, not specific to OBI, and the slippage figure is high for BTC perps.
- **Quantpedia [PRAC, summary].** Summarizes Kolm et al. Useful as an explainer only. — [Quantpedia](https://quantpedia.com/how-to-use-deep-order-flow-imbalance/)

### Inferences
- Credibility ranking for this topic: live-data academic study (Albers et al.) > peer-reviewed forecasting studies (CKS, Kolm, Lucchese, Briola, LOBCAST) > reproducible open-source backtests (hftbacktest) > preprint backtests without stated fees or latency (Bieganowski) > blogs and forums. Marketing pages from "order-flow" indicator vendors were not used.

### Gaps
- A targeted search did not surface Robot Wealth, HangukQuant or high-quality r/algotrading posts testing OBI on crypto at 1–5 minutes. Treat any such claims the writer finds as unverified unless they show fees, latency and out-of-sample results.

---

## Q6. Required data and infrastructure

### Takeaway
Computing true OFI requires event-level or diff-level L2 depth plus aggressor-flagged trades. Binance public streams give 100 ms-aggregated diffs, so event-level OFI is only approximated. Historical replay needs a vendor such as Tardis.dev or self-recording. Compute itself is trivial; the binding constraints are network latency and data completeness.

### Cited Findings
- **Binance spot [DOC].** Diff depth `<symbol>@depth` or `<symbol>@depth@100ms` (1000 ms or 100 ms). Partial book `<symbol>@depth<5|10|20>[@100ms]`. Local book procedure: buffer events, fetch a REST snapshot (`/api/v3/depth?limit=5000`), drop events with `u <= lastUpdateId`, require `U <= lastUpdateId+1`, and resync on any gap where `U > local_id+1`. aggTrade field `m` = buyer is maker. — [Binance spot WebSocket docs](https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md)
- **Binance USDⓈ-M futures [BK, the official page fetch failed].** Diff depth `<symbol>@depth` (250 ms), `@depth@500ms` and `@depth@100ms`. Partial depth `@depth5/10/20` at 100/250/500 ms. Futures events carry `pu` (previous final update ID) for sequencing. Snapshot via `/fapi/v1/depth?limit=1000`. — [Binance derivatives docs](https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams/Diff-Book-Depth-Streams) (content not retrieved; verify)
- Jeon (2026) used a vendor snapshot archive of the top 20 levels sampled once per minute, not reconstructed real-time books. That illustrates the cheap-data option, and it is insufficient for OFI. — [arXiv 2607.09230](https://arxiv.org/html/2607.09230v1)
- Bieganowski & Ślepaczuk used Binance Futures perp order books and trades resampled to 1 second over 2022–2025. — [arXiv 2602.00776](https://arxiv.org/html/2602.00776v1)
- hftbacktest replays Binance Futures depth and trades with latency and queue models. Its tutorials include data-collection utilities. — [hftbacktest docs](https://hftbacktest.readthedocs.io/en/latest/tutorials/Market%20Making%20with%20Alpha%20-%20Order%20Book%20Imbalance.html)
- **Tardis.dev [BK, DOC not fetched].** Historical tick-level `incremental_book_L2`, `book_snapshot_25`, `trades`, derivative ticker and liquidations data for Binance and Bybit, recorded from exchange real-time WebSocket feeds. Delivered as downloadable CSV datasets or replay APIs. — [Tardis docs](https://docs.tardis.dev/) (verify coverage and pricing)

### Inferences
- **Minimum viable stack for 1–5 minute OFI research.** Record `@depth@100ms` (or rely on Tardis incremental L2) and `@aggTrade` for target symbols. Rebuild the book locally. Compute OFI per diff message (a 100 ms net change, so the true event OFI is netted within each 100 ms). Bucket to 1 s, then roll to 10/30/60 s.
- Latency budget: at a 1–5 minute hold, 50–300 ms of retail latency matters little for the hold itself. It matters a lot if the entry trigger is an OFI spike, because the informative part of OFI decays within seconds (Q2). Colocating a VPS in AWS Tokyo (ap-northeast-1) is a common practitioner choice for Binance. That is [BK], unverified.
- For MES, compute the signals from the ES book (CME MDP 3.0 market-by-price or market-by-order via a vendor such as Databento or Rithmic), not the thin MES book. This is [BK] and the researcher's recommendation.

### Gaps
- Binance futures stream speeds and the Tardis dataset list were not verified this session.
- No source was found quantifying OFI degradation from 100 ms aggregation versus true event data on Binance.

---

## Q7. Failure modes

### Takeaway
The main risks are decay speed (alpha lives in seconds), fee dominance, adverse selection on maker fills, regime dependence (results driven by stress events such as 10 Oct 2025), non-stationarity across years (the hftbacktest edge per trade halved from 2023 to 2025), and fake or fleeting depth beyond L1.

### Cited Findings
- **Decay.** Lagged cross-impact "decays rapidly in time." The 1-minute-ahead out-of-sample R² is negative. — [CCZ](https://arxiv.org/abs/2112.13213)
- **Edge erosion over time.** hftbacktest OBI return per trade fell from 0.0139% (May 2023) to 0.0086% (Jan–Feb 2025) to 0.0044% (May–Jul 2025). Sharpe fell from 10.8 to 5.4 to 3.0. — [hftbacktest](https://hftbacktest.readthedocs.io/en/latest/tutorials/Market%20Making%20with%20Alpha%20-%20Order%20Book%20Imbalance.html)
- **Event dependence.** The ROSE taker profit was "largely due to the extreme event on 2025-10-10." In that flash crash the maker strategy "suffers significant losses" while the taker profited. — [Bieganowski & Ślepaczuk 2026](https://arxiv.org/html/2602.00776v1)
- **Regime dependence.** The order-flow increment rises from calm to stressed regimes (ETH), and no effect is established for BTC. — [Jeon 2026](https://arxiv.org/html/2607.09230v1)
- **Overfitting and benchmark fragility.** Deep LOB models degrade on unseen data. — [LOBCAST](https://arxiv.org/abs/2308.01915v2). Forecast accuracy does not imply tradability. — [Briola et al. 2025](https://arxiv.org/html/2403.09267v3)
- **Scalability.** The contrarian maker profit is "likely not scalable" beyond minimum size, and "even minor changes to these assumptions could result in a significantly lower Sharpe ratio." — [Albers et al.](https://arxiv.org/html/2502.18625v2)
- **Asset heterogeneity.** In the same study, BTC and LTC taker IR* was about 0.25/0.07 versus 5–9 for small alts. — [Bieganowski & Ślepaczuk](https://arxiv.org/html/2602.00776v1). Crypto's thin depth and low update rates differ from established markets. — [Silantyev](https://link.springer.com/doi/10.1007/s42521-019-00007-w)
- **Periodic algorithmic flow at 15-minute boundaries [WP, snippet only].** This creates clock-time structure in imbalance. — [arXiv 2607.09426](https://arxiv.org/html/2607.09426v1)

### Inferences
- **Spoofing and layering.** Deep-book depth imbalance (e.g., ±2.5% bands) is vulnerable to large resting orders that are pulled before the price arrives. Mitigations: favour event-flow measures (OFI counts cancels and executions), weight depth by survival time, cap any single level's contribution, and prefer TFI (executed volume cannot be spoofed). This is the researcher's inference; no crypto-spoofing quantification was retrieved.
- **Small-alt edges.** Apparent high-IR edges on illiquid alts are where slippage, latency and data errors are worst. Treat them as upper bounds.
- **Exchange quirks.** 100 ms netting of diffs, snapshot resync gaps, funding-time flows and liquidation cascades all distort OFI. Albers' tick of ≈0.03 bp also means L1 queue imbalance on BTC perps behaves very differently from large-tick equities.

### Gaps
- No source quantified spoofing prevalence on Binance or Bybit books, or crowding in OBI signals.

---

## Q8. Concrete codable rules for a 1–5 minute strategy, and an honest edge assessment

### Takeaway
A standalone taker OFI/OBI scalp at 1–5 minutes on Binance retail is unsupported by evidence and very likely negative expectancy: gross edge of ~0–2 bp against ~10 bp costs. The rules below are written so the hypothesis can be tested cheaply and falsified. Lean toward (a) maker entries with OFI as an adverse-selection filter, (b) MES/ES where round-trip cost is ~1.2–1.8 bp, and (c) OFI as a meta-label feature for slower signals.

### Cited Findings
- Cost anchors: live BTC-perp imbalance taker gross ≈ +1 bp and net −1.96 bp at 3 bp round-trip fees. — [Albers et al.](https://arxiv.org/html/2502.18625v2)
- Normalization template: rolling 1-hour z-score of depth imbalance within a band of mid. — [hftbacktest](https://hftbacktest.readthedocs.io/en/latest/tutorials/Market%20Making%20with%20Alpha%20-%20Order%20Book%20Imbalance.html). Depth-normalized multi-level OFI. — [CCZ](https://arxiv.org/abs/2112.13213)
- Trading only when the forecast exceeds the spread is an established gating rule. — [CCZ Eq. 18](https://arxiv.org/abs/2112.13213)

### Inferences (proposed rules; researcher's design, untested)

**Feature computation (every 1 s bucket):**
1. `ofi1_1s` = Σ CKS e_n over book diffs in the second (best level). `ofiI_1s` = integrated 10-level OFI, with PCA weights from the previous UTC day, each level divided by average depth.
2. `OFI60 = Σ_{last 60 s} ofiI_1s`. `zOFI60 = (OFI60 − mean_60min)/std_60min`. Do the same for 10 s and 30 s windows.
3. `TFI60 = (buyTakerQty − sellTakerQty)/totalQty` over 60 s, from aggTrade `m`. `zTFI60` uses a rolling 60-minute window.
4. `DBI = (ΣQbid − ΣQask)/(ΣQbid + ΣQask)` within ±0.1% of mid, z-scored over 60 minutes.
5. `micro_dev = (P_micro − mid)/tick`. Use Stoikov g(I, S) for ES/MES. For BTC perps, use weighted mid over the top 5 levels.
6. Regime: `rv5m` (realized vol over 5 minutes from 1 s returns), its 24-hour percentile, `VPIN50` on 1-minute bars, and spread in ticks.

**Variant A, taker momentum (test only; expected to fail on Binance retail):**
- Long when `zOFI60 > 2`, `zTFI60 > 1.5`, `micro_dev > 0`, `spread == 1 tick`, `rv5m` percentile is between 20 and 80, and the time is not within ±2 minutes of funding or a scheduled macro release. Mirror the rules for shorts.
- Exit at the first of: a time stop of 120 s (also test 60/180/300 s); take-profit = max(1.5 × round-trip cost, 0.75 × ATR_1m); stop-loss = 1.0 × ATR_1m; or `zOFI10 < −1` (flow reversal).
- Gate: trade only if the out-of-sample model-predicted move `E[r|features]` exceeds 1.5 × the round-trip cost (CCZ-style gating).
- Expected result: from Q2 arithmetic and Albers et al., gross ≈ 0–2 bp per trade against a 10 bp cost, so the net is about −8 to −10 bp per trade. On MES (~1.5 bp cost) it might approach break-even. That is not established.

**Variant B, also test the contrarian or reversal version:**
- Fade extreme `zOFI60 > 3` when `zTFI60` is diverging (flow not confirmed by executions) or `micro_dev` has already reverted. Albers et al. found reversals were where maker profit lay. Use the same exits.

**Variant C, maker entry with OFI filter (most defensible):**
- A primary directional signal comes from a slower model (e.g., 15-minute). Post a post-only limit at the touch on the signal side only if `zOFI10` and `micro_dev` are not adverse (e.g., for a buy, `zOFI10 > −0.5`).
- Cancel if `zOFI10 < −1.5` or the queue ahead exceeds X% of touch depth. The back of the queue costs about 0.8–1.2 bp per Albers.
- Exit passively at TP or by time stop. Cross the spread only at the stop-loss.
- Cost basis is ~2–4 bp round trip at VIP0, or ~7 bp with a taker exit. The filter is expected to save ~0.3–1 bp per fill in adverse selection.

**Variant D, meta-labelling:**
- Use triple-barrier labels (TP/SL in ATR multiples, vertical barrier 5 minutes) on the primary signal's events. Fit a gradient-boosted classifier with features {zOFI10/30/60, zTFI60, DBI, micro_dev, spread, rv5m, VPIN50, time of day}. Trade only when p > p* chosen out-of-sample net of costs. Use purged walk-forward CV, as Bieganowski & Ślepaczuk did.

**Validation protocol:**
- Walk-forward over at least 12 months, including a stress event (e.g., Oct 10 2025).
- Report per-trade gross and net bp, the hit rate, and how markouts decay at 1/5/30/60/120/300 s after the signal.
- Run a fee sensitivity analysis: 0, 2, 5, 10 bp round trip.
- Break results down by asset (BTC vs alts) and by vol regime.
- Treat any edge that exists only on alts or only around one crash as non-robust.

**Honest bottom line:** On Binance and Bybit at retail tiers, the documented predictable component of OFI/OBI at 1–5 minutes is far below 10 bp, in the low single bp at best. Gross edges that do exist (≈1 bp at ~15 s holds) are consumed even by top-tier fees. MES is about 6–8 times cheaper per unit of notional, so it is the only venue where a 1–5 minute OFI-informed taker scalp is even arithmetically plausible. ES is also among the most competitive books, and no supporting study was found.

### Gaps
- No empirical source was found for 1–5 minute OFI markouts on Binance, Bybit or CME, so all variant expectations are inferences from shorter-horizon evidence plus volatility arithmetic.
- The ATR multiples and z thresholds proposed are unvalidated design choices.
