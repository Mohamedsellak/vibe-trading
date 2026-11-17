# Reality Check: Retail Algorithmic Scalping Bots (2026) — Success Rates, Failure Modes, "Million-Dollar Bot" Math, Scams, Legal/Regulatory and Tax

Research date: 16 November 2026. Jurisdictions covered: US, EU, UK, India, Australia (plus Brazil/Taiwan academic evidence). Rules vary by jurisdiction and change often; everything below should be re-checked against the primary regulator/tax-authority page before being relied on. Sources are mostly regulators, courts, academic papers and trade press; where only secondary/commercial sources were available this is flagged.

---

## Key Question 1: What do regulators, brokers and academics report about retail trader (and specifically bot/prop-firm) profitability?

### Takeaway
Every independent dataset found says the large majority of active retail speculators lose money: 68–82% of CFD accounts at regulated EU/UK brokers (mandatory disclosures, 2026), ~91–93% of Indian F&O traders (SEBI, FY22–FY25), 97% of persistent Brazilian index-futures day traders (Chague et al.), and "less than 1%" of Taiwanese day traders reliably profitable net of fees (Barber/Odean). For prop firms, the only large dataset (FPFX, 300k accounts) shows ~14% pass a challenge and ~7% of all participants ever receive a payout. No rigorous survival statistics for retail bots/EAs on Myfxbook/MQL5/Darwinex/Collective2 could be found; this is a genuine data gap, not evidence that bots do better.

### Cited Findings

**Broker CFD loss disclosures (ESMA/FCA-mandated, 2026 figures)**
- IG UK: "69% of retail investor accounts lose money when trading spread bets and CFDs with this provider" (IG press release, July 2026) — [IG UK](https://www.ig.com/uk/media-centre/press-release-overview/nearly-one-in-four-UK-investors-reduce-exposure-to-domestic-stocks-as-political-uncertainty-reaches-record-high)
- IG International: 71% of retail client accounts lose money trading CFDs — [IG CFD page](https://www.ig.com/uk/cfd); IG Ireland: 72% — [IG IE](https://www.ig.com/ie/media-centre/press-release-overview/ig-calls-for-urgent-clarity-on-investment-account); IG Switzerland: 78%, and 2.15% of accounts had positions closed by margin call in the last 12 months — [IG CH](https://www.ig.com/en-ch/profile/fabien-yip1)
- Pepperstone: "79.6% of retail investor accounts lose money when trading CFDs" (2026 site footer) — [Pepperstone](https://pepperstone.com/en/insights/market-analysis); another Pepperstone page shows 80% — [Pepperstone cTrader page](https://pepperstone.com/en/platforms/tools/ctrader-automate)
- IC Markets (EU): 73.42% of retail CFD accounts lose money (third-party reproduction of the broker's warning) — [BrokerChooser IC Markets](https://brokerchooser.com/broker-reviews/ic-markets-review/cfd-risk-warning)
- BrokerRank 2026 study of 49 EU/FCA-regulated brokers: sample average 71.1% losing; lowest eToro 51%; highest Plus500 82% — [BrokerRank](https://brokerrank.net/research/retail-loss-rates)
- ESMA's original standardized warning text (2018) stated 74–89% of retail CFD accounts lose money — [BrokerChooser IG review](https://brokerchooser.com/broker-reviews/ig-review)
- Caveat: the disclosed percentage is the share of *accounts* losing over a 12-month window at that broker, not a per-trader probability, and does not isolate algorithmic users — [BrokerRank](https://brokerrank.net/research/retail-loss-rates)

**SEBI (India) — equity derivatives (F&O) studies**
- FY25 study (July 2025): ~91% of individual traders in equity derivatives made net losses; aggregate net losses ₹1.05 lakh crore (≈US$12bn), up 41% from ₹74,812 crore in FY24; average loss per trader ₹1.1 lakh (up 27%) — [Moneylife](https://moneylife.in/article/91-percentage-of-retail-traders-lost-money-in-derivatives-losses-in-fo-surged-41-percentage-to-rs105-lakh-crore-in-fy25-sebi-study/77613.html); [Business Standard](https://www.business-standard.com/markets/news/net-losses-of-traders-in-fo-widens-in-fy25-sebi-study-125070701221_1.html)
- Unique F&O traders fell 20% to 6.7 million (Dec 2024–May 2025 vs prior year) after SEBI tightened rules — [Business Standard](https://www.business-standard.com/markets/news/individual-investors-shrink-20-percent-fo-segment-125070800801_1.html)
- Sept 2024 study (FY22–FY24): 93% of >1 crore (10m) individual F&O traders lost money, average loss ≈₹2 lakh incl. transaction costs; FY24 alone 91.1% lost; ~60% lost in futures vs 91.5% in options; >75% of loss-makers kept trading after two consecutive losing years — [TaxGuru summary of SEBI](https://taxguru.in/sebi/sebi-study-shows-93-percent-individual-fo-traders-incur-losses.html); [NISM](https://www.nism.ac.in/blog/equity-linked-exchange-traded-derivative-contracts-the-retail-rush-and-regulatory-measures/)

**Academic day-trading studies**
- Chague, De-Losso & Giovannetti, "Day Trading for a Living?" (SSRN 3423101, rev. June 2020): 19,646 Brazilians who began day-trading Mini-Ibovespa futures 2013–2015; of the 1,551 who persisted >300 days, 97% lost money; 1.1% (17 people) earned more than Brazilian minimum wage (US$16/day); 0.5% (8 people) earned more than a bank teller's starting salary (US$54/day); the single best trader averaged US$310/day with a daily standard deviation of US$2,560; "no evidence of learning by day trading" — [Quantpedia summary](https://quantpedia.com/retail-day-trading-is-an-uphill-battle/); [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3423101)
- Barber, Lee, Liu & Odean (Taiwan, 15 years of data; J. Financial Markets 2014): aggregate day-trader performance net of fees is negative in every one of the 15 years studied; "less than 1% of the day trader population is able to predictably and reliably earn positive abnormal returns net of fees"; ~82% of all traders lose money; >8 in 10 day traders lose in a typical six-month period — [Berkeley Haas PDF](https://faculty.haas.berkeley.edu/odean/papers/day%20traders/Day%20Trading%20Skill%20110523.pdf); [RePEc](https://econpapers.repec.org/RePEc:eee:finmar:v:18:y:2014:i:c:p:1-24)

**Prop-firm pass/payout rates**
- FPFX Tech data (Sept 2024, via Finance Magnates): ~100,000 traders / 300,000 accounts across 10 firms — ~14% passed a challenge; ~45% of funded traders got at least one payout; therefore ~7% of all participants were ever paid; average total payout ≈4% of nominal account size (a "$100k" trader who is paid withdraws roughly $4,000 in total) — [The Prop Firm Guide (compiles FPFX/FM)](https://thepropfirmguide.com/prop-firm-statistics/)
- Topstep 2024 (via Business Insider, Dec 2025): 12.4% funded rate; 28.3% of funded traders paid — [The Prop Firm Guide](https://thepropfirmguide.com/prop-firm-statistics/)
- Goat Funded Trader (Finance Magnates, Oct 2026): 22,279 of 594,997 challenge buyers paid (~3.7%), $26.16m total — [The Prop Firm Guide](https://thepropfirmguide.com/prop-firm-statistics/)
- FTMO does not publish an official pass rate; third-party estimates of ~10–12% across both phases are community compilations, not disclosures — [Backtrex](https://backtrex.com/en/blog/prop-firm-challenge-success-rate); [Track360](https://track360.io/blog/prop-trading-industry-statistics-2026)
- FTMO 2023 revenue $203.9m vs operating costs $100.3m (Trade Informer) — i.e., challenge fees are the business model — [Trade Informer](https://tradeinformer.com/prop-weekly/what-ftmo-tells-us-about-prop-firm-finances)
- 80–100 prop firms closed in 2024 (Finance Magnates); Brokeree found 71 of 82 tracked firms still operating at end-2024 — [The Prop Firm Guide](https://thepropfirmguide.com/prop-firm-statistics/)
- Tracked industry payouts 2025 ≈ $325m across tracked firms excluding FTMO/The5ers — [Finance Magnates](https://www.financemagnates.com/forex/prop-firm-e8-markets-warns-retail-traders-off-cfd-brokers-as-industry-leans-harder-on-educational-labels/)

**Bot/EA-specific evidence**
- A 2009 analysis of 193 active Collective2 stock systems found "young systems appear to have a high mortality rate due to poor performance" and that aggregate performance was "not encouraging"; no one-year survival % reported — [CXO Advisory](https://www.cxoadvisory.com/?p=4128)
- MQL5 Market signal pages routinely carry the platform's own disclaimer "This is a newly opened account, and the trading results may be of random nature" and drawdown flags such as "High current drawdown in 33% indicates the absence of risk limitation" — [MQL5 signal example](https://www.mql5.com/en/signals/2380485)
- Example of marketing vs live divergence: a Darwinex-linked EA signal advertised "validated over 4.25 years of history… profitable in all 5 years" while its live stats showed a 50% win rate, 0.52 profit factor and −1% growth in 2026 — [MQL5 signal 2380485](https://www.mql5.com/en/signals/2380485)

### Inferences
- The consistent 70–95% loss rates across unrelated markets (CFDs, Indian options, Brazilian futures, Taiwanese equities) and decades indicate a structural result (costs + zero-sum vs better-informed counterparties), not a product of any single market's design.
- Options/leveraged products show worse outcomes than futures (SEBI: 91.5% vs 60%), which is consistent with higher-cost, higher-gamma instruments amplifying the cost drag — scalping, which maximizes trade count, sits at the high-cost end.
- Prop-firm funnel math: ~14% pass × ~45% paid × avg 4% of nominal size means the expected payout per challenge entrant is on the order of a few hundred dollars against a challenge fee of similar magnitude — the firm's revenue model is the fee, not trader profit.
- No platform (Myfxbook, MQL5, Darwinex, Collective2) publishes a strategy survival/base-rate statistic in 2026; the visible population on these platforms is survivorship-biased because dead accounts are delisted or silently stop updating.

### Gaps
- No FINRA/SEC statistic on the share of US retail day traders who are profitable was found; FINRA's PDT rulemaking (see Q5) did not cite such a figure in the sources retrieved.
- No published, independently verified survival rate for automated EAs/bots on Myfxbook, MQL5 Market, Darwinex or Collective2 as of 2026. One blog claim that "fewer than 3% of scalpers are profitable after 2 years" cites no study and should not be used — [unsourced example](https://vector-ridge-293.pages.dev/learn/forex-scalping-strategies-2026.html).
- SEBI's studies do not break out API/algo users separately in the sources retrieved.
- The SSRN page for Chague et al. and the Moneylife SEBI article returned HTTP 403; figures come from reliable secondary summaries (Quantpedia, Business Standard).

---

## Key Question 2: Why do retail scalping bots fail?

### Takeaway
Scalping concentrates every structural disadvantage a retail participant has: per-trade costs are a large fraction of the 3–10 pip target, so break-even win rates of 55–65% are needed before any edge is counted; retail latency (tens to hundreds of ms) is roughly 1,000× slower than colocated market makers; brokers explicitly prohibit or penalize latency arbitrage/"tick scalping"; and the research-side failure (overfitting across many backtest configurations, post-publication decay of ~26–58%) means most apparent edges never existed.

### Cited Findings

**Transaction-cost math**
- Worked example: 5-pip target, 5-pip stop, 1-pip spread → win nets +4, loss costs −6 → break-even win rate ≈60% — [BabyPips forum](https://forums.babypips.com/t/what-is-correct-risk-reward-ratio-for-scalping/80643); with a 2-pip cost on a 5-pip target the trader "only win[s] 3 pips" — [BabyPips](https://forums.babypips.com/t/scalping-3-5-pips/69709)
- Expected-value example after costs: at a 60% win rate, 0.60×0.9 − 0.40×1.3 = +0.02 units per trade, "essentially break-even before platform mistakes" — [GO Markets](https://gomarkets.com/en-svg/articles/is-a-successful-scalping-strategy-possible)
- Retail anecdote illustrating cost drag: 900+ trades in <1 year, $37m notional, net loss ~$4k, but transaction costs >$30k — [EnergyExch forum](https://www.energyexch.com/thread/469858-a-couple-questions-to-all-the-scalpers-out)
- SEBI: FY22–24 average loss ≈₹2 lakh per trader *inclusive of transaction costs*, i.e., costs are a material part of the loss — [TaxGuru/SEBI](https://taxguru.in/sebi/sebi-study-shows-93-percent-individual-fo-traders-incur-losses.html)

**Latency and adverse selection**
- Typical US retail round-trip latency 50–150 ms vs 200–500 µs for a colocated institutional firm; HFT colocated at NYSE/Nasdaq execute round trips in under 100 µs — "roughly 1,000 times faster" — [NexusFi](https://nexusfi.com/a/automation/high-frequency-trading-hft-futures); [Lime](https://lime.co/high-frequency-trading-colocation-and-the-limits-of-the-speed-of-light)
- Latency arbitrage works because fast firms "receive market data updates faster than slower participants, including retail traders, can see them"; resting retail limit orders get picked off when prices move — [NexusFi](https://nexusfi.com/a/infrastructure/exchange-colocation-futures-traders)
- Own compute time matters: "if your strategy compute takes 50ms, shaving 30ms off network latency saves only 25% of total delay" — [uTrade Algos](https://www.utradealgos.com/blog/high-frequency-trading-demands-low-latency-systems-heres-why)
- One scalping blog reports slippage accounting for an additional 8% loss during high volatility (anecdotal) — [TheLedgerMind](https://theledgermind.com/scalping-forex-complete-guide/)

**Broker execution and terms**
- Gate TradFi CFD: trading "that consistently occurs around the exact moment of a price update" is treated as latency arbitrage; all order flow is monitored — [Gate](https://www.gate.com/help/tradfi/cfd/50268)
- Bitget CFD classifies latency arbitrage as "abusive structural arbitrage" — [Bitget](https://www.bitget.com/support/articles/12560603873369)
- Fusion Markets "discourages arbitrage trading in most forms, specifically latency arbitrage" — [Fusion Markets](https://fusionmarkets.freshdesk.com/support/solutions/articles/51000308112-do-you-allow-arbitrage-)
- Trive Africa scalping policy: does not forbid scalping but may move scalpers to another account type and refuse compensation for trades relying on latency/arbitrage — [Trive policy PDF](https://trive.com/afr/assets/docs/legal-documents/en/Trive_Africa-Scalping_Policy.pdf)
- Prop firm (Evercrest) prohibited practices include latency arbitrage and "high-frequency 'tick scalping' / order flooding" — [Evercrest](https://intercom.help/evercrestfunding/en/articles/16696830-prohibited-practices)
- UK Financial Ombudsman case DRN-4175490: broker (LCG) voided profitable trades citing "abusive market conduct"/suspected latency exploitation; ombudsman found the client acted within terms — [FOS decision](https://www.financial-ombudsman.org.uk/decision/DRN-4175490.pdf)
- Vendor tooling exists to flag "simple scalping patterns" and share "abusive trader" databases across brokers (vendor marketing, Tapaas) — [Investing.com Studios](https://www.investing.com/studios/article-383262)
- Commentary: a broker alleging abuse should be able to show "a stale price, a measurable latency window" — [DayTrading.com](https://www.daytrading.com/safety/price-feed-latency-arbitrage)

**Overfitting and edge decay**
- Bailey, Borwein, López de Prado & Zhu, "The Probability of Backtest Overfitting" (J. Computational Finance 2017): hold-out methods "tend to be unreliable and inaccurate in the context of investment backtests"; the more configurations tried, the higher the probability the best backtest is overfit; proposes CSCV — [SSRN](https://papers.ssrn.com/abstract=2326253); [eScholarship PDF](https://escholarship.org/content/qt4w1110bb/qt4w1110bb.pdf)
- McLean & Pontiff, "Does Academic Research Destroy Stock Return Predictability?" (J. Finance 2016): 97 published predictors; post-publication returns decay substantially (search results cite ~32–35% in working-paper versions; the published abstract's 26% out-of-sample / 58% post-publication figures were not retrievable here and should be verified at DOI 10.1111/jofi.12365) — [Ivey PDF](https://ivey.uwo.ca/media/3775549/pontiff.pdf); [Counterpoint PDF](https://counterpointfunds.com/wp-content/uploads/2017/07/PredictabilityMcleanPontiff.pdf)

**Behavioural persistence**
- SEBI: >75% of loss-making F&O traders continued trading after two consecutive losing years — [TaxGuru/SEBI](https://taxguru.in/sebi/sebi-study-shows-93-percent-individual-fo-traders-incur-losses.html); Chague et al.: no learning effect with experience — [Quantpedia](https://quantpedia.com/retail-day-trading-is-an-uphill-battle/)

### Inferences
- Illustrative cost ratio (own arithmetic, assumptions stated): on a "raw-spread" ECN account with ~0.1–0.2 pip EUR/USD spread plus ~$7/round-turn lot commission (~0.7 pip), all-in cost ≈0.8–0.9 pip. Against a 5-pip target that is ~16–18% of gross profit per winner; against a 3-pip target ~27–30%. Add 0.5–1 pip average slippage on a market-order scalper and costs reach 25–60% of target. A strategy needs a gross edge of several pips per trade just to be flat — an edge of that size at 1-minute horizons is exactly what HFT market makers compete for with microsecond latency.
- The broker policies above mean that even a *working* fast scalper on a CFD/market-maker broker faces counterparty risk: profits can be voided, accounts moved to worse pricing, or closed. Exchange-traded futures/crypto CEX order books remove the "broker voids profits" risk but expose the bot directly to HFT competition.
- Overfitting is the dominant *research* failure: an AI/ML pipeline that searches thousands of feature/parameter combinations on minute bars will almost always produce a backtest that looks excellent and is false; without CSCV/deflated Sharpe/walk-forward discipline and out-of-sample live paper-trading, the bot is being evaluated on noise.
- Regime change + edge decay imply any real micro-edge has a half-life; a scalping bot is a research-and-maintenance process, not a one-time build.

### Gaps
- No peer-reviewed estimate of adverse-selection cost specifically borne by retail algorithmic orders was found; latency figures above come from broker/vendor content.
- Could not retrieve a primary-source quantification of "last look" rejection rates or news-time spread widening at retail brokers in 2026.

---

## Key Question 3: Is a "million-dollar bot" realistic? What would it take, and what are realistic alternatives?

### Takeaway
Sustained 100%+/yr is extraordinarily rare even for the best-resourced quant firms: Medallion (the all-time best) averaged ~66% gross / ~39% net arithmetic (1988–2018) with thousands of staff and closed capital. For a retail scalper, reaching $1m from $5k at an already-excellent 3%/month takes ~15 years with no drawdowns and no withdrawals; from $100k at the same rate ~6.5 years. Edge decays with size (liquidity at the touch, broker lot limits, counterparty flags), so compounding at a fixed rate is itself an unrealistic assumption. Realistic goals are prop-firm payouts (small, lumpy, ~7% of entrants), a modest supplementary income on $25–100k, or selling tooling/research — not a seven-figure account from a laptop bot.

### Cited Findings
- Medallion Fund: average gross return 66.1% and net 39.2% per year 1988–2018 (Cornell, 2019; arithmetic averages); compound gross ≈63.3%; fees 5% management + 44% performance; $100 grew to ≈$398.7m gross — [CXO Advisory on Cornell](https://www.cxoadvisory.com/?p=33535); [Quantt](https://www.quantt.co.uk/resources/medallion-fund-history); [247WallSt](https://247wallst.com/investing/2026/06/21/the-greatest-fund-ever-why-jim-simons-medallion-fund-keeps-winning-without-him/)
- Treating 39% as a steady compound rate overstates realized results; figures are reported estimates for a private fund, not audited — [Quantt](https://www.quantt.co.uk/resources/medallion-fund-history)
- Renaissance's outside fund RIEF targets beating the S&P 500 gross, not Medallion-like returns — [Institutional Investor](https://institutionalinvestor.com/article/2ekcf5cio9yw4k7nv7hmo/hedge-funds/renaissance-continues-to-surge)
- Chague et al.: the *best* of 19,646 traders averaged US$310/day with SD US$2,560 — [Quantpedia](https://quantpedia.com/retail-day-trading-is-an-uphill-battle/)
- Barber/Odean: <1% of day traders reliably earn positive abnormal returns net of fees — [Berkeley Haas PDF](https://faculty.haas.berkeley.edu/odean/papers/day%20traders/Day%20Trading%20Skill%20110523.pdf)
- Prop-firm payouts: average ≈4% of nominal account; Q1 2026 crypto prop payouts averaged $1,865 across 61,682 payouts (FM Intelligence) — [The Prop Firm Guide](https://thepropfirmguide.com/prop-firm-statistics/)
- Leverage caps that bound retail position size: ESMA 30:1 FX majors / 20:1 indices / 10:1 commodities / 2:1 crypto; US retail forex 50:1 — [Track360](https://track360.io/blog/forex-leverage-regulation-by-region-esma-asic-cftc-2026); ASIC 30:1 to 2:1, order in force to 23 May 2027 with a proposed 10-year extension to 2037 (CS 64, Oct 2026) — [ASIC 26-239MR](https://asic.gov.au/about-asic/news-centre/find-a-media-release/2026-releases/26-239mr-asic-moves-to-extend-and-strengthen-cfd-consumer-protections)
- Broker "abusive trading" policies that cap or void scalper profits (see Q2) — [Trive](https://trive.com/afr/assets/docs/legal-documents/en/Trive_Africa-Scalping_Policy.pdf); [Gate](https://www.gate.com/help/tradfi/cfd/50268)
- CFTC advisory: schemes promising "at least 10% monthly returns (over 200% per year)" from a bot are cited as the archetypal fraud (Mirror Trading International) — [CFTC advisory](https://www.cftc.gov/LearnAndProtect/AdvisoriesAndArticles/AITradingBots.html)

### Inferences — compounding table (own arithmetic; assumes constant monthly rate, no drawdowns, no withdrawals, no taxes, no size limits — i.e., best case)

Annualized equivalents: 1%/mo ≈ 12.7%/yr; 2%/mo ≈ 26.8%; 3%/mo ≈ 42.6%; 5%/mo ≈ 79.6%; 10%/mo ≈ 213.8%.

| Start capital | 2%/month | 3%/month | 5%/month | 10%/month |
|---|---|---|---|---|
| $5,000 → $1m (×200) | ~22.3 yrs | ~14.9 yrs | ~9.0 yrs | ~4.6 yrs |
| $25,000 → $1m (×40) | ~15.5 yrs | ~10.4 yrs | ~6.3 yrs | ~3.2 yrs |
| $100,000 → $1m (×10) | ~9.7 yrs | ~6.5 yrs | ~3.9 yrs | ~2.0 yrs |

Context for the columns: 3%/month (≈43%/yr) already exceeds Medallion's *net* average; 5%/month (≈80%/yr) exceeds Medallion's *gross* average; 10%/month is the exact figure the CFTC cites as a fraud red flag.

Income-not-compounding view: at 3%/month, $25k yields ≈$750/month gross before tax; $100k yields ≈$3,000/month. To net $1m/year at 30%/yr requires ≈$3.3m of working capital; at 50%/yr ≈$2m.

Drawdown arithmetic: a 20% drawdown needs +25% to recover; 30% needs +43%; 50% needs +100%. A scalper running the leverage needed for 5%/month will, by construction, see such drawdowns.

Why fixed-rate compounding fails for scalpers specifically:
- Edge is bounded by liquidity at the touch and by the number of opportunities per day, not by capital; doubling size does not double profit, it increases slippage and market impact (thin crypto altcoin books especially).
- Brokers cap lot size, flag "toxic" flow and can void profits (Q2); exchanges impose position limits; prop firms impose consistency/lot rules.
- Regulatory leverage caps (30:1 EU/AU, 50:1 US FX, 2:1 crypto CFDs EU) bound notional per dollar of equity.
- Taxes (Q6) take 20–45% of gains annually in most jurisdictions, cutting the compounding rate roughly proportionally.

What it would actually take (inference from the funds data above): proprietary data/feeds, colocation or at least exchange-proximate hosting, a research process with overfitting controls (CSCV/deflated Sharpe), continuous re-research as edges decay, risk systems, capital in the millions, and a team — i.e., the structure of a quant firm. A solo developer can realistically achieve: (a) a robust, cost-aware, modest-frequency system targeting low-double-digit annual returns on real capital; (b) prop-firm payouts (small and lumpy; treat the challenge fee as the cost of an option); (c) revenue from tooling, education or signals (note that selling signals/advice may itself be regulated activity); (d) a portfolio of several uncorrelated slower strategies rather than one scalper.

Survivorship bias: social-media bot vendors show only live winners; Myfxbook/MQL5 populations are what remains after blown accounts stop reporting (see Q1 gaps). The "validated 4.25 years, profitable every year" marketing vs 0.52 live profit factor example in Q1 is typical.

### Gaps
- No independent dataset of returns for *successful* retail algo traders (the right tail) exists; the only tail evidence is Chague's best trader ($310/day, SD $2,560) and Barber/Odean's "<1%".
- "Typical quant fund 10–20%/yr" could not be sourced in this research round; the only sourced benchmark is Medallion vs RIEF (which targets S&P-plus). Treat 10–20% as unsourced folk knowledge.
- No published study on how retail scalping edge decays with trade size (market impact at retail scale) was found.

---

## Key Question 4: Scams to avoid, enforcement actions, and a red-flag checklist

### Takeaway
"AI trading bot" is now one of the most common fraud wrappers: the FBI's IC3 recorded $20.9bn in 2025 internet-crime losses, of which $7.2bn was crypto investment fraud (the largest category) and $893m was tagged AI-assisted; the SEC brought at least five AI-bot/AI-signal Ponzi cases in 2025–2026 (Privvy $12.3m, PGI Global $198m, TSAI/Cryptoaiml, a $130m+ "SEC-registered" signals scheme, $14m AI investment clubs); the CFTC's flagship example (Mirror Trading International) promised 10%/month from a "bot" and took ~29,420 BTC from 23,000 US victims. Regulators in Belgium, Italy, Spain and the UK have warned about prop firms; the US CFTC's own prop-firm case collapsed on procedural grounds, leaving the sector unregulated.

### Cited Findings

**Scale of losses (US, 2025)**
- FBI IC3 2025 report (released 6 April 2026): 1,008,597 complaints, $20.877bn losses (+26% YoY); crypto-tagged losses $11.366bn across 181,565 complaints; crypto investment fraud $7.2bn (highest category); investment fraud overall ≈$8.6bn; first year tracking AI: 22,364 complaints, $893m — [Decrypt](https://decrypt.co/363486/11-4b-lost-to-crypto-scams-in-2025-fbi-internet-crime-report); [Fortra](https://fortra.com/blog/ai-and-cryptocurrency-scams-are-costing-americans-billions-fbi-reports); [Gizmodo](https://gizmodo.com/crypto-investment-scams-were-the-most-costly-type-of-fraud-in-the-u-s-in-2025-2000743099)
- FTC: 2025 investment-scam losses >$7.9bn, median individual loss >$10,000 (April 2026 consumer alert, via Bitcoin.com); New York DCP cites 144,041 consumers and >$8bn, +38% vs 2024 — [Bitcoin.com](https://news.bitcoin.com/new-york-warns-of-fake-crypto-and-ai-as-scam-losses-hit-8-billion/); [Crypto Briefing](https://cryptobriefing.com/new-york-warns-ai-investment-scams-8-billion/)
- FTC Consumer Sentinel 2025: ~3m fraud reports, ~$15.9bn reported losses (vs >$12bn in 2024) — [Bitdefender on FTC](https://bitdefender.com/en-au/blog/hotforsecurity/ftc-americans-lost-12-5-billion-to-scams-last-year)

**Regulator advisories**
- CFTC Customer Advisory "AI Won't Turn Trading Bots into Money Machines" (25 Jan 2024, re-issued; refers to "super intelligence"): red flags = huge returns ("tens of thousands of percent"), 100% win rates, guaranteed returns, "no trading experience required", referral/affiliate pay structures, influencer hype, demo balances presented as real funds; precautions = reverse-image-search personnel, check domain age via ICANN, factor in fees/spreads/subscriptions — [CFTC advisory](https://www.cftc.gov/LearnAndProtect/AdvisoriesAndArticles/AITradingBots.html); [CFTC release 8854-24](https://www.cftc.gov/PressRoom/PressReleases/8854-24)
- Mirror Trading International (CFTC): default judgment April 2023 — >$1.7bn restitution + >$1.7bn civil penalty (highest in CFTC history); ~29,421 BTC from ≥23,000 US persons; promised ≥10%/month from a forex "bot"; almost no trading occurred; collection stayed by bankruptcy — [CFTC 8772-23](https://www.cftc.gov/PressRoom/PressReleases/8772-23); [Cointelegraph](https://cointelegraph.com/news/cftc-fines-mti-1-7b-for-bitcoin-related-forex-fraud)

**SEC enforcement 2025–2026 (AI-bot wrappers)**
- Privvy / Nathan Fuller (SEC, filed late May 2026, S.D. Tex.): $12.3m from ~150 investors; promised 40–50% in 30–45 days from "AI arbitrage bots"; ~$380k (≈3%) actually traded; $6.2m personal use; $5.5m Ponzi payments — [The Block](https://www.theblock.co/post/403118/sec-sues-privvy-founder-over-12-3-million-crypto-scheme-as-ai-bots-turn-out-to-be-neither); [Cointelegraph](https://cointelegraph.com/news/sec-charges-texas-man-with-123m-crypto-fraud-fake-ai-trading-bots)
- PGI Global / Ramil Palafox (SEC, 2025): $198m scheme masking a fake AI auto-trading platform — [The Block](https://www.theblock.co/post/403118/sec-sues-privvy-founder-over-12-3-million-crypto-scheme-as-ai-bots-turn-out-to-be-neither)
- TSAI & Cryptoaiml (SEC, Sept 2025): "rent" AI trading bots via website/Facebook/WhatsApp with guaranteed profits; companion case for AI-generated signals — [Investment Executive](https://www.investmentexecutive.com/?p=118596)
- Foreign firms falsely claiming SEC registration (2026): >$130m raised Oct 2025–Jun 2026 promising "high, risk-free returns using AI-generated crypto trading signals" — [Investment Executive](https://www.investmentexecutive.com/?p=118596)
- "AI investment clubs" network (SEC, Dec 2025): $14m — [Investment Executive](https://www.investmentexecutive.com/?p=118596)

**Market-manipulation-as-a-service (relevant both as scam and as what a bot must not do)**
- DOJ (April 2026, "Operation Token Mirrors" follow-on): 10 individuals at market makers Gotbit, Vortex, Antier, Contrarian charged with wash trading/wire fraud after an FBI/IRS-CI sting using FBI-created tokens; bots used to fake volume; >$1m seized and bots disabled; 18 defendants charged in Oct 2024 in a related case — [CoinDesk](https://www.coindesk.com/business/2026/04/02/doj-sting-exposes-crypto-wash-trading-continues-to-be-far-more-common-than-expected); [Decrypt](https://decrypt.co/362999/doj-charges-10-foreign-nationals-over-crypto-wash-trading-scheme)

**Prop-firm warnings**
- Belgium FSMA (Mar 2024): prop trading is "a game of shadow investing, a practice that costs money and can lead to reckless behaviour" — [Finance Magnates](https://www.financemagnates.com/forex/fsma-warns-public-against-dubious-practices-of-prop-trading-firms/)
- Italy CONSOB (Jul 2024): prop sites "simulate online trading in a type of finance video game" — [Finance Magnates](https://www.financemagnates.com/forex/another-regulator-warns-against-prop-firms-calls-them-trading-video-games/); Spain CNMV warned in 2019 — same source
- UK FCA added "Funded Trader" to its warning list (Aug 2025) — [DayTradingToolkit](https://daytradingtoolkit.com/market-insights/prop-firm-regulation-funded-traders-guide)
- CFTC v. Traders Global Group (My Forex Funds): dismissed with prejudice 13 May 2025 (D.N.J., Judge Kiel) after findings that the CFTC "acted willfully and in bad faith"; ≈$3.1m fees awarded against the CFTC; five CFTC staff placed on leave; dismissal was on the agency's conduct, not the merits — [Willkie](https://complianceconcourse.willkie.com/articles/new-jersey-federal-judge-dismisses-forex-case-with-prejudice-and-awards-attorney-fees/); [Finance Magnates](https://www.financemagnates.com/forex/my-forex-funds-parent-defeats-cftc-in-court-as-judge-imposes-sanctions/); [Reuters via TradingView](https://tw.tradingview.com/news/reuters.com%2C2025%3Anewsml_L1N3TB0SH%3A0-cftc-ordered-to-pay-3-1-million-legal-tab-in-my-forex-funds-case)
- Most prop-firm complaints concern denied payouts; challenge fees and payouts come from the same pool — [Global Trading](https://globaltrading.net/?p=36415)
- ESMA/regulators are studying prop regulation; no EU-wide prop-firm rule in force as of 2026 — [Finance Magnates](https://financemagnates.com/forex/exclusive-regulators-conducted-preliminary-reviews-on-potential-prop-trading-regulations)

**EA/bot vendor patterns**
- MQL5 signal disclaimers and drawdown flags (see Q1) — [MQL5](https://www.mql5.com/en/signals/2380485)

### Inferences — Red-flag checklist (each item traceable to the CFTC advisory, SEC cases or platform evidence above)
1. Any stated monthly return ≥5% or "10%/month", or 40–50% in 30–45 days (MTI, Privvy) — assume fraud.
2. "Guaranteed", "risk-free", "100% win rate", "no losing months", "no experience required".
3. Returns paid in your deposited crypto/BTC and withdrawals that are delayed, taxed by the "platform", or require a further deposit (pig-butchering pattern; IC3 crypto investment fraud $7.2bn).
4. Referral/affiliate/MLM pay structures (MTI was an MLM).
5. Backtest-only or demo-account "proof"; Myfxbook/MQL5 links with <12 months live, "newly opened account" tags, equity curves without drawdown, or marketing claims that contradict the live stats on the same page.
6. Martingale/grid EAs: smooth equity, very high win rate, then one catastrophic month (MQL5 drawdown flags "absence of risk limitation").
7. Vendor does not publish verified live track record on a regulated broker with investor-password access; no third-party audit.
8. Claims of SEC/FCA "registration" — check the register yourself (SEC 2026 case: >$130m raised with fake registration claims).
9. Unregulated/offshore broker recommended by the bot vendor (vendor earns IB rebates; broker may widen spreads/void profits).
10. Telegram/WhatsApp signal groups, influencer-fronted "AI quant" apps, YouTube "I made $X with a ChatGPT bot" without broker statements.
11. Newly registered domain (CFTC: check ICANN registration age), stock-photo team (reverse-image search).
12. Prop firm: no published pass/payout data, rule changes after you pass, "consistency" clauses that void payouts, payouts only in crypto, firm younger than 2 years (80–100 closures in 2024).
13. Any product that asks for your exchange API keys with withdrawal permission, or your broker login.

### Gaps
- No dedicated FTC report quantifying losses attributable specifically to "AI trading bots" was found; the figures above are investment-fraud totals.
- No CFTC (as opposed to SEC/DOJ) AI-bot enforcement action from 2025–2026 surfaced in searches; the CFTC's cited cases are MTI (2022–2023) and earlier.
- Yield Nodes and similar European "AI node" Ponzis were not researched in this round.

---

## Key Question 5: Is retail algorithmic trading legal, and what regulatory rules apply (US, EU, UK, India, Australia; brokers; market abuse)?

### Takeaway
Running your own bot on your own account is legal in all jurisdictions covered, but each attaches conditions: the US scrapped the $25k Pattern Day Trader rule effective 4 June 2026 (replaced by intraday margin), US retail forex remains capped at 50:1 under CFTC/NFA, and US crypto market-structure law (CLARITY Act) stalled in the Senate in September 2026 after the GENIUS stablecoin act passed in July 2025; the EU caps CFD leverage at 30:1 and in February 2026 declared crypto perpetuals to be CFDs, while MiFID II Art. 17/RTS 6 algo-trading obligations bind investment firms and venue members, not clients trading through a broker; the UK still bans retail crypto derivatives (ETNs were un-banned Oct 2025); India now requires retail algos to run through broker APIs with exchange registration above an order-rate threshold (fully mandatory 1 April 2026); Australia's CFD intervention order runs to May 2027 with a proposed extension to 2037. Market-abuse law (spoofing, layering, wash trading) applies to the bot's operator regardless of who "decided".

### Cited Findings

**United States**
- SEC approved FINRA's amendments to Rule 4210 on 14 April 2026; effective 4 June 2026; removes the four-day-trades-in-five-days test, the PDT designation and the $25,000 minimum equity, replacing them with intraday margin requirements; some firms have extended adoption to 20 Oct 2027 — [Federal Register 2026-07485](https://www.govinfo.gov/content/pkg/FR-2026-04-17/html/2026-07485.htm); [ACA Global](https://www.acaglobal.com/industry-insights/finra-ends-the-pattern-day-trader-rule/); [E*TRADE](https://us.etrade.com/knowledge/library/margin/pattern-day-trading-rule-change); [QuantInsti](https://www.quantinsti.com/articles/finra-pdt-rule-removal-2026/)
- US retail forex: leverage capped at 50:1; firms soliciting US retail forex must register as RFED or FCM with CFTC/NFA — [Track360](https://track360.io/blog/forex-leverage-regulation-by-region-esma-asic-cftc-2026)
- GENIUS Act (stablecoins) signed 18 July 2025; rulemaking deadlines through July 2026; issuers may not pay interest to holders — [Spark](https://www.spark.money/research/genius-act-stablecoin-regulation-explained); [KuCoin blog](https://www.kucoin.com/blog/en-stablecoin-regulation-updates-2026-genius-act-mica-enforcement-global-compliance-trends)
- CLARITY Act (market structure): passed House 294–134 on 17 July 2025; cleared Senate Banking 15–9 on 14 May 2026; failed to reach 60 votes on 15 Sept 2026, "significantly diminishing the chances of passage in this Congress" — [Orrick](https://www.orrick.com/Insights/2026/10/The-CLARITY-Act-Stalls-in-the-Senate-Whats-Next-for-Digital-Asset-Regulation); [Bloomberg Law](https://news.bloomberglaw.com/banking-law/crypto-bill-languishes-in-senate-leaving-tiny-cftc-in-limbo)
- SEC–CFTC joint taxonomy (17 March 2026) classified 16 tokens as "digital commodities", clarifying CFTC manipulation jurisdiction — [CoinDesk](https://www.coindesk.com/business/2026/04/02/doj-sting-exposes-crypto-wash-trading-continues-to-be-far-more-common-than-expected)
- Prop firms: CFTC v. My Forex Funds dismissed May 2025 on agency misconduct; "regulatory questions unresolved" — [Today's General Counsel](https://todaysgeneralcounsel.com/proprietary-trading-lawsuit-dismissal-left-regulatory-questions-unresolved/)

**European Union**
- ESMA retail CFD product intervention (since 2018, now national measures): 30:1 FX majors, 20:1 indices, 10:1 commodities, 2:1 crypto; negative balance protection; margin close-out — [Track360](https://track360.io/blog/forex-leverage-regulation-by-region-esma-asic-cftc-2026)
- ESMA public statement 24 Feb 2026 (ESMA35-243228190-8024): instruments marketed as "perpetual futures" that meet the CFD definition fall within CFD product-intervention measures; "the commercial name… is irrelevant"; five obligations incl. leverage limits apply with immediate effect to firms offering them to EU retail — [Regulation Tomorrow](https://www.regulationtomorrow.com/2026/02/esma-reminds-firms-of-their-obligations-under-cfd-product-intervention-measures-amid-rising-offerings-of-perpetual-futures/); [ESMA statement PDF](https://www.dirittobancario.it/wp-content/uploads/2026/02/Dichiarazione-ESMA-24-febbraio-2026-ESMA35-243228190-8024.pdf); [Finance Magnates](https://www.financemagnates.com/forex/regulation/esma-tells-firms-perpetual-futures-fall-under-eu-cfd-rules/)
- MiFID II Art. 17: an *investment firm* engaging in algorithmic trading must notify its home NCA and the venue; RTS 6 (Reg. 2017/589) applies to firms within the MiFID II investment-firm definition; MiFID II withdrew the own-account exemption (Art. 2(1)(d)) for persons applying high-frequency algorithmic techniques and for venue members/participants — [ESMA single rulebook Art. 17](https://www.esma.europa.eu/publications-and-data/interactive-single-rulebook/mifid-ii/article-17-algorithmic-trading); [Hogan Lovells](https://www.hoganlovells.com/~/media/hogan-lovells/pdf/mifid/new_mifid_update_31_dec_2016/5466119v1mifid-ii-algorithmic-trading-29122016lwdlib01.pdf); [Deloitte RTS 6](https://www.deloitte.com/uk/en/services/audit-assurance/blogs/mifid-ii-rts-6-requirements-annual-self-assessment.html)
- MiCA: fully applicable Dec 2024; CASP transitional period ended 1 July 2026 (secondary source; verify) — [KuCoin blog](https://www.kucoin.com/blog/en-stablecoin-regulation-updates-2026-genius-act-mica-enforcement-global-compliance-trends)

**United Kingdom**
- FCA ban on sale/marketing of crypto derivatives to retail in force since Jan 2021; crypto ETN ban lifted 8 Oct 2025; derivatives ban remains (source updated Oct 2026) — [FCA press release](https://www.fca.org.uk/news/press-releases/fca-opens-retail-access-crypto-etns/printable/print); [Bitcoin Street Journal](https://thebitcoinstreetjournal.com/uk-regulators-ban-crypto-derivatives-to-retail-consumers)
- UK Cryptoassets Regulations effective 4 Feb 2026 extended the FSMA market-abuse perimeter to crypto (secondary source) — [Track360](https://track360.io/blog/forex-leverage-regulation-by-region-esma-asic-cftc-2026)
- FCA retail CFD loss disclosure regime (see Q1) and FOS decision on voided scalping profits (Q2) — [FOS DRN-4175490](https://www.financial-ombudsman.org.uk/decision/DRN-4175490.pdf)

**India**
- SEBI circular 4 Feb 2025 "Safer participation of retail investors in Algorithmic trading"; original effective 1 Aug 2025 → extended to 1 Oct 2025 (circular SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/108, 29 Jul 2025) → phased "glide path" (circular 30 Sept 2025) with full mandatory applicability 1 April 2026 — [Taxscan](https://www.taxscan.in/top-stories/sebi-extends-timeline-for-retail-algo-trading-framework-full-implementation-from-apr-1-2026-1433982); [Taxmann](https://www.taxmann.com/post/blog/sebi-extends-deadline-for-retail-algo-trading-framework/); [The Week/PTI](https://www.theweek.in/wire-updates/business/2025/07/29/dcm84-biz-sebi-algo.html)
- Framework substance (per law-firm/industry summaries, primary circular not fetched): retail algos must route via broker-provided APIs; brokers responsible; algos tagged with unique IDs; exchanges register algos; algo providers empanelled through brokers — [K&S Partners](https://ksandk.com/md/corporate/sebis-new-regulatory-framework-for-retail-algorithmic-trading/); [uTrade Algos](https://utradealgos.com/blog/decoding-sebis-new-algo-trading-rules-for-retail-investors-all-you-need-to-know)
- SEBI F&O measures (2024–2025) cut unique F&O traders by 20% — [Business Standard](https://www.business-standard.com/markets/news/individual-investors-shrink-20-percent-fo-segment-125070800801_1.html)

**Australia**
- ASIC CFD Product Intervention Order: leverage 30:1 to 2:1 for retail, in force until 23 May 2027 (extended Apr 2022); ASIC reports a 91% reduction in retail net losses; CS 64 (12 Oct 2026) proposes a further 10-year extension to 2037 plus crypto-settlement and record-keeping amendments — [ASIC 22-082MR](https://asic.gov.au/about-asic/news-centre/find-a-media-release/2022-releases/22-082mr-asic-s-cfd-product-intervention-order-extended-for-five-years/); [ASIC 26-239MR](https://asic.gov.au/about-asic/news-centre/find-a-media-release/2026-releases/26-239mr-asic-moves-to-extend-and-strengthen-cfd-consumer-protections); [ASIC CS 64](https://asic.gov.au/regulatory-resources/find-a-document/consultations/cs-64-protecting-retail-investors-proposed-extension-and-amendments-to-the-cfd-product-intervention-order)

**Market abuse that a bot can commit**
- DOJ April 2026 charges: bots used to "inflate trading volume and prices" (wash trading) = wire fraud; prior Oct 2024 case charged 18 — [Decrypt](https://decrypt.co/362999/doj-charges-10-foreign-nationals-over-crypto-wash-trading-scheme); [CoinDesk](https://www.coindesk.com/business/2026/04/02/doj-sting-exposes-crypto-wash-trading-continues-to-be-far-more-common-than-expected)
- Broker ToS: latency arbitrage, "tick scalping", order flooding prohibited; profits can be voided (Q2 sources) — [Gate](https://www.gate.com/help/tradfi/cfd/50268); [Evercrest](https://intercom.help/evercrestfunding/en/articles/16696830-prohibited-practices)

### Inferences
- "Legal to run a bot" ≠ "unregulated": the individual trades as a *client*; the broker/venue carries MiFID II Art. 17/RTS 6 or SEBI obligations and pushes them down contractually (API limits, order-rate thresholds, kill switches, ToS on abusive patterns). Violating those is a contract breach with account closure/voided profits as the sanction.
- An individual who becomes a direct venue member or uses HFT techniques at scale in the EU can fall inside the investment-firm perimeter (Art. 2(1)(d) exemption withdrawn for HFT) — i.e., scaling a scalper past retail-broker access changes your regulatory status.
- The PDT repeal removes a capital gate for US stock scalpers but not the economics; intraday margin still scales with exposure.
- US crypto: with CLARITY stalled, the legal perimeter for altcoin spot/perps remains agency-defined (SEC/CFTC taxonomy, DOJ wire-fraud); offshore perps platforms accessed from the US/EU/UK are either unlicensed or prohibited for retail (UK ban, ESMA Feb 2026).
- Bot-specific liabilities: (1) spoofing/layering/wash patterns can arise unintentionally from naive order-management logic (cancel/replace storms, self-matching across sub-accounts) — the operator is liable, and no source suggests "the algorithm decided" is a defence; the DOJ cases charged the humans who ran the bots. (2) API-key security: a key with withdrawal rights is a theft vector; the scam checklist includes any vendor asking for it.

### Gaps
- NFA FIFO and no-hedging rules (Compliance Rule 2-43) were not confirmed from a primary source in this round; the 50:1 cap was. Verify at nfa.futures.org.
- Canada (CIRO) rules for retail CFD/algo trading: no sources retrieved.
- Exact SEBI order-per-second registration threshold and static-IP/2FA requirements could not be confirmed (primary circular not fetched; fetch tool rate-limited).
- No case law specifically rejecting an "AI made the decision" defence was found; the inference rests on the DOJ bot-manipulation prosecutions charging operators.
- MiCA CASP transition end date (1 July 2026) is from a secondary source.

---

## Key Question 6: Tax treatment of high-frequency/bot trading gains (US, UK, EU examples, India) and record-keeping

### Takeaway
Scalping gains are short-term everywhere and are generally taxed at the highest applicable rate: US ordinary rates (or 60/40 for Section 1256 futures; Section 988 ordinary for spot forex by default; 475(f) mark-to-market available to qualifying traders and must be elected in advance), UK CGT 18%/24% above a £3,000 allowance (spread betting outside CGT but challengeable if it is your trade), Germany 25% flat + solidarity surcharge with the €20,000 derivatives-loss cap repealed by the JStG 2024, France 30% PFU (12.8% + 17.2% social charges; some sources now cite 31.4%), India slab-rate business income for F&O and a flat 30% + 1% TDS for crypto with no loss offset. A bot generating thousands of fills creates thousands of taxable events; US crypto brokers now report proceeds on Form 1099-DA, with cost basis reported for 2026-acquired "covered" assets.

### Cited Findings

**United States**
- IRS Topic 429: trader status requires seeking profit from daily price movements, substantial activity, and continuity/regularity; traders without a 475(f) election report capital gains on Schedule D/8949 with wash-sale rules and capital-loss limits; expenses on Schedule C; gains not subject to self-employment tax — [IRS Topic 429](https://www.irs.gov/taxtopics/tc429)
- 475(f) mark-to-market election: must be made by the due date (without extensions) of the *prior* year's return via attached statement; late elections generally not allowed; converts gains/losses to ordinary (Form 4797 Part II); wash-sale rules and capital-loss limits do not apply; method change via Form 3115 under Rev. Proc. 2025-23; revocation also requires notification + Form 3115 — [IRS Topic 429](https://www.irs.gov/taxtopics/tc429); [Journal of Accountancy](https://www.journalofaccountancy.com/issues/2022/jun/tax-advice-clients-day-trade-stocks.html)
- 475(f)(1) (securities) and 475(f)(2) (commodities/Section 1256) are separate elections; many traders elect securities only and leave futures/broad-based index options under 60/40 — [TSCPA](https://tscpatax.com/articles/section-475-mark-to-market-options-traders)
- Section 1256 contracts (regulated futures, broad-based index options): 60% long-term / 40% short-term regardless of holding period, marked to market at year-end, Form 6781 — [Terms.law](https://terms.law/Trading-Legal/guides/section-1256-contracts.html); [Beancount guide](https://beancount.io/blog/2026/05/14/section-1256-contracts-60-40-tax-treatment-futures-broad-based-index-options-regulated-forex-form-6781-mark-to-market-traders-guide)
- Spot forex: default Section 988 — ordinary gains/losses, losses fully deductible against other income; trader may opt out under 988(a)(1)(B) by an internal contemporaneous election made *before* positions are opened; whether retail spot forex then qualifies for 1256(g) 60/40 is contested and the IRS may challenge it if the dealer is unregulated or no active forward market exists; retroactive elections at tax time are invalid — [DayTradingToolkit](https://daytradingtoolkit.com/day-trading-basics/forex-trading-tax-section-988-vs-1256); [Terms.law forum](https://terms.law/forum/thread/forex-trader-tax-treatment.html); [tastyfx](https://tastyfx.com/help-and-support/my-accounts/tax-information)
- Crypto: Form 1099-DA — brokers report gross proceeds; for "covered" assets acquired from 1 Jan 2026 brokers also report cost basis (first reported in 2027 for TY2026); earlier-acquired assets are "noncovered" with basis blank — taxpayer must track; per-wallet basis tracking required under Rev. Proc. 2024-28; if basis is undocumented the IRS may treat it as zero — [Harness](https://www.harness.co/articles/new-1099-da-broker-reporting-rules-for-2026-what-crypto-investors-need-to-know); [IRS 1099-DA instructions](https://www.irs.gov/instructions/i1099da); [KuCoin blog](https://www.kucoin.com/blog/irs-cost-basis-rule)
- Wash-sale rule (IRC 1091) does not currently apply to crypto treated as property (only to digital assets that are securities; 1099-DA Box 1i); legislative proposals to extend it have not been enacted as of mid-2026 — [Harness](https://www.harness.co/articles/new-1099-da-broker-reporting-rules-for-2026-what-crypto-investors-need-to-know); [Beancount](https://beancount.io/blog/2026/05/10/form-1099-da-digital-asset-broker-reporting-2026-crypto-investors-cost-basis-form-8949-guide)

**United Kingdom**
- Spread betting: HMRC treats as gambling, outside CGT, no reporting; losses not deductible; HMRC may challenge the exemption if trading is your sole/main income and reclassify under the badges of trade — [IG](https://www.ig.com/uk/spread-betting/spread-betting-vs-cfds/tax); [CMC Markets](https://www.cmcmarkets.com/en-gb/trading-guides/day-trading-tax-guide); [Trade Nation](https://tradenation.com/en-gb/articles/spread-betting-tax-in-uk/)
- CFDs/forex/crypto: CGT at 18% (within unused basic-rate band) / 24% above; annual exempt amount £3,000 (2026/27, not carry-forwardable); crypto rates rose from 10%/20% to 18%/24% for disposals on/after 30 Oct 2024; report on SA108; CFD losses offset other gains — [gov.uk CGT (archived copy)](https://tnaqa.mirrorweb.com/ukgwa/20260715154742mp_/https://www.gov.uk/capital-gains-tax/print); [UK CGT calculator 2026/27](https://ukcapitalgainstaxcalculator.co.uk/blog/cgt-rates-2026-27); [CMC CFD tax](https://www.cmcmarkets.com/en-gb/cfd-trading/cfd-trading-tax)
- Crypto-to-crypto swaps are disposals; UK Cryptoasset Reporting Framework in force 1 Jan 2026 requires platforms to report user transactions to HMRC — [Coincub Europe guide](https://coincub.com/blog/europe-crypto-tax-guide/)

**Germany**
- Capital gains (incl. CFDs/futures): 25% Abgeltungsteuer + Solidaritätszuschlag (+ church tax where applicable); the €20,000/yr derivatives (Termingeschäfte) loss-offset cap, ruled unconstitutional by the BFH, was repealed by the Jahressteuergesetz 2024 (Bundesrat 22 Nov 2024) retroactively for all open cases — [CMS Law](https://cms.law/de/deu/legal-updates/Verlustverrechnungsbeschraenkung-bei-Termingeschaeften-Gesetzgeber-schafft-Vorschrift-ab); [KPMG](https://kpmg.com/de/de/home/themen/2024/12/steuertipp-termingeschaeftsverluste-der-fiskus-gibt-nach.html); [Trade Informer](https://tradeinformer.com/?p=5851)
- Crypto (private sale): tax-free after 1-year holding; within one year taxed at progressive income tax up to 45% (sources differ on the de minimis threshold: €600 vs €1,000) — [Coincub](https://coincub.com/blog/europe-crypto-tax-guide/); [Koinly](https://koinly.io/fi/blog/crypto-tax-world/)

**France**
- Crypto gains (non-professional): PFU 30% (12.8% income tax + 17.2% social charges); some 2026 sources cite 31.4% (12.8% + 18.6%) — verify current social-charge rate; crypto-to-crypto swaps not taxable events — [Coincub](https://coincub.com/blog/europe-crypto-tax-guide/); [Spark](https://www.spark.money/tools/crypto-tax-rules-by-country)

**India**
- F&O: non-speculative business income (s.43(5)); taxed at slab rates; file ITR-3; losses offset against other heads except salary, carry-forward 8 years; tax audit under s.44AB depends on turnover (absolute-value method) — thresholds cited inconsistently (₹10 crore with ≥95% digital; ₹3 crore/profit <6% rules) — [Quicko](https://learn.quicko.com/fo-trading-tax-treatment); [ClearTax](https://cleartax.in/s/tax-filing-security-traders); [Business Today](https://www.businesstoday.in/personal-finance/tax/story/fo-income-taxation-heres-what-indian-nri-investors-should-note-481635-2025-06-24)
- Crypto (VDA): flat 30% + 4% cess (≈31.2%) + 1% TDS on transfers; no set-off of losses — [AvaTrade](https://www.avatrade.com/education/correct-trading-rules/crypto-taxation); [KoinX](https://www.koinx.com/stats/crypto-tax-rates-by-country)

### Inferences
- Event count: a bot doing 20 round-trips/day × 250 days = 5,000 taxable disposals/year; on crypto with per-wallet basis rules and partially "noncovered" lots this is unmanageable without automated lot-level accounting from day one. Manual spreadsheets will fail at this scale.
- Tax drag materially lowers the compounding rate in Q3's table: a 42.6%/yr gross (3%/month) becomes ≈32% at a 25% flat rate and ≈25% at a 40% marginal rate.
- US choices must be made *before* the year/positions: 475(f) by the prior-year return deadline; 988 opt-out before opening positions. A retail scalper who first thinks about tax in April has already lost the options.
- Loss-handling asymmetry matters because most scalpers lose: US 988 ordinary losses are fully deductible; UK spread-bet losses are not; India crypto losses cannot be set off; Germany's cap is gone. For a losing bot, the jurisdiction/instrument determines whether losses are even usable.
- Generic advice (inference from the above): keep raw fill logs and broker statements for every account; reconcile monthly; use lot-level software; confirm whether your activity is "trading income" vs "capital gains" with a local accountant before scaling, because reclassification (UK badges of trade, US trader status) changes rates, deductions and filing forms.

### Gaps
- US "trader tax status" has no bright-line trade count in Topic 429; case-law thresholds were not researched.
- Exact 2026 French social-charge rate (17.2% vs 18.6%) and German crypto de-minimis threshold conflict across sources; verify with impots.gouv.fr / BMF.
- Indian s.44AB audit thresholds conflict across practitioner sites; verify against the Income-tax Act as amended for FY2025-26/2026-27.
- No primary HMRC manual page (BIM22015/CG56100) was fetched; UK findings rely on broker guides that agree with each other and with the gov.uk CGT page.
- Canada and Australia tax treatment were not researched.
