# MetaTrader 4 vs MetaTrader 5 programmatic trading APIs for an AI-driven scalping bot (state as of mid-November 2026)

Scope note: "official" below means shipped/documented by MetaQuotes (MQL4/MQL5 language, the `MetaTrader5` pip package, Manager/Web API). Everything else (ZeroMQ bridges, MetaApi.cloud, mt5linux, mtapi, REST gateways) is third-party. Dates of sources are given inline where known. Web search/fetch quota was exhausted part-way through; a few items were taken from search-result snippets rather than fetched pages and are flagged as such.

## Key Question 1: Do MT4 and MT5 have official APIs for placing/modifying/closing orders, and what exactly exists?

### Takeaway
MT5 has three official programmatic routes for a retail account: MQL5 code running inside the terminal (`OrderSend`/`OrderSendAsync`, `CTrade`), the official `MetaTrader5` Python package (Windows-only, talks to a running terminal over IPC), and a broker-side Manager/Web API that is not available to retail traders. MT4 has only MQL4 inside the terminal (`OrderSend`, `OrderClose`, `OrderModify`); there is no official external/Python API for MT4, so every "MT4 Python API" is a third-party bridge EA.

### Cited Findings
- MQL5 trade requests are described by `MqlTradeRequest` with fields `action, magic, order, symbol, volume, price, stoplimit, sl, tp, deviation, type, type_filling, type_time, expiration, comment, position, position_by`; `deviation` is "maximum acceptable deviation from the requested price, in points"; `position` is the "position ticket, used to change or close a specific position" — [MQL5 docs: order_send](https://www.mql5.com/en/docs/python_metatrader5/mt5ordersend_py)
- `TRADE_REQUEST_ACTIONS`: `TRADE_ACTION_DEAL` (market order executed immediately), `TRADE_ACTION_PENDING`, `TRADE_ACTION_SLTP` ("changes the stop loss and take profit of an open position"), `TRADE_ACTION_MODIFY`, `TRADE_ACTION_REMOVE`, `TRADE_ACTION_CLOSE_BY` ("closes a position by an opposite position") — [MQL5 docs: order_check](https://www.mql5.com/en/docs/python_metatrader5/mt5ordercheck_py)
- `ORDER_TYPE_FILLING`: `ORDER_FILLING_FOK` (full volume or nothing), `ORDER_FILLING_IOC` (fill what is available, cancel remainder), `ORDER_FILLING_RETURN` (partial fill leaves remainder active; "applies only to market, limit, and stop-limit orders on symbols with Market or Exchange execution") — [MQL5 docs: order_check](https://www.mql5.com/en/docs/python_metatrader5/mt5ordercheck_py)
- Symbol-level filling flags: `SYMBOL_FILLING_FOK`=1, `SYMBOL_FILLING_IOC`=2, `SYMBOL_FILLING_BOC`=4 ("must rest in the Depth of Market and cannot execute immediately, or it is cancelled. Only limit and stop-limit orders"); Return mode "is disabled in Market execution mode" — [MQL5 docs: symbol constants](https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants)
- `OrderSendAsync` "does not hold the program operation while waiting for the function execution result", is "meant for high-frequency trading", returns `TRADE_RETCODE_PLACED` (10008) which "means only the fact of sending"; results arrive in `OnTradeTransaction`, which "is called several times for one request" — [MQL5 docs: OrderSendAsync](https://www.mql5.com/en/docs/trading/ordersendasync)
- `CTrade` (Trade/Trade.mqh) exposes `SetExpertMagicNumber`, `SetDeviationInPoints`, `SetTypeFilling`, `SetTypeFillingBySymbol`, `SetAsyncMode`, `SetMarginMode`, `PositionOpen`, `PositionModify`, `PositionClose`, `PositionClosePartial`, `PositionCloseBy`, `Buy`, `Sell`, `BuyLimit/BuyStop/SellLimit/SellStop`, `OrderOpen/OrderModify/OrderDelete`, plus `ResultRetcode`, `ResultDeal`, `ResultOrder`, `ResultPrice`, `CheckResult*` — [MQL5 docs: CTrade](https://www.mql5.com/en/docs/standardlibrary/tradeclasses/ctrade)
- MQL4's `OrderSend(symbol, cmd, volume, price, slippage, stoploss, takeprofit, comment=NULL, magic=0, expiration=0, arrow_color=clrNONE)` returns the ticket or -1; stale price gives error 138 `ERR_REQUOTE` "independently on the slippage parameter"; stops too close give error 130 `ERR_INVALID_STOPS`; min stop distance read via `MarketInfo(..., MODE_STOPLEVEL)`; a zero stop level may mean the server "utilizes some external mechanisms for dynamic level control" so error 130 can still occur — [MQL4 docs: OrderSend](https://docs.mql4.com/trading/ordersend)
- MQL4 trade functions are the order-ticket model: `OrderSend, OrderClose, OrderCloseBy, OrderModify, OrderDelete, OrderSelect, OrdersTotal, OrdersHistoryTotal` — [MQL4 docs: OrderSend sidebar](https://docs.mql4.com/trading/ordersend)
- The official Python package is documented only for MetaTrader 5 ("MetaTrader 5 package for Python ... obtaining of exchange data via interprocessor communication directly from the MetaTrader 5 terminal") — [MQL5 docs: Python integration](https://www.mql5.com/en/docs/python_metatrader5)
- MT5 Manager API is for brokers: it "lets a broker write its own administrator and manager utilities, or a custom manager terminal"; the Web API is for "connecting the platform to a company's web resources and other services" — [MetaQuotes broker page (RU)](https://www.metatrader5.com/ru/brokers); a `mt5manager` PyPI package exists whose docs point to support.metaquotes.net — [PyPI mt5manager](https://pypi.org/project/mt5manager); a vendor describes the Web API as "a RESTful and WebSocket-based interface provided by MetaQuotes that allows external applications to communicate with the MT5 trading server" — [B2Broker](https://b2broker.com/news/web-api-for-metatrader-how-does-it-work/)
- Trade server return codes relevant to bots: 10024 `TRADE_RETCODE_TOO_MANY_REQUESTS` "Too frequent requests"; 10029 `TRADE_RETCODE_FROZEN` order/position frozen — [MQL5 docs: trade return codes](https://mql5.com/en/docs/constants/errorswarnings/enum_trade_return_codes)

### Inferences
- The Manager/Web API require a server-side license (the broker's MT5 server), so for a retail developer the realistic "official" surface is MQL5 in-terminal plus the Python package; the Web API is not something a retail account can activate (a 2026 mql5.com forum question asking whether a demo account is enough to test the Web API had no answer in results — [forum](https://www.mql5.com/en/forum/496437)).
- Because MT4 has no IPC/Python layer and no `OnTradeTransaction`-style async event model, any MT4 automation from Python is necessarily EA + bridge (DLL sockets, files), with the latency and maintenance costs described in Q4.

### Gaps
- No official MetaQuotes page was retrieved that states "Web API/Manager API is broker-only" in those words; this is inferred from the broker-page description and the vendor ecosystem.
- `ORDER_FILLING_BOC` is listed under symbol flags but the Python `order_check` page did not list it as an order filling value; not verified whether the Python package exposes `ORDER_FILLING_BOC`.

## Key Question 2: The official `MetaTrader5` Python package: capabilities, requirements, latency characteristics, and working code

### Takeaway
The package (v5.0.6231, released 27 Sep 2026, Windows x86-64 wheels only, Python 3.6–3.14) is a synchronous, poll-only IPC client of a running MT5 terminal: it can read ticks/bars/DOM and send/modify/close via `order_send`, but it has no push callbacks, `order_send` blocks until the broker replies, and the GIL prevents parallel sends. It is excellent for research and acceptable for second-scale automation; it is a poor fit for sub-second scalping.

### Cited Findings
- PyPI: version 5.0.6231 "Released: Sep 27, 2026"; "Python <4, >=3.6"; classifiers and wheels for CPython 3.6–3.14; every release file is a Windows x86-64 wheel, no sdist; MIT license; author MetaQuotes Ltd.; platform launch and sync with broker "performed automatically" on `initialize` — [PyPI MetaTrader5](https://pypi.org/project/MetaTrader5/)
- Function surface: `initialize, login, shutdown, version, last_error, account_info, terminal_info, symbols_total, symbols_get, symbol_info, symbol_info_tick, symbol_select, market_book_add, market_book_get, market_book_release, copy_rates_from, copy_rates_from_pos, copy_rates_range, copy_ticks_from, copy_ticks_range, orders_total, orders_get, order_calc_margin, order_calc_profit, order_check, order_send, positions_total, positions_get, history_orders_total, history_orders_get, history_deals_total, history_deals_get` — [MQL5 docs: Python integration](https://www.mql5.com/en/docs/python_metatrader5)
- Communication is "interprocessor communication directly from the MetaTrader 5 terminal"; the only subscription-style API documented is Market Depth (`market_book_add`) and even that is read by polling `market_book_get`; no event callbacks are documented — [MQL5 docs: Python integration](https://www.mql5.com/en/docs/python_metatrader5)
- `symbol_info_tick` returns the last tick with the `MqlTick` fields and `None` on error; "the symbol must be enabled in Market Watch" — [MQL5 docs: symbol_info_tick](https://www.mql5.com/en/docs/python_metatrader5/mt5symbolinfotick_py)
- `order_send` example: enable symbol via `symbol_select` if not `visible`, `TRADE_ACTION_DEAL` + `ORDER_TYPE_BUY` at ask with `sl/tp = price ∓ 100*point`, `deviation=20`, `ORDER_FILLING_RETURN`; close by sending the opposite `ORDER_TYPE_SELL` deal with `position` = the opening position ticket at bid; success is `result.retcode == TRADE_RETCODE_DONE` (10009) — [MQL5 docs: order_send](https://www.mql5.com/en/docs/python_metatrader5/mt5ordersend_py)
- `order_send()` in the Python package is synchronous ("the caller has to wait for the MT5 server response before proceeding"); a user trying to parallelize with threads reported that the GIL means "each thread has to run one by one and this is equivalent to send order in the main thread one by one" — [mql5.com forum: Asynchronous OrderSend() in Python](https://www.mql5.com/en/forum/454563)
- Tick timestamps from Python (`symbol_info_tick().time/time_msc`) are broker-server time, reported ~10,800 s ahead of UTC on MetaQuotes-Demo by a user on Python 5.0.6180, terminal builds 6238/6241 — [mql5.com forum (Nov 2026)](https://www.mql5.com/en/forum/517763)
- A separate Oct-2026 user comparison of 476 Python polls vs 120 native MQL5 tick samples found that `SymbolInfoTick()` and `CopyTicksRange()` can return different bid/ask at identical ms timestamps; the author states the comparison "did not establish verified subsecond synchronization or arrival latency" — [mql5.com forum](https://www.mql5.com/en/forum/520318) (search snippet; thread not fully read)
- No controlled benchmark of Python `order_send` latency in ms was found; the closest MetaQuotes figure is for MQL5 itself: average synchronous trade operation 9.59 ms vs 0.09 ms asynchronous (MQL5 vs QLUA benchmark) — [MQL5 article 2635](https://www.mql5.com/en/articles/2635)
- Real-world terminal-to-broker numbers from an mql5.com thread (Apr–May 2024): terminal status showed ~0.5 ms ping but the journal showed ~40 ms from entering a trade to logged entry (user in Equinix NY); "network delivery typically takes 20 to 200 ms"; "full fills typically take about 60 to 200ms in MT5 and 200 to 400ms in MT4" (forum estimates, not measured standards) — [mql5.com forum: Latency for trading](https://mql5.com/en/forum/465784)
- An Aug-2026 mql5.com blog says Python's "communication layer may add delay" vs an in-terminal EA, "a connected MT5 terminal must be running", and warns "Do not assume a specific latency number will apply to every setup" — [MQL5 blog: MQL5 vs Python (12 Aug 2026)](https://www.mql5.com/en/blogs/post/774018)
- A second Aug-2026 blog warns that direct order submission from Python "can bypass the EA's risk logic, broker-aware validation, and position-management policy" and recommends timing every stage "from market snapshot to broker response", noting "tail latency matters more than averages" — [MQL5 blog: Connecting Python AI models to MT5 (21 Aug 2026)](https://www.mql5.com/en/blogs/post/774493)

### Inferences
- "No push callbacks" is an inference from the documented function list (no `on_tick`, no subscription other than DOM); you must spin a loop calling `symbol_info_tick`/`copy_ticks_from` and dedupe on `time_msc`. Every poll is an IPC round-trip to the terminal; the package does not publish its per-call overhead, so you must measure it yourself.
- For scalping, the practical latency floor is dominated by terminal→broker (tens of ms even co-located) plus broker processing, so the Python IPC hop (unmeasured publicly; likely low single-digit ms per call) is not the main problem; the lack of events and the blocking `order_send` are.

### Complete Python example (official package; tested-looking, not executed here)

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
        time.sleep(1.0)                          # beware broker min-hold rules; see Q7
        close_position(find_position(SYMBOL, MAGIC))
    finally:
        mt5.shutdown()
```

Notes on the snippet (all tied to cited docs above): `order_send` field names and `TRADE_ACTION_*`/`ORDER_FILLING_*` constants follow the official pages; `position` must be set to close a specific position; `deviation` is in points; `10010` (`TRADE_RETCODE_DONE_PARTIAL`) and the filling bitmask values (FOK=1, IOC=2) come from the return-code and symbol-constant pages. `account_info().margin_mode == 2` corresponds to `ACCOUNT_MARGIN_MODE_RETAIL_HEDGING` (see Q7); verify against your build.

### Gaps
- No published measurement of the Python↔terminal IPC overhead per call (ms); you must benchmark `symbol_info_tick` and `order_send` on your own host.
- Whether `initialize()` can attach to a terminal running as a different Windows user/session was not verified.

## Key Question 3: Running the `MetaTrader5` package (and the terminal) on Linux via Wine/Docker — options and caveats

### Takeaway
The package has Windows-only wheels, so Linux users run a Windows Python inside Wine and bridge to it (mt5linux over RPyC) or use community Docker images that wrap MT5+Wine+bridge; all of these are unofficial, version-pin sensitive, and add another IPC hop — acceptable for research, questionable for a latency-sensitive live bot.

### Cited Findings
- MetaQuotes' own help says the platform runs on Linux using Wine — [MetaTrader 5 help: Install on Linux](https://www.metatrader5.com/en/terminal/help/start_advanced/install_linux.md)
- mt5linux: "uses wine, rpyc and a Python Windows version"; a Windows Python inside Wine hosts an RPyC server (TCP :18812 by default) and the Linux Python imports `MetaTrader5` from `mt5linux` — [GitHub tiloye/mt5linux](https://github.com/tiloye/mt5linux); [PyPI mt5linux](https://pypi.org/project/mt5linux)
- A reported working pin set: Wine 10.0, MetaTrader5 5.0.5735, Windows Python 3.10.11, `numpy<2.0` inside the prefix, Linux client Python 3.11 — [GitHub tiloye/mt5linux](https://github.com/tiloye/mt5linux) (via search summary)
- Docker options: an image running MT5 on Wine with an mt5linux bridge on a mapped port — [Docker Hub mintjetos/metatrader](https://hub.docker.com/r/mintjetos/metatrader); a headless project running MT5 on WineHQ Staging exposing a Flask REST API — [GitHub pixelwhiz/metatrader5-quant-server-python](https://github.com/pixelwhiz/metatrader5-quant-server-python); an MT5 client with VNC — [Docker Hub crazykoodaa/mt5_client_vnc](https://hub.docker.com/r/crazykoodaa/mt5_client_vnc); mql5.com thread on Docker/Linux/MT5 — [mql5.com forum 345149](https://www.mql5.com/en/forum/345149)
- DWX Connect's README gives Linux paths for the MT4 Files folder under `~/.wine/drive_c/...`, i.e. the file bridge is used under Wine — [GitHub darwinex/dwxconnect](https://github.com/darwinex/dwxconnect)
- The DWX ZeroMQ connector states it "has not been tested under emulators such as WINE or VMware" and targets Windows 10 only — [GitHub darwinex/dwx-zeromq-connector](https://github.com/darwinex/dwx-zeromq-connector)
- MQL5 VPS does not support Python or DLL-based EAs (forum consensus; "MQL5 VPS does not support Python ... users can't install Python, its libraries, or other external software") — [mql5.com forum: Python use on VPS](https://www.mql5.com/en/forum/509181); DLL imports not allowed on MQL5 VPS — [mql5.com forum 377409](https://www.mql5.com/en/forum/377409)

### Inferences
- Linux+Wine adds: (1) Wine's networking/timer behaviour, (2) an RPyC/TCP hop on top of the terminal IPC, (3) numpy/Python version coupling. None is documented by MetaQuotes; treat as research-only or run the live bot on a Windows VPS near the broker.

### Gaps
- No latency measurements for mt5linux/Wine setups were found.
- Current mt5linux PyPI release date/maintenance status not verified (fetch quota).

## Key Question 4: Third-party bridges (ZeroMQ, file, REST/MetaApi, .NET, gRPC), FIX from brokers, and in-terminal ONNX — compared on latency, reliability, maintenance

### Takeaway
Every external bridge is "EA inside the terminal + transport to your process"; latency and reliability are set by the transport (files ≈ 5 ms polling, ZeroMQ/TCP ≈ sub-ms local, cloud REST/websocket ≈ +6 ms median plus internet) and by how well the EA is maintained. ONNX inference natively in MQL5 (since 2023, improved through 2026) removes the bridge entirely and is the only option that also works on MQL5 VPS and in the Strategy Tester. Retail FIX exists but is gated by very high volume/deposit thresholds at most brokers.

### Cited Findings
**ZeroMQ / socket bridges**
- DWX ZeroMQ connector (Darwinex): MT4-only EA + Python; needs `libzmq.dll`/`libsodium.dll` in MQL4/Libraries (libzmq ≥4.2.5, pyzmq ≥17.1.2); supports open/modify/close (by ticket/magic/all), open trades, history, bid/ask stream; README says the project "will soon be archived (available to use, but not actively maintained)"; BSD-3; successor is DWX Connect — [GitHub darwinex/dwx-zeromq-connector](https://github.com/darwinex/dwx-zeromq-connector)
- vnpy_mt5 gateway is "built on an MT5 ZeroMQ connection and supports all MT5 trading, but only for netting position mode" — [GitHub vn-crypto/vnpy_mt5](https://github.com/vn-crypto/vnpy_mt5) (search snippet)
- Precompiled ZeroMQ DLLs/MQL bindings (mql-zmq by Ding Li, Apache-2.0) are what most MT4/MT5 ZMQ bridges embed — [Gitee mirror mql-zmq](https://gitee.com/vnpyx/mql-zmq); original bundled in DWX repo — [GitHub darwinex/dwx-zeromq-connector](https://github.com/darwinex/dwx-zeromq-connector)
- MQL5 has native socket functions (`SocketCreate, SocketConnect, SocketSend, SocketRead, SocketIsConnected, SocketClose`) so an MT5 EA can be a TCP client without any DLL — [MQL5 docs: Network functions](https://www.mql5.com/en/docs/network); a 2020 article says sockets were added "about a year ago" (≈2019) — [MQL5 article 7117](https://www.mql5.com/en/articles/7117?print=)
- A 2026 mql5.com article describes a TCP→gRPC Python shim relaying protobuf messages from an EA — [MQL5 article 24008](https://www.mql5.com/en/articles/24008) (search snippet)
- MQL5-PyBridge (ZeroMQ/WebSocket/named pipe options) exists but its "zero-latency" claims are unverified README text — [GitHub mirror jackal-eye/MQL5-PyBridge](https://1clonegithubbyxjn.1934672944.workers.dev/jackal-eye/MQL5-PyBridge)

**File-based bridge**
- DWX Connect: "simple, file-based communication mechanism", server EA for MT4 (`dwx_server_mt4.mq4`) and MT5 (`dwx_server_mt5.mq5`), Python client; EA polls on `MILLISECOND_TIMER`; Python `sleep_delay` default 0.005 s (5 ms); commands can collide ("Python side is not able to write to the command file when the mql side is just reading it", handled by `max_retry_command_seconds`); "cannot be used for backtesting"; on_tick/on_bar_data/on_historic_data callbacks; MaximumOrders/MaximumLotSize guards — [GitHub darwinex/dwxconnect](https://github.com/darwinex/dwxconnect)

**.NET / WebSocket**
- mtapi (vdemydiuk): ".NET bridge for MetaTrader (MT4/MT5) that enables C# applications to execute MQL commands and receive trading events via WebSockets"; "not API for connection to MT servers directly"; EA listens on 8222 (MT4) / 8228 (MT5); MIT; latest MT4 tag v1.0.43; current maintenance not confirmed — [GitHub vdemydiuk/mtapi](https://github.com/vdemydiuk/mtapi)

**gRPC reimplementations (no terminal)**
- pymt5 / MetaRpcMT5 is "a separate async client that reimplements these calls rather than using the desktop terminal" and documents a comparison with the official package — [pymt5 docs](https://pymt5.readthedocs.io/en/latest/python_api_detailed_comparison.html) (not independently verified; appears to depend on a hosted gRPC gateway)

**Cloud REST/websocket: MetaApi.cloud**
- "Same stable API for both MT4 and MT5", "Supports any MetaTrader broker", websocket streaming + SDKs (Python/JS), real-time prices and "ECN Level-2 market depth" — [metaapi.cloud](https://metaapi.cloud/)
- "Median trade execution latency introduced by our servers was measured to be 6ms"; streaming latency added "less than 1ms"; NY server to NY broker network latency "under 0.5ms"; latency is "added on top of the broker's own latency"; avg per-account uptime >99.5%, high-reliability tier up to 99.96%; each server start billed for 6 hours — [MetaApi FAQ](https://metaapi.cloud/docs/client/faq/)
- "the primary intended use of REST API is creating trade monitoring applications" (trading via REST is possible but secondary) — [MetaApi REST docs](https://metaapi.cloud/docs/client/) (search snippet)
- Rate limits (CPU credits): per application 1000 credits/s, 6000/min, 18000/h, 43200/6h, multiplied by number of deployed accounts; per front-end server 2000/s (12 servers at time of writing); per account 5000 credits per 10 s; each REST read call (account info, positions, orders, …) costs 50 credits; 5 concurrent historical-data requests per account; streaming credits per account 31,500/10 s, 126,000/min, 315,000/5 min with 2 credits per quote/candle and 1 per tick/book entry ("5 minute limit allows you to receive approximately 200K ticks ... daily throughput on most active EURUSD symbol") — [MetaApi rate limiting](https://metaapi.cloud/docs/client/rateLimiting/)
- Pricing (search snippet of metaapi.cloud; pricing page returned 404 on fetch): Regular subscription $30/month, Extended $100/month (ex-VAT), Manager API add-on $125 per MT server/month; a free tier for "testing and personal use" is mentioned in docs — [metaapi.cloud](https://metaapi.cloud/) / [MetaApi CopyFactory FAQ](https://metaapi.cloud/docs/copyfactory/faq/). Treat exact prices as unverified.

**FIX API from brokers (retail)**
- Pepperstone: "account holders with a minimum trading volume of €160 million per month can request access to our FIX demo environment" (AU page: AUD 250m/month); standard API requires requesting an API key — [Pepperstone API trading](https://pepperstone.com/en/platforms/integrations/api-trading/)
- Darwinex advertises "TWS API, FIX API, MetaTrader 4 and 5" — [GitHub darwinex/dwxconnect README](https://github.com/darwinex/dwxconnect); a review says clients can "access Darwinex liquidity via FIX" — [tradingbrokers Darwinex review](https://tradingbrokers.com/?p=2195). Requirements not found.
- IC Markets: review sites list FIX API alongside MT4/MT5/cTrader; no FIX-specific minimum found; third-party claim of no minimum holding time — [intercom guide on IC Markets](https://intercom.help/theguides/en/articles/16559589-is-ic-markets-a-good-broker-for-you); [investingoal](https://investingoal.com/ic-markets-review)
- Typical institutional gating example: "deposit at least USD 50,000, and may face a monthly minimum commission" (Advanced Markets, 2018) — [LiquidityFinder / Advanced Markets blog](https://liquidityfinder.com/news/advanced-markets-blog-fix-api-how-to-get-one); cTrader FIX is available to retail without such thresholds — [cTrader FIX help](https://help.ctrader.com/fix/); FXCM documents a retail FIX API — [FXCM FIX docs](https://fxcm-api.readthedocs.io/en/latest/fixdocs/fixapi.html)

**ONNX natively in MQL5**
- ONNX support lets you "run ONNX models directly in the MetaTrader 5 terminal"; functions `OnnxCreate, OnnxCreateFromBuffer, OnnxRun, OnnxSetInputShape, OnnxSetOutputShape, OnnxRelease`; `OnnxCreate` loads from `MQL5\Files` (flags `ONNX_COMMON_FOLDER`, `ONNX_DEBUG_LOGS`) — [MQL5 docs: OnnxCreate](https://www.mql5.com/en/docs/onnx/onnxcreate); [MQL5 docs: ONNX intro](https://www.mql5.com/en/docs/onnx/onnx_intro)
- MetaQuotes article (5 Apr 2023): train CNN-LSTM in Keras, export with tf2onnx, embed via `#resource`, `OnnxCreateFromBuffer(ExtModel, ONNX_DEFAULT)`, `OnnxSetInputShape(h, ONNX_DEFAULT, {1,SAMPLE_SIZE,1})`, `OnnxSetOutputShape(h, 0, {1,1})`, `OnnxRun(h, ONNX_NO_CONVERSION, x, y)`; debug log shows "Adding default CPU execution provider" (no GPU provider mentioned); "Not all models have fully defined sizes input and/or output tensor" so shapes must be set; changing an embedded model requires recompiling; terminal dump shows build 3640 — [MQL5 article 12373](https://www.mql5.com/en/articles/12373)
- MT5 build 5572 (Jan 2026) "ONNX and Chart Rendering Improvements" — [MT5 release notes build 5572](https://www.metatrader5.com/en/releasenotes/terminal/2426); 2026 article on an OO ONNX inference engine in MQL5 — [MQL5 article 22527](https://www.mql5.com/en/articles/22527)
- MQL5 execution speed is "comparable to that of C++ applications" (MetaQuotes benchmark claim) — [MQL5 docs: ONNX intro](https://www.mql5.com/en/docs/onnx/onnx_intro)

### Inferences
- Latency ladder (local machine, same host): in-terminal MQL5+ONNX < MQL5 EA + native `Socket*`/ZeroMQ to a local Python process (sub-ms transport, but you add Python inference time) < official Python package polling (IPC per call) ≈ file bridge (5 ms poll default) << cloud REST/websocket (≥6 ms added + WAN). All of these sit on top of 20–200 ms terminal↔broker delivery (Q6).
- Maintenance burden: ZeroMQ bridges need DLLs (forbidden on MQL5 VPS, flagged by terminal security), DWX ZMQ is being archived, DWX Connect is simple but file-polling; MetaApi outsources maintenance but adds cost, a vendor dependency and rate limits; ONNX-in-MQL5 has zero runtime dependencies but ties you to CPU inference and MQL5's model-loading workflow.

### Gaps
- Could not fetch MetaApi's pricing page (404) or confirm per-account pricing; could not fetch Darwinex platforms page (redirect loop) for FIX terms.
- No source for the exact MT5 build that introduced ONNX (article dated April 2023 shows build 3640).
- Whether MQL5 ONNX supports GPU/DirectML execution providers was not confirmed (only the CPU provider appears in the cited log).

## Key Question 5: MT4 status in 2026 and why new projects should pick MT5

### Takeaway
MetaQuotes announced in January 2018 that it would stop selling MT4 licenses and would not issue new MT4 servers; by December 2024 Finance Magnates reported MT4 as "no new licenses, brokers pushed to MT5" with fee increases from 1 Jan 2025; in November 2026 OANDA Japan shut MT4 (14 Nov 2026) citing security and stating MetaQuotes "has ceased official support and system maintenance for MT4". MT5 meanwhile received builds 5572 → 6230+ in 2026 with ONNX, MCP/AI-assistant and tester upgrades.

### Cited Findings
- Finance Magnates, 12 Jan 2018: MetaQuotes "will stop selling MT4"; "New licenses will no longer be granted to new clients"; existing brokers "cannot expand on the platform, because no new servers will be issued"; existing customers keep support, "Security updates and bug fixes will continue"; MetaQuotes quote: "The architecture was designed under the limitations of a different time" — [Finance Magnates (2018)](https://www.financemagnates.com/forex/technology/metaquotes-will-no-longer-offer-mt4-trading-platform/)
- Finance Magnates, 6 Dec 2024: MetaQuotes notified brokers of MT4/MT5 license fee increases effective 1 Jan 2025 (industry estimate ≥20%; a single MetaTrader license ≈ $10k/month, both platforms ≈ $15–20k/month); "MetaQuotes has stopped issuing new MT4 licenses and is pushing brokers toward MT5" — [Finance Magnates (Dec 2024)](https://www.financemagnates.com/forex/metaquotes-to-increase-metatrader-licensing-fees-from-january-1/amp)
- Finance Magnates, 6 Nov 2026: OANDA Securities (Japan) moved MT4 termination to 14 Nov 2026, citing "recent security breaches and mounting cyber risks within external VPS environments"; article states MetaQuotes "has ceased official support and system maintenance for MT4" — [Finance Magnates (Nov 2026)](https://www.financemagnates.com/forex/oanda-japan-accelerates-mt4-retirement-citing-security-breaches-and-legacy-vulnerabilities/); FOREX.com Japan also migrating MT4→MT5 — [FX News Group](https://fxnewsgroup.com/?p=48738)
- Secondary sources disagree on when "no new MT4 licenses" started (2018 / 2022 / 2024) — [B2Broker](https://b2broker.com/news/mt4-vs-mt5/); [Fynxt 2026](https://fynxt.com/blog/mt4-vs-mt5-for-brokers-technology-operations-back-office-2026); the primary 2018 Finance Magnates report is the earliest authoritative date.
- MT5 2026 builds: 5572 (29 Jan 2026, ONNX + chart rendering) — [release notes](https://www.metatrader5.com/en/releasenotes/terminal/2426); 5640 (20 Feb 2026, MetaEditor markdown) — [forum](https://www.mql5.com/en/forum/505660); 6060 (Jul 2026, built-in MCP and AI agents, Passkey) — [forum](https://www.mql5.com/en/forum/512830); 6090 (31 Jul 2026, more MCP methods) — [FX News Group](https://fxnewsgroup.com/forex-news/platforms/new-mt5-platform-build-expands-set-of-mcp-methods-for-ai-assistant/); 6140 (20 Aug 2026, more LLM providers) — [MT5 news](https://www.metatrader5.com/en/news/2459); 6180 (3 Sep 2026, AI Assistant for Strategy Tester) — [release notes](https://www.metatrader5.com/en/releasenotes/terminal/2464); 6230 (25 Sep 2026, expanded AI capabilities) — [forum](https://www.mql5.com/en/forum/516900); user reports reference builds 6238/6241 in Nov 2026 — [forum](https://www.mql5.com/en/forum/517763)
- The Python package version (5.0.6231) tracks the terminal build numbering — [PyPI MetaTrader5](https://pypi.org/project/MetaTrader5/)

### Inferences
- For a new bot there is no reason to target MT4: no Python package, no ONNX, no async order API, no real-tick tester, DLL-only bridges, shrinking broker support and a documented security narrative being used by brokers to retire it.
- The 2026 MT5 builds' MCP/AI-assistant features are terminal-UI/assistant features, not a new trading API; they do not change the retail programmatic surface (MQL5 + Python package).

### Gaps
- No primary MetaQuotes statement from 2025–2026 about MT4 end-of-support was found; the "ceased support" wording is Finance Magnates' paraphrase.

## Key Question 6: Best architecture for an AI-driven scalping bot — (a) pure MQL5 + ONNX, (b) MQL5 EA + Python sidecar, (c) Python-only via the package — with latency numbers

### Takeaway
For sub-minute scalping: (a) pure MQL5 EA with inline ONNX is the lowest-latency, most robust and only VPS/tester-compatible option; (b) EA + local Python sidecar (native `Socket*` or ZeroMQ) is the pragmatic choice when the model cannot be exported to ONNX, provided the EA keeps execution authority; (c) Python-only is fine for research, demo and minute-scale bots but structurally wrong for sub-second scalping (poll-only, blocking sends, Windows-only, no tester). Whatever you pick, terminal↔broker round trips of ~20–200 ms and broker-side processing dominate.

### Cited Findings
- MQL5 synchronous trade op ≈ 9.59 ms average vs 0.09 ms async (MetaQuotes benchmark vs QLUA) — [MQL5 article 2635](https://www.mql5.com/en/articles/2635)
- `OrderSendAsync` is explicitly "meant for high-frequency trading, where waiting for the server's reply is unacceptable" — [MQL5 docs: OrderSendAsync](https://www.mql5.com/en/docs/trading/ordersendasync)
- Terminal-side observations: ~40 ms journal time per trade from an Equinix NY host; "network delivery typically takes 20 to 200 ms"; forum estimate "60 to 200ms" to fully fill in MT5 vs "200 to 400ms in MT4"; broker queuing during news "can take minutes" — [mql5.com forum 465784](https://mql5.com/en/forum/465784)
- One trader reported first-order transfer time terminal→AMP of 162.77 ms and 200–243 ms for later orders (futures broker via MT5) — [mql5.com forum 500999](https://www.mql5.com/en/forum/500999) (search snippet)
- "a low ping does not guarantee fast execution, since the broker may take several hundred ms to process an order" — [NYC Servers KB: order execution vs latency](https://knowledgebase.newyorkcityservers.com/troubleshooting/order-execution-vs-latency)
- MQL5 VPS: "0-5 ms latency" execution core, "96% of broker servers can be accessed in less than 10 ms", 84% under 3 ms, home PC "from 100 ms"; $15/month (1 mo) down to $10/month (12 mo); 24 h free trial; "more than thirty hosting points" — [MQL5 VPS](https://www.mql5.com/en/vps); Python and DLLs cannot run there — [forum 509181](https://www.mql5.com/en/forum/509181), [forum 377409](https://www.mql5.com/en/forum/377409)
- Python package: synchronous `order_send`, GIL-serialized — [forum 454563](https://www.mql5.com/en/forum/454563); Windows-only wheels — [PyPI](https://pypi.org/project/MetaTrader5/); DWX Connect file bridge polls at 5 ms and "cannot be used for backtesting" — [dwxconnect](https://github.com/darwinex/dwxconnect)
- MetaApi adds median 6 ms + WAN, and recommends co-locating the app with its servers — [MetaApi FAQ](https://metaapi.cloud/docs/client/faq/)
- MetaQuotes-community guidance (Aug 2026): hybrid — Python for research/validation, MQL5 for live execution and risk controls, Python optionally read-only monitoring; ONNX export for in-EA inference — [MQL5 blog 774018](https://www.mql5.com/en/blogs/post/774018); EA should "retain final execution authority", "Python may recommend"; choose "the simplest transport that meets measured requirements"; measure tail latency — [MQL5 blog 774493](https://www.mql5.com/en/blogs/post/774493)
- ONNX inference in-EA ran a three-month H1 backtest in "only a few seconds" (inference once per bar) — [MQL5 article 12373](https://www.mql5.com/en/articles/12373)

### Inferences
- Option (a) latency budget per tick ≈ ONNX CPU inference (sub-ms to a few ms for small models; unmeasured for large ones) + `OrderSendAsync` ≈ 0.1 ms local + 20–200 ms wire/broker. Option (b) adds serialization + local socket (sub-ms) + Python inference (ms) + Python scheduling jitter. Option (c) adds IPC poll latency and a blocking `order_send` that stalls your tick loop for the whole broker round trip unless you thread it (GIL-bound).
- Critical flags for MetaTrader as a scalping venue at all: no official event push to external processes; no documented request-rate SLA (10024 "too frequent requests" is broker-tuned, Q7); market-execution symbols ignore your `price` and only honor `deviation`; freeze/stops levels can block modifications near price; MetaQuotes' own tester "Random Delay" models 0–18 s (!) delays, signalling how non-deterministic retail execution can be. For true sub-second edge, FIX/cTrader Open API or exchange-native APIs are the better fit; MetaTrader is viable for "fast intraday" (seconds to minutes) scalping.

### Short MQL5 CTrade example (pure-EA execution path; pairs with ONNX inference)

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
Method names and semantics follow the [CTrade docs](https://www.mql5.com/en/docs/standardlibrary/tradeclasses/ctrade); ONNX calls follow [MQL5 article 12373](https://www.mql5.com/en/articles/12373) and [OnnxCreate docs](https://www.mql5.com/en/docs/onnx/onnxcreate). Input-shape index/flags vary by model; verify with `ONNX_DEBUG_LOGS`.

### Gaps
- No published end-to-end latency measurement for an MQL5 EA + Python sidecar over ZeroMQ/sockets vs in-EA ONNX; numbers above are component-level.
- ONNX inference time in MQL5 for realistic model sizes (e.g. transformer encoders) not found.

## Key Question 7: Broker restrictions relevant to scalping/EAs on MetaTrader (stops/freeze levels, execution modes, hedging vs netting, rate limits, scalping clauses, VPS/latency)

### Takeaway
Scalping bots on MT5 must handle: broker-set stops level and freeze level (retcodes 10016/10029), execution mode (Instant → requotes vs Market → price ignored, only `deviation`), symbol filling-mode bitmask, hedging vs netting position accounting, undocumented per-broker request-rate limits (retcode 10024), and contractual limits (minimum hold times at some brokers/prop firms; ECN/STP brokers such as IC Markets/Pepperstone/Darwinex advertise no scalping restrictions). Retail round-trips are tens to hundreds of ms even from a co-located VPS.

### Cited Findings
- `SYMBOL_TRADE_STOPS_LEVEL`: "Minimal indention in points from the current close price to place Stop orders"; `SYMBOL_TRADE_FREEZE_LEVEL`: "Distance to freeze trade operations in points" — [MQL5 docs](https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants)
- Freeze level: "minimum distance in pips, measured from the current spot price (Bid/Ask), to trigger a temporary ban on modifying, deleting, or closing orders which are near to execution"; "In a calm market, the freeze level is usually less than 2 pips"; attempts inside the zone return `TRADE_RETCODE_FROZEN` (10029) — [EarnForex: What is freeze level](https://www.earnforex.com/guides/what-is-freeze-level); forum definitions differ on whether it applies to a position's SL/TP distance or only pending-order open price — [mql5.com forum 2574](https://www.mql5.com/en/forum/2574), [forum 502486](https://www.mql5.com/en/forum/502486)
- Execution modes: `SYMBOL_TRADE_EXECUTION_INSTANT` — platform attaches current prices, broker may "return a requote with executable prices"; `SYMBOL_TRADE_EXECUTION_MARKET` — "A broker makes a decision about the order execution price without any additional discussion with the trader"; `SYMBOL_TRADE_EXECUTION_EXCHANGE` — fills at current market offers; `REQUEST` — price requested first — [MQL5 docs](https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants)
- Tester note mirroring live behaviour: "In instant execution mode, the EA can receive requotes when the price difference exceeds the order's deviation value" — [MT5 help: Testing](https://www.metatrader5.com/en/terminal/help/algotrading/testing)
- Hedging vs netting: `ACCOUNT_MARGIN_MODE_RETAIL_NETTING` (one net position per symbol), `ACCOUNT_MARGIN_MODE_EXCHANGE`, `ACCOUNT_MARGIN_MODE_RETAIL_HEDGING` (independent positions); "On hedging accounts, a position cannot be reversed; the current position is closed and a new one with the remaining volume is opened"; Close By is a hedging-only operation; a symbol-only `PositionClose` on a hedging account selects the lowest-ticket position, so close by ticket — [MQL5 blog: hedging and netting](https://www.mql5.com/en/blogs/post/774939); [mql5.com forum on hedging article](https://www.mql5.com/en/forum/158672/3811719); `SYMBOL_ORDER_CLOSEBY` flag (64) "applies to hedging accounts" — [MQL5 docs](https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants)
- vnpy's MT5 gateway supports netting mode only — [vnpy_mt5](https://github.com/vn-crypto/vnpy_mt5)
- Rate limits: 10024 `TRADE_RETCODE_TOO_MANY_REQUESTS` "Too frequent requests" — [MQL5 docs](https://mql5.com/en/docs/constants/errorswarnings/enum_trade_return_codes); a vendor blog says it "fires when an Expert Advisor breaches the broker's API gateway throughput limit" and "brokers limit how many requests your account can send per second", often during XAUUSD volatility; the numeric limit is not published — [fxnx blog](https://fxnx.com/en/blog/mt5-trade-context-busy-too-many-requests-expert-advisors); MT4 equivalent is error 141 `ERR_TOO_MANY_REQUESTS` — [mql5.com forum 139656](https://www.mql5.com/en/forum/139656)
- Scalping clauses: XM states no minimum holding period — [XM scalping rules page](https://sites.google.com/view/xm-forex-scalping-rules/home); prop-firm/broker help pages show hold-time floors from 30 s to 3 min and bans on "micro-scalping" (≈<10 s) — [Winbance](https://intercom.help/faqwinbance/en/articles/13217001-is-scalping-allowed), [Tycoon Funded](https://intercom.help/tycoon-funded/en/articles/10372885-what-is-the-minimum-hold-time-for-a-trade), [FXIFY](https://intercom.help/fxify-futures/en/articles/10235983-what-is-micro-scalping-and-why-is-it-prohibited), [FundedNext rules summary](https://www.jptradingcapital.com/blog/en/fundednext-scalping-rules); market makers restrict because "the broker is often holding the other side of the trades" — [babypips thread](https://forums.babypips.com/t/scalping-with-fxcm/37567)
- IC Markets: third-party sources say scalping and EAs allowed on all account types with "no minimum holding time" — [intercom guide](https://intercom.help/theguides/en/articles/16559589-is-ic-markets-a-good-broker-for-you); Pepperstone: EAs run on MT4/MT5 "without restriction" (third-party) — [The Investors Centre (2026)](https://www.theinvestorscentre.co.uk/reviews/pepperstone-review/automated-trading-vps/); Pepperstone's own guide notes scalping algorithms "send a significant number of orders, sometimes over a very short period of time" — [Pepperstone guide](https://pepperstone.com/ar/insights/guides/automated-trading/why-use-your-expert-advisor-with-pepperstone)
- Co-location: "Equinix NY4 in New Jersey houses most North American brokers, Equinix LD4 near London is the main venue for European spot forex"; vendor latency claims range from sub-1 ms (same metro) to 70–80 ms cross-Atlantic — [ForexVPS (2026)](https://www.forexvps.net/resources/?p=7541), [NYC Servers](https://newyorkcityservers.com/mt4-vps); MQL5 VPS: 96% of broker servers <10 ms — [MQL5 VPS](https://www.mql5.com/en/vps)
- Observed retail round trips: ~40 ms per trade from Equinix NY; 20–200 ms typical delivery; 60–200 ms full fill (forum) — [mql5.com forum 465784](https://mql5.com/en/forum/465784); 162–243 ms terminal→AMP — [forum 500999](https://www.mql5.com/en/forum/500999)
- MQL4 reminder on stops: zero `MODE_STOPLEVEL` may still produce error 130 because the server enforces dynamic levels — [MQL4 docs: OrderSend](https://docs.mql4.com/trading/ordersend)

### Inferences
- A scalping EA must: read `SYMBOL_TRADE_STOPS_LEVEL`/`FREEZE_LEVEL` per symbol at runtime (they change with volatility), treat 10029/10024 as retry-after-backoff, never spin-retry, and choose SL/TP distances ≥ stops level plus spread. On Market-execution symbols your `price` is advisory; only `deviation` protects you — and many brokers ignore it in Market mode (DWX notes `SlippagePoints` "is usually ignored by the broker").
- "Last look"/requotes: `INSTANT` symbols can requote (10004); `MARKET` symbols cannot requote but can fill at any price. For scalping, prefer ECN/STP brokers with Market execution and tight stops levels (often 0), and verify the broker's terms for hold-time rules.

### Gaps
- No broker publishes its MT5 request-rate limit (orders/second); treat 10024 as the signal.
- Pepperstone/IC Markets/Darwinex/Exness/OANDA scalping clauses were not read from the brokers' own terms (search budget); the claims above are third-party or marketing pages.
- No authoritative statement found on how `deviation` is honored in `SYMBOL_TRADE_EXECUTION_MARKET` mode beyond the docs' "broker makes a decision ... without any additional discussion".

## Key Question 8: Strategy tester capabilities — MT5 vs MT4 — for scalping backtests

### Takeaway
MT5's tester supports "Every tick based on real ticks" (broker-recorded ticks, no simulation), multi-currency testing, multi-threaded/local-agent and MQL5 Cloud Network optimization, forward testing and execution-delay emulation (fixed/random/measured ping); MT4's tester interpolates ticks from M1 bars (≈90% modelling quality) and needs third-party tick imports to reach ~99.9%. For tick-level scalping only MT5's real-tick mode is credible, and even it depends on how complete the broker's tick history is.

### Cited Findings
- MT5 tick modes: "Every tick — the most accurate but the slowest mode" (simulated); "Every tick based on real ticks" uses "real ticks of financial instruments, accumulated by brokers" with no simulation; "1 minute OHLC"; "Open prices only"; "Math calculations"; real-tick download "during the first testing run may take a long time" — [MT5 help: Testing](https://www.metatrader5.com/en/terminal/help/algotrading/testing)
- Multi-currency: "automatically processes all symbols the strategy uses"; symbols must be enabled in Market Watch first — [MT5 help: Testing](https://www.metatrader5.com/en/terminal/help/algotrading/testing)
- Optimization "is multi-threaded and runs on agents installed as services"; "An unlimited number of remote agents can be connected"; MQL5 Cloud Network "brings together thousands of agents around the world"; forward testing on 1/2, 1/3, 1/4 or custom; visual testing only on local agents and not during optimization — [MT5 help: Testing](https://www.metatrader5.com/en/terminal/help/algotrading/testing)
- Execution delay emulation: No Delay ("executed at requested prices without requotes"); Random Delay (0–8 s with 90% probability, 9–18 s with 10%); Fixed Delay (predefined/custom, or measured ping to the trade server); delays apply only to EA-initiated actions, not pending-order triggers; instant-execution requotes emulated when deviation exceeded — [MT5 help: Testing](https://www.metatrader5.com/en/terminal/help/algotrading/testing)
- Build 6180 (Sep 2026) expanded the AI Assistant for the Strategy Tester — [MT5 release notes 6180](https://www.metatrader5.com/en/releasenotes/terminal/2464)
- MT4: "Standard history data in MT4 only contains bar data (M1, M5, H1, etc.). When you run a backtest, the MT4 Strategy Tester 'interpolates' or artificially generates ticks inside those bars", capping modelling quality at ~90%; imported tick data can show "a completely different result" at 99.9% — [MQL5 blog 774193 (vendor tutorial)](https://www.mql5.com/en/blogs/post/774193); the 25% figure on M1 "does not measure any quality of the input data" — [mql5.com forum 279717](https://mql5.com/en/forum/279717); MT4 vs MT5 tester comparison thread — [mql5.com forum 410692](https://mql5.com/en/forum/410692)
- Same-EA comparison on gold showed different results between MT4 (commercial real ticks) and MT5 (generated ticks), partly due to different simulated spread costs — [MQL5 blog 773496](https://www.mql5.com/en/blogs/post/773496)
- External Python bridges cannot use the tester (DWX Connect "cannot be used for backtesting") — [dwxconnect](https://github.com/darwinex/dwxconnect); in-EA ONNX runs inside the tester (3-month backtest "takes only a few seconds") — [MQL5 article 12373](https://www.mql5.com/en/articles/12373)

### Inferences
- Architecture (a) is the only one whose live code path is byte-identical to the backtested path; (b)/(c) require a separate Python backtester fed by `copy_ticks_range`, which re-introduces simulation/slippage-model divergence.
- For scalping, run MT5 real-tick tests with Fixed Delay set from measured ping (or worse) and with the broker's actual stops/freeze levels; "No Delay" results are meaningless for sub-minute strategies.

### Gaps
- No source quantifies gaps/completeness of broker real-tick histories on MT5 (one search snippet notes "scope for missing data" without detail).
- Tick-data retention limits of `copy_ticks_range` (how far back brokers serve ticks) were not verified.

## Consolidated gaps and source-quality caveats (for the report writer)

### Takeaway
The official documentation is strong on API shape but silent on latency; latency figures here are forum/vendor numbers (2024–2026) and MetaApi self-reports. Several broker-policy and pricing items rely on snippets or third-party pages because fetch quota was exhausted.

### Cited Findings
- Items fetched directly from primary pages: MQL5/MQL4 docs, PyPI, MT5 help (tester), MQL5 VPS page, MetaApi FAQ and rate-limiting pages, DWX GitHub READMEs, Finance Magnates articles (2018, 2024, 2026), MQL5 blog posts (Aug 2026), MQL5 article 12373 (2023). See inline links above.
- Items from search snippets only (not fetched): MetaApi prices ($30/$100/$125), vnpy_mt5 netting-only note, Pepperstone FIX thresholds (€160m / AUD250m per month), IC Markets scalping claims, build 6230/6238/6241 details, the Oct-2026 Python-vs-MQL5 tick comparison thread.

### Inferences
- None beyond those stated per question.

### Gaps
- Per-call IPC latency of the `MetaTrader5` Python package (no benchmark found).
- MetaApi current pricing page (404), MetaApi data-center region list (only New York named).
- Darwinex FIX terms (page redirect loop); Exness/OANDA MT5 scalping and EA policies (not searched before quota ran out).
- Exact MT5 build/year ONNX was introduced; GPU execution-provider support in MQL5 ONNX.
- MT4 end-of-support statement from MetaQuotes itself (only broker/press paraphrases found).
- Broker-specific order-rate limits behind retcode 10024.
