# Retail Fees Erase Every Documented Scalping Edge

**No 1–5 minute scalping strategy in the evidence reviewed here has solid, net-of-cost proof of profit for a retail trader paying retail fees, and the earlier blueprint's core recommendation (maker-biased 1–5 minute scalping of BTC/ETH perpetuals with an order-flow filter) should be retired.** The most relevant evidence is a live experiment on Binance's BTC perpetual: an order-book-imbalance taker strategy earned about +1 bp gross per round trip and lost −1.96 bp net at the *best* fee tier, and a naive at-the-touch market maker lost almost 60% of its capital in about 3.3 days even while collecting a maker rebate ([Albers et al. 2025](https://arxiv.org/html/2502.18625v2)). At regular-tier fees (Binance USD-M 2.0 bp maker / 5.0 bp taker; Bybit 2.0 / 5.5) a round trip costs 4–11 bp, several times larger than any gross edge measured at minute horizons. Order-flow signals stop predicting anything after about a minute: out-of-sample R² for 1-minute-ahead returns is negative ([Cont, Cucuringu & Zhang](https://arxiv.org/abs/2112.13213)). Cost-inclusive tests of minute-bar mean reversion lose money despite 55–68% win rates ([WhatDoesntWork](https://whatdoesntwork.com/research/bollinger-rsi-adx-crypto-mean-reversion/)). The most defensible alternative is a slow, structural trade: **delta-neutral BTC/ETH funding carry** (long spot, short perpetual, entered with post-only orders, held for weeks). It earned a Sharpe of 1.80 on BTC after fees that were still cheaper than retail in the best academic test ([He et al.](https://arxiv.org/html/2212.06888v5)). It rests on a documented economic premium paid by leveraged retail longs ([BIS WP 1087](https://bis.org/publ/work1087.htm)). It is also honest about its ceiling: at baseline funding and retail fees it nets roughly 5–6% a year on capital, only 1–2 points above Treasury bills, with exchange-failure risk in the tail. For a directional sleeve that keeps the blueprint's rule-plus-meta-label architecture, the best-documented candidate holds positions for hours, not minutes: noise-area intraday momentum on index futures. Even that has decayed to roughly zero Sharpe in 2025–26 ([Brusco replication](https://github.com/giovannibrusco/zarattini-2024-momentum-spy)). Liquidation-cascade fades on crypto perpetuals have the right cost structure but no direct test yet. The NautilusTrader engine, the meta-label filter (now used only as an overlay) and the blueprint's validation discipline all carry over. The holding period, the venue logic and several fee assumptions do not.

## Fourteen strategies ranked: only slow, structural edges clear retail costs

The ranking below weighs four things: the quality of evidence for net-of-cost profit, how much of the gross edge retail costs consume, how hard the strategy is to build, and whether a solo developer can run it through a broker or exchange API. "Evidence strength" rates the best independent support for *net* profitability, not for the underlying statistical pattern. Order-flow imbalance, for example, has strong evidence as a *predictor* but no evidence of *profit* at retail costs.

| Rank | Strategy | Typical hold | Evidence strength (net of costs) | Cost sensitivity at retail fees | Complexity | Suitability for retail with an API |
|---|---|---|---|---|---|---|
| 1 | **Delta-neutral funding/basis carry** (BTC/ETH spot long + perp short) | Days to weeks | **Moderate**: two strong working papers (He et al.; BIS) plus a yield you can observe directly; no audited retail record | **Low**: 24–30 bp per round trip against ~3 bp/day of baseline funding | Medium (two legs, two account types, margin) | **High** outside US/EU/UK; US route (CME basis) earns ~T-bills |
| 2 | **Noise-area intraday momentum** (ES/MES/MNQ, decisions every 30 min) | 30 min to the close | **Moderate in-sample, decayed**: vendor-authored paper plus two independent replications; Sharpe ≈ 0 in 2025–26 | **High on MES** (1.2–1.5 bp cost vs ~2 bp edge per trade); medium on ES | Low–medium | Good via CME futures APIs; full ES needs ~$300k notional per contract |
| 3 | **Liquidation-cascade fade** (BTC/ETH perps) | 15–60 min | **Weak–moderate**: strong peer-reviewed mechanism, no direct net-of-cost test | **Low**: 4–12 bp cost vs ~150 bp target; break-even win rate 51–54% | Medium–high (liquidation data, news veto) | Medium: rare events, data gaps |
| 4 | **Rule trigger + ML meta-label filter** (overlay) | Inherits the primary rule's | **Weak–moderate**: conflict-of-interest-heavy, +3 to +6 points of out-of-sample precision, no independent minute-horizon test | Inherits the primary rule's | High | Good **only as an overlay** on an edge that already exists |
| 5 | FX benchmark-fix reversal (added) | ~30 min | Moderate working paper; authors say it is exploitable only by low-cost traders | High (needs <1 bp round trip) | Medium | Low–medium (ECN FX, outside the blueprint's venues) |
| 6 | MES VWAP ±2σ fade in balanced sessions | ≤45 min | **None independent** (rules proposed, untested) | Medium: 12–20 tick target vs ~1.5 tick cost, break-even ≈46% | Low | Mechanically easy; unproven |
| 7 | Opening-range / session-open breakout (MES/MNQ; crypto session opens) | Hours | **Weak**: vendor-authored QQQ paper assumed zero slippage; independent MNQ walk-forward is null; crypto session rules failed a pre-registered test | High: cost is 5–15% of R against a +0.13R expectancy | Low | Easy to code; no edge shown |
| 8 | Short-horizon stat arb / pairs (crypto 5 min–1 h; lead-lag) | Minutes to hours | **Low**: fragile, cost-sensitive; lead-lag plays out over ~55 ms | Very high (four fills per round trip) | High | Low |
| 9 | OFI / microprice directional scalping | 1–5 min | **Negative**: strong at predicting the *current* move, out-of-sample R² < 0 at 1 min; live taker test lost money at best fees | Extreme (~10 bp cost vs ~0–2 bp edge) | High (full order-book data) | Feature or execution filter only |
| 10 | Market making / maker spread capture at regular tier | Seconds | **Strong evidence that it fails** at regular-tier fees | Extreme (4 bp round trip vs a 0.03 bp tick on BTC) | Very high | None at regular tier |
| 11 | Mean reversion on minute bars (Bollinger, RSI(2), IBS) | Minutes | **Negative** (cost-inclusive backtests lose; data-snooping literature) | Very high (break-even win rate 73–87%) | Low | Keep only as a null control |
| 12 | Volatility-expansion breakout scalps (squeeze, Donchian) on 1–5 min bars | Minutes | **None**; contradicted by minute-level reversal in BTC | Very high | Low | None |
| 13 | Liquidity-sweep / stop-hunt reversal (ICT/SMC) | Minutes | **Marketing only**; peer-reviewed stop-cluster data show *continuation* | High | Low | None |
| 14 | Funding-timestamp scalp; cross-venue funding differential | Hours | None / very weak | Negative (a 1 bp payment vs multi-bp costs) | Medium | None / speculative |

Two patterns explain the ordering. First, every strategy whose evidence survives costs earns a **structural premium that does not depend on speed**: leverage demand in carry, temporary price pressure from forced selling in cascades, dealer hedging in intraday momentum. Every 1–5 minute idea, by contrast, competes for microstructure alpha that decays within seconds and is captured by colocated firms. Second, **holding period is the main cost lever**. The same 4–10 bp round trip that swamps a 1-minute scalp is trivial against a 150 bp cascade retracement or a multi-week funding stream.

## Fee arithmetic decides viability, and the blueprint understated it

### Regular-tier costs per round trip

Binance USD-M futures charge **0.02% maker / 0.05% taker** at the regular (VIP0) tier ([Finder](https://www.finder.com/cryptocurrency/trading/binance-futures-fees)), with a **10% discount** for paying fees in BNB ([Binance FAQ](https://www.binance.com/en/support/faq/360033544231)). Bybit's non-VIP perpetuals charge **0.02% / 0.055%** and settle funding every 8 hours ([Bybit help center](https://bybit.nl/en-NL/help-center/article/Perpetual-Futures-Contract-Fees-Explained)). Binance spot charges 0.10% / 0.10% ([Binance fee schedule](https://www.binance.com/en/fee/schedule)). On Binance futures the maker fee falls to zero only at VIP9 ([Datawallet](https://www.datawallet.com/crypto/binance-vip-levels-explained), third-party; verify against the official table). Maker *rebates* (best −0.005% on USDT-M) are paid only inside the Liquidity Provider Program, which ranks participants by their share of weekly exchange maker volume ([Binance LP program](https://www.binance.com/en/support/announcement/detail/f5d3200b65104308b8349cee59a2296e)).

| Venue / tier | Entry | Exit | Round trip | Note |
|---|---|---|---|---|
| Binance VIP0, maker/maker | 2.0 | 2.0 | **4.0 bp** | 3.6 bp with BNB |
| Binance VIP0, maker entry / taker exit | 2.0 | 5.0 | **7.0 bp** | 6.3 bp with BNB |
| Binance VIP0, taker/taker | 5.0 | 5.0 | **10.0 bp** | plus slippage |
| Bybit non-VIP, maker/maker | 2.0 | 2.0 | **4.0 bp** | |
| Bybit non-VIP, maker/taker | 2.0 | 5.5 | **7.5 bp** | taker/taker 11 bp |
| Binance best LP rebate, maker/maker | −0.5 | −0.5 | **−1.0 bp** | needs institutional maker-volume share |
| Funding carry, VIP0, four maker fills | spot 10 + perp 2 | spot 10 + perp 2 | **24 bp** | 30 bp if all four fills are taker |
| MES, retail broker example | ~$0.75 | ~$0.75 | **~$1.50 ≈ 1.2 ticks** before slippage | ≈1.2–1.8 bp all-in with a tick of slippage |

The MES line combines a **$0.39 per side** broker commission ([TradeZero](https://tradezero.com/en-us/support/questions/what-are-the-contract-specifications-for-the-micro-e-mini-s-and-p-500-mes-tradezero-america)) with roughly **$0.35 exchange-plus-clearing and $0.01 NFA per side** ([TradeStation](https://tradestation.com/pricing/exchange-execution-and-clearing-fees/)). One tick is $1.25, so a one-tick spread capture nets about −$0.25 before any adverse selection. An independent MNQ study assumed $4.00 per round trip ([Tradoki summary of arXiv 2605.04004](https://blog.tradoki.com/posts/opening-range-breakout-stocks-in-play-research)).

### Break-even win rates

The break-even formula to use everywhere is **p\* = (L + C) / (W + L)**. Here W is the average gross win, L the average gross loss and C the round-trip cost, all in bp. Expectancy is E = pW − (1 − p)L − C. This replaces the blueprint's (1 + c)/(1 + R) shorthand.

A typical mean-reversion scalp on a BTC perpetual (W = 20 bp, L = 40 bp) needs a win rate of **86.7% with taker fills** (C = 12 including 2 bp slippage), **80% with maker entry and taker exit**, and **73.3% with maker fills on both legs**. A "70% win-rate" scalp therefore loses money even at the cheapest retail execution. A cascade fade (W = L = 150 bp) needs only **51–54%**. An MES 4-tick target with a 6-tick stop needs about **75%**. An MES VWAP fade with a 15-tick target and 10-tick stop needs about **46%**. Turnover compounds the problem: 20 trades a day at 8 bp costs about **400% of notional per year** at 1× leverage, which is why continuous minute-bar systems fail.

A volatility check makes the same point from the signal side, on the researcher's own arithmetic. At 50% annualised volatility, BTC's 1-minute σ is about 6.9 bp and its 5-minute σ about 15 bp. An optimistic signal with forecast correlation 0.05 at a 2σ reading therefore predicts a move of only 0.7–1.5 bp. Clearing a 10 bp taker round trip at 5 minutes would need a correlation of about 0.33, which no study supports.

### Corrections to the earlier blueprint

| Earlier blueprint statement | Correction from the new evidence |
|---|---|
| Target "a venue with free depth and maker rebates" | At regular tier you **pay** +2.0 bp per maker fill (1.8 bp with BNB). Rebates exist only in LP programs ([Binance LP](https://www.binance.com/en/support/announcement/detail/f5d3200b65104308b8349cee59a2296e)). The gap between VIP0 and the best LP tier is **2.5 bp per fill, 5 bp per maker round trip**. |
| Seconds-scale holds are viable "where maker fees are ≤2 bps" | 2 bp is not low enough. Even *with* a −0.5 bp rebate, naive at-touch quoting lost −0.43 bp per trade on BTC perps ([Albers et al.](https://arxiv.org/html/2502.18625v2)). Viability requires a rebate tier plus colocation, not a 2 bp maker fee. |
| Any working assumption of a "~1 bp maker" fee | Binance and Bybit regular-tier makers pay **~2 bp**; takers pay 5.0 / 5.5 bp. |
| At minutes, OFI "becomes a legitimate adverse-selection filter for passive entries," the one place the signal maps to positive expectancy | Imbalance-aware maker quoting with cancels did **worse** (−0.49 bp) than naive quoting (−0.43 bp) at best-tier fees. Only a contrarian, fill-model-driven maker earned +0.7 to +1.2 bp per fill, and only with rebates, minimum size and a result the authors call "likely not scalable" ([Albers et al.](https://arxiv.org/html/2502.18625v2)). |
| MES "≈ $1.0–1.9 + $1.25 tick" round trip | Fees alone are ~$1.50 per round trip at one broker; with a tick of slippage per side it is ~$4 (about 1.2–1.8 bp at an S&P level of 6,000–6,500). |
| Recommended holding period 1–5 minutes | No strategy with net-of-cost evidence holds for 1–5 minutes. The defensible holds are **weeks** (carry), **hours** (intraday momentum) or **event windows of 15–60 minutes** (cascade fades). |

## The best strategy: delta-neutral funding carry beats every scalp, modestly

### Core logic and why the inefficiency persists

Perpetual futures have no expiry. Instead they pay a periodic funding transfer that ties their price to spot. Binance sets funding as F = average premium index + clamp(0.01% − premium, −0.05%, +0.05%) per 8 hours, scaled down for symbols on 4-hour or 1-hour intervals ([Binance funding formula](https://www.binance.com/fr/support/announcement/detail/c00588a7e8504b3eb28d02a2da00530b)). Hyperliquid uses the same structure, paid hourly and capped at 0.5% per hour ([Hyperliquid docs](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding)). Whenever the premium is small, funding **pins at 0.01% per 8 hours, about 10.95% a year paid by longs to shorts**. That floor comes from the exchange's own formula, not from the market.

A trader who is long spot and short an equal amount of perpetual holds no net price exposure and collects that transfer, plus any convergence of an elevated perpetual premium. The BIS finds that crypto carry averages **more than 10% a year and reaches 60%**. Interest-rate differentials explain almost none of it. What drives it is retail demand for leverage and the scarcity of arbitrage capital, which stays scarce because margin calls and liquidations spike in drawdowns ([Schmeling, Schrimpf & Todorov, BIS WP 1087](https://bis.org/publ/work1087.htm)). The premium persists for the same reason: the people paying it are trend-chasing leveraged longs, and the people who could arbitrage it away face real tail risk.

Convergence matters more than funding in the best backtest. For BTC with no fees, **8.64% of the 13.70% annual return came from the perpetual–spot gap closing and only 5.06% from funding** ([He, Manela, Ross & von Wachter](https://arxiv.org/html/2212.06888v5)).

### Codable rules

The bot decides once an hour, five minutes after the hour, on UTC timestamps.

**Signal.** First compute annualised funding: apr_now = rate per interval × (24 / interval hours) × 365. Read the interval for each symbol from the exchange, because Binance now moves some symbols to 4-hour or 1-hour funding. Then compute a 7-day trailing mean of hourly samples, apr_7d.

**Capital efficiency and fees.** Capital per unit of notional is 1 + 1/L, where L is the perpetual leverage (2 by default). The fee drag is fee_rt × 365 / expected hold days, with fee_rt = 24 bp for four maker fills at VIP0 and an expected hold of 45 days.

**Entry.** Enter if (apr_7d − fee drag)/(1 + 1/L) is at least the T-bill yield plus a premium (default 1%). Alternatively, enter on the He et al. deviation rule: ρ = 1095·(ln F − ln S), where F and S are the perpetual and spot prices, exceeds a bound of 1095 × fee_rt. At VIP0 maker fees that bound is about 263% annualised, meaning a perpetual premium of 24 bp; this is my arithmetic from the paper's definition. Skip any entry or exit within ±15 minutes of a funding settlement (00:00, 08:00 and 16:00 UTC by default). Working-paper evidence describes a U-shaped market-quality pattern around settlement, attributed to informed trading ([AFA submission](https://afajof.org/management/viewp.php?n=169764), abstract only, unverified).

**Execution.** Post-only limit orders join the touch on both legs: buy spot at the bid, sell perpetual at the ask. They are repriced to the touch every 10 seconds. After 120 seconds, cancel the lagging leg and complete the residual with a taker order so a naked leg never persists.

**Exit.** There is no take-profit and no conventional stop-loss, because the position has no price exposure. Exit when any of the following holds:
- apr_7d stays below the exit hurdle (T-bills × (1 + 1/L)) for 3 consecutive daily checks; the lower exit hurdle gives deliberate hysteresis against churn;
- apr_7d turns negative;
- the perpetual trades more than 50 bp below spot;
- the liquidation-distance check fails;
- one leg disappears (auto-deleveraging, liquidation, manual intervention);
- a venue or collateral incident occurs;
- the kill switch fires.

There is no trailing stop, and there is no fixed time stop. Instead, every position is re-justified against the entry hurdle daily.

**Risk and sizing.** Size by notional, not by stop distance:
- deploy at most 60% of capital per leg;
- hard-cap notional per symbol and per venue at 30–50% of total capital;
- run the perpetual at 2× isolated leverage, which puts the initial liquidation distance near 50%;
- de-risk by cutting both legs by a third if the liquidation distance falls below 30%;
- re-hedge if the two legs mismatch by more than 2%;
- hold BTC, ETH or USDC collateral rather than synthetic stablecoins or liquid-staking tokens.

These defaults are the notes' synthesis, not empirically validated values.

### Required data

The strategy needs:
- funding-rate history and the live predicted rate (the Binance mark-price stream, or REST);
- the per-symbol funding interval;
- spot and perpetual best bid/ask;
- mark and index price;
- account margin, liquidation price and the auto-deleveraging (ADL) indicator the exchanges expose;
- a T-bill yield series.

The backtest needs hourly bars plus funding at each settlement from 2020 onward. It also needs quote data (for example Tardis) to test the leg-in mechanics.

### When it works, when it fails, and the regime switch

Carry pays most in euphoric, leverage-heavy markets and least in bear markets, when funding goes flat or negative. He et al.'s BTC Sharpe ran **2.26 (2020), 2.39 (2021), 0.70 (2022) and 1.32 (2023)** at their highest-cost tier, and time in market fell from 28.7% to 9.2% between 2020 and 2022 ([He et al.](https://arxiv.org/html/2212.06888v5)). The regime switch is the entry and exit hurdle itself: the bot stays flat whenever trailing funding does not beat T-bills plus fees.

A second, counter-intuitive filter comes from the BIS finding that **high carry predicts future crashes**. When funding is extreme, the bot should *raise* its liquidation buffer and cut leverage rather than size up. The failure regime is a crash that breaks the hedge mechanically rather than economically. During 10–11 October 2025, about $19–20bn was liquidated in 24 hours ([insights4vc](https://insights4vc.substack.com/p/inside-the-19b-flash-crash)). Auto-deleveraging closed profitable positions, so hedged traders could be "right" and still lose ([Forklog](https://forklog.com/en/whales-adl-and-the-end-of-the-bull-what-really-happened-on-cryptos-black-saturday/)). Binance paid $283m in compensation after depegs of order-book-valued collateral (USDe, bnSOL, wBETH) ([insights4vc](https://insights4vc.substack.com/p/inside-the-19b-flash-crash)). Funding on major venues nonetheless stayed positive through the crash ([Coin Metrics](https://coinmetrics.substack.com/p/state-of-the-network-issue-335)).

### Costs and realistic return

A full cycle has four fills. At VIP0 maker prices it costs 24 bp of notional, roughly **8 days of baseline funding** (0.03% per day). Taker fills cost 30 bp, or about 10 days. Turnover is a handful of cycles a year, so fees are a drag rather than the deciding factor.

My arithmetic at L = 2 and a 45-day average hold runs as follows. Baseline funding of 10.95% minus a 1.95% fee drag gives about 9.0% on notional, or **about 6.0% on capital**. If funding runs at twice the baseline, the figure is about 13.3% on capital. Against that, the CME basis traded near 4.8% in 2026, which "barely beats Treasuries" ([The Block](https://www.theblock.co/post/396722/cme-bitcoin-futures-activity-slumps-to-14-month-low-as-basis-trade-unwind-drains-institutional-demand)). Ethena's sUSDe, which is essentially pooled funding carry, fell to about 3.5–5% after the October 2025 crash, and its TVL halved from more than $14.8bn ([The Block](https://www.theblock.co/post/380210/yield-compression-triggers-50-tvl-drop-in-usde-despite-rising-onchain-usage)).

The honest expectation is **T-bills plus 0–4 points, with venue tail risk**. In the "trade" sense there is one round trip per episode. The meaningful win/loss unit is the monthly carry P&L, which is positive in most months by construction and negative mainly when funding turns or the leg-in slips.

### Evidence and source quality

The core paper is He et al. (2020 to March 2024, Binance, hourly). It is a strong working paper by well-regarded authors, and its publication status is unconfirmed. At their "High" cost tier it reports Sharpe ratios of **1.80 (BTC), 2.55 (ETH) and 4.84 (BNB)**, annual returns of **6.38%, 9.59% and 18.41%**, and maximum drawdowns of **−4.43%, −3.94% and −1.11%**. Average holding time was about 135 hours, against 19 hours with no fees ([He et al.](https://arxiv.org/html/2212.06888v5)).

That "High" tier is **still cheaper than retail**: 6.75 bp spot and 1.44 bp futures maker fees, against VIP0's 10 bp and 2 bp. A retail run should therefore underperform the paper. The deviations the strategy trades shrank **about 11% per year**. The BIS paper is central-bank research of high credibility but not peer-reviewed.

Vendor claims of "10–40% APY" ([Sharpe AI](https://sharpe.ai/blog/funding-rate-arbitrage)) and "19% in 2025" ([OneKey](https://onekey.so/blog/ecosystem/hyperliquid-funding-rate-arbitrage/)) are **unverified marketing**. There is no peer-reviewed study at VIP0 fees and no audited retail track record. The 3–8% net-on-capital range is the researchers' estimate, consistent with the arithmetic above.

### Failure modes

**Decay and crowding.** Ethena's growth and the institutional CME basis trade are exactly the arbitrage capital that compressed the premium. Hedge funds reportedly cut net CME shorts by 89% from the December 2024 peak ([crypto.news](https://crypto.news/cme-bitcoin-futures-slump-as-basis-trade-unwinds-and-wall-street-steps-back/), secondary, unverified).

**Overfitting** risk is lower than for any directional strategy, because the rule has four or five economically anchored parameters. The real danger is regime overfitting: calibrating on 2020–21 euphoria.

**Operational tails dominate everything else:**
- auto-deleveraging of the short leg;
- collateral depeg;
- API-key compromise;
- account freezes;
- venue insolvency of the FTX type, whose probability-weighted loss can exceed a year of carry.

Mitigations are low leverage, BTC/ETH/USDC collateral, an automatic re-hedge when a leg disappears, and splitting capital across at least two venues.

**Jurisdiction.** Binance ceased EU services on 1 July 2026 ([Finance Magnates](https://www.financemagnates.com/cryptocurrency/regulation/europes-crypto-market-after-july-1-who-stays-who-leaves-and-what-changes-under-mica/)). The UK bans retail crypto derivatives ([FCA](https://www.fca.org.uk/news/press-releases/fca-opens-retail-access-crypto-etns/printable/print)). US persons are limited to CME basis at about T-bill yields, or the newly approved Deribit and Kalshi perpetual routes ([CoinDesk, May 2026](https://www.coindesk.com/policy/2026/05/28/u-s-cftc-opens-crypto-perp-door-with-approval-of-first-regulated-firm)).

## Second and third: hours-long momentum and event-driven cascade fades

### Noise-area intraday momentum on index futures (rank 2)

**Core logic.** Market intraday momentum holds that early-session moves predict late-session moves. It was documented on SPY for 1993–2013, with out-of-sample R² of 1.2–1.8%, and it was stronger on volatile, high-volume and macro-news days ([Gao, Han, Li & Zhou](https://c.mql5.com/forextsd/forum/173/intraday_momentum_-_the_first_half-hour_return_predicts_the_last_half-hour_return.pdf), JFE 2018, peer-reviewed). The leading explanation is short-gamma dealer hedging: dealers trade in the direction of the move near the close ([Baltussen et al. as summarised by FirmTape](https://dev.to/firmtape/intraday-momentum-is-dead-in-the-0dte-era-we-measured-it-on-1085-spx-sessions-43g0)). Its persistence is now in doubt. Across 1,085 SPX sessions in the 0DTE era (2022–2026), the unconditional slope is **+0.006 (t = 0.6)**. Continuation appears only on proprietary-estimated short-gamma closes, about 15% of sessions ([FirmTape](https://dev.to/firmtape/intraday-momentum-is-dead-in-the-0dte-era-we-measured-it-on-1085-spx-sessions-43g0); vendor conflict).

**Codable rules** come from Zarattini, Aziz & Barbon ([paper PDF](https://alexandria.unisg.ch/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/download); vendor conflict):

1. For each minute of the session, σ = the 14-day average of |Close at that minute / 09:30 Open − 1|. This makes the band time-of-day specific.
2. Upper band = max(today's open, yesterday's close) × (1 + VM·σ). Lower band = min(today's open, yesterday's close) × (1 − VM·σ). VM = 1 in the base case.
3. Check only at HH:00 and HH:30, starting at 10:00 ET. Go long above the upper band, short below the lower band.
4. Use a trailing stop evaluated at the same half-hour marks: max(upper band, VWAP) for longs, min(lower band, VWAP) for shorts. Crossing the opposite band reverses the position.
5. Flatten everything by the 16:00 close (15:59 ET in practice).
6. Size as AUM × min(4, 2% / 14-day σ of daily returns) / open.

For MES/MNQ, convert shares to contracts by notional ($5 × index for MES).

**Meta-label overlay.** This is where the blueprint's architecture fits:
- *Label:* each half-hour trigger is labelled 1 if the trade closes net-profitable after costs.
- *Features:* VIX at the open; NR4/NR7 compression flags; the prior day's 5-day RSI; overnight gap divided by σ; first-30-minute realised volatility; first-30-minute relative volume against 14 days; macro-calendar flags (FOMC, CPI); time of day.
- *Model and rule:* a gradient-boosted classifier, calibrated, trading only when p > p\*.

**Data.** 1-minute RTH OHLCV for ES/MES/MNQ (for example Databento), a roll-adjusted continuous contract, VIX at the open and a macro calendar.

**When it works and fails.** The paper's in-sample Sharpe rises with VIX at the open (about 3.5 above 40). Returns are higher on NR4 days (22 bp/day against 12 unconditional) and after recent declines (β = −3.25 on RSI5). The strategy's best years were crises: 2022 returned +25.8% while SPY fell 19.5% ([Brusco](https://github.com/giovannibrusco/zarattini-2024-momentum-spy)). It fails in calm, dealer-long-gamma tapes like 2025–26. A defensible regime switch is to trade, or size up, only when VIX at the open is at least about 20 or realised volatility is above its median. That threshold is not validated out of sample. Avoid day-of-week filters, which are a multiple-testing trap.

**Costs and viability.** The paper reports about **1.8 trades per day** (roughly 450 a year), a 37% trade hit rate, and positive skew, with a best trade of +9.1% and a worst of −2.9%. The independent replication finds about **+2 bp per trade on ES with a 36% win rate and a 2.1 payoff ratio**, with ES costs modelled at about 0.4 bp ([Brusco](https://github.com/giovannibrusco/zarattini-2024-momentum-spy)). On MES, all-in costs of about 1.2–1.5 bp consume most of that edge. On my arithmetic, one MES contract (~$30k notional) nets roughly $0–3 per trade, or at most about $1,000 a year *in years when the strategy works*. Full ES contracts (~$300k notional) cut costs per bp by about ten times.

**Evidence quality.** The vendor-authored paper reports **Sharpe 1.33 in-sample, 2007–2024**, with its stop and sizing rules added step by step on the same sample. The Brusco replication shows Sharpe 1.11 from 2020, yearly Sharpe of about 1.4–2.0 in 2020–24, and **then two years below zero (2025–26)**. Quarterly walk-forward reselection did worse than fixed parameters (0.57 vs 0.92).

A June 2026 out-of-sample study found May 2024 – March 2026 "told a very different story" ([Swedroe Substack](https://larryswedroe.substack.com/p/when-beat-the-market-meets-the-real); exact numbers paywalled). An NQ rebuild with parameters fixed on 2010–17 found long-only Sharpe 0.90 in-sample and 0.68 out-of-sample ([EdgeLab](https://edgelabtrading.com/blog/zarattini-intraday-momentum-nasdaq/); seller of strategies). The crypto analogue, Bitcoin intraday momentum ([Shen, Urquhart & Wang](https://onlinelibrary.wiley.com/doi/abs/10.1111/fire.12290), peer-reviewed), **failed a pre-registered out-of-sample test on Binance perpetuals, 2022–2026, with no gross edge** ([pre-registered test](https://github.com/nishimweprince/trading-algos/pull/98)). That test used a fixed UTC clock rather than Shen et al.'s volume-defined sessions.

**Failure modes.** The strategy has suffered rapid post-publication decay. It is regime-dependent and behaves more like a crisis-alpha sleeve than steady income. On micros it is cost-fragile. Its rules were assembled in-sample.

### Liquidation-cascade fade on BTC/ETH perps (rank 3)

**Core logic.** Forced selling creates temporary price pressure that later reverses. This is documented for forced mutual-fund sales (Coval & Stafford) and modelled in margin spirals (Brunnermeier & Pedersen) ([Open-Alpha-Lab references](https://github.com/Guillain-RDCDE/Open-Alpha-Lab/blob/main/studies/586-liquidation-cascade/docs/references.md)). Returns to liquidity provision rise "enormously" with VIX in turmoil ([Nagel 2012](https://nber.org/papers/w17653), peer-reviewed). Bitcoin shows intraday reversal after large jumps ([Wen et al. 2022](https://www.sciencedirect.com/science/article/abs/pii/S1062940822000833), peer-reviewed). In the October 2025 crash, the mark price used to trigger liquidations on Binance and Bybit **undershot both spot and futures** ([Lim, SSRN 6579278](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6579278), snippet only). The premium should persist because liquidity providers withdraw exactly when cascades hit.

**Codable rules** are the notes' starting points for walk-forward testing; none is validated. Let σ5 be the standard deviation of 5-minute log returns over the trailing 7 days, excluding the current hour.

*Long-fade trigger.* All of the following must hold at a 1-minute close:
1. The 15-minute return is at most −4·σ5·√3.
2. Long-liquidation notional over 15 minutes is at or above the 99th percentile of the trailing 30 days.
3. Open interest has fallen at least 3% over 15 minutes, which signals forced deleveraging rather than new shorts.
4. No scheduled macro release falls between t−30 and t+15 minutes, and no exchange-solvency or depeg headline is live.

Mirror the rules for short squeezes. A compression of taker order-flow variance in the prior 6 hours, which preceded six of seven major cascades ([Seuma 2026](https://arxiv.org/html/2607.27070v1)), is used only to cut size.

*Entry.* A post-only ladder at P − {0.5, 1.0, 1.5}·σ5·√3, one-third size each, live for 10 minutes. In backtests, count a fill only when price trades through the limit.

*Exits.* The first of the following:
- a target at the nearer of a 50% retracement of the cascade or the VWAP anchored at cascade start;
- a 60-minute time stop, with a passive exit at mid for 2 minutes and taker after that;
- a hard stop-market at the cascade low minus one cascade range (or 6 × 1-minute ATR), assuming 3–5× normal slippage.

*Risk.* Risk 0.25–0.5% of equity per event, cap BTC and ETH exposure jointly, and halt for the day after a 1.5R loss.

**Data.** 1-minute bid/ask, 5-minute open interest, the liquidation feed (Binance `!forceOrder@arr`, Bybit `liquidation`), funding and a macro and news feed. Binance's per-event liquidation snapshots are discontinued ([Seuma](https://arxiv.org/html/2607.27070v1)). The public stream reportedly reports at most one liquidation per symbol per second, which would understate volume (unverified). Historical backtests therefore need paid data from Coinglass, Amberdata or Kaiko.

**When it works and fails.** It works on leverage-driven cascades without fundamental news. It fails on information events such as FTX and LUNA, where the "overshoot" is the new price. Strong trends also defeat it: large liquidations "do not directly guarantee an immediate trend reversal" ([Coinglass](https://www.coinglass.com/liquidations/BTC)). After October 2025, order-book depth stayed depressed for weeks, which raises slippage ([Lim, SSRN 6636998](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6636998)). The regime switch is the headline veto plus the open-interest condition.

**Costs and viability.** Round-trip cost of 4–12 bp against a target of about 150 bp gives a break-even win rate of **51–54%**. The strategy trades perhaps tens of events a year per asset (unverified).

**Evidence.** The mechanism is peer-reviewed. Direct evidence is **absent**: no peer-reviewed or reputable independent study of forward returns after Binance or Bybit liquidation spikes exists, and an open lab rates the "buy the blood" idea as folklore ([Open-Alpha-Lab](https://github.com/Guillain-RDCDE/Open-Alpha-Lab/blob/main/studies/586-liquidation-cascade/docs/references.md)).

**Failure modes.** The main ones are misclassifying information events, too few events for statistical power, exchange outages mid-cascade, and the possibility that the growth of crypto market making and auto-deleveraging has shrunk overshoots. The first deliverable is an **event study against a placebo**, not a strategy.

## Why the other ten fail the cost test

### Market making at regular tier is mathematically underwater on BTC/ETH

**Logic and why it persists.** A market maker earns the spread as payment for immediacy, minus adverse selection and inventory losses. A real HFT market maker earned **€1.55 per trade from the spread and lost €0.68 to positioning** ([Menkveld 2013](https://econpapers.repec.org/RePEc:eee:finmar:v:16:y:2013:i:4:p:712-740)). Profits concentrate among firms ranked fastest on latency ([Baron et al. 2019](https://ideas.repec.org/a/cup/jfinqa/v54y2019i03p993-1024_00.html)). The premium persists, but it goes to the lowest-cost provider.

**Rules.** The standard codable stack is Avellaneda–Stoikov or GLFT quoting:
- reservation price r = s − qγσ²(T − t);
- half-spread c₁ + ½σc₂;
- an inventory cap, with taker flattening at the cap;
- quotes pulled when |OFI z| or the volatility ratio exceeds a threshold.

The hftbacktest tutorial publishes a fitted GLFT model ([hftbacktest GLFT](https://hftbacktest.readthedocs.io/en/latest/tutorials/GLFT%20Market%20Making%20Model%20and%20Grid%20Trading.html)).

**Data and regime.** It needs tick-level L2 depth, the trade tape, measured latency and a queue model. Trends and liquidation cascades are where inventory blows up.

**Costs.** BTCUSDT's tick is **about 0.03 bp** against a 4 bp maker round trip. To break even, quotes must sit at least 2 bp plus half the adverse selection away from mid on each side. That turns market making into a bet on sweeps reverting.

**Evidence** (strong, and negative for retail):
- Naive at-touch quoting lost −0.43 bp per trade *with* a rebate (Sharpe −109).
- The best contrarian model earned +1.21 bp per fill at 426 fills a day, which converts to about −1.3 bp at a +2 bp maker fee.
- hftbacktest's order-book-imbalance market maker fell from 1.39 bp per trade in 2023 to **0.44 bp in mid-2025, less than the rebate itself**, implying about −2.1 bp per trade at VIP0 ([hftbacktest OBI](https://hftbacktest.readthedocs.io/en/latest/tutorials/Market%20Making%20with%20Alpha%20-%20Order%20Book%20Imbalance.html); [Albers et al.](https://arxiv.org/html/2502.18625v2)).

**Failure modes.** Being picked off by faster traders, fee-schedule changes, inventory drift and edge decay.

### Order-flow imbalance and microprice predict the present, not the next minute

**Logic.** Order-flow imbalance (OFI) is the net of limit arrivals, cancels and market orders at the best quotes ([Cont, Kukanov & Stoikov](https://arxiv.org/abs/1011.6402)). It explains **71–87% of same-minute price changes**. Its 1-minute-ahead out-of-sample R² is **−0.10% to −0.37%**, no better than a return autoregression ([CCZ](https://arxiv.org/abs/2112.13213)). Deep-OFI models forecast only "approximately two average price changes" ahead ([Kolm et al. 2023](https://papers.ssrn.com/abstract=3900141)), and predictability is high only out to about 500 ms ([Lucchese et al. 2024](https://arxiv.org/abs/2211.13777v3)).

**Rules to falsify** the hypothesis: go long when the 60-second integrated-OFI z-score exceeds 2, the 60-second trade-flow z-score exceeds 1.5, the microprice sits above mid and the spread is one tick. Use a 120-second time stop, a stop at 1 × 1-minute ATR, and exit on a flow reversal. Trade only when the predicted move exceeds 1.5× costs.

**Data.** `@depth@100ms` diffs, `aggTrade` and a local book rebuild. Tardis provides history.

**Costs and evidence.** The live Binance imbalance taker made +1 bp gross and lost −1.96 bp net at 3 bp round-trip fees. At retail's ~10 bp that becomes about −9 bp per trade. A 3-second CatBoost study on Binance perpetuals stated no fees and modelled no latency, and its edge sat on small altcoins plus a single crash day ([Bieganowski & Ślepaczuk](https://arxiv.org/html/2602.00776v1), upper bound). Deep limit-order-book benchmarks overfit, and "high forecasting power does not necessarily correspond to actionable trading signals" ([Briola et al. 2025](https://arxiv.org/html/2403.09267v3); [LOBCAST](https://arxiv.org/abs/2308.01915v2)). On BTC perps the tiny tick makes L1 imbalance degenerate. MES's large tick makes the signal more relevant there, and MES's ~1.2–1.8 bp cost is the only arithmetically plausible venue for it, but no study supports even that.

**Verdict.** Use OFI only as a meta-label feature, or as a toxicity gate that tells a passive order on a slower signal when to cancel.

### Volatility-expansion breakouts scalp against minute-level reversal

**Logic.** A Bollinger/Keltner squeeze or a Donchian breakout is supposed to catch the start of a trend. **No cost-adjusted, snooping-corrected study** supports it on 1–5 minute ES/NQ or BTC bars.

**Evidence against.** BTC shows **negative autocorrelation at 1-, 5- and 15-minute horizons**, partly linked to liquidation cascades ([Ledger](https://ledgerjournal.org/ojs/ledger/article/download/213/212/1232)). Even in-sample technical-rule profits are offset by low transaction costs ([Bajgrowicz & Scaillet](https://bashtage.github.io/kevinsheppard.com/files/teaching/mfe/advanced-econometrics/Bajgrowicz_Scaillet.pdf)). The best rules from 1897–1986 showed no superior performance afterwards ([Sullivan, Timmermann & White](https://econpapers.repec.org/RePEc:bla:jfinan:v:54:y:1999:i:5:p:1647-1691)).

**What evidence does exist.** The only volatility conditioning with support works at *daily* scale: NR4/NR7 compression applied to the hours-long noise-area rule. The noise-area band is itself a time-of-day-normalised breakout. That is the defensible form of the idea, and its evidence is in rank 2.

**Costs and verdict.** Taker breakouts at 10 bp need multi-σ follow-through that minute data do not show.

### Mean reversion on minute bars wins often and loses money

**Logic.** Short-horizon reversal in last-trade prices is largely **mechanical bid-ask bounce** ([Heston, Korajczyk & Sadka](https://arxiv.org/pdf/1005.3535.pdf)). Takers pay that bounce back. The genuine liquidity-provision premium is time-varying and largest in volatility spikes ([Nagel](https://nber.org/papers/w17653)), which is the opposite of the "ranging market" filter most retail systems use.

**Rules tested** (with costs):
- **BB(20,2) on 1-hour bars** with RSI/ADX filters, a 4.5 ATR stop and 10 bp round-trip costs averaged **−20.6% across nine perpetuals**. Only BTC was positive (+15 bp per trade on 38 trades) ([WhatDoesntWork](https://whatdoesntwork.com/research/bollinger-rsi-adx-crypto-mean-reversion/)).
- **78 Bollinger/RSI(2)/SMA-distance backtests** averaged −14.4% on 15-minute bars. Fourteen cells won at least 65% of trades yet lost money ([Coinquant](https://www.coinquant.ai/blog/building-a-mean-reversion-strategy-in-cryptocurrency-markets-evidence-from-78-backtests), vendor; fee rates not stated).
- **Default-setting indicator strategies** beat buy-and-hold in 0 of 42 tests, and costs took 51% of gross on 4-hour bars ([Edgoro](https://edgoro.com/blog/default-indicator-settings-crypto-backtest)).

**The only untested variant worth trying** is MES VWAP ±2σ fades between 10:00 and 15:30 ET with a trend-day veto: target VWAP, stop at ±3σ, 45-minute time stop, news blackouts. Its break-even of about 46% is arithmetically fine, but it is **unverified**.

**Failure modes.** Trend days, fat left tails, bounce artefacts in last-trade data, VWAP look-ahead and hindsight regime labels.

### Opening-range breakouts lack an independent futures result

**Logic.** Volatility and information arrive at the open, so the first bar's direction should persist.

**Rules** (QQQ version): take the direction of the 09:30–09:35 candle at 09:35, stop at that candle's opposite extreme, target 10R or the close, and risk 1% per trade ([Zarattini & Aziz](https://static1.squarespace.com/static/5983d931579fb366729580d8/t/643ed6765176b45506e41a01/1681839734183/SSRN-id4416622.pdf); vendor conflict).

**Results and their limits.** The paper reports Sharpe 1.12, a **24% win rate and +0.13R per trade, with zero slippage assumed**. The headline "stocks in play" version (Sharpe 2.81) depends on a cross-sectional relative-volume screen that does not exist for a single index future. Unfiltered, it scored Sharpe 0.48 ([Tradoki](https://blog.tradoki.com/posts/opening-range-breakout-stocks-in-play-research)).

**Independent futures evidence.** An independent **MNQ walk-forward test over 947 days (2021–2025), at $4 round trip, found no ORB variant significant** ([Tradoki summary of arXiv 2605.04004](https://blog.tradoki.com/posts/opening-range-breakout-stocks-in-play-research); the arXiv paper itself was not read). With R set by the first-bar range, costs are 5–15% of R, which consumes 40–100% of a 0.13R expectancy.

**Crypto session opens** have no natural open. The pre-registered Binance test found chance-level counts of significant UTC-hour effects ([pre-registered test](https://github.com/nishimweprince/trading-algos/pull/98)).

### Liquidity-sweep reversals invert what the order data show

**The peer-reviewed evidence.** The only order-level evidence is Osler's FX data, which cover more than $55bn of orders. Stop-loss buys cluster just *above* round numbers and stop-loss sells just *below* them, while take-profits sit *at* the round number. Prices reverse at round numbers slightly more often (**59.3% vs 54.8%**). But after crossing a stop cluster they **accelerate**: USD/DEM moved 0.061% in the following 15 minutes against 0.054% after an arbitrary level ([Osler, NY Fed SR 150](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf)). That excess is 0.7 bp, on 1996–98 data.

**Implication.** Fading *after* stops run fights a continuation that is "statistically significant for hours."

**ICT/SMC claims** have no independent tests. One vendor claims a profit factor of 1.68 without an out-of-sample split or cost model ([Backtrex](https://backtrex.com/en/blog/liquidity-sweep-strategy-backtest-results), marketing). One script author warns that "in strongly trending markets, sweeps frequently continue rather than reverse" ([TradingView](https://www.tradingview.com/script/GoeqO1ev-Sweep-Reverse-Liquidity-Sweep-Reversal-Strategy/)).

**A codable test, if desired:** the bar's high exceeds the prior day's high and it closes back below it; short at the next open, stop above the high, target session VWAP. Treat it as a hypothesis.

### Short-horizon funding tricks pay less than their fees

**Funding-timestamp scalp.** Collecting a single 8-hour payment earns about 1 bp at baseline. Four retail fills cost more than that, so it is **not viable** without new evidence.

**Cross-venue funding differential.** Shorting the perpetual on the high-funding venue and going long on the low-funding venue avoids the spot leg. It carries double venue risk and mark divergence, and **no net-of-cost evidence** was found. Cross-venue spreads peak about 2 hours after settlement ([MDPI IJFS 2026](https://www.mdpi.com/2227-7072/14/5/103), snippet only, unverified).

**Better use.** Funding works as a slow regime filter, not as a trigger.

### Pairs and short-horizon stat arb are latency and cost races

**Equities.** Daily distance pairs earned up to 11% a year in 1962–2002 ([Gatev et al. via Alpha Architect](https://alphaarchitect.com/pairs-trading-kicks-butt/)) and were "largely unprofitable after 2002" ([Do & Faff 2012](https://strathprints.strath.ac.uk/41722/)). Intraday pairs on 60-minute FTSE bars lost more than half their profit to 0.15% one-way costs, and a **one-bar execution delay turned them negative** ([Bowen et al. via CXO](https://www.cxoadvisory.com/technical-trading/success-factors-for-high-frequency-pairs-trading/)).

**Crypto.** 5-minute distance and cointegration pairs on Binance "underperform classical benchmarks" and are "quite sensitive" to costs and execution windows. A reported 11.61% a month is implausible live ([Fil & Kristoufek](https://doaj.org/article/8fbfa5ffeaae44a5a4c635f23f5ca05c)). CME futures lead Binance spot by about **55 ms** ([arXiv 2506.08718](https://arxiv.org/abs/2506.08718v1)), which is HFT territory.

**Codable rules** if tested:
- rolling-OLS or Kalman hedge ratio;
- z-score with a lookback of 3–5 half-lives;
- Engle–Granger p < 0.05;
- half-life of 2–48 hours;
- entry at |z| ≥ 2, exit at 0, stop at |z| ≥ 4, time stop at 2–3 half-lives;
- trade only if the expected reversion exceeds 3× the cost of four fills.

### Meta-labeling is a filter on an edge, never the edge

**Mechanism.** A rule picks the side, and a calibrated classifier decides whether to trade and how much ([AFML ch. 3 and 10](https://toc.uni.li/FLMF049641.pdf)). The size map is m = 2Φ((p − ½)/√(p(1 − p))) − 1, discretised.

**Evidence.** The only quantified out-of-sample result is from authors affiliated with the tool's vendor: precision rose **0.17 → 0.20** for mean reversion and **0.48 → 0.54** for trend following on E-mini data ([Singh & Joubert](https://hudsonthames.org/wp-content/uploads/2022/04/Does-Meta-Labeling-Add-to-Signal-Efficacy.pdf)). Later JFDS papers on calibration, sizing and ensembles give no public effect sizes ([hudson-and-thames/meta-labeling](https://github.com/hudson-and-thames/meta-labeling)). An independent QuantConnect grid found **average Sharpe lower with the meta-model**. The author's verdict is that it is useful mainly for sizing rule-based strategies with orthogonal features ([QuantConnect forum](https://www.quantconnect.com/forum/discussion/14706/why-meta-labeling-is-not-a-silver-bullet/)).

**Cost math.** With fees dominating at minute horizons, a +3 to +6 point precision lift cannot turn a −8 bp per trade scalp positive. Applied to rank 2, the same lift is material.

**Requirement.** The meta-model must beat a **random filter at the same trade rate** in most walk-forward folds.

## Implementing the carry bot in NautilusTrader 1.231.0

As of November 2026, the stable line is `nautilus_trader==1.231.0` (Cython; published 2026-08-02; branch `develop_v1`). The v2 Rust/PyO3 line is a pre-release (2.0.0rc9, 2026-11-10) installed with `--pre` ([PyPI](https://pypi.org/project/nautilus_trader/)). Both import as `nautilus_trader`, so use separate virtual environments. v1 receives only critical backports for about three months after the v2 cutover ([MIGRATION_V2.md](https://github.com/nautechsystems/nautilus_trader/blob/develop/MIGRATION_V2.md)).

### Names verified against v1 source

The names below were verified against the v1 source (not executed):
- [`StrategyConfig`](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/trading/config.py);
- the Strategy hooks `on_start`/`on_stop`/`on_order_filled`/`on_order_rejected`/`on_position_closed`;
- `submit_order(order, position_id=None, client_id=None, params=None)`, `modify_order`, `cancel_order`, `cancel_all_orders`, `close_position`, `close_all_positions` and `market_exit()` ([strategy.pyx](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/trading/strategy.pyx));
- `order_factory.limit(..., price=..., post_only=..., time_in_force=...)` and `order_factory.bracket(...)` ([factories.pyx](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/common/factories.pyx));
- `clock.set_timer(name, interval, start_time=None, stop_time=None, callback=None, ...)` and `clock.set_time_alert` ([component.pyx](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/common/component.pyx));
- `portfolio.net_position`, `is_flat`, `unrealized_pnl` and `account` ([portfolio.pyx](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/portfolio/portfolio.pyx));
- `cache.instrument`, `cache.orders_inflight`, `subscribe_quote_ticks`, `instrument.make_qty`/`make_price`;
- `BinanceAccountType.SPOT`/`USDT_FUTURES`, the Binance data and exec client configs and factories, and `BinanceFuturesMarkPriceUpdate` ([Binance adapter](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/adapters/binance/__init__.py));
- `RiskEngineConfig(max_order_submit_rate, max_order_modify_rate, max_notional_per_order)`, which has **no built-in daily-loss limit** ([risk/config.py](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/risk/config.py)).

### Names that remain unverified

The following were **not verified** and are tagged `[U]` in the code:
- `order_factory.market` and the `reduce_only` keyword on `limit`;
- the `modify_order` keyword names;
- the `ClientId` import path;
- `subscribe_data`/`DataType`, `on_data` and the `funding_rate` field of the mark-price update;
- `cache.positions_open`, `position.avg_px_open` and `instrument.size_increment`;
- order properties such as `is_open`/`is_closed`;
- `clock.timestamp_ns`;
- running a SPOT client and a USDT_FUTURES client in one node under separate keys;
- whether a spot CASH account reports positions through `net_position`;
- `cache.orders_open`, `OrderList.first`, `clock.cancel_timer` and `Account.balance_total`.

Check all of these against the 1.231.0 docs before running anything.

### Pseudocode

```text
STATE in {FLAT, ENTERING, HEDGED, EXITING, HALTED}

every hour at HH:05 UTC:
    f      <- latest predicted funding rate per interval (mark-price stream or REST)
    N      <- funding interval hours for the symbol (from exchange; never hard-code)
    apr    <- f * (24/N) * 365 ; push into window W (last 168 hourly samples)
    apr7   <- mean(W)
    cpn    <- 1 + 1/L                                   # capital per unit notional
    drag   <- fee_rt * 365 / expected_hold_days         # fee_rt = 0.0024 at VIP0 maker
    net    <- (apr7 - drag) / cpn                       # expected net APR on capital
    rho    <- 1095 * (ln(perp_mid) - ln(spot_mid))      # He et al. deviation (r - r' omitted)
    bound  <- 1095 * fee_rt                             # ~2.63 (263% p.a.) at VIP0 maker
    if STATE == FLAT and data_fresh and not near_settlement(+-15 min):
        if net >= tbill + premium or rho >= bound: OPEN()
    if STATE == HEDGED and (apr7 < 0 or rho <= -1095*0.005): CLOSE("negative funding / inversion")

every day at 00:00 UTC:
    if STATE == HEDGED:
        below_days <- below_days + 1 if apr7 < tbill * cpn else 0     # lower exit hurdle = hysteresis
        if below_days >= 3: CLOSE("carry below T-bills")

every 10 s (ENTERING or EXITING):
    reprice each working post-only order to the touch (bid for buys, ask for sells)
    if elapsed > 120 s: cancel working orders; take the residual with a taker order
                        (ENTERING: match the larger filled leg; EXITING: flatten both legs)
    promote ENTERING->HEDGED when |spot + perp| <= 2% of spot; EXITING->FLAT when both ~0

every 60 s (HEDGED):
    if a leg vanished (ADL, liquidation, manual): CLOSE(urgent) -- never hold a naked leg
    if |spot + perp| / spot > 2%: rebalance the perp leg
    if liquidation distance < 30%: scale both legs down by 1/3 and alert
    if quotes stale > 30 s: block new orders and alert

OPEN():  qty <- floor(min(capital*0.6, max_notional) / spot_mid, common step size)
         post-only LIMIT BUY spot @ bid (spot client); post-only LIMIT SELL perp @ ask (futures client)
CLOSE(): cancel all; post-only LIMIT SELL spot @ ask; post-only LIMIT BUY perp @ bid reduce-only
         (urgent: go straight to taker)
HALT():  on >= 3 rejects or a manual signal: cancel all, restore hedge if broken, block entries
```

### Python skeleton (untested reference code)

```python
"""
funding_carry.py - delta-neutral funding carry: long spot / short USDT-M perpetual.

Reference skeleton for nautilus_trader==1.231.0 (stable v1, Cython). NOT EXECUTED.
[U] = name not verified against the 1.231.0 source; check https://nautilustrader.io/docs/latest/.
v2 renames are listed in the report (e.g. subscribe_quote_ticks -> subscribe_quotes).
"""
from __future__ import annotations

import math
from collections import deque
from datetime import datetime, timedelta
from decimal import Decimal

from nautilus_trader.config import PositiveFloat, PositiveInt, StrategyConfig
from nautilus_trader.model.data import QuoteTick
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.events import OrderFilled
from nautilus_trader.model.identifiers import ClientId, InstrumentId      # ClientId path [U]
from nautilus_trader.trading.strategy import Strategy

FLAT, ENTERING, HEDGED, EXITING, HALTED = "FLAT", "ENTERING", "HEDGED", "EXITING", "HALTED"
NS = 1_000_000_000


class CarryConfig(StrategyConfig, frozen=True):
    spot_id: InstrumentId                    # InstrumentId.from_str("BTCUSDT.BINANCE")
    perp_id: InstrumentId                    # InstrumentId.from_str("BTCUSDT-PERP.BINANCE")
    spot_client: str = "BINANCE_SPOT"        # [U] must equal the TradingNodeConfig client key
    perp_client: str = "BINANCE_FUTURES"     # [U]
    capital_usdt: PositiveFloat = 10_000.0
    deploy_frac: PositiveFloat = 0.60        # notional per leg / capital
    max_notional_usdt: PositiveFloat = 6_000.0
    perp_leverage: PositiveFloat = 2.0       # risk policy, NOT an optimized parameter
    maint_margin_rate: PositiveFloat = 0.004 # check the venue's tier table
    funding_interval_h: PositiveInt = 8      # read per symbol from the venue in production
    lookback_h: PositiveInt = 168            # 7 days of hourly samples
    fee_rt_bps: PositiveFloat = 24.0         # VIP0 maker: spot 10+10, perp 2+2
    tbill_apr: PositiveFloat = 0.042         # input: current 3-month T-bill yield
    premium_apr: PositiveFloat = 0.01        # required excess over T-bills, on capital
    expected_hold_days: PositiveFloat = 45.0
    exit_days_below: PositiveInt = 3
    hedge_tol: PositiveFloat = 0.02
    reprice_secs: PositiveInt = 10
    leg_timeout_secs: PositiveInt = 120
    stale_quote_secs: PositiveInt = 30
    inversion_bps: PositiveFloat = 50.0
    derisk_liq_distance: PositiveFloat = 0.30
    settlement_blackout_min: PositiveInt = 15
    max_rejects: PositiveInt = 3
    flatten_on_stop: bool = False            # a hedged book should not be dumped on restart


def _next_boundary(now: datetime, hours: int, minute: int = 0) -> datetime:
    base = now.replace(minute=0, second=0, microsecond=0)
    nxt = base + timedelta(hours=1)
    while nxt.hour % hours != 0:
        nxt += timedelta(hours=1)
    return nxt + timedelta(minutes=minute)


class FundingCarry(Strategy):
    def __init__(self, config: CarryConfig) -> None:
        super().__init__(config)
        self.state = FLAT
        self.apr_window: deque[float] = deque(maxlen=config.lookback_h)
        self.below_days = 0
        self.funding_rate: float | None = None      # per funding interval, decimal (0.0001 = 1 bp)
        self.quotes: dict[InstrumentId, QuoteTick] = {}
        self.working: dict[InstrumentId, object] = {}
        self.leg_started_ns = 0
        self.rejects = 0

    # ------------------------------------------------------------------ lifecycle
    def on_start(self) -> None:
        self.spot = self.cache.instrument(self.config.spot_id)
        self.perp = self.cache.instrument(self.config.perp_id)
        if self.spot is None or self.perp is None:
            self.log.error("Instruments not in cache")
            self.stop()
            return
        self.subscribe_quote_ticks(self.config.spot_id)        # v2: subscribe_quotes
        self.subscribe_quote_ticks(self.config.perp_id)
        self._subscribe_funding()
        now = self.clock.utc_now()
        self.clock.set_timer("hourly", timedelta(hours=1),
                             start_time=_next_boundary(now, 1, minute=5), callback=self._on_hour)
        self.clock.set_timer("daily", timedelta(days=1),
                             start_time=_next_boundary(now, 24), callback=self._on_day)
        self.clock.set_timer("exec", timedelta(seconds=self.config.reprice_secs),
                             callback=self._on_exec_tick)
        self.clock.set_timer("risk", timedelta(seconds=60), callback=self._on_risk_tick)

    def on_stop(self) -> None:
        self.cancel_all_orders(self.config.spot_id)
        self.cancel_all_orders(self.config.perp_id)
        if self.config.flatten_on_stop:
            self._close_hedge("strategy stop", urgent=True)

    # ------------------------------------------------------------------ data
    def _subscribe_funding(self) -> None:
        # [U] Binance mark-price updates carry the predicted funding rate.
        from nautilus_trader.adapters.binance import BinanceFuturesMarkPriceUpdate   # verified export
        from nautilus_trader.model.data import DataType                              # [U] path
        self.subscribe_data(                                                          # [U]
            DataType(BinanceFuturesMarkPriceUpdate, metadata={"instrument_id": self.config.perp_id}),
            client_id=ClientId(self.config.perp_client),
        )

    def on_data(self, data) -> None:                       # [U] custom-data handler
        rate = getattr(data, "funding_rate", None)         # [U] field name
        if rate is not None:
            self.funding_rate = float(rate)

    def on_quote_tick(self, tick: QuoteTick) -> None:      # v2: on_quote
        self.quotes[tick.instrument_id] = tick

    def _mid(self, iid: InstrumentId) -> float | None:
        q = self.quotes.get(iid)
        return None if q is None else 0.5 * (q.bid_price.as_double() + q.ask_price.as_double())

    def _fresh(self) -> bool:
        now = self.clock.timestamp_ns()                    # [U]
        lim = self.config.stale_quote_secs * NS
        return all(i in self.quotes and now - self.quotes[i].ts_event <= lim
                   for i in (self.config.spot_id, self.config.perp_id))

    def _net(self, iid: InstrumentId) -> Decimal:
        # Verified name. [U] for a spot CASH account confirm it tracks a position;
        # otherwise use the base-currency balance as the source of truth.
        return Decimal(str(self.portfolio.net_position(iid)))

    # ------------------------------------------------------------------ signals
    def _cpn(self) -> float:
        return 1.0 + 1.0 / self.config.perp_leverage

    def _rho_bound(self) -> tuple[float | None, float]:
        s, f = self._mid(self.config.spot_id), self._mid(self.config.perp_id)
        bound = 1095.0 * self.config.fee_rt_bps / 1e4
        if not s or not f:
            return None, bound
        return 1095.0 * (math.log(f) - math.log(s)), bound

    def _apr7(self) -> float | None:
        return sum(self.apr_window) / len(self.apr_window) if self.apr_window else None

    def _near_settlement(self) -> bool:
        now, h = self.clock.utc_now(), self.config.funding_interval_h
        into = (now.hour % h) * 60 + now.minute
        return min(into, h * 60 - into) < self.config.settlement_blackout_min

    def _on_hour(self, _event) -> None:
        if self.funding_rate is None or self.state == HALTED:
            return
        self.apr_window.append(self.funding_rate * (24.0 / self.config.funding_interval_h) * 365.0)
        if len(self.apr_window) < self.apr_window.maxlen:
            return                                          # warm-up: need a full 7-day window
        apr7 = self._apr7()
        drag = self.config.fee_rt_bps / 1e4 * 365.0 / self.config.expected_hold_days
        net_cap = (apr7 - drag) / self._cpn()
        rho, bound = self._rho_bound()
        self.log.info(f"apr7={apr7:.4f} net_on_capital={net_cap:.4f} rho={rho} bound={bound:.2f}")
        if self.state == FLAT and self._fresh() and not self._near_settlement():
            if net_cap >= self.config.tbill_apr + self.config.premium_apr or (rho is not None and rho >= bound):
                self._open_hedge()
        elif self.state == HEDGED:
            inverted = rho is not None and rho <= -1095.0 * self.config.inversion_bps / 1e4
            if apr7 < 0 or inverted:
                self._close_hedge("negative funding or basis inversion")

    def _on_day(self, _event) -> None:
        apr7 = self._apr7()
        if self.state != HEDGED or apr7 is None:
            return
        exit_hurdle = self.config.tbill_apr * self._cpn()   # lower than entry hurdle: hysteresis
        self.below_days = self.below_days + 1 if apr7 < exit_hurdle else 0
        if self.below_days >= self.config.exit_days_below:
            self._close_hedge(f"carry below T-bills for {self.below_days} days")

    # ------------------------------------------------------------------ execution
    def _step(self) -> Decimal:
        # [U] attribute name; assumes one increment is a multiple of the other (else use their LCM)
        return max(self.spot.size_increment.as_decimal(), self.perp.size_increment.as_decimal())

    def _target_qty(self) -> Decimal:
        notional = min(self.config.capital_usdt * self.config.deploy_frac, self.config.max_notional_usdt)
        raw = Decimal(str(notional / self._mid(self.config.spot_id)))
        return (raw // self._step()) * self._step()

    def _passive(self, inst, side: OrderSide, qty: Decimal, client: str, reduce_only: bool) -> None:
        q = self.quotes[inst.id]
        px = q.bid_price if side == OrderSide.BUY else q.ask_price      # join the touch, never cross
        order = self.order_factory.limit(
            instrument_id=inst.id, order_side=side, quantity=inst.make_qty(qty),
            price=px, post_only=True, time_in_force=TimeInForce.GTC,
            reduce_only=reduce_only,                                    # [U] kw; spot must be False
        )
        self.working[inst.id] = order
        self.submit_order(order, client_id=ClientId(client))           # client_id param verified

    def _take(self, inst, side: OrderSide, qty: Decimal, client: str, reduce_only: bool) -> None:
        if qty <= 0:
            return
        order = self.order_factory.market(                              # [U]
            instrument_id=inst.id, order_side=side, quantity=inst.make_qty(qty),
            reduce_only=reduce_only,
        )
        self.submit_order(order, client_id=ClientId(client))

    def _open_hedge(self) -> None:
        qty = self._target_qty()
        if qty <= 0:
            return
        self.state, self.leg_started_ns = ENTERING, self.clock.timestamp_ns()
        self._passive(self.spot, OrderSide.BUY, qty, self.config.spot_client, reduce_only=False)
        self._passive(self.perp, OrderSide.SELL, qty, self.config.perp_client, reduce_only=False)
        self.log.info(f"OPEN carry qty={qty}")

    def _close_hedge(self, reason: str, urgent: bool = False) -> None:
        if self.state in (EXITING, FLAT):
            return
        self.log.warning(f"CLOSE carry: {reason}")
        self.cancel_all_orders(self.config.spot_id)
        self.cancel_all_orders(self.config.perp_id)
        self.working.clear()
        self.state = EXITING
        self.leg_started_ns = 0 if urgent else self.clock.timestamp_ns()   # 0 => taker on next tick
        if urgent:
            return
        spot_q, perp_q = self._net(self.config.spot_id), self._net(self.config.perp_id)
        if spot_q > 0:
            self._passive(self.spot, OrderSide.SELL, spot_q, self.config.spot_client, reduce_only=False)
        if perp_q < 0:
            self._passive(self.perp, OrderSide.BUY, -perp_q, self.config.perp_client, reduce_only=True)

    def _on_exec_tick(self, _event) -> None:
        if self.state not in (ENTERING, EXITING):
            return
        if not self._fresh() and self.leg_started_ns != 0:   # urgent exits (leg_started_ns == 0) proceed on stale data
            return
        for iid, order in list(self.working.items()):
            if order.is_closed:                                         # [U]
                self.working.pop(iid)
                continue
            q = self.quotes[iid]
            touch = q.bid_price if order.side == OrderSide.BUY else q.ask_price
            if order.price != touch:
                self.modify_order(order, price=touch)                   # verified name; kw [U]
        if self.clock.timestamp_ns() - self.leg_started_ns > self.config.leg_timeout_secs * NS:
            self._complete_legs()
        self._promote_state()

    def _complete_legs(self) -> None:
        for order in list(self.working.values()):
            if order.is_open:                                           # [U]
                self.cancel_order(order)
        self.working.clear()
        spot_q, perp_q = self._net(self.config.spot_id), self._net(self.config.perp_id)
        if self.state == ENTERING:                                      # accept partial size, but hedged
            gap = spot_q + perp_q                                       # >0 needs more short perp
            if gap > 0:
                self._take(self.perp, OrderSide.SELL, gap, self.config.perp_client, reduce_only=False)
            elif gap < 0:
                self._take(self.spot, OrderSide.BUY, -gap, self.config.spot_client, reduce_only=False)
        elif self.state == EXITING:
            self._take(self.spot, OrderSide.SELL, max(spot_q, Decimal(0)), self.config.spot_client, False)
            self._take(self.perp, OrderSide.BUY, max(-perp_q, Decimal(0)), self.config.perp_client, True)
        self.leg_started_ns = self.clock.timestamp_ns()

    def _promote_state(self) -> None:
        if self.working or self.cache.orders_inflight(strategy_id=self.id):   # verified name
            return
        spot_q, perp_q = self._net(self.config.spot_id), self._net(self.config.perp_id)
        tol = Decimal(str(self.config.hedge_tol))
        if self.state == ENTERING and spot_q > 0 and abs(spot_q + perp_q) <= spot_q * tol:
            self.state, self.below_days = HEDGED, 0
            self.log.info(f"HEDGED spot={spot_q} perp={perp_q}")
        elif self.state == EXITING and spot_q < self._step() and perp_q == 0:
            self.state = FLAT
            self.log.info("FLAT")

    # ------------------------------------------------------------------ risk
    def _liq_distance(self) -> float:
        pos = self.cache.positions_open(instrument_id=self.config.perp_id)      # [U]
        mark = self._mid(self.config.perp_id)
        if not pos or not mark:
            return 1.0
        entry = float(pos[0].avg_px_open)                                        # [U]
        liq = entry * (1 + 1 / self.config.perp_leverage - self.config.maint_margin_rate)  # isolated short, approx.
        return liq / mark - 1.0

    def _on_risk_tick(self, _event) -> None:
        if not self._fresh():
            self.log.warning("Stale quotes: entries blocked")
        if self.state != HEDGED or self.cache.orders_inflight(strategy_id=self.id):
            return                                          # avoid double-submitting while orders are in flight
        spot_q, perp_q = self._net(self.config.spot_id), self._net(self.config.perp_id)
        if spot_q <= 0 or perp_q >= 0:
            self._close_hedge("one leg lost (ADL/liquidation/manual)", urgent=True)
            return
        gap = spot_q + perp_q
        if abs(gap) / spot_q > Decimal(str(self.config.hedge_tol)):
            if gap > 0:
                self._take(self.perp, OrderSide.SELL, gap, self.config.perp_client, reduce_only=False)
            else:
                self._take(self.perp, OrderSide.BUY, -gap, self.config.perp_client, reduce_only=True)
        if self._liq_distance() < self.config.derisk_liq_distance:
            cut = (spot_q / 3 // self._step()) * self._step()
            self.log.warning(f"Liquidation buffer thin: cutting both legs by {cut}")
            self._take(self.spot, OrderSide.SELL, cut, self.config.spot_client, reduce_only=False)
            self._take(self.perp, OrderSide.BUY, cut, self.config.perp_client, reduce_only=True)

    # ------------------------------------------------------------------ events
    def on_order_filled(self, event: OrderFilled) -> None:
        self.log.info(f"FILL {event.instrument_id} {event.order_side} {event.last_qty} @ {event.last_px}")  # fields [U]

    def on_order_rejected(self, event) -> None:
        self.rejects += 1
        self.log.error(f"REJECT #{self.rejects}: {event}")
        if self.rejects >= self.config.max_rejects:
            self._halt("too many rejects")

    def _halt(self, reason: str) -> None:
        self.log.error(f"HALT: {reason}")
        self.cancel_all_orders(self.config.spot_id)
        self.cancel_all_orders(self.config.perp_id)
        spot_q, perp_q = self._net(self.config.spot_id), self._net(self.config.perp_id)
        if abs(spot_q + perp_q) > 0:                    # never leave price exposure while halted
            self._take(self.perp, OrderSide.SELL if spot_q + perp_q > 0 else OrderSide.BUY,
                       abs(spot_q + perp_q), self.config.perp_client, reduce_only=spot_q + perp_q < 0)
        self.state = HALTED                             # manual reset required
```

Live wiring follows the v1 `TradingNodeConfig(data_clients=..., exec_clients=..., risk_engine=LiveRiskEngineConfig(...))` pattern ([live/config.py](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/live/config.py)). Keys come from environment variables, never from code. Use `environment=BinanceEnvironment.TESTNET` first.

```python
from nautilus_trader.adapters.binance import (
    BinanceAccountType, BinanceDataClientConfig, BinanceEnvironment, BinanceExecClientConfig,
    BinanceLiveDataClientFactory, BinanceLiveExecClientFactory)
from nautilus_trader.config import LiveRiskEngineConfig, TradingNodeConfig   # import path [U]
from nautilus_trader.live.node import TradingNode                            # v2: nautilus_trader.live.LiveNode
from nautilus_trader.model.identifiers import InstrumentId
from funding_carry import CarryConfig, FundingCarry

clients = {"BINANCE_SPOT": BinanceAccountType.SPOT, "BINANCE_FUTURES": BinanceAccountType.USDT_FUTURES}
node = TradingNode(config=TradingNodeConfig(
    trader_id="CARRY-001",
    data_clients={k: BinanceDataClientConfig(account_type=t, environment=BinanceEnvironment.TESTNET)
                  for k, t in clients.items()},
    exec_clients={k: BinanceExecClientConfig(account_type=t, environment=BinanceEnvironment.TESTNET)
                  for k, t in clients.items()},
    risk_engine=LiveRiskEngineConfig(
        max_order_submit_rate="5/00:00:01", max_order_modify_rate="5/00:00:01",
        max_notional_per_order={"BTCUSDT.BINANCE": 7_000, "BTCUSDT-PERP.BINANCE": 7_000}),
))
node.trader.add_strategy(FundingCarry(CarryConfig(              # [U] add_strategy path
    spot_id=InstrumentId.from_str("BTCUSDT.BINANCE"),
    perp_id=InstrumentId.from_str("BTCUSDT-PERP.BINANCE"))))
for key in clients:                                              # [U] multi-key factory registration
    node.add_data_client_factory(key, BinanceLiveDataClientFactory)
    node.add_exec_client_factory(key, BinanceLiveExecClientFactory)
node.build()
node.run()
```

The kill switch lives in the strategy, because v1 `RiskEngineConfig` has no daily-loss limit. If an engine-level brake is wanted, set `TradingState.REDUCING` rather than `HALTED`. In v1, HALTED denies every order, exits included ([risk/engine.pyx](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/risk/engine.pyx)). A carry book must always be able to re-hedge.

### v2.0 renames to apply when migrating

| v1.231.0 | v2.0 (rc) |
|---|---|
| `on_quote_tick`, `on_trade_tick`, `on_order_book_deltas` | `on_quote`, `on_trade`, `on_book_deltas` |
| `subscribe_quote_ticks`, `subscribe_trade_ticks`, `subscribe_order_book_deltas`, `request_quote_ticks` | `subscribe_quotes`, `subscribe_trades`, `subscribe_book_deltas`, `request_quotes` |
| `cache.quote_tick` | `cache.quote` |
| `nautilus_trader.backtest.engine.BacktestEngine`; `nautilus_trader.live.node.TradingNode`; `nautilus_trader.model.enums.OrderSide` | `nautilus_trader.backtest.BacktestEngine`; `nautilus_trader.live.LiveNode`; `nautilus_trader.model.OrderSide` |
| `Importable*ModelConfig` wrappers | construct `ProbabilisticFillModel`, `FixedFeeModel`, `StaticLatencyModel` directly |
| omitted backtest `default_leverage` = 1× | defaults to **10×** for margin accounts; set `Decimal(1)` explicitly |
| instrument `maker_fee`/`taker_fee` | removed in rc6; set rates on the venue `fee_model` |
| `TradingState` HALTED/REDUCING semantics | rc5 renumbered values; REDUCING allows only reduce-only orders; rc8: HALTED denies stops |
| `add_venue()` positional models | rc8 changed the argument order; pass models by keyword |

The renames come from [MIGRATION_V2.md](https://github.com/nautechsystems/nautilus_trader/blob/develop/MIGRATION_V2.md). The rc-by-rc changes (rc7 batches book deltas in `BacktestNode`; rc9 Binance REST blocks on HTTP 418 and Bybit `modify_order` takes `trigger_price`) come from the [release notes](https://github.com/nautechsystems/nautilus_trader/releases).

## A backtest that can kill the strategy before it costs money

### Data and fills

Research runs in two stages. **Stage 1** is an hourly event-driven research backtest in pandas or Polars covering January 2020 to the present on BTC and ETH, using:
- Binance (and Bybit) funding at every settlement, with the real per-symbol interval;
- hourly spot and perpetual mid prices plus bid/ask from Tardis or exchange dumps;
- mark and index prices;
- a T-bill series.

Fills are charged at **VIP0: spot 10 bp maker / 10 bp taker, perpetual 2 bp maker / 5 bp taker**, plus half the spread plus one tick. On 30% of entries and exits, assume the lagging leg goes taker. Funding is credited exactly at settlement on perpetual notional. The test must include LUNA (May 2022), FTX (November 2022), August 2024 and 10 October 2025. In those windows, model 3–10× slippage and a forced leg loss (auto-deleveraging of the short at the crash low, spot left naked for 10 minutes).

**Stage 2** is a NautilusTrader `BacktestEngine` replay of quote ticks, used to test the leg-in and re-hedge state machine. Use the verified `add_venue` arguments ([backtest/engine.pyx](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/backtest/engine.pyx)):
- `fill_model=FillModel(prob_fill_on_limit=0.3, prob_slippage=0.5, random_seed=42)`;
- `fee_model=MakerTakerFeeModel()`, with the instrument's `maker_fee`/`taker_fee` set to the VIP0 rates, since v1 reads fees from the instrument ([fee.pyx](https://github.com/nautechsystems/nautilus_trader/blob/develop_v1/nautilus_trader/backtest/models/fee.pyx));
- `latency_model=LatencyModel(base_latency_nanos=50_000_000)`;
- `bar_adaptive_high_low_ordering=True`.

Beware that `LatencyModelConfig` defaults to **1 second** while the Cython class defaults to 1 ms. Whether the v1 backtest accrues perpetual funding automatically is unverified, so credit funding from the Stage 1 ledger. A single backtest venue has one account type. Model spot and perpetual as two venues, or test only the perpetual leg in Nautilus.

### Walk-forward and the two-track gates

Because carry trades a few times a year, validation centres on daily P&L and episodes, not on trade count alone. Use an anchored walk-forward: choose parameters on 2020–2022, then roll yearly through 2023, 2024, 2025 and 2026 year-to-date, giving at least 24 out-of-sample months. Keep the grid small and log every configuration tried. The Deflated Sharpe Ratio needs the true trial count N ([Bailey & López de Prado](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf)):

DSR = Z[(SR − SR₀)·√(T−1) / √(1 − γ₃SR + ((γ₄ − 1)/4)SR²)]

Here SR₀ is the expected maximum Sharpe of N zero-skill trials, T the sample length, γ₃ the skewness and γ₄ the kurtosis. PBO comes from CSCV with S = 16 blocks (12,870 combinations), and models with PBO above 0.05 are customarily rejected ([Bailey et al.](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)). The directional strategies in ranks 2 and 3 use the notes' minute-horizon gates. Those gates rest on t-statistic arithmetic: at a per-trade μ/σ of 0.05–0.10, rejecting zero expectancy needs about 270–1,080 trades.

| Gate | Carry (rank 1) | Directional (ranks 2–3) |
|---|---|---|
| Out-of-sample span / count | ≥24 OOS months; ≥20 entry-to-exit episodes; ≥500 daily P&L observations | ≥500 OOS trades (floor 300); rank 3 instead needs an event study significant vs placebo |
| Net return | Excess over T-bills > 0 in ≥2 of 3 OOS years; ≥ T-bill + 1.5% on capital overall | — |
| Profit factor | Episode PF ≥ 1.5 | ≥1.25 with taker fees + 1 tick; ≥1.10 at 2× costs |
| Sharpe / DSR | Daily net excess Sharpe ≥ 1.0 (haircut from He et al.'s 1.80); DSR ≥ 0.95 | Net Sharpe ≥ 1.5; DSR ≥ 0.95 |
| PBO | ≤ 0.05 over the full grid | ≤ 0.05 strict (≤ 0.20 relaxed) |
| Max drawdown | ≤ 5% realised (He et al. BTC −4.4%); Monte Carlo 95th percentile ≤ 8%; **no liquidation in any stress window** | ≤10%; Monte Carlo 95th percentile ≤15% |
| Ablation | Beats always-on carry and T-bills | Meta filter beats a random filter at equal trade rate in ≥70% of folds |
| Paper / small live | ≥4 weeks testnet for leg mechanics, then ≥3 months live at 10–25% size; realised funding within 10% of computed; fees ≤1.2× modelled; hedge mismatch never >5% | ≥4 weeks and ≥100 trades, or MinTRL; median slippage ≤1 tick and ≤1.5× modelled |
| Kill / rollback | Leg lost, buffer breach, ≥3 rejects, venue incident | Daily loss ≥2%; drawdown >1.5× the Monte Carlo 95th percentile; rolling 100-trade PF <1.0; probability-drift PSI >0.2 |

Only the DSR and PBO thresholds come from the academic literature. The profit-factor, drawdown, paper-trading and slippage thresholds are practitioner rules of thumb synthesised in the notes ([QuantConnect forum](https://www.quantconnect.com/forum/discussion/14706/why-meta-labeling-is-not-a-silver-bullet/) and blog sources rated low quality). Treat them as house rules, not science.

### Parameters to optimise and how not to curve-fit

The carry grid has five dimensions:
- the entry premium over T-bills ({0, 1, 2}%);
- the funding lookback ({72, 168, 336} hours);
- consecutive days below the exit hurdle ({1, 3, 5});
- entry mode (persistent funding only, or persistent plus He et al.'s deviation trigger);
- expected hold for the fee-drag term ({30, 45, 60} days).

That is 162 configurations, so N = 162 in the DSR. Leverage (2×), the liquidation de-risk threshold and venue caps are **risk policy and are never optimised**.

Five disciplines keep the result honest:
1. **Anchor every parameter to arithmetic** (fees, T-bills, settlement times) rather than fitting it.
2. **Use one parameter set for BTC and ETH**, then test it unchanged on assets that were never tuned (SOL, BNB, DOGE). He et al. found altcoin Sharpes of 2.7–4.8 with heavier tails.
3. **Require a plateau.** Neighbouring cells must perform within 20–30% of the chosen cell.
4. **Freeze everything before the last out-of-sample year** and block-bootstrap by month (at least 10,000 resamples) for drawdown distributions.
5. **Haircut expectations for decay.** The convergence component shrank 11% a year, so a 2021-calibrated configuration should be expected to underperform.

For the rank-2 directional sleeve, optimise only VM ({1.0, 1.25, 1.5}), the VIX gate and the meta-label threshold p\*. Do not retune the paper's 14-day lookback or its 30-minute decision grid; the replication found reselection hurt ([Brusco](https://github.com/giovannibrusco/zarattini-2024-momentum-spy)).

## Conclusion

The research inverts the blueprint's premise. The blueprint treated cost as an engineering problem, to be solved with a Tokyo VPS, post-only orders and a better filter. The evidence says cost is the *strategy-selection* problem. On BTC/ETH perpetuals, the gap between a regular-tier account and the best liquidity-provider tier is 2.5 bp per fill. That gap is larger than every net edge per fill documented in the sources, so no amount of model quality closes it at a 1–5 minute horizon. What survives at retail fees are premiums paid by *other people's constraints*: leveraged longs funding shorts, forced sellers overshooting, dealers hedging gamma into the close. These premiums pay over hours to weeks, and none of them requires winning a latency race.

The practical consequence is a different bot with the same skeleton:
- **Core sleeve:** a funding-carry engine on NautilusTrader, expected to earn T-bills plus a few points and judged on whether it survives the 2022 and October 2025 stress windows with its hedge intact.
- **Optional directional sleeve:** noise-area momentum on futures, kept only if its meta-label filter beats a random filter out of sample.
- **Research project:** a liquidation-cascade event study, which costs nothing but data to run.

If any sleeve fails its gates, the honest fallback is T-bills, and that comparison should be printed on the bot's daily report.

## The next 5 concrete steps to implement and test the chosen strategy

1. **Confirm venue access and your real fee tier, then write down the four-fill round-trip cost.** Check whether your jurisdiction permits Binance or Bybit spot plus perpetuals (US persons: CME basis or the CFTC-approved Deribit/Kalshi routes; EU/UK: likely blocked). Then record your actual spot and perpetual maker/taker rates, including BNB discounts. Recompute the 24 bp default, the entry hurdle and the ±263% deviation bound with your numbers before writing any code.
2. **Build the Stage 1 carry ledger from public data.** Download BTCUSDT and ETHUSDT funding history with the true per-symbol intervals, hourly spot and perpetual prices, mark/index prices and a T-bill series for 2020 to now. Code the hourly rules exactly as in the pseudocode, charge VIP0 fees, credit funding at settlement, and inject the four stress windows with a forced leg-loss scenario. Report net excess return, daily Sharpe, max drawdown, episode profit factor and time in market per year.
3. **Run the 162-configuration walk-forward and compute DSR and PBO honestly.** Train on 2020–22, roll yearly to 2026, log every configuration, and compute DSR with N = 162 and PBO via CSCV (S = 16). Test the chosen configuration unchanged on SOL/BNB/DOGE. Stop here if DSR < 0.95, PBO > 0.05, or the excess over T-bills is not positive in at least two of three out-of-sample years.
4. **Verify every `[U]` NautilusTrader name against 1.231.0, then run the state machine on testnet.** Pin `nautilus_trader==1.231.0` in its own virtual environment. Confirm the dual-client node configuration, the mark-price/funding subscription, `order_factory.market`, the `reduce_only`/`modify_order` keywords and spot position tracking. Then run four weeks on Binance testnet, deliberately cancelling legs, killing the process mid-entry and simulating auto-deleveraging by closing the perpetual manually, to prove the bot never holds a naked leg.
5. **Go live at 10–25% of target size for at least three funding-months with hard monitoring.** Track realised funding against the computed rate (within 10%), realised fees against the model (≤1.2×), hedge mismatch (never above 5%), liquidation distance and ADL indicator, and put net excess over T-bills on a daily report. In parallel, start recording liquidation, open-interest and 1-minute bid/ask data so the cascade-fade event study (rank 3) can begin once three months of your own data exist.
