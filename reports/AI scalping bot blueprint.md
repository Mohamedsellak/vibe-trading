# Build a Scalping Bot That Survives Its Costs

A real-time AI scalping bot is buildable by one developer for roughly **$10–35/month** of infrastructure at the hobby tier and **$160–350/month** at a serious tier, but the evidence says the bot's survival will be decided by transaction costs, latency and research discipline, not by the cleverness of its model. The strongest short-horizon signals in the peer-reviewed literature (order-flow imbalance, microprice) decay within about **two average price changes** and have never been shown to pay a retail participant after spread, fees and tens of milliseconds of latency ([Kolm et al. 2023](https://papers.ssrn.com/abstract=3900141); [Bilokon & Qiu 2023](https://arxiv.org/pdf/2309.11400)); LLM trading agents mostly lose to buy-and-hold ([StockBench](https://arxiv.org/abs/2510.02209)); and 68–82% of retail CFD accounts at regulated brokers lose money in any 12-month window ([BrokerRank](https://brokerrank.net/research/retail-loss-rates)). The practical recommendation is therefore to aim at **minutes-scale, cost-aware, maker-biased trading on a venue with free order-book data** (BTC/ETH perpetuals on Binance or Bybit from a Tokyo/Singapore VPS, or micro E-mini futures from Chicago for US residents), to use machine learning only as a **meta-label filter and position sizer** over a transparent rule-based trigger, and to treat MetaTrader 5 as a viable but second-choice execution venue for FX where a pure MQL5 Expert Advisor with embedded ONNX inference is the only architecture whose live path matches its backtest. A "million-dollar bot" from a few thousand dollars is not a realistic plan: at an already-exceptional 3% per month it takes about **15 years** to turn $5,000 into $1 million with no drawdowns, taxes or withdrawals, and 10%/month is the exact figure the CFTC cites as a fraud red flag ([CFTC advisory](https://www.cftc.gov/LearnAndProtect/AdvisoriesAndArticles/AITradingBots.html)). What is realistic is a robust, modest-frequency system on $10–50k that targets low-double-digit annual returns and is run as a continuous research process with kill switches, deflated-Sharpe gating and lot-level tax records from day one.

## Recommended best path in one table

The nine questions below reduce to a small set of decisions. The table states the recommended choice at each layer and the reason; the sections that follow give the evidence and the alternatives.

| Layer | Recommendation | Why | Fallback |
|---|---|---|---|
| Holding period | **1–5 minutes**, not seconds | Sub-second edges are won in 5–10 µs races ([Aquilina, Budish & O'Neill](https://www.fca.org.uk/publications/occasional-papers/occasional-paper-no-50-quantifying-high-frequency-trading-arms-race-new-methodology)); retail round trips are 20–200 ms | 30–60 s only on crypto with maker orders |
| Venue (non-US, non-EU) | BTC/ETH perps on **Binance or Bybit**, maker-biased | Free L2 data, 0.02% maker fee, ~8–10 ms from AWS Tokyo/Singapore ([CCXT latency study](https://docs.ccxt.com/blog/how-far-is-your-exchange)) | cTrader Open API with a raw-spread FX broker |
| Venue (US) | **MES/MNQ via Tradovate API or Rithmic** from a Chicago VPS | ~$1.0–1.9 all-in round trip, no PDT, sub-ms vendor latency claims ([PickMyTrade](https://blog.pickmytrade.io/rithmic-vs-tradovate-vs-cqg-fees-latency-measured-2026/)) | Alpaca Elite for minute-scale equities |
| Venue (FX via MetaTrader) | **MT5 only**, pure MQL5 EA + ONNX on MetaQuotes VPS | Only architecture that runs in the real-tick tester and on the $10–15/mo VPS; MT4 is end-of-life | MQL5 EA + local Python sidecar over sockets |
| Engine | **NautilusTrader** (crypto/IB/Databento) or hftbacktest for L2 maker strategies | Same code in backtest and live; Rust core; stable Binance/Bybit adapters ([NautilusTrader](https://github.com/nautechsystems/nautilus_trader)) | Hand-rolled asyncio loop only for MT5 |
| Model | **Rule-based trigger + LightGBM meta-label + simple vol/spread gate** | The only ML uses with evidence at these horizons are false-positive filtering and sizing | Passive quoting with OFI-based adverse-selection gating |
| Hosting | AWS Tokyo/Singapore Linux ($40–80/mo) or broker-adjacent Windows VPS ($30–65/mo) | Right-region placement removes network latency as the binding constraint | MetaQuotes VPS $10–15/mo for a pure EA |
| Capital | **$10k serious / $25–50k semi-pro**; below ~$1k expectancy is negative after costs | Infrastructure must stay under 2–3% of capital per month | Paper and $100-notional live for learning |
| Validation | Walk-forward + purged CV + DSR/PBO + shadow + 10–20% size live | Multiple testing guarantees a false positive otherwise ([Bailey & López de Prado](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf)) | — |

## 1. Requirements and budget: $10 a month to start, $10k of capital to be serious

The hardware question is easier than most beginners expect because the hot path of a retail scalper is tiny. A gradient-boosted tree prediction costs about **10–50 µs** on commodity x86 (LightGBM native 52 µs, ONNX Runtime 11 µs, lleaves 9.6 µs at batch size 1) ([lleaves benchmarks](https://www.github.com/siboehm/lleaves)), and QuantConnect runs live algorithms on a **1-core, 0.5 GB** node ([QuantConnect live deployment docs](https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/deployment)). What matters is location. A broker-adjacent Windows forex VPS in Equinix LD4/NY4/TY3 costs **$10–65/month**: MetaQuotes' built-in VPS is $10–15/month with a claim that 84% of broker servers are reachable in under 3 ms, ForexVPS runs $32–64/month on a current promo, Beeks roughly $41–129/month ([MQL5 VPS](https://www.mql5.com/en/vps); [ForexVPS pricing](https://www.forexvps.net/pricing/); [CloudsPress Beeks listing](https://www.cloudspress.com/hosts/beeks-financial-cloud/)). The MetaQuotes VPS cannot run Python or DLL-based EAs, so it only suits a pure MQL5 bot ([mql5.com forum](https://www.mql5.com/en/forum/509181)). For crypto, the standard is a Linux instance in AWS ap-northeast-1 (Tokyo) for Binance or ap-southeast-1 (Singapore) for Bybit; a t3.medium in Tokyo is about **$40/month** before storage ([issoh.co.jp](https://www.issoh.co.jp/md/tech/17857)), and CCXT's July 2026 probe measured Binance at **8 ms from Tokyo versus 229–230 ms from London or Frankfurt** ([CCXT latency study](https://docs.ccxt.com/blog/how-far-is-your-exchange)). Hetzner's €5.99–29.99/month boxes are excellent research machines but sit in the wrong continent for Binance ([Hetzner cost-optimized](https://www.hetzner.com/cloud/cost-optimized/)). A local research workstation with 8–16 cores, 32–64 GB RAM and 1–2 TB NVMe ($1,000–2,000 if you do not already own one) covers feature engineering and tree-model training; GPUs are rented by the hour when needed, at **$0.34–0.74/hr for an RTX 4090** and $1.4–4/hr for A100/H100 class ([RunPod pricing](https://www.runpod.io/gpu-cloud/pricing)).

Data is free where it matters most. Binance publishes aggTrades, trades, klines and bookTicker files for spot and futures, plus bookDepth for USD-M and COIN-M futures ([binance-public-data](https://github.com/binance/binance-public-data/)), and its live diff-depth WebSocket now updates every **20 ms** ([Binance CHANGELOG](https://developers.binance.com/en/docs/products/spot/CHANGELOG)). Dukascopy bid/ask ticks are downloadable free through community tools, though forum users flag sparse ticks and estimated volumes ([theorycraft-trading/dukascopy](https://github.com/theorycraft-trading/dukascopy); [NinjaTrader forum](https://forum.ninjatrader.com/forum/ninjatrader-7/platform-technical-support/32700-historical-high-quality-fx-tick-data?p=553164)). Tardis.dev gives the first day of every month free for every exchange ([Tardis billing FAQ](https://docs.tardis.dev/faq/billing-and-subscriptions)) and Databento gives $125 of signup credit ([Databento pricing](https://databento.com/pricing)). Paid tiers start at **$49/month** for Massive (ex-Polygon) Currencies Starter real-time FX and crypto, **$199/month** for Databento Standard with live CME data for personal use, and **$108/month** plus exchange fees for IQFeed ([Massive currencies](https://massive.com/currencies); [Databento pricing](https://databento.com/pricing); [DTN fees](https://iqhelp.dtn.com/core-service-fees/)). CME non-professional fees are $1.55–1.60/month top-of-book and $12.10/month depth per exchange ([CME Jan 2026 fee list](https://www.cmegroup.com/market-data/files/january-2026-market-data-fee-list.pdf)). Compressed FX tick data is small (one user reports **219 MB for a year of EURUSD**) while MT4-format exports balloon to 10 GB per symbol-year ([Tickstory support](https://support.tickstory.com/viewtopic.php?p=9377); [Tickstory support](https://support.tickstory.com/viewtopic.php?p=12367)), so plan 5–20 GB for a few FX pairs over five years and a 1–2 TB NVMe if you record crypto L2 yourself.

Broker costs define the game. An ECN FX account costs **$3.50 per lot per side** at IC Markets or Pepperstone on MT4/MT5 ($3.00 on cTrader) on top of a raw EURUSD spread that third-party tests put at 0.1–0.19 pips, giving about **$8–9 per round-turn standard lot** ([IC Markets](https://www.icmarkets.com/global/en/start-forex-trading); [Pepperstone pricing](https://pepperstone.com/en-gb/ways-to-trade/pricing); [CompareForexBrokers](https://www.compareforexbrokers.com/reviews/pepperstone-review/razor-vs-standard-account)). Binance USD-M futures charge **0.02% maker / 0.05% taker** for regular users, spot 0.10%/0.10% ([Binance Futures fee FAQ](https://www.binance.com/support/faq/360033544231); [Binance fee schedule](https://www.binance.com/en/fee/schedule)). A taker scalp on crypto therefore costs ~10 bps round trip against ~0.8–0.9 pips (roughly 0.8 bps) on raw FX, which is why crypto scalping has to be maker-biased. The arithmetic also sets the capital floor: a $1,000 account trading 0.1 lots pays about $0.90 per trade, so 50 trades a day is $45 of cost against a few dollars of gross edge, which is infeasible; at $10k the infrastructure budget below stays under 2–3% of capital and the strategy can clear ~1 pip net per trade without being swamped.

| Line item (USD/month, Nov 2026 prices) | Hobby / MVP | Serious retail | Semi-professional |
|---|---|---|---|
| Hosting | MetaQuotes VPS $10–15 or Hetzner $7–10 | ForexVPS/Beeks Windows $48–73 or AWS Tokyo $40–80 | Dedicated Equinix-adjacent $270–300 + AWS + backup |
| Market data | $0 (Dukascopy, MT5 ticks, Binance public data, Tardis free days) | $49 Massive or ~$50–150 Tardis Solo (third-party estimate) | Databento $199 + CME depth bundle $36.50 + Tardis Pro (est.) |
| Research software | $0 (NautilusTrader, vectorbt OSS) | vectorbt PRO $25 ([vectorbt.pro](https://vectorbt.pro/become-a-member)) | + QuantConnect Researcher $84 ([QuantConnect pricing](https://www.quantconnect.com/pricing)) |
| GPU rental | $0 | ~$17–37 (50 h RTX 4090) | ~$140–400 (100 h A100/H100) |
| LLM API (offline news scoring) | $0–10 (Haiku 5.5 at $0.10/$0.50 per MTok) ([Claude pricing](https://platform.claude.com/docs/en/about-claude/pricing)) | $20–60 | $100–300 |
| **Infrastructure total** | **≈ $10–35** | **≈ $160–350** | **≈ $650–1,350** |
| **Minimum trading capital** | **$1–2k (tuition money)** | **$10k** | **$25–50k** |

Tardis plan prices, QuantConnect node prices and Beeks' official GBP prices were not verifiable from vendor pages, so the serious and semi-pro totals carry roughly ±20% uncertainty.

## 2. MetaTrader: MT5 has real APIs, MT4 is dead, and only a pure EA matches its backtest

Both platforms let you place, modify and close orders programmatically, but through very different surfaces. MQL4 inside the MT4 terminal exposes the order-ticket model (`OrderSend`, `OrderModify`, `OrderClose`, `OrderDelete`), returns a ticket or −1, and throws error 138 on requotes and 130 on stops placed inside the broker's minimum distance ([MQL4 docs: OrderSend](https://docs.mql4.com/trading/ordersend)). There is no official external or Python API for MT4; every "MT4 Python API" is a third-party bridge EA. MT5 offers three official routes: MQL5 inside the terminal (`OrderSend`, `OrderSendAsync`, the `CTrade` class with `PositionOpen`, `PositionModify`, `PositionClose`, `PositionClosePartial`), the official `MetaTrader5` Python package (version **5.0.6231, released 27 September 2026**, Windows x86-64 wheels only, Python 3.6–3.14), and a Manager/Web API that is licensed to brokers, not retail accounts ([MQL5 docs: CTrade](https://www.mql5.com/en/docs/standardlibrary/tradeclasses/ctrade); [PyPI MetaTrader5](https://pypi.org/project/MetaTrader5/); [MetaQuotes broker page](https://www.metatrader5.com/ru/brokers)). The trade request model is a `MqlTradeRequest` with `action` (`TRADE_ACTION_DEAL` for market, `TRADE_ACTION_SLTP` to change stops on a position, `TRADE_ACTION_MODIFY`/`REMOVE` for pending orders), `deviation` in points, `position` ticket for closes, and a filling mode (`FOK`, `IOC`, `RETURN`) that must match the symbol's bitmask ([MQL5 docs: order_send](https://www.mql5.com/en/docs/python_metatrader5/mt5ordersend_py); [MQL5 docs: order_check](https://www.mql5.com/en/docs/python_metatrader5/mt5ordercheck_py)).

MT4 should not be the target of any new project. MetaQuotes announced in January 2018 that it would stop selling MT4 licenses and issue no new servers ([Finance Magnates 2018](https://www.financemagnates.com/forex/technology/metaquotes-will-no-longer-offer-mt4-trading-platform/)); by December 2024 brokers were being pushed to MT5 with licence fee increases ([Finance Magnates 2024](https://www.financemagnates.com/forex/metaquotes-to-increase-metatrader-licensing-fees-from-january-1/amp)); and on 14 November 2026 OANDA Japan shut MT4 citing security breaches, with Finance Magnates reporting that MetaQuotes has ceased official support ([Finance Magnates 2026](https://www.financemagnates.com/forex/oanda-japan-accelerates-mt4-retirement-citing-security-breaches-and-legacy-vulnerabilities/)). MT5 meanwhile shipped builds 5572 through 6230+ in 2026 with ONNX and tester improvements ([MT5 release notes build 5572](https://www.metatrader5.com/en/releasenotes/terminal/2426)). MT4 also has no async order API, no real-tick tester (it interpolates ticks from M1 bars, capping modelling quality at ~90% without imports) ([MQL5 blog 774193](https://www.mql5.com/en/blogs/post/774193)), and DLL-only bridges.

The three ways to attach an AI model to MT5 have sharply different latency and robustness profiles. The official Python package is a **synchronous, poll-only IPC client**: there are no push callbacks (the only subscription is Market Depth, and even that is read by polling), `order_send` blocks until the broker replies, and a user who tried threading found the GIL serialises sends anyway ([MQL5 docs: Python integration](https://www.mql5.com/en/docs/python_metatrader5); [mql5.com forum 454563](https://www.mql5.com/en/forum/454563)). It also cannot use the Strategy Tester and runs only on Windows, so Linux users go through Wine plus an RPyC bridge (mt5linux) with pinned versions ([mt5linux](https://github.com/tiloye/mt5linux)). Third-party bridges all follow the pattern "EA inside the terminal plus a transport": the Darwinex ZeroMQ connector is MT4-only and about to be archived, DWX Connect is a file-based bridge polling at **5 ms** that "cannot be used for backtesting", and MetaApi.cloud adds a self-reported **median 6 ms** plus WAN latency and rate limits for roughly $30–100/month ([dwx-zeromq-connector](https://github.com/darwinex/dwx-zeromq-connector); [dwxconnect](https://github.com/darwinex/dwxconnect); [MetaApi FAQ](https://metaapi.cloud/docs/client/faq/)). MQL5 has native `Socket*` functions since about 2019, so an EA can talk TCP to a local Python process without any DLL ([MQL5 docs: Network functions](https://www.mql5.com/en/docs/network)). The cleanest option is to export the model to ONNX and run it inside the EA with `OnnxCreateFromBuffer`/`OnnxRun`, which MetaQuotes has supported since 2023 and improved in build 5572; inference then has zero runtime dependencies, works on the MetaQuotes VPS and in the tester, and a three-month backtest with per-bar inference ran "in only a few seconds" ([MQL5 article 12373](https://www.mql5.com/en/articles/12373); [MQL5 docs: OnnxCreate](https://www.mql5.com/en/docs/onnx/onnxcreate)). MetaQuotes' own 2026 guidance matches this: Python for research, MQL5 for live execution and risk controls, and the EA should "retain final execution authority" ([MQL5 blog 774018](https://www.mql5.com/en/blogs/post/774018); [MQL5 blog 774493](https://www.mql5.com/en/blogs/post/774493)).

| MT5 attachment option | Latency added | Tester support | MetaQuotes VPS | Maintenance | Verdict for scalping |
|---|---|---|---|---|---|
| Pure MQL5 EA + embedded ONNX | Sub-ms to few ms CPU inference; `OrderSendAsync` ≈ 0.09 ms vs 9.59 ms sync ([MQL5 article 2635](https://www.mql5.com/en/articles/2635)) | Yes, byte-identical to live | Yes | Recompile to change model | **Best** |
| MQL5 EA + local Python sidecar (native sockets / ZeroMQ) | Sub-ms transport + Python inference + scheduling jitter | No (external process) | No (DLL/Python forbidden) | Two codebases | Pragmatic when model cannot export to ONNX |
| Official `MetaTrader5` Python package | IPC per poll (unpublished), blocking `order_send` | No | No | Simple | Research, demo, minute-scale bots only |
| File bridge (DWX Connect) | 5 ms poll, file collisions | No | No | Low | Avoid for scalping |
| MetaApi.cloud REST/WebSocket | Median 6 ms + internet; rate-limited | No | n/a | Vendor-managed | Monitoring and slow bots |

Whichever route you choose, broker-side realities dominate. A forum user on an Equinix NY host saw ~0.5 ms ping but **~40 ms per trade** in the journal, with "network delivery typically 20 to 200 ms" and full fills of 60–200 ms on MT5 (200–400 ms on MT4) ([mql5.com forum 465784](https://mql5.com/en/forum/465784)). Brokers enforce stops and freeze levels (retcodes 10016/10029), undocumented per-account request rates (retcode 10024 "Too frequent requests"), and execution modes where `MARKET` symbols ignore your price and honour only `deviation` while `INSTANT` symbols requote ([MQL5 docs: trade return codes](https://mql5.com/en/docs/constants/errorswarnings/enum_trade_return_codes); [MQL5 docs: symbol constants](https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants)). Hedging and netting accounts behave differently (close by ticket on hedging accounts, since a symbol-only close picks the lowest ticket) ([MQL5 blog: hedging and netting](https://www.mql5.com/en/blogs/post/774939)). ECN brokers such as IC Markets and Pepperstone advertise no scalping restrictions, but prop firms and market makers impose hold-time floors from 30 seconds to 3 minutes ([Tycoon Funded](https://intercom.help/tycoon-funded/en/articles/10372885-what-is-the-minimum-hold-time-for-a-trade); [Pepperstone guide](https://pepperstone.com/ar/insights/guides/automated-trading/why-use-your-expert-advisor-with-pepperstone)). Retail FIX from Pepperstone requires **€160 million** of monthly volume ([Pepperstone API trading](https://pepperstone.com/en/platforms/integrations/api-trading/)), so MetaTrader is viable for "fast intraday" (seconds to minutes) but not for true sub-second edge.

### Python example: place, modify and close with the official MetaTrader5 package

The following cycle (initialize → read ticks → market buy with SL/TP → modify SL/TP → close by opposite deal) uses only documented fields and constants; it has not been executed here and requires Windows, a running MT5 terminal and `pip install MetaTrader5` ([MQL5 docs: order_send](https://www.mql5.com/en/docs/python_metatrader5/mt5ordersend_py)).

```python
"""
Minimal MT5 trading cycle with the official MetaTrader5 package.
Requires: Windows, a running/installed MT5 terminal, `pip install MetaTrader5`.
Steps: initialize/login -> read tick -> market buy with SL/TP -> modify SL/TP -> close.
"""
import time
import MetaTrader5 as mt5

SYMBOL   = "EURUSD"
LOT      = 0.01
MAGIC    = 20261117
DEV_PTS  = 10          # max slippage in points
SL_PTS   = 100         # 10 pips on a 5-digit symbol
TP_PTS   = 100

def init(login=None, password=None, server=None, terminal_path=None):
    kwargs = {}
    if terminal_path:
        kwargs["path"] = terminal_path            # e.g. r"C:\Program Files\MetaTrader 5\terminal64.exe"
    if login:
        kwargs.update(login=login, password=password, server=server)
    if not mt5.initialize(**kwargs):            # launches the terminal if needed, syncs with broker
        raise RuntimeError(f"initialize() failed: {mt5.last_error()}")
    acc = mt5.account_info()
    print("connected:", acc.login, acc.server, "hedging" if acc.margin_mode == 2 else "netting/exchange")

def prepare_symbol(symbol):
    info = mt5.symbol_info(symbol)
    if info is None:
        raise RuntimeError(f"{symbol} not found on this server")
    if not info.visible and not mt5.symbol_select(symbol, True):
        raise RuntimeError(f"symbol_select({symbol}) failed")
    return info

def pick_filling(info):
    """Choose a filling mode the broker allows for this symbol (bitmask: FOK=1, IOC=2)."""
    fm = info.filling_mode
    if fm & 1:
        return mt5.ORDER_FILLING_FOK
    if fm & 2:
        return mt5.ORDER_FILLING_IOC
    return mt5.ORDER_FILLING_RETURN             # only valid on Market/Exchange-execution symbols

def send(request):
    chk = mt5.order_check(request)              # pre-flight: margin, stops, filling
    if chk is None or chk.retcode != 0:
        raise RuntimeError(f"order_check failed: {chk}")
    res = mt5.order_send(request)               # BLOCKS until the broker answers
    if res is None or res.retcode not in (mt5.TRADE_RETCODE_DONE, 10010):  # 10010 = DONE_PARTIAL
        raise RuntimeError(f"order_send failed retcode={getattr(res, 'retcode', None)} {res}")
    return res

def market_buy(symbol, lot):
    info = prepare_symbol(symbol)
    tick = mt5.symbol_info_tick(symbol)
    point = info.point
    # respect broker stops level (points); 0 may still mean dynamic server-side control
    min_dist = max(info.trade_stops_level, 1) * point
    sl = tick.ask - max(SL_PTS * point, min_dist)
    tp = tick.ask + max(TP_PTS * point, min_dist)
    req = {
        "action":       mt5.TRADE_ACTION_DEAL,
        "symbol":       symbol,
        "volume":       lot,
        "type":         mt5.ORDER_TYPE_BUY,
        "price":        tick.ask,               # ignored/approximate on Market-execution symbols
        "sl":           round(sl, info.digits),
        "tp":           round(tp, info.digits),
        "deviation":    DEV_PTS,
        "magic":        MAGIC,
        "comment":      "ai-scalp",
        "type_time":    mt5.ORDER_TIME_GTC,
        "type_filling": pick_filling(info),
    }
    res = send(req)
    print(f"BUY ok deal={res.deal} order={res.order} price={res.price} vol={res.volume}")
    return res

def find_position(symbol, magic):
    for p in mt5.positions_get(symbol=symbol) or ():
        if p.magic == magic:
            return p
    return None

def modify_sltp(pos, new_sl, new_tp):
    info = mt5.symbol_info(pos.symbol)
    req = {
        "action":   mt5.TRADE_ACTION_SLTP,
        "symbol":   pos.symbol,
        "position": pos.ticket,
        "sl":       round(new_sl, info.digits),
        "tp":       round(new_tp, info.digits),
        "magic":    MAGIC,
    }
    res = send(req)
    print(f"SLTP ok ticket={pos.ticket} sl={new_sl} tp={new_tp}")
    return res

def close_position(pos):
    """Close by sending the opposite deal referencing the position ticket (works on hedging and netting)."""
    info = mt5.symbol_info(pos.symbol)
    tick = mt5.symbol_info_tick(pos.symbol)
    is_long = pos.type == mt5.POSITION_TYPE_BUY
    req = {
        "action":       mt5.TRADE_ACTION_DEAL,
        "symbol":       pos.symbol,
        "position":     pos.ticket,
        "volume":       pos.volume,
        "type":         mt5.ORDER_TYPE_SELL if is_long else mt5.ORDER_TYPE_BUY,
        "price":        tick.bid if is_long else tick.ask,
        "deviation":    DEV_PTS,
        "magic":        MAGIC,
        "comment":      "ai-scalp close",
        "type_time":    mt5.ORDER_TIME_GTC,
        "type_filling": pick_filling(info),
    }
    res = send(req)
    print(f"CLOSE ok ticket={pos.ticket} price={res.price}")
    return res

def poll_ticks(symbol, seconds=2.0, interval_s=0.01):
    """There are no push callbacks: poll and dedupe on time_msc."""
    last_msc, n, t_end = 0, 0, time.perf_counter() + seconds
    while time.perf_counter() < t_end:
        t = mt5.symbol_info_tick(symbol)
        if t and t.time_msc != last_msc:
            last_msc, n = t.time_msc, n + 1
            # feed (t.bid, t.ask, t.time_msc) to the model here
        time.sleep(interval_s)
    print(f"{n} distinct ticks in {seconds}s")

if __name__ == "__main__":
    init()                                      # or init(login=..., password=..., server="Broker-Demo")
    try:
        poll_ticks(SYMBOL, seconds=2)
        market_buy(SYMBOL, LOT)
        pos = find_position(SYMBOL, MAGIC)
        if pos is None:
            raise RuntimeError("position not found after fill (check positions_get / netting mode)")
        info = mt5.symbol_info(SYMBOL)
        modify_sltp(pos, new_sl=pos.price_open - 150 * info.point, new_tp=pos.price_open + 60 * info.point)
        time.sleep(1.0)                          # beware broker min-hold rules
        close_position(find_position(SYMBOL, MAGIC))
    finally:
        mt5.shutdown()
```

### MQL5 example: CTrade open, modify and close with an ONNX hook

```mql5
// AiScalper.mq5 — minimal CTrade usage (open with SL/TP, modify, close) + ONNX hook
#include <Trade/Trade.mqh>
#resource "model.onnx" as uchar ExtModel[]      // embedded ONNX model (recompile EA to change it)

input double InpLots      = 0.01;
input int    InpSlPoints  = 100;
input int    InpTpPoints  = 60;
input int    InpDeviation = 10;
input ulong  InpMagic     = 20261117;

CTrade trade;
long   onnx = INVALID_HANDLE;
static vectorf x(32);          // feature vector, size must match model input
static vectorf y(1);

int OnInit()
{
   trade.SetExpertMagicNumber(InpMagic);
   trade.SetDeviationInPoints(InpDeviation);
   trade.SetTypeFillingBySymbol(_Symbol);        // picks FOK/IOC/RETURN the broker allows
   trade.SetAsyncMode(false);                    // true => OrderSendAsync, results via OnTradeTransaction
   trade.SetMarginMode();                        // match hedging/netting account
   onnx = OnnxCreateFromBuffer(ExtModel, ONNX_DEFAULT);
   if(onnx == INVALID_HANDLE) return INIT_FAILED;
   const long in_shape[]  = {1, 32};
   const long out_shape[] = {1, 1};
   if(!OnnxSetInputShape(onnx, 0, in_shape) || !OnnxSetOutputShape(onnx, 0, out_shape)) return INIT_FAILED;
   return INIT_SUCCEEDED;
}
void OnDeinit(const int reason) { if(onnx != INVALID_HANDLE) OnnxRelease(onnx); }

void OnTick()
{
   MqlTick t; if(!SymbolInfoTick(_Symbol, t)) return;
   // ... fill x[] with features from recent ticks/bars ...
   if(!OnnxRun(onnx, ONNX_NO_CONVERSION, x, y)) return;
   double score = y[0];

   // broker constraints
   int    stops  = (int)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double minD   = MathMax(stops, 1) * _Point;
   double slD    = MathMax(InpSlPoints * _Point, minD);
   double tpD    = MathMax(InpTpPoints * _Point, minD);

   if(!PositionSelect(_Symbol))
   {
      if(score > 0.6)
         trade.Buy(InpLots, _Symbol, t.ask, t.ask - slD, t.ask + tpD, "ai-scalp");
      else if(score < 0.4)
         trade.Sell(InpLots, _Symbol, t.bid, t.bid + slD, t.bid - tpD, "ai-scalp");
      if(trade.ResultRetcode() != TRADE_RETCODE_DONE && trade.ResultRetcode() != TRADE_RETCODE_PLACED)
         PrintFormat("open failed: %d %s", trade.ResultRetcode(), trade.ResultRetcodeDescription());
      return;
   }
   ulong ticket = PositionGetInteger(POSITION_TICKET);
   long  ptype  = PositionGetInteger(POSITION_TYPE);
   double open  = PositionGetDouble(POSITION_PRICE_OPEN);
   // trail / modify (TRADE_ACTION_SLTP under the hood)
   if(ptype == POSITION_TYPE_BUY && t.bid - open > tpD * 0.5)
      trade.PositionModify(ticket, open + minD, PositionGetDouble(POSITION_TP));
   // model flip -> close (opposite deal with position ticket under the hood)
   if((ptype == POSITION_TYPE_BUY && score < 0.4) || (ptype == POSITION_TYPE_SELL && score > 0.6))
      trade.PositionClose(ticket, InpDeviation);
}
```

Method names follow the [CTrade docs](https://www.mql5.com/en/docs/standardlibrary/tradeclasses/ctrade) and the ONNX calls follow [MQL5 article 12373](https://www.mql5.com/en/articles/12373); input-shape indices vary by model and should be verified with `ONNX_DEBUG_LOGS`. Backtest this EA only in "Every tick based on real ticks" mode with a Fixed Delay set from measured ping, because "No Delay" results are meaningless for a scalper and MetaQuotes' own Random Delay model spans 0–18 seconds ([MT5 help: Testing](https://www.metatrader5.com/en/terminal/help/algotrading/testing)).

## 3. Alternative platforms: crypto exchanges and micro-futures beat every FX and equity API on cost and access

Retail-accessible APIs fall into three families: broker socket APIs that need a running gateway (Interactive Brokers TWS/Gateway, cTrader Open API over protobuf), pure cloud REST+WebSocket APIs (Alpaca, OANDA, Saxo, TradeStation, every crypto exchange), and futures execution networks (Rithmic, Tradovate, CQG, NinjaTrader). Crypto exchanges are the only venues where a solo developer gets FIX/SBE-class protocols and free full-depth data just by opening an account: Binance offers a spot FIX API at 10,000 messages per 10 seconds and SBE market data ([Binance FIX API](https://developers.binance.com/en/dev-docs/products/spot/fix-api)), Bybit allows 10–20 orders per second per UID ([Bybit V5 rate limit](https://bybit-exchange.github.io/docs/v5/rate-limit)), and Hyperliquid publishes maker rebates down to −0.003% ([Hyperliquid fees](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees)). The catch is jurisdiction: Binance ceased EU services on 1 July 2026 after failing to obtain MiCA authorisation, EU perpetuals require both MiCA and MiFID II licences ([Finance Magnates MiCA](https://www.financemagnates.com/cryptocurrency/regulation/europes-crypto-market-after-july-1-who-stays-who-leaves-and-what-changes-under-mica/)), Binance and Bybit block New York probes ([CCXT latency study](https://docs.ccxt.com/blog/how-far-is-your-exchange)), and the UK bans retail crypto derivatives ([FCA press release](https://www.fca.org.uk/news/press-releases/fca-opens-retail-access-crypto-etns/printable/print)).

Interactive Brokers is the most operationally hostile choice for an unattended bot: TWS and IB Gateway restart daily by design and need a fresh 2FA login roughly weekly ([IBKR Campus](https://www.interactivebrokers.com/campus/?p=259814)), pacing is 50 messages per second with session termination after three violations ([IBKR TWS API pacing](https://www.interactivebrokers.com/docs/tws-api/doc/pacing-limitations)), OAuth 2.0 is not available to individuals ([IBKR OAuth 2](https://www.interactivebrokers.com/docs/web-api/authentication/oauth-2/register.md)), and a 2025 review measured a **~180 ms median** from marketable limit to fill confirmation ([dev.to IBKR review](https://dev.to/pickuma/interactive-brokers-api-review-what-retail-traders-actually-get-1n6d)). Alpaca is cheap (commission-free, or $0.004/share all-in on Elite) and has replaced the PDT rule with an intraday margin framework after FINRA's Rule 4210 amendment took effect on 4 June 2026 ([Alpaca Elite](https://alpaca.markets/elite); [Alpaca blog](https://alpaca.markets/blog/finra-retires-the-pdt-rule-introducing-alpacas-new-intraday-margin-framework/)), but the free Basic plan is IEX-only, scalping needs the **$99/month** SIP feed, trading calls are capped at 200/minute, and users report paper-trading limit fills delayed **50–260 seconds** ([Alpaca market data](https://docs.alpaca.markets/docs/about-market-data-api); [Alpaca forum](https://forum.alpaca.markets/t/paper-trading-fill-delays-of-50-260-seconds-limit-orders-filled-minutes-after-price-crossed/18223)). cTrader Open API is the most MetaTrader-like substitute for FX: broker-agnostic, free, protobuf or JSON, 50 requests per second per connection, an official Python SDK (built on Twisted, which is an integration tax for asyncio pipelines), and a free FIX API with no documented latency edge over normal execution ([help.ctrader.com Open API](https://help.ctrader.com/open-api); [Spotware FIX](https://www.spotware.com/ctrader-fix-api)). OANDA v20 is the simplest REST API but US standard pricing is ~1.4 pips on EUR/USD (about $14 per lot round trip) ([forexbrokers.com OANDA](https://forexbrokers.com/reviews/oanda)). For US residents, micro E-mini futures are the sweet spot: Tradovate's API costs $25/month with a $1,000 live account, MES all-in round trips run about $1.0–1.9, Rithmic claims sub-millisecond R|API latency from Chicago, and there is no PDT ([Tradovate pricing](https://www.tradovate.com/pricing/); [PickMyTrade](https://blog.pickmytrade.io/rithmic-vs-tradovate-vs-cqg-fees-latency-measured-2026/)). NinjaTrader is a Windows desktop with C# NinjaScript, awkward for Python/AI pipelines and adding $0.25/contract routing via Rithmic/CQG ([NinjaTrader costs](https://ninjatrader.com/futures/blogs/futures-trading-costs/)). Prop firms are the wrong venue for an AI scalper: FTMO bars "software, artificial intelligence, ultra-high-speed tools, or mass data entry" that give an unfair advantage and Topstep names "running scalping algorithms designed to exploit unrealistic SIM fills" as abuse ([FTMO forbidden practices](https://ftmo.com/en/forbidden-trading-practices/); [Topstep prohibited strategies](https://help.topstep.com/en/articles/10305426)).

| Platform | Assets | API | Latency class (well-placed VPS) | Cost per typical scalp round trip | Scalping constraints | Verdict (sec–min holds) |
|---|---|---|---|---|---|---|
| Binance (USDⓈ-M) | Crypto perps/spot | REST, WS, WS-API, FIX (spot), SBE; testnet | ~8 ms from Tokyo; 160–260 ms from EU/US | 0.02%/0.05% → $4–10 per $10k; free L2 | 6,000 weight/min; ~300 orders/10 s futures; not US/EU | **Strong** (where legal) |
| Bybit | Crypto perps/spot | REST, WS trade, batch | ~10 ms from Singapore | 0.02%/0.055% → $4–11 per $10k | 10–20 orders/s per UID | **Strong** (non-US) |
| Hyperliquid | On-chain perps | REST + WS, wallet signing | **~884 ms median fill** even from Tokyo ([Glassnode](https://hyperlatency.glassnode.com/fill-latency)) | 0.015%/0.045% → $3–9 per $10k; rebates | 1 action per $1 traded | Poor for seconds; fair for 1–5 min maker |
| Tradovate / Rithmic | CME futures | REST+WS ($25/mo) / R\|API (C++/.NET) | <1 ms vendor claim from Chicago | MES ≈ $1.0–1.9 + $1.25 tick | None; no PDT | **Good** (US) |
| cTrader Open API | FX/CFD | Protobuf/JSON, C#/Python SDK, free FIX | 150–250 ms execution reported at brokers | Raw spread + ~$6 RT commission | 50 req/s per connection | Good MT replacement, non-US |
| OANDA v20 | FX/CFD | REST + HTTP streaming | Unmeasured | ~$14/lot standard; $10 + 0.4 pip core | 100 req/s per connection | Fair, minute-scale only |
| Alpaca | US stocks/options/crypto | REST + WS, paper env | ~20 ms RTT anecdotal | $0 commission + spread; SIP $99/mo | 200 req/min; paper fills delayed minutes | Reasonable, minute-scale equities |
| Interactive Brokers | Everything | TWS socket, Web API, FIX (institutional) | ~180 ms median; 100–600 ms anecdotal | $1 min/side stocks; 0.2 bps FX | 50 msg/s; daily gateway restart; weekly 2FA | Poor for seconds; heavy ops burden |
| NinjaTrader | Futures | C# NinjaScript desktop | Rithmic path <1 ms (vendor) | $0.09–0.39/side + ~$0.55 fees + routing | None | Fair for C# devs only |
| Saxo / TradeStation / Tradier | Multi / US | REST + streaming | Unmeasured | Varies | Saxo 1 order/s; TS 30 depth calls/min | Poor to fair |
| LMAX Global | FX/metals/crypto | FIX 4.4, Java/.NET | ECN, unmeasured | Activity-based; $300/venue data | $10k minimum ([LMAX FAQ](https://www.lmax.com/?p=19298)) | Institutional-leaning |
| Prop firms (FTMO, Topstep) | Sim FX/futures | MT/cTrader; ProjectX | n/a | Challenge fee | AI/HFT/mass-entry banned | **Avoid** |

The pattern is that network latency stops being the binding constraint once the bot sits in the right region (Tokyo or Singapore for crypto, Chicago for CME, New Jersey for US equities); the venues where latency actually breaks seconds-scale trading are Hyperliquid (block-bound fills) and IBKR via the gateway. Seconds-scale holds are economically viable only where maker fees are ≤2 bps with free L2 (crypto) or where tick-to-fee ratios are favourable (MES on a low-commission plan); OANDA retail spreads and Alpaca IEX data do not support them.

## 4. AI approach: order flow is real, deep learning is a nowcast, LLMs belong offline

The question "what actually works" has a clear answer in the peer-reviewed literature, and it is narrower than the marketing. Order-flow imbalance (OFI) has the best evidence of any short-horizon signal: Cont, Kukanov and Stoikov found a linear relation between OFI and mid-price changes across 50 NYSE stocks ([Cont et al. 2014](https://arxiv.org/abs/1011.6402)); Kolm, Turiel and Westray showed on 115 Nasdaq stocks that models trained on multi-level order flow "significantly outperform" models trained on raw book states, with forecast accuracy peaking at about **two average price changes** ahead ([Kolm et al. 2023](https://papers.ssrn.com/abstract=3900141)); Lucchese, Pakkanen and Veraart found mid-price predictability "ubiquitous" out to ~50 book events, with order-flow and volume representations in the superior model set 85–90% of the time versus 5–11% for raw-state DeepLOB, and no gain from L3 over L2 ([Lucchese et al. 2024](https://arxiv.org/abs/2211.13777v3)); and Sirignano and Cont showed a single model pooled across all US stocks generalised to unseen names ([Sirignano & Cont 2019](https://arxiv.org/abs/1803.06917v1)). Every one of these papers stops at prediction quality. None reports net-of-cost P&L achievable by a retail participant, and the half-life of the signal (a couple of price changes, i.e. sub-second in liquid names) is shorter than a retail order's time in flight. The FCA's study of LSE latency races shows why: races occur about once a minute per FTSE-100 symbol, the modal race lasts **5–10 microseconds**, and each is worth about half a tick ([FCA OP50](https://www.fca.org.uk/publications/occasional-papers/occasional-paper-no-50-quantifying-high-frequency-trading-arms-race-new-methodology)). A cloud box 10–100 ms from the matching engine is three to four orders of magnitude too slow to capture that edge, so a retail backtest that assumes execution at the observed quote is usually measuring a phantom.

Deep learning on the order book learns a slightly better microprice, which is a market-maker's tool rather than a directional retail signal. Bilokon and Qiu's Imperial College study on Binance BTC/ETH books is the only cost-aware benchmark found: their DLSTM reached 73.1% three-class accuracy at 20 events ahead, but a transaction cost of just **0.002%** cut cumulative return for the best models by roughly 85% and pushed transformer-family models negative, and the authors themselves call the simulated Sharpes unrealistic ([Bilokon & Qiu 2023](https://arxiv.org/pdf/2309.11400)). That 0.002% is 10–50 times smaller than a retail crypto taker fee. Transformers did not beat LSTMs on LOB data and were more fragile to costs; the DeepLOB authors' own trading simulation ignored costs ([DeepLOB](https://arxiv.org/abs/1808.03668)). Time-series foundation models fare worse: a 2026 benchmark concluded Moirai, TimesFM and Chronos are "useful practical priors" but "not universal engines for statistically reliable alpha" ([arXiv 2606.27100](https://econpapers.repec.org/paper/arxpapers/2606.27100.htm)), and naive or ARIMA baselines remained strongest at short horizons ([arXiv 2507.07296](https://arxiv.org/html/2507.07296v1)). Reinforcement learning has credible use in execution optimisation and market making, where the reward is dense and the simulator is close to reality (Oxford-Man's agent translates a given signal into limit orders) ([Synced on Nagy et al.](https://syncedreview.com/2023/01/25/oxford-us-deep-double-duelling-q-learning-translates-trading-signals-into-sota-trading-strategies/amp/)), but FinRL-affiliated authors admit prior DRL trading papers "gave the false impression that DRL-based trading strategies may be ready to deploy" ([arXiv 2209.05559](https://arxiv.org/pdf/2209.05559)). LLM agents are the weakest: StockBench found most models struggle to beat buy-and-hold ([StockBench](https://arxiv.org/abs/2510.02209)), LiveTradeBench found reasoning scores do not correlate with trading outcomes ([LiveTradeBench summary](https://www.emergentmind.com/papers/2511.03628)), FINSABER's 20-year backtest found LLM strategies underperform in bull markets and lose disproportionately in bear markets ([FINSABER](https://arxiv.org/pdf/2505.07078v4)), and a May 2026 position paper argues reported LLM-agent alpha "should not be treated as deployment evidence" ([The Alpha Illusion](https://arxiv.org/abs/2605.16895)). Every one of those benchmarks runs at daily frequency; with time-to-first-token of 0.35 s at best and p99 up to 5× p50 ([LLM latency benchmarks](https://www.kunalganglani.com/blog/llm-latency-benchmark-optimization.md)), an LLM call in a scalping order path would exceed the whole tick-to-order budget by 100–1,000×.

What survives scrutiny is a hybrid. Meta-labelling, in which a simple, explainable rule generates candidate trades and a binary classifier predicts whether each candidate will hit its target before its stop, attacks the two things that kill retail bots, false positives and oversizing, rather than attempting to forecast direction. The supporting evidence is partly commercial (Hudson & Thames sells the tooling) and one independent QuantConnect grid search found no gain over an end-to-end model, so expect modest, not transformative, improvements ([Hudson & Thames](https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy/); [QuantConnect forum](https://www.quantconnect.com/forum/discussion/14706/why-meta-labeling-is-not-a-silver-bullet/)). Ernest Chan's firm applies ML to predicting the profitability of a strategy's trades and to risk, not to price direction ([IBKR Campus](https://www.interactivebrokers.com/campus/ibkr-quant-news/algo-advantage-032-dr-ernest-chan-the-breakthrough-uses-of-machine-learning-in-risk-management/)). Regime filters should stay simple: a summarised 31-asset study found a 200-day moving average did as well as or better than HMMs and that "no single config survives correction" ([SozAI transcript](https://sozai.app/transcript/testing-market-regimes-trading-strategies/index.md)).

The concrete first model, then, is a LightGBM meta-labeller with at most ~25 features computed only from data time-stamped at or before decision time minus your measured feed latency: level-1 and 3/5-level book imbalance; multi-level OFI over the last 10/50/200 events; microprice minus mid in ticks ([Stoikov 2018](https://ideas.repec.org/a/taf/quantf/v18y2018i12p1959-1966.html)); signed aggressor volume over 1/5/30 s; spread in ticks with a "do not trade when wide" flag; realised volatility over 1 and 5 minutes; mid returns and deviation from session VWAP; book-update and trade rates as the "information-rich" proxy; time-of-day, session and minutes-to-scheduled-events; and a queue-position proxy for passive entries. Labels come from a triple barrier applied to a rule-based trigger with entry assumed at decision time plus your p90 order latency at the ask for buys or bid for sells, TP/SL in ATR units, a time barrier in price changes or 30–120 s, and the label set to 1 only if TP is hit first net of your actual fees and half-spread. Instrument choice follows the evidence: large-tick, deep-book, 24/7 instruments with free L2 (BTC/ETH perps) first, US large-caps via Databento MBP-10 second, retail FX last, because single-broker top-of-book with tick-count "volume" and dealer last-look is the thinnest information environment (an inference, not a sourced finding). A meta-model that lifts a trigger's precision from 50% to **54–56% on net-of-cost labels** is the realistic ceiling to aim for; headline 70%+ accuracies vanish under costs. Pooled training across BTC and ETH is reasonable per Sirignano and Cont.

| Claim seen online | Status in 2026 | Best evidence |
|---|---|---|
| "Order-book imbalance predicts the next tick" | True for mid-price, decays within ~2 price changes; not a retail P&L claim | Cont et al. 2014; Kolm et al. 2023 |
| "DeepLOB gives 70–80% accuracy, so it's profitable" | Accuracy real on event-horizon labels; profit disappears at 0.002% cost | Bilokon & Qiu 2023 |
| "Transformers beat LSTMs for trading" | Not on LOB data; more fragile to costs | Bilokon & Qiu 2023 |
| "Chronos/TimesFM forecast markets" | Beaten by naive/ARIMA at short horizons | arXiv 2606.27100; 2507.07296 |
| "RL agent made X% in backtest" | Field admits overfitting and selection-on-test | FinRL-Meta; arXiv 2209.05559 |
| "LLM agents beat the market" | Most lose to buy-and-hold; gross alpha → net loss | StockBench; FINSABER; Alpha Illusion |
| "HMM regimes fix the strategy" | 200-day MA does as well | 31-asset study summary |
| "Meta-labelling doubles Sharpe" | Modest filter/sizing gains; one test found none | Hudson & Thames; QuantConnect forum |
| "A VPS lets you out-scalp HFT" | Races decided in 5–10 µs; retail 10³–10⁴× too slow | Aquilina, Budish & O'Neill 2022 |

## 5. Architecture: copy NautilusTrader's single-threaded core and keep everything else off the hot path

The mature pattern, shared by NautilusTrader and the LMAX exchange, is a single-threaded, event-driven core where data handling, strategy, risk, execution and portfolio are separate components that talk only through a message bus, with network, logging and persistence pushed to background threads; the same strategy code runs in backtest, sandbox and live by swapping only the venue adapter. NautilusTrader's docs name the techniques directly ("domain-driven design, event-driven architecture, messaging patterns … ports and adapters, and crash-only design"), state that "within a node, the core consumes and dispatches messages on a single thread", and describe a RiskEngine that "validates orders against configured checks and applies submission and modification rate limits" ([NautilusTrader Architecture](https://nautilustrader.io/docs/latest/concepts/architecture/)). LMAX's business logic processor ran entirely single-threaded in memory, fed by ring buffers, because "the single biggest limitation on scalability is having multiple writers contend for any item of data" ([Martin Fowler, The LMAX Architecture](https://www.martinfowler.com/articles/lmax.html); [Mechanical Sympathy](https://mechanical-sympathy.blogspot.ch/2011/09/single-writer-principle.html)). For a solo developer this is also the simplest design to reason about and makes replay deterministic. Build-versus-adopt is clear: adopt NautilusTrader (LGPL-3.0, Rust core, Python control plane, stable adapters for Binance, Bybit, OKX, Coinbase, Kraken, Deribit, Hyperliquid, dYdX, Interactive Brokers, Databento and Tardis, version 1.231.0 stable with 2.0.0rc4 pre-releases) or hftbacktest (queue-position and latency-aware L2/L3 simulation, Rust live for Binance Futures and Bybit) and write only the strategy, feature and, where needed, venue-adapter layers ([nautilus_trader GitHub](https://github.com/nautechsystems/nautilus_trader); [hftbacktest docs](https://hftbacktest.readthedocs.io/)). Freqtrade decides once per candle from pandas DataFrames and Hummingbot is market-making oriented; neither suits tick-level scalping ([CCXT vs Freqtrade](https://docs.ccxt.com/docs/comparisons/ccxt-vs-freqtrade)). Nautilus has no MT5 adapter, so an MT5 bot is either a pure MQL5 EA or a hand-rolled asyncio loop.

The hot path contains only: parse tick → update rolling features → model or rule evaluation → synchronous pre-trade risk checks → submit/cancel → kill-switch evaluation. Everything else (tick/decision/order persistence, metrics, Telegram alerts, dashboards, retraining, end-of-day reports) is cold and asynchronous. State management is where home-grown bots die: use deterministic client order IDs as idempotency keys, write intent to durable local storage before sending, never auto-resubmit with a new ID while prior state is unknown, deduplicate fills by execution ID, and run startup plus periodic reconciliation that adopts unknown venue orders and holds the strategy-start barrier until it completes, which is exactly how Nautilus's execution policies behave ([NautilusTrader Execution Policies](https://nautilustrader.io/docs/latest/concepts/execution/policies/); [idempotent order pipeline](https://dev.to/cvchelles/building-an-idempotent-crypto-order-pipeline-in-nodejs-9ip)). Store both exchange and local receive timestamps on every event (Databento supplies up to four nanosecond timestamps per event) so you can measure your own latency distribution ([Databento tick data](https://databento.com/tick-data)); log the mid at decision time so slippage can be split into delay and impact ([QuestDB implementation shortfall](https://questdb.com/docs/cookbook/sql/finance/implementation-shortfall-order/)).

| Component | Responsibility | Path | Suggested tech |
|---|---|---|---|
| Market data adapter | WebSocket/FIX/MT5 feed → normalised events with exchange + local timestamps; stale/gap detection | Hot | Nautilus adapter, asyncio websockets, MT5 `OnTick`; Rust only for very high L2 rates |
| Message bus | Pub/sub, deterministic ordering, replayable | Hot | In-process (Nautilus msgbus); Redis only cross-process |
| Feature/signal engine | Rolling microstructure features, inference, signal events | Hot | numpy/numba; LightGBM via ONNX Runtime or lleaves; rules in plain Python or MQL5 |
| Risk engine | Synchronous pre-trade checks, rate limits, drawdown gates, kill-switch latch | Hot | Pure, unit-tested module; Nautilus RiskEngine config |
| Execution engine / adapter | Order state machine, client IDs, submit/cancel/modify, fills, reconciliation | Hot | Nautilus ExecutionEngine; CTrade in MQL5 |
| Portfolio/cache | Positions, balances, exposure, PnL from events | Hot (memory) | In-memory dataclasses; snapshot to SQLite/Redis |
| Persistence | Append-only ticks, decisions, orders, fills | Cold | Parquet per day (Polars/DuckDB) or QuestDB/ClickHouse |
| Monitoring/alerting | Metrics, heartbeat, dashboards, alerts | Cold | Prometheus + Grafana; Telegram bot |
| Watchdog | Independent process that cancels/flattens when heartbeat is stale | Separate | systemd service with its own cancel-only API key |
| Research/backtest | Same strategy code on historical ticks with fill/latency models; WFA, CPCV, DSR | Offline | Nautilus backtest node, hftbacktest, MT5 real-tick tester |
| Offline intelligence | LLM news/event scoring into a slow feature; regime labelling | Cold | Batch API into Redis key; never in the order path |

Language choice follows the path: Python 3.13+ (asyncio, numpy, Polars) for strategy, research and glue, Rust only if you need sub-100 µs reaction or high-rate L2 book reconstruction (hftbacktest's live path is Rust for this reason), and MQL5 or C# when the platform owns the connection and the tester. Deployment is one VPS in the venue's region, the bot as a systemd service or Docker container with restart-on-failure paired with a persisted kill-switch latch so a crash loop can never re-enter the market, secrets in 0600 env files, and the deployed version hash logged at startup.

## 6. Risk management: pre-trade controls modelled on Rule 15c3-5, limits modelled on FTMO

The canonical warning is Knight Capital. On 1 August 2012 a flag repurposed from dead "Power Peg" code, left on one of eight servers after an incomplete deployment, turned 212 retail orders into **4 million executions in 45 minutes** and a loss of over **$460 million**; 97 automated reject emails referencing "Power Peg disabled" went out before the open and were not acted on, and the SEC found Knight had no automated capital-threshold rejects as Rule 15c3-5 requires ([SEC Order 34-70694](https://www.sec.gov/files/litigation/admin/2013/34-70694.pdf)). Rule 15c3-5 demands controls "implemented on a pre-trade, automated basis" that limit financial exposure through pre-set capital thresholds and prevent erroneous or duplicative orders ([FINRA Market Access Rule](https://finra.org/rules-guidance/guidance/reports/2026-finra-annual-regulatory-oversight-report/market-access-rule)). Translated into a retail bot, every order passes synchronous checks for aggregate and per-instrument exposure caps, maximum order size and notional, a price collar versus current mid (for example ±25 bps on a liquid major), duplicate detection by client order ID and by (symbol, side, qty, 1-second window), maximum orders per second and per minute (5/s and 60/min are sensible defaults for a scalper that is not a market maker), maximum open positions, a stale-data gate (no entries if the last tick is older than 2–5 s, flatten if older than 30–60 s), a connectivity gate, and the kill-switch latch checked at startup. These numeric thresholds are proposals derived from the control categories, not sourced standards.

Position sizing starts from fixed-fractional risk of **0.1–0.5% of equity per trade** (0.25% default), with size equal to risk dollars divided by stop distance including spread. Fractional Kelly is a ceiling, never a target: Thorp and co-authors advise "bet Kelly or less", calling fractional Kelly a blend of Kelly and cash that trades growth for security ([MacLean, Thorp & Ziemba](https://www.stat.berkeley.edu/~aldous/157/Papers/Good_Bad_Kelly.pdf)), and because the edge is estimated and the penalty for over-betting is asymmetric, use at most quarter-Kelly computed from live out-of-sample statistics on a rolling window, capped at roughly 2% of equity in notional risk. The constraint that actually binds a scalper is the losing streak: with a 3% daily limit and ten consecutive losses, per-trade risk cannot exceed 0.3%. FTMO's published objectives are a widely copied template: daily loss of **3–5% of initial capital measured on equity including floating P&L**, reset at 00:00 CE(S)T, and a 10% maximum loss (static or trailing by account type) ([FTMO Trading Objectives](https://ftmo.com/en/trading-objectives/)). A bot can halt itself automatically, so set internal limits tighter than the external ones: soft daily loss 2% (no new entries), hard 3% (flatten and lock to next session), weekly 5%, peak-to-trough 8% (halt and require manual review), 6–8 consecutive losses triggering a 30–60 minute cool-off, and an equity-curve throttle that halves size after a losing 20-trade window.

Stops come in layers. A software stop evaluated on every tick with a market-order exit is primary; a broker-side hard stop placed 1.5–2× wider is purely a disconnect and crash backstop; a time stop closes any scalp that has neither hit target nor stop within 5–15 minutes, since stalled scalps have lost their edge; stop distance is sized from ATR plus spread so it exceeds noise; and trailing begins only after a move of ≥1R. Brokers impose minimum stop and freeze distances and may ignore your deviation on market-execution symbols, so read `SYMBOL_TRADE_STOPS_LEVEL` and `FREEZE_LEVEL` at runtime and treat retcodes 10029 and 10024 as retry-after-backoff, never spin-retry ([MQL5 docs: symbol constants](https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants); [EarnForex freeze level](https://www.earnforex.com/guides/what-is-freeze-level)). Pause trading around scheduled high-impact news rather than widening stops, because flattening in thin liquidity "can cost several ticks of slippage" ([NexusFi emergency protocols](https://nexusfi.com/a/automation/automated-trading-emergency-protocols)).

Cost handling is a gate, not an afterthought. Break-even win rate is 1/(1+R) before costs and **(1+c)/(1+R)** with cost c expressed in R units ([MQL5 blog 779062](https://www.mql5.com/en/blogs/post/779062)); a 5-pip target with a 5-pip stop and 1-pip spread nets +4 on wins and −6 on losses, so break-even is ~60% ([BabyPips forum](https://forums.babypips.com/t/what-is-correct-risk-reward-ratio-for-scalping/80643)). Model round-trip cost as full spread (taker) or expected adverse selection (maker) plus commission plus slippage as a function of volatility and size relative to top-of-book depth, plus funding if the position crosses a funding timestamp; require expected net edge ≥1.5–2× round-trip cost before a strategy is considered viable, and measure realised slippage live as fill minus mid at decision timestamp in bps, using the arrival price as the benchmark ([Talos TCA](https://www.talos.com/insights/execution-insights-through-transaction-cost-analysis-tca-benchmarks-and-slippage)). The kill switch itself is an independent process: the bot pings an outside service every minute and an external watchdog with its own cancel-only API key flattens all positions, cancels all orders and disables trading when more than 30 seconds pass without a heartbeat, writing the trip to a dated file that the bot checks on startup so an automatic restart cannot silently resume; clearing is manual ([NexusFi monitoring](https://nexusfi.com/a/automation/trading-bot-monitoring); [NexusFi emergency protocols](https://nexusfi.com/a/automation/automated-trading-emergency-protocols)). Hummingbot's `kill_switch_rate` is a PnL-rate stop but its docs do not say whether positions are closed, so do not rely on a framework default ([Hummingbot kill switch](https://hummingbot.org/client/global-configs/kill-switch/)).

Overfitting protection is a risk control, not a research nicety. Bailey and López de Prado show that with enough trials "it is guaranteed that a researcher will always find a misleadingly profitable strategy", and the Deflated Sharpe Ratio corrects for the number of trials, non-normality and series length ([Bailey & López de Prado, DSR](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf)); the Probability of Backtest Overfitting via combinatorially symmetric cross-validation estimates how likely the in-sample winner underperforms out of sample ([Bailey et al., PBO](https://papers.ssrn.com/abstract=2326253)). Minimum protocol: log every backtest run so the trial count N is known, keep an untouched final holdout, fix walk-forward windows before fitting (choosing anchored versus rolling after seeing results is meta-overfitting) ([LuxAlgo walk-forward](https://www.luxalgo.com/library/concept/walk-forward-analysis/)), run combinatorial purged CV with an embargo at least as long as the longest label barrier for any ML model ([Purged cross-validation](https://en.wikipedia.org/wiki/Purged_cross-validation)), reject when DSR < 0.95 or PBO is high, require parameter plateaus, and keep a rule-based scalper to fewer than ~5 free parameters.

## 7. Testing pipeline: eight stages, pessimistic fills, and a chaos test before live

Historical tick data comes from three ecosystems. For crypto, Tardis.dev reconstructs tick-level L2 from exchange WebSocket feeds across 50+ exchanges ([Tardis order books FAQ](https://docs.tardis.dev/faq/order-books)) and Binance's own public files cover trades and futures depth ([binance-public-data](https://github.com/binance/binance-public-data/)); for US futures and equities, Databento supplies MBO and MBP-10 with nanosecond multi-timestamps and a data-quality flags field ([Databento tick data](https://databento.com/tick-data)); for FX, Dukascopy SWFX ticks are free but of anecdotal quality ([EliteTrader thread](https://elitetrader.com/et/threads/interpreting-dukascopy-tick-data.352792/)), and MT5's tester downloads the broker's real ticks but silently simulates any missing intervals, with a real-tick EURUSD test using 34 million ticks versus 19 million generated and producing a materially different result ([MQL5 article 2612](https://www.mql5.com/en/articles/2612)). MT5's "modelling quality" percentage "describes how densely the tester filled the intervals with ticks, not how good the underlying data is" ([MQL5 blog 762517](https://www.mql5.com/en/blogs/post/762517)). Validate any source before use: gap distribution per session, weekend and DST boundaries, spread distribution versus your live broker, outlier ticks, and the presence of real bid/ask rather than mid or last. The live broker's own feed is the only one that matches live spreads; backtesting on another vendor's ticks is a known source of backtest-live divergence.

Only two open-source engines model what scalps depend on. hftbacktest offers queue-position-aware fills, feed and order latency models and L2/L3 reconstruction ([hftbacktest docs](https://hftbacktest.readthedocs.io/)); NautilusTrader's fill model has `prob_fill_on_limit` (default 1.0, meaning limit orders fill on touch) and `prob_slippage` (default 0.0), both optimistic until you change them, and walks L2/L3 levels when book data is supplied ([NautilusTrader Fill Models](https://nautilustrader.io/docs/latest/concepts/backtesting/fill-models/)). QuantConnect LEAN assumes complete fills unless you write a custom fill model ([QuantConnect Trade Fills](https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/trade-fills/key-concepts)); vectorbt is for screening parameter sweeps; Backtrader is effectively unmaintained ([TradingStrategy.ai frameworks](https://tradingstrategy.ai/docs/learn/algorithmic-trading-frameworks.html)); bar-based engines cannot order a stop and target inside the same bar at all ([ABC Trading Group](https://www.abctradinggroup.com/backtesting-pitfalls/)). MT5's workflow is screen on "1 minute OHLC", debug on "Every tick", optimise on real ticks with a Fixed Delay set from measured ping ([MQL5 article 2612](https://www.mql5.com/en/articles/2612); [MT5 help: Testing](https://www.metatrader5.com/en/terminal/help/algotrading/testing)).

Paper trading cannot validate a scalper's performance anywhere. Simulators "fill your limit orders on first touch", which "systematically inflates your results", whereas live "your limit order fills when every order ahead of you in the queue has been filled AND an aggressive counter-order matches yours" ([NexusFi paper trading](https://nexusfi.com/a/brokers/paper-trading-futures-simulators)); Alpaca's paper environment delays limit fills by minutes and Topstep's SIM is explicitly "unrealistic". Demo is for validating plumbing: which account, symbol, size and exit orders the bot actually sends, reconciliation after restart, and kill-switch behaviour ([TradersPost](https://blog.traderspost.io/article/paper-trading-strategy-development-guide)). The honest path is to go live at **10–20% of intended size** or the venue's minimum lot ([DayTradingToolkit](https://daytradingtoolkit.com/beginners-guide/paper-to-live-trading-transition)) and scale only when live slippage, fill rate and expectancy match the backtest.

| Stage | Exit criterion (researcher synthesis anchored to sourced rules) |
|---|---|
| 1. Data validation | Gap/outlier/DST audits pass; backtest spread distribution matches live broker |
| 2. In-sample research with trial logging | ≥300 trades, parameter plateau, net edge ≥1.5× round-trip cost |
| 3. Walk-forward (rolling, protocol fixed, ≥5 OOS windows) | Walk-forward efficiency ≥0.5; no catastrophic OOS window |
| 4. DSR / PBO / Monte Carlo | DSR ≥0.95 given logged N; low PBO; 95th-percentile drawdown < max-drawdown limit |
| 5. Shadow mode (real-time data, no orders; Nautilus "sandbox") ≥2 weeks | Signal timing, latency and would-be fills logged; no plumbing bugs |
| 6. Paper/demo ≥2–4 weeks | Order lifecycle, reconciliation, restarts and kill switches exercised incl. forced disconnect |
| 7. Chaos test | Kill process mid-position, drop network, inject duplicate fill, replay stale snapshot; watchdog flattens, restart reconciles without new orders |
| 8. Live minimum size ≥100–200 trades | Realised slippage ≤ modelled + tolerance; fill rate within 10–15% of backtest; expectancy sign matches |
| 9. Stepwise scaling | Double only after each step repeats stage 8; any kill-switch trip resets to the previous step |

The mistakes that make backtests lie cluster into four families. Information leakage: features that use the current bar's close before it closes, repainting indicators, future-shifted joins, and signals at bar close with entry assumed in the same bar ([LuxAlgo backtesting traps](https://www.luxalgo.com/blog/backtesting-traps-common-errors-to-avoid/)). Execution optimism: fills at mid or last rather than ask for buys and bid for sells, limit fills on touch with no queue position, full fills with no rejects or latency, and stop-and-target resolved optimistically within one bar ([NexusFi backtest-to-live gap](https://nexusfi.com/a/automation/backtest-to-live-performance-gap)). Data defects: synthetic ticks, gaps, and a backtest feed that differs from the live broker's. Statistical abuse: too few trades (scalping needs 200–500+), unlogged grid searches, and protocols chosen after seeing results. A scalping backtest with a 60% win rate and ~$400/day was profitable only at zero slippage once realistic costs were added ([dev.to backtesting mistakes](https://dev.to/qcautomation/5-backtesting-mistakes-that-make-your-algo-look-like-a-money-printer-until-it-isnt-2kf1)). Treat any backtest not re-run with pessimistic settings (limit fills on trade-through only, ≥1-tick adverse slippage, latency ≥ measured live round trip) as an upper bound.

## 8. Roadmap: roughly six to nine months from zero to a small live bot, most of it spent on data and validation

The time estimates below assume a developer who already writes Python competently and can give the project 10–15 hours a week; they are this report's synthesis, not sourced durations. The sequence is deliberately data-first and model-last, because the evidence in sections 4 and 7 says the model is the least important and most over-invested component.

| Phase | Weeks | Milestone | Done when |
|---|---|---|---|
| 0. Decide venue and jurisdiction | 1 | Account opened (demo + small live), VPS region chosen, tax elections researched | You can state your round-trip cost in bps and your legal constraints in one paragraph |
| 1. Record your own data | 2–4 (runs in background thereafter) | WebSocket/MT5 recorder on the VPS writing L2 updates, trades and your own acks with exchange + local timestamps to daily Parquet | Measured feed-latency and order-ack latency distributions (p50/p90/p99) |
| 2. Cost and latency reality check | 1 | Spreadsheet of spread, fees, slippage, funding versus candidate targets | Break-even win rate per candidate computed from (1+c)/(1+R) |
| 3. Rule-based trigger research | 3–4 | 1–3 explainable triggers (e.g. imbalance-confirmed mean reversion after a sweep, session-open structure) backtested in Nautilus/hftbacktest or MT5 real-tick with pessimistic fills | ≥300 trades, net edge ≥1.5× cost, parameter plateau, every trial logged |
| 4. Meta-label model | 3–4 | Triple-barrier labels net of fees, ≤25 microstructure features, LightGBM with purged CPCV, exported to ONNX | Precision lift on net-of-cost labels; DSR ≥0.95 with logged N |
| 5. Execution and risk engine | 3–4 | Strategy in Nautilus (or MQL5 EA), 15c3-5-style pre-trade checks, kill-switch latch, independent watchdog, reconciliation on restart | Chaos test passes |
| 6. Shadow and demo | 4–6 | Sandbox then demo on the VPS with Prometheus/Grafana and Telegram alerts | Logged would-be fills and latency; forced-disconnect test passes |
| 7. Live at minimum size | 6–8 | $100-notional crypto or 1 MES/0.01 lot | 100–200 trades; slippage and fill rate within tolerance of backtest |
| 8. Scale and maintain | Ongoing | Monthly re-validation, retraining, DSR tracking on live, tax reconciliation | Each doubling repeats phase 7's criteria; any trip resets a step |

Total: about **24–32 weeks** to a small live bot, with phase 1's recorder started in week one because your own latency-faithful capture is the one dataset nobody sells. Shortcuts that lose time rather than save it: skipping the recorder and buying history that does not match your broker's spreads, starting with an LSTM or transformer, and going to a prop-firm challenge, which bans the approach outright.

## 9. Reality check: most retail scalpers lose, the "million-dollar bot" needs a quant firm, and the legal and tax burdens are real

Every independent dataset says the large majority of active retail speculators lose. Mandatory 2026 disclosures show **69–80% of CFD accounts** losing at IG and Pepperstone, with a 49-broker average of 71.1% ([IG UK](https://www.ig.com/uk/media-centre/press-release-overview/nearly-one-in-four-UK-investors-reduce-exposure-to-domestic-stocks-as-political-uncertainty-reaches-record-high); [Pepperstone](https://pepperstone.com/en/insights/market-analysis); [BrokerRank](https://brokerrank.net/research/retail-loss-rates)); SEBI found **~91% of Indian equity-derivatives traders** lost money in FY25 with aggregate losses of about US$12 billion ([Business Standard](https://www.business-standard.com/markets/news/net-losses-of-traders-in-fo-widens-in-fy25-sebi-study-125070701221_1.html)); of 1,551 Brazilians who day-traded index futures for more than 300 days, **97% lost money** and only 17 earned more than minimum wage, with "no evidence of learning" ([Quantpedia on Chague et al.](https://quantpedia.com/retail-day-trading-is-an-uphill-battle/)); and Barber, Lee, Liu and Odean found "less than 1%" of Taiwanese day traders reliably profitable net of fees over 15 years ([Barber et al.](https://faculty.haas.berkeley.edu/odean/papers/day%20traders/Day%20Trading%20Skill%20110523.pdf)). For prop firms, FPFX data on 300,000 accounts shows ~14% pass a challenge and ~7% of all entrants ever receive a payout, averaging about 4% of nominal account size ([The Prop Firm Guide](https://thepropfirmguide.com/prop-firm-statistics/)); FTMO's 2023 revenue was $203.9 million against $100.3 million of costs, which says the challenge fee is the business model ([Trade Informer](https://tradeinformer.com/prop-weekly/what-ftmo-tells-us-about-prop-firm-finances)). No platform (Myfxbook, MQL5, Darwinex, Collective2) publishes a bot survival rate, and the visible population is survivorship-biased; a typical MQL5 signal advertised "profitable in all 5 years" of backtest while its live stats showed a 0.52 profit factor ([MQL5 signal](https://www.mql5.com/en/signals/2380485)). The absence of bot statistics is a data gap, not evidence that bots do better.

Scalping concentrates every structural disadvantage. Costs are a large fraction of a 3–10 pip target, so break-even win rates of 55–65% are needed before any edge counts; one retail scalper logged 900+ trades and $37 million of notional for a net loss of ~$4k against **over $30k of transaction costs** ([EnergyExch forum](https://www.energyexch.com/thread/469858-a-couple-questions-to-all-the-scalpers-out)). Retail round trips of 50–150 ms are roughly 1,000× slower than colocated firms ([NexusFi HFT](https://nexusfi.com/a/automation/high-frequency-trading-hft-futures)). CFD brokers monitor for trading "around the exact moment of a price update" and classify it as latency arbitrage, move scalpers to worse account types, or void profits; a UK ombudsman case found a client acted within terms after a broker voided profitable trades as "abusive" ([Gate TradFi](https://www.gate.com/help/tradfi/cfd/50268); [Trive policy](https://trive.com/afr/assets/docs/legal-documents/en/Trive_Africa-Scalping_Policy.pdf); [FOS decision](https://www.financial-ombudsman.org.uk/decision/DRN-4175490.pdf)). And published predictors decay substantially after publication ([McLean & Pontiff](https://ivey.uwo.ca/media/3775549/pontiff.pdf)), so a bot is a research-and-maintenance process rather than a one-time build.

The million-dollar question has an arithmetic answer. Medallion, the best fund in history, averaged **66% gross and 39% net** per year from 1988 to 2018 with thousands of staff and closed capital ([CXO Advisory on Cornell](https://www.cxoadvisory.com/?p=33535)); Renaissance's outside funds only target beating the S&P 500 ([Institutional Investor](https://institutionalinvestor.com/article/2ekcf5cio9yw4k7nv7hmo/hedge-funds/renaissance-continues-to-surge)). The table assumes constant monthly returns with no drawdowns, withdrawals, taxes or size limits, which is the best case and not a forecast.

| Start capital → $1m | 2%/month (27%/yr) | 3%/month (43%/yr) | 5%/month (80%/yr) | 10%/month (214%/yr) |
|---|---|---|---|---|
| $5,000 (×200) | ~22 years | ~15 years | ~9 years | ~4.6 years |
| $25,000 (×40) | ~15.5 years | ~10 years | ~6 years | ~3 years |
| $100,000 (×10) | ~10 years | ~6.5 years | ~4 years | ~2 years |

Three percent a month already exceeds Medallion's net average; five exceeds its gross; ten is the figure the CFTC names as the archetypal fraud promise ([CFTC advisory](https://www.cftc.gov/LearnAndProtect/AdvisoriesAndArticles/AITradingBots.html)). Fixed-rate compounding also fails specifically for scalpers: edge is bounded by liquidity at the touch and the number of opportunities per day rather than by capital; brokers cap lots and flag toxic flow; ESMA caps leverage at 30:1 for FX majors and 2:1 for crypto and the US at 50:1 ([Track360](https://track360.io/blog/forex-leverage-regulation-by-region-esma-asic-cftc-2026)); and taxes take 20–45% of gains annually. A 20% drawdown needs +25% to recover and 50% needs +100%, and the leverage required for 5%/month produces such drawdowns by construction. What a million-dollar bot would actually take is the structure of a quant firm: proprietary data, exchange-proximate hosting, a research process with overfitting controls, continuous re-research as edges decay, capital in the millions, and a team. The realistic solo outcomes are a robust modest-frequency system targeting low-double-digit annual returns on $25–100k (3%/month on $25k is ~$750/month gross), several uncorrelated slower strategies rather than one scalper, or revenue from tooling and research, noting that selling signals may itself be regulated activity.

Scams wear the "AI bot" label more than any other. The FBI's IC3 recorded **$20.9 billion** of 2025 internet-crime losses, with crypto investment fraud at $7.2 billion the largest category and $893 million tagged AI-assisted ([Decrypt on IC3](https://decrypt.co/363486/11-4b-lost-to-crypto-scams-in-2025-fbi-internet-crime-report)); the CFTC's Mirror Trading International case involved a "bot" promising 10% a month that took ~29,000 BTC from 23,000 US victims and yielded a $1.7 billion penalty ([CFTC 8772-23](https://www.cftc.gov/PressRoom/PressReleases/8772-23)); and the SEC's 2026 Privvy case charged a founder who raised $12.3 million for "AI arbitrage bots" of which about 3% was ever traded ([The Block](https://www.theblock.co/post/403118/sec-sues-privvy-founder-over-12-3-million-crypto-scheme-as-ai-bots-turn-out-to-be-neither)). The red flags to apply to any vendor, signal group or prop firm: any stated monthly return of 5% or more; "guaranteed", "risk-free" or "100% win rate"; returns paid in deposited crypto with delayed or "taxed" withdrawals; referral or MLM structures; backtest-only or newly opened account "proof" and martingale/grid equity curves; claims of SEC/FCA registration you have not checked yourself; recommended offshore brokers; and any product asking for exchange API keys with withdrawal permission. Belgium's FSMA and Italy's CONSOB have warned that prop trading is "shadow investing" and a "finance video game", and the CFTC's own prop-firm case was dismissed on agency misconduct, leaving the sector unregulated ([Finance Magnates FSMA](https://www.financemagnates.com/forex/fsma-warns-public-against-dubious-practices-of-prop-trading-firms/); [Willkie](https://complianceconcourse.willkie.com/articles/new-jersey-federal-judge-dismisses-forex-case-with-prejudice-and-awards-attorney-fees/)).

Running your own bot on your own account is legal in every jurisdiction covered, with conditions. The US removed the $25,000 Pattern Day Trader rule effective **4 June 2026** in favour of intraday margin ([Federal Register](https://www.govinfo.gov/content/pkg/FR-2026-04-17/html/2026-07485.htm)), keeps retail forex at 50:1, and left crypto market structure unresolved when the CLARITY Act failed a Senate vote in September 2026 ([Orrick](https://www.orrick.com/Insights/2026/10/The-CLARITY-Act-Stalls-in-the-Senate-Whats-Next-for-Digital-Asset-Regulation)). The EU caps CFD leverage and in February 2026 ESMA declared that instruments marketed as perpetual futures fall under CFD intervention measures regardless of name ([Regulation Tomorrow](https://www.regulationtomorrow.com/2026/02/esma-reminds-firms-of-their-obligations-under-cfd-product-intervention-measures-amid-rising-offerings-of-perpetual-futures/)); MiFID II Article 17 algo obligations bind investment firms and venue members rather than clients trading through a broker, but the own-account exemption is withdrawn for anyone applying high-frequency techniques, so scaling past retail-broker access changes your regulatory status ([ESMA Art. 17](https://www.esma.europa.eu/publications-and-data/interactive-single-rulebook/mifid-ii/article-17-algorithmic-trading)). India now requires retail algos to run through broker APIs with exchange registration, fully mandatory from 1 April 2026 ([Taxscan](https://www.taxscan.in/top-stories/sebi-extends-timeline-for-retail-algo-trading-framework-full-implementation-from-apr-1-2026-1433982)); Australia's CFD order runs to May 2027 with a proposed extension to 2037 ([ASIC 26-239MR](https://asic.gov.au/about-asic/news-centre/find-a-media-release/2026-releases/26-239mr-asic-moves-to-extend-and-strengthen-cfd-consumer-protections)). Market-abuse law applies to the operator regardless of who "decided": the DOJ charged the humans running wash-trading bots in April 2026 ([CoinDesk](https://www.coindesk.com/business/2026/04/02/doj-sting-exposes-crypto-wash-trading-continues-to-be-far-more-common-than-expected)), and naive cancel/replace storms or self-matching across sub-accounts can look like spoofing or layering.

Tax is where a scalper's event count bites. Twenty round trips a day for 250 days is 5,000 taxable disposals a year, which no spreadsheet survives. In the US, trader status is defined by IRS Topic 429, the Section 475(f) mark-to-market election must be filed by the prior year's return deadline, spot forex defaults to Section 988 ordinary treatment with any opt-out required before positions are opened, regulated futures get 60/40 treatment, and crypto brokers now issue Form 1099-DA with cost basis reported for assets acquired from 2026 under per-wallet tracking rules ([IRS Topic 429](https://www.irs.gov/taxtopics/tc429); [IRS 1099-DA instructions](https://www.irs.gov/instructions/i1099da); [Harness](https://www.harness.co/articles/new-1099-da-broker-reporting-rules-for-2026-what-crypto-investors-need-to-know)). The UK taxes CFD, forex and crypto gains at 18%/24% above a £3,000 allowance while spread betting is outside CGT unless HMRC reclassifies it as your trade ([gov.uk CGT](https://tnaqa.mirrorweb.com/ukgwa/20260715154742mp_/https://www.gov.uk/capital-gains-tax/print); [IG tax](https://www.ig.com/uk/spread-betting/spread-betting-vs-cfds/tax)); Germany charges 25% plus solidarity surcharge and repealed the €20,000 derivatives loss cap in the JStG 2024 ([CMS Law](https://cms.law/de/deu/legal-updates/Verlustverrechnungsbeschraenkung-bei-Termingeschaeften-Gesetzgeber-schafft-Vorschrift-ab)); France applies the 30% flat tax to crypto ([Coincub](https://coincub.com/blog/europe-crypto-tax-guide/)); India taxes F&O as business income at slab rates and crypto at a flat 30% plus 1% TDS with no loss offset ([Quicko](https://learn.quicko.com/fo-trading-tax-treatment); [KoinX](https://www.koinx.com/stats/crypto-tax-rates-by-country)). Because most scalpers lose, the loss-handling asymmetry matters as much as the rate: US Section 988 losses are fully deductible, UK spread-bet losses are not, Indian crypto losses cannot be set off. A 3%/month gross becomes roughly 32%/year at a 25% flat rate and 25%/year at a 40% marginal rate, which should be fed back into the compounding table above.

## Conclusion

The research reframes the project. The interesting engineering problem is not the model but the measurement apparatus around it: your own timestamped capture of feed and order latency, a cost model honest enough to kill most ideas, a trial log that makes the Deflated Sharpe Ratio computable, and an independent watchdog that assumes the bot will one day misbehave. Once those exist, the choice of learner becomes almost incidental, and a LightGBM filter on a transparent trigger will outperform a transformer on raw ticks in every way that matters live. The second reframing is about the holding period. "Scalping" at seconds is a race the literature shows is decided in microseconds; at minutes, on a venue with free depth and maker rebates, the same microstructure features become a legitimate adverse-selection filter for passive entries, which is the one place where the peer-reviewed signal maps onto a positive-expectation structure.

The implication for ambition is that compounding is the wrong mental model for a scalper and capacity is the right one: edge is bounded by opportunities per day and liquidity at the touch, so the bot's realistic ceiling is an income stream proportional to a modest capital base, not an exponential curve. Building it well still has value, because the same discipline (cost-aware validation, state reconciliation, risk latches, lot-level records) transfers directly to slower strategies with more capacity, and a portfolio of those is the path that the evidence, rather than the marketing, supports.

## The 5 most important next steps this week

1. **Pick the venue by jurisdiction and write down your all-in round-trip cost in basis points.** Non-US/non-EU: open Binance or Bybit demo plus a small live account; US: open a Tradovate or Rithmic-backed futures account; FX-only: an IC Markets or Pepperstone raw-spread MT5 demo. Compute break-even win rate from (1+c)/(1+R) for a 10 bp and a 20 bp target before writing any strategy code.
2. **Rent the VPS in the right region and start recording your own data today.** An AWS Tokyo/Singapore t3.medium (or MetaQuotes VPS for a pure EA) running a WebSocket or MT5 tick recorder that writes L2 updates, trades and your own test-order acks with exchange and local timestamps to daily Parquet files. This dataset is the one input nobody sells and every later stage depends on it.
3. **Measure your latency distribution with ten tiny test orders.** Log decision timestamp, ack timestamp and fill timestamp; record p50/p90/p99. The p90 becomes the entry delay in every label and backtest you build.
4. **Stand up NautilusTrader (or the MT5 real-tick tester) with pessimistic fills and a trial log.** Set `prob_fill_on_limit` below 1 and `prob_slippage` above 0, load the Binance order-book tutorial or your broker's real ticks, and create the experiment log that will feed the Deflated Sharpe Ratio from the first backtest onward.
5. **Settle the legal and tax scaffolding before the first live trade.** Confirm your broker's terms on scalping and EAs, check whether any Section 475(f)/988 election or local equivalent must be made in advance, set up lot-level trade accounting, and create a separate cancel-only API key for the watchdog process.
