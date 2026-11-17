# Practical requirements and realistic costs for a solo developer building/running a real-time AI-powered scalping bot (2026)

All prices below were checked on 2026-11-16 unless a different "page date" is stated. "Accessed" = date I read the page. Prices from vendor pages are preferred; third-party/aggregator figures are flagged as such. Currency as quoted by the source.

## VPS / hosting: options, prices, latency to broker/exchange servers

### Takeaway
A broker-adjacent Windows forex VPS (Equinix LD4/NY4/TY3-class) costs ~US$10–65/month in 2026 (MetaQuotes built-in VPS from $10–15/mo; ForexVPS $32–64/mo promo; FXVM $14–69/mo; Beeks ~$41–129/mo), with vendors claiming 0–5 ms to most broker servers. Generic cloud (Hetzner €5.99–29.99/mo Linux, AWS Tokyo t3.medium ~$40/mo Linux, roughly 2x for Windows) is far cheaper per core but you own the latency problem; AWS ap-northeast-1 (Tokyo) is the widely reported co-region for Binance with ~1–5 ms reported round-trips.

### Cited Findings
**Specialist forex VPS (Windows, broker-adjacent)**
- MetaQuotes built-in MetaTrader VPS (MQL5 hosting): Mini 15 USD/month (1-month term), Optimal 13 USD/month (3-month), Long 10.83 USD/month (6-month), Max 10 USD/month (12-month); "up to 3 GB of RAM, up to 16 GB of hard disk"; "More than thirty hosting points around the world"; "96% of broker servers can be accessed in less than 10 ms, while 84% — in less than 3 ms"; "0-5 ms latency" claim vs "from 100 ms" for a home PC; 24-hour free trial that auto-converts to paid. Accessed 2026-11-16. — [MQL5 VPS page](https://www.mql5.com/en/vps)
- ForexVPS.net (Windows Server 2025/22/19): Core $32/mo (2 vCPU, 4 GB RAM, 100 GB; list $40), Edge $48/mo (4 vCPU, 6 GB, 150 GB; list $60), Prime $64/mo (6 vCPU, 8 GB, 200 GB; list $80); annual billing $25.60/$38.40/$51.20 per month; "22 Locations included"; claims orders "reach the market in as little as 1ms"; 1 Gb/s; 14-day money-back; Dedicated server from $270/mo, GPU dedicated from $640/mo. Prices shown under a Black Friday "save 35%" promo (code BF2026); page is undated beyond that promo. Accessed 2026-11-16. — [ForexVPS pricing](https://www.forexvps.net/pricing/)
- FXVM: Virtual Desktop $14/mo, Lite VPS $20/mo, Basic VPS $29/mo, Advanced VPS $50/mo (standard rates per multiple directory listings); a Sept-2026 review lists regular prices Virtual Desktop $15, Lite $25, Basic $35, Advanced $50, High Freq VPS $69 with a 15% promo. Third-party listings, not the vendor page. — [Findstack FXVM pricing](https://findstack.com/products/fxvm/pricing); [GeekChamp FXVM review 2026](https://geekchamp.com/products/fxvm/review/)
- Beeks (BeeksFX retail VPS): Bronze $41.08/mo (1 vCPU, 2.6 GB RAM, 30 GB), Silver $72.89/mo (2 vCPU, 4.1 GB, 50 GB), Gold $128.55/mo (4 vCPU, 6.7 GB, 75 GB), as read from Beeks' pricing pages on 24 Sept 2026 by an aggregator — [CloudsPress Beeks listing](https://www.cloudspress.com/hosts/beeks-financial-cloud/); a competitor comparison cites Beeks Bronze at £32/month ex-VAT (1 vCPU, 2,560 MB RAM, 30 GB SSD) as of 24 Oct 2026 — [MassiveGRID vs Beeks](https://massivegrid.com/compare/massivegrid-vs-beeks.html); Beeks' own exchange-cloud store lists a Gold VM at £116.40 — [Beeks exchange-cloud store](https://kraken.exchange-cloud.beeksgroup.com/). Beeks expanded into Tokyo TY3 (Equinix) per Finance Magnates — [Finance Magnates](https://www.financemagnates.com/institutional-forex/technology/beeksfx-vps-expands-into-beeks-financial-cloud-launches-in-tokyo-ty3/). Beeks' own VPS page could not be fetched (returned an image), so the GBP prices for all tiers are unverified.
- Commercial Network Services (CNS): published pricing reported at $35–70/month (Value and Standard editions); data-centre location undisclosed in that review. Third-party. — [Brokerage Atlas CNS review](https://brokerage-atlas.pages.dev/setup/brokerage-hosting/reviews/commercial-network-services/)
- QuantVPS NY4 forex VPS: VPS Pro $99.99/mo, Dedicated $299.99/mo (vendor page). — [QuantVPS NY4](https://www.quantvps.com/ny4-forex-vps)
- NexusFi (futures community) anecdote: dedicated server in Chicago with sub-1 ms ping to CME at ~$200/month; a managed VPS "delivers 80-90% of co-location's latency benefit at 5-15% of the cost" (expert estimate, not measured). — [NexusFi colocation article](https://nexusfi.com/a/infrastructure/exchange-colocation-futures-traders)
- Latency tiers commonly cited by VPS vendors: home connection adds 50–200 ms, VPS in wrong city 20–80 ms, VPS in broker's city 1–10 ms, co-located <1 ms (vendor-authored guide). — [HostAdvice trading VPS guide](https://hostadvice.com/blog/web-hosting/vps/what-is-trading-vps/)
- Hidden add-ons: some plans add $10–25/month for Windows licensing. — [HostAdvice trading VPS guide](https://hostadvice.com/blog/web-hosting/vps/what-is-trading-vps/)

**Generic cloud**
- Hetzner Cloud "Cost-Optimized" (Linux, EU-Central FSN/NBG/HEL only, 20 TB traffic, ex-VAT): CX23 2 vCPU/4 GB/40 GB €5.99/mo; CX33 4 vCPU/8 GB/80 GB €8.99; CX43 8 vCPU/16 GB/160 GB €16.49; CX53 16 vCPU/32 GB/320 GB €29.99; Ampere CAX11/21/31/41 €6.49/€10.99/€21.49/€41.49. Page showed "currently unavailable" at capture time. Accessed 2026-11-16. — [Hetzner cost-optimized](https://www.hetzner.com/cloud/cost-optimized/). Hetzner raised prices for new orders from 15 June 2026 (e.g., CX23 €3.99→€5.49/€5.99; EU CPX22 reportedly €7.99→€19.49). — [Hetzner price adjustment page](https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/) (page returned 404 on direct fetch; figures via search snippet) and [third-party review](https://bestusavps.pages.dev/reviews/hetzner). Hetzner locations: Falkenstein, Nuremberg, Helsinki, Hillsboro OR, Ashburn VA, Singapore; US locations priced higher than Germany. — [Hetzner cloud](https://www.hetzner.com/cloud/)
- AWS EC2 t3.medium (2 vCPU, 4 GB) Linux on-demand in ap-northeast-1 (Tokyo): $0.0544/hr ≈ $39.7/month at 730 h before EBS/IPv4/data transfer; Windows roughly 2x Linux per a cost-estimator (approximation, not an AWS quote). — [DoiT t3.medium Tokyo](https://www.doit.com/compute/spot/ap-northeast-1/t3.medium); [issoh.co.jp](https://www.issoh.co.jp/md/tech/17857); [UtilityForge estimator](https://utilityforge.pages.dev/aws-ec2-cost-estimator/)
- Binance location: Glassnode's latency monitor describes Binance WebSocket/FIX endpoints as going "straight to AWS Tokyo" — [Glassnode HyperLatency](https://hyperlatency.glassnode.com/cex/about); CCXT's blog measures Tokyo at ~2 ms with 1–3 ms TCP handshake — [CCXT "How far is your exchange"](https://docs.ccxt.com/blog/how-far-is-your-exchange); a VPS vendor reports 1–2 ms from its Japan VPS — [EDIS Global](https://edisglobal.com/blog/crypto-trading-vps); one blog claims Binance USDT-M futures matching is in us-east-1 — [nikhilpadala blog](https://nikhilpadala-site.pages.dev/blog/exchange-co-location-cloud) — contradicting the Tokyo consensus; Binance does not officially disclose locations per [Valebyte](https://valebyte.com/en/blog/vps-for-binance-setting-up-a-trading-bot-with-minimal-latency/).
- Windows is required for MetaTrader VPS use: all specialist forex VPS plans above are Windows Server; ForexVPS lists MT4/MT5/cTrader support and "Core can run up to 3 MetaTraders." — [ForexVPS pricing](https://www.forexvps.net/pricing/)

### Inferences
- For MT5-based FX scalping, the cheapest credible broker-adjacent option is MetaQuotes' own VPS at $10–15/mo (Linux-free, no Windows licence to manage, 3 GB RAM cap means no Python/ML side-car on that box). A full Windows VPS from ForexVPS/FXVM/Beeks ($30–65/mo) is needed if you want to run a Python/Rust engine next to MT5.
- For crypto (Binance/Bybit), a Linux box in AWS ap-northeast-1 (Tokyo) is the standard; budget ~$40–80/mo for a t3.medium/t3.large-class instance with EBS. Hetzner (EU/US/Singapore only, no Tokyo) adds tens of ms to Binance; fine for non-latency-critical bots but wrong for scalping. Equinix TY3 Beeks VPS is the premium choice for Binance-adjacent Windows.
- Expect to add $10–25/mo for Windows licensing on generic clouds; specialist forex VPS bundle it.

### Gaps
- Could not fetch official Beeks or CNS pricing pages (image/404); GBP/USD figures are from aggregators dated Sept–Oct 2026.
- No official AWS Windows on-demand price for Tokyo retrieved; the 2x multiplier is an estimate.
- No vendor publishes measured ms-to-broker tables that I could cite (ForexVPS points to a broker-latency lookup page not retrieved).

## Local hardware for research/model training, cloud GPU rental, and tick-data storage sizes

### Takeaway
Research/training for scalping-scale models (gradient-boosted trees on tick features) runs fine on a mid-range CPU box with 32–64 GB RAM; GPUs are optional and cheap to rent on demand (RTX 4090 ~$0.34–0.74/hr, A100 80GB ~$1.39–1.89/hr, H100 ~$2–4/hr on RunPod in mid-2026). Compressed raw FX tick data is on the order of hundreds of MB to low single-digit GB per symbol-year; platform-exported formats and L2 order-book data are 10x+ larger.

### Cited Findings
- RunPod (mid-2026, third-party snapshots of runpod.io pricing): RTX 4090 from $0.34/GPU-hr Community Cloud (Secure Cloud $0.69–0.74/hr, Aug 2026); A100 80GB PCIe Community $1.39/hr (June 2026), $1.79–1.89/hr Secure (Oct 2026); H100 80GB $1.99/hr on-demand per RunPod page updated July 2026, $2.89/hr PCIe (Aug 2026 snapshot), $3.99 on one Oct-2026 comparison. — [RunPod pricing](https://www.runpod.io/gpu-cloud/pricing); [Hivenet RunPod guide](https://www.hivenet.com/post/runpod-pricing-complete-guide-to-gpu-cloud-costs); [Thunder Compute comparison](https://www.thundercompute.com/blog/Runpod-pricing-vs-thunder-compute); [computeprices.com RTX4090](https://computeprices.com/providers/runpod/gpus/rtx4090); [dev.to RunPod vs Vast vs Lambda 2026](https://dev.to/jovan_chan_9500711396d4e6/cloud-gpu-pricing-compared-runpod-vs-vastai-vs-lambda-labs-2026-35bn)
- FX tick data sizes (forum anecdotes, units inconsistent): 1 year of EURUSD ticks = 219.37 MB in one Tickstory user report — [Tickstory support](https://support.tickstory.com/viewtopic.php?p=9377); Dukascopy compressed database ≈ 25–30 GB for 10+ years across 30+ symbols, CSV 3–10x larger — [Dukascopy forum](https://www.dukascopy.com/swiss/english/forex/jforex/forum/viewtopic.php?p=77954); 1 year EURJPY exported to MT4 format = 10 GB — [Tickstory support](https://support.tickstory.com/viewtopic.php?p=12367); 1 month GBPUSD tick ≈ 1 GB (format unstated) — [StrategyQuant forum](https://strategyquant.com/forum/topic/tick-data-size/)
- Crypto L2: CryptoHFTData cites "150M+ daily updates" for its free order-book API (a volume, not a size) — [CryptoHFTData](https://www.cryptohftdata.com/datasets/crypto-orderbook-data); Binance publishes T_DEPTH (tick-level L2 from matching-engine logs, "no data gaps") and S_DEPTH snapshot files, snapshots from 2020-01, no file sizes given — [Binance FAQ](https://www.binance.com/ro/support/faq/e707685b4e0f408fa7c1b9ccd8ea7aa9); Tardis' Binance Spot incremental book is aggregated at 100 ms intervals, USDS-M futures include all L2 updates — [Tardis Binance Spot](https://docs.tardis.dev/historical-data-details/binance); [Tardis Binance Futures](https://docs.tardis.dev/historical-data-details/binance-futures)
- QuantConnect's L-MICRO live node is 1 core/0.5 GB RAM (algorithm must average <80% of 410 MB) — an indication of how small a pure execution process can be. — [QuantConnect live deployment docs](https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/deployment)

### Inferences
- Storage plan: for 3–5 FX pairs × 5 years of bid/ask ticks, budget ~5–20 GB compressed (parquet/zstd) and 50–200 GB if you keep CSV or MT5 .hcc exports. For crypto L2 on a handful of perps, assume ~1–5 GB/day raw per liquid pair (inference from "150M+ updates/day"; not measured) — so a 1–2 TB NVMe plus cold object storage is sensible at the "serious" tier.
- Local box: any modern 8–16 core CPU with 32–64 GB RAM and 1–2 TB NVMe (~US$1,000–2,000 one-off) covers feature engineering in polars and LightGBM/XGBoost training; rent GPU hours only for deep-learning experiments (a 100-hour month on a 4090 ≈ $35–75).

### Gaps
- No authoritative measured GB/day for Binance BTCUSDT L2 was found; sizes above are inferred.
- No 2026 source on desktop hardware pricing was searched (out of scope for sourced numbers).

## Market data: free vs paid tick/order-book sources and what scalping needs

### Takeaway
For FX and crypto a solo developer can get tick-level bid/ask history free (Dukascopy via dukascopy-node/tickterial, MT5 broker history, Binance data.binance.vision aggTrades/trades plus futures bookDepth) and free real-time WebSocket feeds from crypto exchanges; paid retail tiers start at $49/mo (Massive/Polygon Currencies Starter real-time FX+crypto), ~$50–900/mo (Tardis.dev L2 crypto, per third parties), $199/mo (Databento Standard incl. live CME/equities), $108/mo + exchange fees (IQFeed core), with CME non-pro exchange fees at $1.55–1.60/mo top-of-book or $12.10–12.50/mo depth per exchange.

### Cited Findings
**Free**
- Dukascopy tick data is downloadable free via community tools; each record carries both bid and ask (forum moderator), tools expose bid/ask/mid selection. — [theorycraft-trading/dukascopy CLI](https://github.com/theorycraft-trading/dukascopy); [dukascopy-node](https://docsearch.algolia.com/mcp/docs/repo/leo4815162342/dukascopy-node); [go-duka](https://github.com/Adyzng/go-duka); [Dukascopy forum](https://www.dukascopy.com/swiss/english/forex/jforex/forum/viewtopic.php?p=4301). Data-quality caveats raised in forums (sparse ticks, estimated volumes). — [NinjaTrader forum thread](https://forum.ninjatrader.com/forum/ninjatrader-7/platform-technical-support/32700-historical-high-quality-fx-tick-data?p=553164)
- Binance public data (data.binance.vision): free daily/monthly files for spot/USD-M/COIN-M aggTrades, trades, klines, bookTicker; bookDepth only for USD-M and COIN-M futures (not spot); spot timestamps in microseconds from 2025-01-01; official download scripts in binance-public-data repo. — [binance-public-data GitHub](https://github.com/binance/binance-public-data/); [Binance FAQ: download historical data](https://www.binance.com/en-BH/support/faq/how-to-download-historical-market-data-on-binance-5810ae42176b4770b880ce1f14932262). Full tick-level order-book history (T_DEPTH) is API-access for VIP 1+ per Binance's futures order-book page (noted in search; unverified for 2026). — [Binance FAQ](https://www.binance.com/ro/support/faq/e707685b4e0f408fa7c1b9ccd8ea7aa9)
- Tardis.dev free access: first day of every month free for every exchange and data type (CSV or replay API, no key); one-month free trial covering days 1–10 of the previous month with 20 GB transfer, no card. — [Tardis billing FAQ](https://docs.tardis.dev/faq/billing-and-subscriptions)
- Databento: $125 free credits on signup (expire after 6 months, one set per team). — [Databento pricing](https://databento.com/pricing)
- Massive (formerly Polygon.io; polygon.io/pricing now 301-redirects to massive.com) Currencies Basic: $0/mo, all forex+crypto tickers, 5 API calls/min, 2 years history, end-of-day only, minute aggregates. — [Massive currencies pricing](https://massive.com/currencies)

**Paid**
- Massive Currencies Starter: $49/mo (annual saves 20%), unlimited API calls, 10+ years history, real-time, crypto trades, quotes, WebSockets, flat files, second aggregates. — [Massive currencies pricing](https://massive.com/currencies). Massive Stocks Advanced: $199/mo (individual), real-time, 20+ years history, websockets. — [Massive pricing](https://massive.com/pricing)
- Databento: Standard $199/mo (monthly; live data, no licence fees, 16+ yrs L0 history, 1 yr L1, 1 month L2/L3); Plus $1,750/mo licence (annual contract); Unlimited $4,500/mo; usage-based historical pay-as-you-go for CME/CBOT/NYMEX/COMEX (per-GB rates not shown; "<$0.01" default estimator); usage-based live billed per message plus pass-through licence fees. — [Databento pricing](https://databento.com/pricing)
- Tardis.dev: plans by data scope (Perpetuals, Options, Spot, Derivatives, All Exchanges; no per-exchange pricing; Coinbase only in All Exchanges) × subscription type (Academic, Solo, Professional, Business); monthly billing gives 4 months history, quarterly 12 months, yearly 4 years (Business: all); prices only in the order form (not retrieved). — [Tardis billing FAQ](https://docs.tardis.dev/faq/billing-and-subscriptions). Third parties: $50–900/mo range — [AlternativeTo](https://alternativeto.net/software/tardis-dev/about); Academic $49/mo — [web-5gv listing](https://web-5gv.pages.dev/resources/tardis-dev); order book is tick-level L2, L3 on some venues (competitor page, data as of July 2025) — [CryptoHFTData vs Tardis](https://www.cryptohftdata.com/vs/tardis-dev)
- IQFeed (DTN, prices as of 1 Dec 2025): startup fee $50; Core Service $108.15/month; Forex Only Service $50.47/month; exchange fees extra and non-refundable. — [DTN core service fees](https://iqhelp.dtn.com/core-service-fees/); [DTN "how much does your data feed cost"](https://iqhelp.dtn.com/how-much-does-your-data-feed-cost/)
- CME Group non-professional fees (official fee lists): January 2026 list — top-of-book $1.55/device/exchange, all-4-exchange bundle $4.65; depth-of-market $12.10/device/exchange, bundle $36.50 — [CME Jan 2026 fee list](https://www.cmegroup.com/market-data/files/january-2026-market-data-fee-list.pdf); June 2026 list top-of-book $1.60 — [CME June 2026 fee list](https://www.cmegroup.com/market-data/files/june-2026-market-data-fee-list.pdf); a January 2027 list ($12.50 depth, $1.60 TOB) is published but not yet in effect — [CME Jan 2027 fee list](https://www.cmegroup.com/market-data/files/january-2027-market-data-fee-list.pdf). Broker resale differs: AMP CME Level 2 bundle $45; TT $14/session. — [AMP data fees](https://www.ampfutures.com/trading-info/platform-data-fees/); [TT market data pricing](https://tradingtechnologies.com/resources/pricing/pricing-details/marketdata-user/)
- dxFeed retail: no single published price; sold via partner platforms; "from $19/month"; Bookmap lists dxFeed Nasdaq depth $40/mo, EDGX depth $30/mo, futures $37/mo per exchange; raw data access excluded from retail; billed 1 month at a time. — [choose.dxfeed.com](https://choose.dxfeed.com/); [Bookmap packages comparison](https://bookmap.com/packages-comparison); [dxFeed retail billing](https://dxfeed-retail.zendesk.com/hc/en-us/articles/7699534444695-Billing-process)
- Kaiko: quote-only pricing (no published retail price); offers tick-level L2 history since 2014 and L1/L2 streaming. — [Datarade Kaiko listing](https://www.datarade.ai/data-products/kaiko-order-book-metric-real-time-ob-depth-breakdown-kaiko); [Kaiko Medium announcement](https://medium.com/@kaikodata/kaiko-launches-historical-tick-by-tick-order-book-data-e34792ce6c01)
- QuantConnect Free plan includes Equity, Indexes, Forex, Crypto, Futures, Options datasets for cloud research/backtests; Futures Live Feed is an add-on on Researcher. — [QuantConnect pricing](https://www.quantconnect.com/pricing)

### Inferences
- What scalping needs: tick-level bid/ask (FX) or trades + L2 deltas (crypto) with exchange timestamps, because fills, spread and queue position dominate PnL at sub-minute holding periods. For FX via an MT5 broker, the broker's own tick stream (free) is what you will actually trade against; Dukascopy ticks are good for research but are not your broker's prices. For crypto, exchange WebSocket feeds (free) are the live source; Tardis or Binance T_DEPTH is for backtesting L2.
- Monthly data budget by tier: hobby $0 (Dukascopy + MT5 ticks + Binance public data + Tardis first-day-of-month); serious $49–199 (Massive Currencies Starter or one Tardis Solo plan, or Databento Standard if trading CME futures); semi-pro $200–500+ (Databento Standard + CME non-pro depth bundle ~$36.50 + Tardis Professional).

### Gaps
- Tardis.dev's actual plan prices are only in its order form and were not retrieved; the $50–900 range is third-party.
- Kaiko has no published prices.
- Could not retrieve a Polygon/Massive crypto-specific tier beyond the combined Currencies plan.

## Broker/exchange account: deposits, commissions, spreads, crypto fees, capital needed

### Takeaway
ECN/raw FX accounts cost ~$3.0–3.5 per lot per side (IC Markets Raw $3.50 MT4/5, $3.00 cTrader; Pepperstone Razor $3.50 or £2.25 per side) on top of raw EURUSD spreads averaging ~0.1–0.2 pips, i.e. ~$8–9 round-turn per standard lot; minimum deposit at IC Markets is $200 (one official EU table shows $0). Binance VIP0 fees are 0.10%/0.10% spot (0.075% with BNB) and 0.02% maker / 0.05% taker USD-M futures — crypto taker scalping costs 5–10 bps round-trip, which is 5–10x FX raw-account costs in bps terms.

### Cited Findings
- IC Markets Raw Spread: USD 3.50 per lot per side ($7 round-turn) on MT4/MT5; cTrader $3.00 per side ($6 round-turn); spreads "from 0.0 pips"; minimum deposit $200 on the global site, while the EU overview table shows $0 — conflicting. — [IC Markets start forex trading](https://www.icmarkets.com/global/en/start-forex-trading); [IC Markets EU account overview](https://www.icmarkets.eu/trading-accounts/overview). Average EURUSD Raw spread ~0.1 pips per third-party review. — [FXScouts IC Markets](https://fxscouts.com/broker/icmarkets/). Note: icmarkets.com now redirects to ic.com, which returned 404 for the accounts page on 2026-11-16.
- Pepperstone Razor: UK site "from £2.25 per lot, per side"; global site "from $3.50 per lot, per side" / "3.5 USD per 1 standard FX lot per side"; cTrader "6 USD roundtrip"; Razor EURUSD raw spread minimum 0 pts. — [Pepperstone UK spreads](https://pepperstone.com/uk/forex-trading/spreads); [Pepperstone pricing](https://pepperstone.com/en-gb/ways-to-trade/pricing); [Pepperstone costs and fees](https://pepperstone.com/en/trading/costs-and-fees). Third-party test (Aug 2026): Razor average 0.1 pips, measured 0.19 pips; round-turn ≈ US$8.90 on Razor (spread + $7 commission) vs US$12.10 on Standard (no commission). — [CompareForexBrokers Razor vs Standard](https://www.compareforexbrokers.com/reviews/pepperstone-review/razor-vs-standard-account). Pepperstone's main spreads/commissions page returned 403 on fetch; XAUUSD average spread not retrieved.
- Binance spot VIP0: 0.100% maker / 0.100% taker; 0.075%/0.075% with BNB discount; VIP1 requires ≥1,000,000 USD 30-day volume and ≥5 BNB (VIP1: 0.090%/0.100%). Accessed 2026-11-16. — [Binance fee schedule](https://www.binance.com/en/fee/schedule)
- Binance USD-M futures Regular User: 0.02% maker / 0.05% taker (Binance FAQ worked examples); BNB discount 10% on futures. — [Binance Futures fee FAQ](https://www.binance.com/support/faq/360033544231); [Finder Binance futures fees](https://www.finder.com/cryptocurrency/trading/binance-futures-fees)
- CME non-pro data fees as above ($1.55–1.60 TOB; $12.10 depth per exchange) apply if trading futures. — [CME Jan 2026 fee list](https://www.cmegroup.com/market-data/files/january-2026-market-data-fee-list.pdf)

### Inferences
- FX cost per round-turn on a raw account ≈ 0.7 pip commission-equivalent + 0.1–0.2 pip spread ≈ 0.8–0.9 pips/lot ($8–9). A scalper targeting 2–3 pips gross per trade pays ~30–45% of gross to costs; the strategy must clear ~1 pip net edge per trade after slippage. With $1,000 and 0.1-lot sizing, $0.90 cost/trade and e.g. 50 trades/day ≈ $45/day costs — infeasible at $1k. At $5k–10k with 0.5–1 lot, costs become proportional and infrastructure ($50–150/mo) is <2% of capital.
- Crypto: taker round-trip ≈ 10 bps on USD-M (0.05%×2), maker round-trip 4 bps (0.02%×2), spot 15–20 bps. On BTC at $100k, 10 bps = $100 per $100k notional; scalping must be maker-biased (post-only) or exploit >10 bps moves. Realistic minimum capital for crypto perps scalping to make infrastructure meaningful: ~$5k; for FX raw-account scalping: ~$5k–10k (swap-free is irrelevant for intraday scalping since positions don't roll).
- Recommended minimum trading capital (to cover costs and infrastructure sensibly): hobby $1k–2k (expect negative expectancy after costs; treat as tuition), serious $10k, semi-pro $25k–50k.

### Gaps
- Pepperstone/IC Markets XAUUSD typical raw spread not retrieved (403/404 on official pages).
- Swap-free (Islamic) availability and fees at IC/Pepperstone not retrieved.
- No source found quantifying "capital needed to make scalping worthwhile"; the figures above are inferences from fee math.

## Software stack recommendations and 2026 state of key libraries

### Takeaway
In 2026 the actively maintained open-source core for a solo scalper is NautilusTrader (Rust-native engine, Python control plane, LGPL-3.0, Python 3.13–3.15, 1.231.0 final 1.x and 2.0.0rc4 pre-releases; stable live adapters for Binance, Bybit, OKX, Coinbase, Kraken, Deribit, dYdX, Hyperliquid, Interactive Brokers, Databento, Tardis), with Freqtrade (monthly releases, 2026.10) for simple crypto bots and Hummingbot (v2.15.1, June 2026) for crypto market making; Backtrader is effectively unmaintained; vectorbt PRO costs $25/mo, $225/yr or $500 lifetime; QuantConnect Researcher is $84/mo.

### Cited Findings
- NautilusTrader: "Production-grade Rust-native trading engine with deterministic event-driven architecture"; LGPL-3.0; Python 3.13–3.15; Rust 1.100.0 toolchain; v2 line published as 2.0.0rcN, latest stable PyPI still 1.x. Stable integrations: AX Exchange, Betfair, Binance, Blockchain (DeFi data), Bybit, Coinbase, Databento, Deribit, Derive, dYdX, Hyperliquid, Interactive Brokers, Kraken, Lighter, Lighter on Robinhood, OKX, Polymarket, Tardis; beta: CoinAPI, FinFeed, Kalshi. — [nautilus_trader GitHub](https://github.com/nautechsystems/nautilus_trader); [NautilusTrader integrations docs](https://nautilustrader.io/docs/latest/integrations). Release notes: 1.231.0 "final 1.x release before the v2 transition"; 2.0.0rc4 is latest as of early Sept 2026 per CCXT's comparison; 1.226.0 added a Rust Interactive Brokers adapter and ADL/liquidation detection for Binance/Bybit/dYdX; Bybit hedge-mode position IDs in 1.227.0. — [newreleases 1.231.0](https://newreleases.io/project/github/nautechsystems/nautilus_trader/release/v1.231.0); [newreleases 2.0.0rc4](https://newreleases.io/project/github/nautechsystems/nautilus_trader/release/v2.0.0rc4); [newreleases 1.226.0](https://newreleases.io/project/github/nautechsystems/nautilus_trader/release/v1.226.0); [CCXT vs NautilusTrader](https://docs.ccxt.com/docs/comparisons/ccxt-vs-nautilustrader); [PyPI nautilus-trader](https://pypi.org/project/nautilus-trader)
- Hummingbot: v2.15.0 and v2.15.1 release notes dated June 17, 2026; Gateway v2.15.1 on June 22, 2026; v2.14.0 announced April 2026; >19,000 stars/4,800 forks mid-2026. — [Hummingbot 2.15.1 notes](https://hummingbot.org/release-notes/2.15.1/); [Hummingbot 2.15.0 notes](https://hummingbot.org/release-notes/2.15.0/); [Hummingbot GitHub](https://github.com/hummingbot/hummingbot)
- Freqtrade: year-based monthly releases; latest 2026.10 on PyPI (aggregator listing, "published 15 days ago"); 2025.11 and 2025.8 release notes exist. — [ecosyste.ms freqtrade](https://summary.ecosyste.ms/projects/357309); [newreleases freqtrade 2025.11](https://newreleases.io/project/github/freqtrade/freqtrade/release/2025.11); [Freqtrade GitHub via Greptile](https://www.greptile.com/grepository/freqtrade)
- Backtrader: "no longer maintained" per a framework guide; a 2026 review says community forks are maintained, code stable, "not in active development." — [TradingStrategy.ai frameworks list](https://tradingstrategy.ai/docs/learn/algorithmic-trading-frameworks.html); [aiindigo Backtrader review 2026](https://aiindigo.com/blog/backtrader-review-2026-the-open-source-standard-for-quant-trading); [Wilmott forum](https://forum.wilmott.com/viewtopic.php?p=876767)
- backtesting.py: described as actively maintained, backtesting-only (no live trading). — [TradingStrategy.ai frameworks list](https://tradingstrategy.ai/docs/learn/algorithmic-trading-frameworks.html)
- vectorbt PRO: Monthly $25; Annual $18.75/mo ($225 billed annually); Lifetime $500 one-time; private GitHub repo + Discord; individual membership is personal/non-commercial; current release v2026.10.5 "includes agent skills"; open-source vectorbt remains MIT. — [vectorbt.pro membership](https://vectorbt.pro/become-a-member); [vectorbt.pro FAQ](https://vectorbt.pro/faq); [vectorbt README](https://cdn.jsdelivr.net/gh/polakowo/vectorbt@master/README.md)
- QuantConnect (LEAN cloud): Free $0 (1 backtest node, 0 live nodes); Researcher $84/mo or $888/yr (2 backtest, 2 live, 1 research node); Team $168/mo ($1,728/yr, 2–10 users); Trading Firm $480/mo ($4,992/yr); Institution $1,272/mo ($12,912/yr). Live nodes: L-MICRO 1 core/0.5 GB, L1-1, L1-2, L2-4, L8-16-GPU; node prices not retrievable from the page (loaded dynamically). Dedicated live servers need 12-month commitment; "Fast Track Your Launch" from $4,800; 1 USD = 100 QCC. — [QuantConnect pricing](https://www.quantconnect.com/pricing); [QuantConnect pricing.md](https://www.quantconnect.com/pricing.md); [QuantConnect live deployment docs](https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/deployment). A 2026 third-party review claims Researcher $60 and L-MICRO $24/mo — conflicts with the official $84 — [NYC Servers QuantConnect review](https://newyorkcityservers.com/blog/quantconnect-review).
- CCXT publishes a maintained comparison with NautilusTrader and a latency map of exchanges by region. — [CCXT vs NautilusTrader](https://docs.ccxt.com/docs/comparisons/ccxt-vs-nautilustrader); [CCXT latency blog](https://docs.ccxt.com/blog/how-far-is-your-exchange)
- NautilusTrader has an official tutorial for backtesting on Binance order-book (L2) data. — [NautilusTrader backtest orderbook Binance tutorial](https://nautilustrader.io/docs/latest/tutorials/backtest_orderbook_binance/)

### Inferences
**Recommended stack (solo developer, 2026)**

| Layer | Recommendation | Why | Alternatives / status |
|---|---|---|---|
| Language | Python 3.13+ for research & control plane; Rust only if you need a custom hot path (NautilusTrader already gives a Rust core) | Nautilus runs the event loop/order routing in Rust; you write strategies in Python | Go / C++ hand-rolled engines: more work, no adapter ecosystem |
| Live/backtest engine | NautilusTrader (1.231.0 stable; 2.0.0rcN) | Same code for backtest and live; stable adapters for Binance, Bybit, OKX, Coinbase, Kraken, Deribit, Hyperliquid, dYdX, IB, Databento, Tardis; nanosecond event-driven backtests on L2 | Freqtrade (crypto, simpler, monthly releases); Hummingbot 2.15.x (crypto MM); LEAN/QuantConnect ($84/mo cloud, MT-style broker coverage); Backtrader = legacy, avoid |
| MT5 FX route | MetaTrader 5 EA (MQL5) on MetaQuotes VPS $10–15/mo, or Python MetaTrader5 package on a Windows VPS | Nautilus has no MT5 adapter; MT5 remains the retail-FX execution standard | cTrader Open API (IC/Pepperstone) if you want Linux-only |
| Vectorized research | vectorbt (MIT) or vectorbt PRO ($25/mo / $500 lifetime) + polars + numpy | Fast parameter sweeps before event-driven validation | backtesting.py (simple, maintained) |
| ML | LightGBM/XGBoost on polars features; PyTorch only when GPU-rented | Tree models dominate tabular tick features; GPU rental $0.34–2/hr covers DL experiments | scikit-learn for baselines |
| Storage | Parquet (zstd) on local NVMe + Nautilus ParquetDataCatalog; ArcticDB or QuestDB/ClickHouse/TimescaleDB if you need SQL over ticks | Parquet is free, portable, and what Nautilus/Databento/Tardis tooling emits | ClickHouse for multi-TB L2 |
| Messaging | Redis (Nautilus cache/message bus backend) or ZeroMQ for MT5↔Python bridges; NATS optional | Nautilus supports Redis-backed cache/bus; ZMQ is the standard MT5 bridge pattern | Kafka is overkill solo |
| Monitoring | Prometheus + Grafana (self-hosted, free) + Telegram bot alerts | Zero licence cost; Freqtrade/Hummingbot ship Telegram integrations | Uptime pings via cron |
| Packaging | Docker Compose on a Linux VPS; systemd for the bot process | Reproducible deploys; Nautilus/Freqtrade/Hummingbot all publish Docker images | — |
| LLM/news | Batch/offline sentiment via cheap API (e.g. Claude Haiku 5.5 $0.10/$0.50 per MTok) feeding a slow-moving feature, never in the order path | TTFT is 350 ms+; see next section | Local small model on the research box |

(Items in the "Storage", "Messaging", "Monitoring" rows are standard practice; I did not fetch 2026 release pages for TimescaleDB/QuestDB/ClickHouse/ArcticDB/ZeroMQ/NATS/Grafana, so maintenance status of those is from general knowledge, not cited.)

### Gaps
- QuantConnect per-node prices (L-MICRO etc.) were not retrievable (dynamic page); one unverified third-party says $24/mo.
- No 2026 primary-source check on Jesse, Zipline-reloaded, QuantRocket, ArcticDB, QuestDB, TimescaleDB, ClickHouse, ZeroMQ, NATS maintenance status.
- Tardis plan prices (needed for the Nautilus Tardis adapter) are not public outside the order form.

## AI/LLM API costs for sentiment/news and why LLMs stay off the execution hot path

### Takeaway
Per-million-token prices in late 2026 span ~$0.05–$10 input / $0.40–$50 output across major providers (Claude Haiku 5.5 $0.10/$0.50; Sonnet 5.5 $2/$10; Opus 5.5 $4/$20; Fable 5.1 $10/$50; GPT-5 nano $0.05/$0.40; Gemini 3.1 Flash-Lite $0.25/$1.50), so a news-sentiment side-process costs dollars to tens of dollars per month — but time-to-first-token of 0.35 s+ (p99 up to 5x p50) makes LLM calls three to five orders of magnitude slower than a microsecond-to-millisecond scalping decision path.

### Cited Findings
- Anthropic official pricing (accessed 2026-11-16): Claude Haiku 5.5 $0.10 in / $0.50 out per MTok (prompts ≤100k tokens; $0.50/$2.50 over 100k); Haiku 4.5 $1/$5; Sonnet 5.5 $2/$10; Sonnet 5 $2/$10; Sonnet 4.6/4.5 $3/$15; Opus 5.5 $4/$20; Opus 5 / 4.8 / 4.7 / 4.6 / 4.5 $5/$25; Fable 5.2 $8/$40; Fable 5.1 $10/$50; cache hits $0.10–$1/MTok; Batch API discount applies. — [Claude platform pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- Third-party cross-provider snapshot (Nov 2026, BenchLM; model names unverified against vendors): GPT-5 nano $0.05/$0.40; GPT-5.4 $2.50/$15; GPT-5.5 Pro $30/$180; Gemini 3.5 Flash $1.50/$9; Gemini 3.1 Flash-Lite $0.25/$1.50; DeepSeek V3.2 $0.14/$0.28. — [BenchLM LLM pricing](https://benchlm.ai/llm-pricing); [Fungies LLM pricing comparison 2026](https://fungies.io/llm-api-pricing-comparison-2026-openai-claude-gemini-deepseek/)
- Latency: fastest API models reach ~0.35 s time-to-first-token; Artificial Analysis snapshot across 29 models ranged 0.4 s–159.2 s; TTFT includes network, gateway, queueing and prefill; p99 can be 5x p50. — [Kunal Ganglani LLM latency benchmarks 2026](https://www.kunalganglani.com/blog/llm-latency-benchmark-optimization.md); [Baseten inference book: latency](https://www.baseten.co/inference-engineering/book/01-prerequisites/measuring-latency-and-throughput/); [GeneralCompute TTFT explainer](https://www.generalcompute.com/blog/ai-inference-latency-explained-ttft-tps-and-how-to-optimize-them)
- Trading-side latency reference: VPS vendors quote 1–10 ms to broker in the right city and <1 ms co-located; MetaQuotes claims 84% of brokers <3 ms. — [HostAdvice guide](https://hostadvice.com/blog/web-hosting/vps/what-is-trading-vps/); [MQL5 VPS](https://www.mql5.com/en/vps)

### Inferences
- Cost magnitude: scoring 5,000 headlines/day at ~300 tokens each with Haiku 5.5 ≈ 1.5M input tokens/day ≈ $0.15/day input + small output ≈ $5–10/month; with Sonnet 5.5 ≈ $90–120/month. Budget $0–20/mo (hobby), $20–100/mo (serious), $100–300/mo (semi-pro, multiple models/backfills).
- Architecture: run LLM scoring asynchronously (batch API where possible, 50% cheaper) into a feature store/Redis key; the execution loop reads the cached score. A 350 ms–2 s call in the order path would exceed the entire tick-to-order budget by 100–1000x and expose you to adverse selection.

### Gaps
- No source directly states "LLMs unsuitable for trading hot path"; the conclusion is derived from TTFT data vs VPS latency figures.
- OpenAI/Google official pricing pages were not fetched; those figures are from aggregators.

## Total budget estimates: itemized monthly costs at three tiers, one-off costs, minimum capital

### Takeaway
A hobby/MVP FX-or-crypto scalping bot can run for ~$10–30/month (MetaQuotes VPS or a Hetzner box, free data, free open-source stack); a serious retail setup lands at ~$150–350/month (broker-adjacent Windows VPS or AWS Tokyo, one paid data feed, vectorbt PRO, GPU hours, LLM API); a semi-professional setup is ~$600–1,300/month (dedicated/Equinix server, Databento Standard + CME depth, Tardis, QuantConnect Researcher or dedicated infra, more GPU/LLM). One-off costs are dominated by a research workstation ($0 if you already have one, $1,000–2,500 otherwise) and minimum trading capital ($1–2k / $10k / $25–50k).

### Cited Findings
(All line items trace to the sources cited in the sections above; key anchors repeated here.)
- MetaQuotes VPS $10–15/mo — [MQL5 VPS](https://www.mql5.com/en/vps); Hetzner CX23 €5.99, CX33 €8.99, CX43 €16.49 — [Hetzner](https://www.hetzner.com/cloud/cost-optimized/); AWS Tokyo t3.medium Linux ≈ $39.7/mo — [issoh.co.jp](https://www.issoh.co.jp/md/tech/17857); ForexVPS Core $32 / Edge $48 / Prime $64 (promo) — [ForexVPS](https://www.forexvps.net/pricing/); Beeks Bronze $41.08 / Silver $72.89 / Gold $128.55 — [CloudsPress](https://www.cloudspress.com/hosts/beeks-financial-cloud/); ForexVPS dedicated from $270/mo — [ForexVPS](https://www.forexvps.net/pricing/); QuantVPS NY4 dedicated $299.99 — [QuantVPS](https://www.quantvps.com/ny4-forex-vps)
- Massive Currencies Starter $49/mo — [Massive](https://massive.com/currencies); Databento Standard $199/mo — [Databento](https://databento.com/pricing); IQFeed core $108.15/mo + $50 startup — [DTN](https://iqhelp.dtn.com/core-service-fees/); CME non-pro depth $12.10/exchange, bundle $36.50 — [CME](https://www.cmegroup.com/market-data/files/january-2026-market-data-fee-list.pdf); Tardis ~$50–900/mo (third-party) — [AlternativeTo](https://alternativeto.net/software/tardis-dev/about)
- vectorbt PRO $25/mo or $500 lifetime — [vectorbt.pro](https://vectorbt.pro/become-a-member); QuantConnect Researcher $84/mo — [QuantConnect](https://www.quantconnect.com/pricing)
- RunPod RTX 4090 $0.34–0.74/hr; A100 $1.39–1.89/hr; H100 $1.99–3.99/hr — [RunPod](https://www.runpod.io/gpu-cloud/pricing); [Hivenet](https://www.hivenet.com/post/runpod-pricing-complete-guide-to-gpu-cloud-costs)
- Claude Haiku 5.5 $0.10/$0.50; Sonnet 5.5 $2/$10 per MTok — [Claude pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- IC Markets min deposit $200; $3.50/lot/side — [IC Markets](https://www.icmarkets.com/global/en/start-forex-trading); Binance USD-M 0.02%/0.05% — [Binance FAQ](https://www.binance.com/support/faq/360033544231)

### Inferences
**Monthly budget by tier (USD, Nov 2026 prices; € converted ~1:1.1)**

| Line item | Hobby / MVP | Serious retail | Semi-professional |
|---|---|---|---|
| Hosting / VPS | MetaQuotes VPS $10–15 (FX) or Hetzner CX23–CX33 $7–10 (crypto, EU latency) | ForexVPS Edge $48 or Beeks Silver $73 (Windows, LD4/NY4) **or** AWS Tokyo t3.medium/large Linux $40–80 (Binance) | Dedicated Equinix-adjacent server $270–300 (ForexVPS/QuantVPS) + AWS Tokyo instance $80 + backup VPS $30 |
| Windows licence (if generic cloud) | $0 (MetaQuotes/Hetzner Linux) | $0–25 | $0–25 |
| Market data | $0 (Dukascopy, MT5 ticks, Binance public data, Tardis free days, Massive Basic) | $49 (Massive Currencies Starter) **or** ~$50–150 Tardis Solo (3rd-party est.) | Databento Standard $199 + CME non-pro depth bundle $36.50 + Tardis Pro ~$200–500 (est.) |
| Research/backtest software | $0 (NautilusTrader, vectorbt OSS, Freqtrade) | vectorbt PRO $25 | vectorbt PRO $25 + QuantConnect Researcher $84 (optional) |
| GPU rental | $0 | 50 h × RTX 4090 @ $0.34–0.74 ≈ $17–37 | 100 h × A100/H100 @ $1.4–4 ≈ $140–400 |
| LLM API (news/sentiment) | $0–10 (Haiku 5.5) | $20–60 (Haiku/Sonnet mix) | $100–300 (Sonnet/Opus, backfills) |
| Monitoring/alerts | $0 (Grafana/Prometheus/Telegram self-hosted) | $0–10 | $0–30 (managed Grafana/uptime) |
| Broker/exchange fees (variable, not infra) | ~$0.90/0.1-lot RT FX; 10 bps taker crypto | same | same |
| **Total infrastructure / month** | **≈ $10–35** | **≈ $160–350** | **≈ $650–1,350** |

**One-off costs**

| Item | Hobby | Serious | Semi-pro |
|---|---|---|---|
| Research workstation | $0 (existing laptop) | $1,000–2,000 (8–16 core, 32–64 GB, 1–2 TB NVMe) | $2,000–3,500 (+ consumer GPU optional) |
| Software | $0 | vectorbt PRO lifetime $500 (instead of monthly) | $500 |
| Data backfill | $0 | $125 Databento free credits → $0–200 pay-as-you-go | $500–2,000 (multi-year L2 via Tardis yearly or Databento PAYG) |
| Feed setup fees | $0 | $0–50 (IQFeed startup $50 if used) | $50 |
| **Minimum trading capital** | **$1,000–2,000** (IC Markets min $200, but costs dominate below ~$1k) | **$10,000** | **$25,000–50,000** |

- Rule of thumb from the fee math: infrastructure should stay under ~2–3% of capital per month; at $160–350/mo that implies ≥$10k capital, at $650–1,350/mo ≥$25–50k. Below those, the bot's expectancy after spread + commission + hosting is very unlikely to be positive.

### Gaps
- Tardis exact plan prices, QuantConnect node prices, and Beeks/CNS official prices remain unverified; totals carry ±20% uncertainty on those rows.
- No sourced r/algotrading or Elite Trader 2024–2026 threads with real-world monthly cost breakdowns were retrievable (search returned vendor blogs and a mirror with titles only); community-reported figures are therefore absent.
