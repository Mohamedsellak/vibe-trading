# MT5 scalping bot (Exness, XAUUSD first, BTCUSD second)

Tick-level backtester plus a live/demo bot for MetaTrader 5. Both share the same
signal, filter and risk code. Three starting strategies are implemented:

| Name | Idea | Entry | Exit |
|---|---|---|---|
| `breakout` | Volatility expansion at the London (08:00 London) and New York (09:30 New York) opens | First 1-minute close beyond the pre-open range whose bar range is at least `exp_mult` x ATR(14) | SL `sl_atr` x ATR, TP `tp_r` x SL, time stop 30 min |
| `meanrev` | VWAP/Bollinger fade, only when the efficiency ratio says the market is ranging | Close below BB(20,k) AND below session VWAP (mirror for shorts), ER(30) < `er_max`, 07:00-20:00 UTC | TP at the middle band, SL `sl_atr` x ATR, time stop 20 min |
| `sweep` | Stop hunt of the Asian-session high/low, then reversal | Price runs `pierce_atr` x ATR beyond the 00:00-06:00 UTC low/high and closes back inside within `confirm_bars` bars | SL beyond the sweep extreme, TP `tp_r` x risk, time stop 45 min |

**Status:** the code is unit tested (56 tests, no MT5 needed). No strategy has been
backtested on real Exness data yet. The data has to come from your MT5 terminal.

## Install (Windows, same machine as MT5)

```
cd bot
python -m pip install -r requirements.txt
copy .env.example .env
```

Edit `.env`. Set your commission to match your Exness account type. Standard accounts
have no commission; Raw Spread and Zero charge per lot per side. In MT5, enable
**Algo Trading**. Under Tools > Options > Charts, set **Max bars in chart** to Unlimited.

Run the tests:

```
python -m pytest -q tests
```

## 1. Pull the history and check it

```
python backtest.py fetch --symbol XAUUSD
python backtest.py fetch --symbol BTCUSD
```

This prints, and saves to `data/<SYMBOL>_data_report.txt`:

- the tick and M1 date ranges, tick count, trading days and gaps;
- the train / validation / final split (50/25/25 of trading days);
- the trades per day a strategy needs to reach 300 trades in the final split.

**If the history is too short.** MT5 brokers often serve only months of ticks. In order of fidelity:

1. Open the symbol chart, scroll far back, or use View > Symbols > Ticks to request older
   ticks, then run `fetch` again.
2. Export ticks from View > Symbols > Ticks > Export and load them:
   `python backtest.py import-csv --symbol XAUUSD --file XAUUSD_ticks.csv`
3. Use a CSV from another tick source (`time,bid,ask` columns, `--tz UTC`). Its spreads differ
   from Exness, so set `EXTRA_SPREAD_PRICE` to the difference.
4. Run on M1 bars with `--source m1`. Each bar becomes four ticks with the adverse extreme
   first and the bar's recorded spread. This is lower fidelity, and every report says so.

## 2. Develop on train + validation only

```
python backtest.py run-all --symbol XAUUSD
```

This runs round 1: the baseline grid of 12 parameter combinations per strategy, on train
and validation. Every variant is logged to `results/experiments.csv`. It then ranks
candidates by the t-statistic of R on validation, with a deflated Sharpe ratio for the
number of variants tried. For up to three eligible finalists it runs the plateau check and
a 5-fold walk-forward inside the development period. It never reads the final split.

Improvement rounds 2-5 take a JSON file. Each variant must give a one-line reason naming
the market behaviour it targets:

```json
[{"strategy": "sweep", "params": {"pierce_atr": 0.2, "confirm_bars": 2},
  "reason": "sweeps that reclaim within 2 bars show rejection without waiting for noise"}]
```

```
python backtest.py dev --symbol XAUUSD --round 2 --variants round2.json
python backtest.py select --symbol XAUUSD
python backtest.py walkforward --symbol XAUUSD --strategy sweep --params "{\"tp_r\": 2.0}"
```

`"base": "best"` starts from that strategy's best logged result. That ranking uses train
and validation only.

Round 2 is ready to run. It tests a trailing stop and a New York-only version of each
strategy, which is 6 variants:

```
python backtest.py dev --symbol XAUUSD --round 2 --variants variants/round2_trail_ny.json
```

- **Trailing stop** (`"trail": true`). Once open profit reaches `TRAIL_ACTIVATE_R` x the
  initial risk, the stop moves to lock `TRAIL_LOCK_FRACTION` of the best open profit. It
  moves in steps of `TRAIL_STEP_R` x risk and never moves back. The fixed target and the
  time stop stay. The values come from `.env` and are copied into the logged params, so
  each run records exactly what was tested.
- **New York only** (`"session": "newyork"`). Entries are allowed only from 08:00 to
  16:00 New York time, with daylight saving handled. The breakout drops the London open.
  The sweep still measures the Asian range but trades only in New York hours.

Both appear in `results/experiments.csv` with their reason. They count toward the variant
total, the deflated Sharpe ratio and the budget. After round 2 each strategy has 14 of its
20 combinations. A plateau check on a round-2 finalist adds up to 5 neighbours, which still
fits the budget.

Budget enforcement: at most 5 rounds and 20 distinct parameter combinations per strategy
per symbol. A new strategy must be added to `STRATEGIES` in `strategy.py`.

## 3. Final test, once

```
python backtest.py final --symbol XAUUSD --strategy sweep --params "{\"pierce_atr\": 0.3, \"confirm_bars\": 3, \"tp_r\": 2.0}"
```

Go-live gates, all on the final split:

- profit factor > 1.3;
- at least 300 trades;
- net profitable with slippage doubled;
- a parameter plateau: at least 75% of one-step grid neighbours show PF >= 1.1 and positive
  expectancy on validation.

The result goes to `results/chosen_strategy.json`. Every access is recorded in
`results/final_test_log.json`. A second look is refused unless you pass `--second-look`,
and the report then marks the result as contaminated.

## 4. Demo forward test

```
python bot.py
```

- The bot reads the account type at startup and refuses a real account.
- It runs only the strategy in `chosen_strategy.json`. A strategy that failed a gate runs
  only with `--allow-failed-gates`, and only on demo.
- It reads the contract spec from MT5: point, tick size and value, contract size, volume
  step, stops level and filling mode.
- It verifies the server time offset against live quotes.
- It adopts open positions with its magic number after a restart.

Everything goes to `logs/bot.sqlite`: signals with skip reasons, orders with retcode,
requested and fill price, slippage, send latency and signal-to-fill latency, trades with
P&L, equity every minute, and risk state. Human-readable logs go to `logs/bot.log`.

Compare the demo with the backtest by checking median slippage and latency against the
backtest assumptions (`SLIPPAGE_*`, `LATENCY_MS`). Also compare trade frequency and
expectancy per trade.

## 5. Live

```
python bot.py --live
```

This needs a strategy that passed every gate, plus a typed confirmation
`TRADE LIVE <login>`. Without `--live`, a real account is always refused.

## Costs and risk model

- **Entry.** First tick at or after the signal time plus `LATENCY_MS`, at the ask (buys) or
  bid (sells), plus slippage. The spread comes from the tick data plus `EXTRA_SPREAD_PRICE`.
- **Stop loss.** Triggers on bid (long) or ask (short), at the worse of the stop and the
  tick price, minus slippage, so gaps fill at the gap price. Take profit needs a
  trade-through and gets no positive slippage. The time stop exits at market minus slippage.
- **Trailing stop** (variant only). The backtester applies the stop from ticks already
  seen. The bot moves the broker-side SL with the same function, skipping a move when it
  falls inside the stops or freeze level. Trades closed this way are reported with exit
  reason `trail`.
- **Commission.** Charged per lot per side. Reports show the average cost per trade in
  points and the break-even win rate after costs.
- **Entry filters.** Spread above `SPREAD_MAX_MULT` x its 60-minute median, 16:50-18:10
  New York rollover, `news_blackout.csv` windows. All session times use IANA time zones,
  so daylight saving time is handled.
- **Risk.** Fixed % risk per trade with lots from SL distance and tick value, rounded down
  to the volume step. Limits: max daily loss (flattens until the next server day), max
  open positions, max trades per day, cooldown after N losses.
- **Drawdown kill switch.** It flattens and stops the bot. It stays on until you delete
  the `risk_<SYMBOL>` row from the `state` table in `logs/bot.sqlite`.

## Files

- `config.py`: settings and `.env` loading.
- `strategy.py`: bars, indicators, the three strategies, grids, trade filters.
- `risk.py`: lot sizing and account limits.
- `broker.py`: the only MT5 code, with retries, filling modes, reconnects and time conversion.
- `backtest.py`: data, simulator, metrics, experiment log, walk-forward, gates.
- `variants/round2_trail_ny.json`: the round-2 trailing-stop and New York-only variants.
- `bot.py`: live loop and SQLite logging.
