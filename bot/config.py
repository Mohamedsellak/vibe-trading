"""Central configuration.

Every value can be overridden from bot/.env (KEY=VALUE lines) or the process
environment. Nothing here talks to MetaTrader, so it imports on any OS.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "results"
LOG_DIR = BASE_DIR / "logs"
ENV_FILE = BASE_DIR / ".env"
NEWS_FILE = BASE_DIR / "news_blackout.csv"
CHOSEN_FILE = RESULTS_DIR / "chosen_strategy.json"
EXPERIMENTS_FILE = RESULTS_DIR / "experiments.csv"
FINAL_TEST_LOG = RESULTS_DIR / "final_test_log.json"
TRADE_DB = LOG_DIR / "bot.sqlite"


def normalize_tz(name: str) -> str:
    """Accept UTC, GMT, fixed offsets like UTC+2 / GMT-5, or IANA names like Europe/Athens."""
    text = (name or "").strip()
    m = re.fullmatch(r"(?i)(UTC|GMT)\s*([+-])\s*(\d{1,2})", text)
    if m:
        hours = int(m.group(3))
        if hours == 0:
            return "UTC"
        # IANA fixed-offset zones have inverted signs: Etc/GMT-2 is UTC+2.
        return f"Etc/GMT{'-' if m.group(2) == '+' else '+'}{hours}"
    if text.upper() in ("UTC", "GMT", "Z", "ETC/UTC", "ETC/GMT"):
        return "UTC"
    from zoneinfo import ZoneInfo
    try:
        ZoneInfo(text)
    except Exception:
        raise SystemExit(f"SERVER_TZ={name!r} is not a time zone. Use UTC, a fixed offset such "
                         "as UTC+2, or a name such as Europe/Athens.") from None
    return text


def load_env(path: Path = ENV_FILE) -> dict:
    """Parse KEY=VALUE lines. Existing environment variables win."""
    values: dict[str, str] = {}
    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            values[key.strip()] = val.strip().strip('"').strip("'")
    for key, val in values.items():
        os.environ.setdefault(key, val)
    return values


def _env(key: str, default, cast=str):
    raw = os.environ.get(key)
    if raw is None or raw == "":
        return default
    if cast is bool:
        return raw.strip().lower() in ("1", "true", "yes", "on")
    return cast(raw)


@dataclass
class SymbolDefaults:
    """Fallback contract data, used ONLY when no MT5 spec file exists.

    bot.py always reads the live spec from MT5 at startup; backtest.py reads
    data/<SYMBOL>_spec.json written by `backtest.py fetch`.
    """
    point: float
    digits: int
    tick_size: float
    tick_value: float          # account currency per tick per 1.0 lot
    contract_size: float
    volume_min: float
    volume_max: float
    volume_step: float
    stops_level: int           # points
    commission_per_lot_side: float   # account currency, per 1.0 lot, per side
    slippage_price: float      # pessimistic slippage per side, in PRICE units


SYMBOL_DEFAULTS: dict[str, SymbolDefaults] = {
    # Exness quotes gold to 3 decimals on most account types; verify via the spec file.
    "XAUUSD": SymbolDefaults(point=0.001, digits=3, tick_size=0.001, tick_value=0.1,
                             contract_size=100.0, volume_min=0.01, volume_max=200.0,
                             volume_step=0.01, stops_level=0,
                             commission_per_lot_side=3.5, slippage_price=0.05),
    "BTCUSD": SymbolDefaults(point=0.01, digits=2, tick_size=0.01, tick_value=0.01,
                             contract_size=1.0, volume_min=0.01, volume_max=100.0,
                             volume_step=0.01, stops_level=0,
                             commission_per_lot_side=0.0, slippage_price=5.0),
}


def defaults_for(symbol: str) -> SymbolDefaults:
    base = symbol.upper()
    for key, val in SYMBOL_DEFAULTS.items():
        if base.startswith(key):      # XAUUSDm, XAUUSDc ... map to XAUUSD
            return val
    raise KeyError(f"No defaults for {symbol}; add it to SYMBOL_DEFAULTS or fetch its spec")


@dataclass
class SymbolSpec:
    """Contract data for one symbol. Live values come from MT5 symbol_info."""
    name: str
    point: float
    digits: int
    tick_size: float
    tick_value: float
    contract_size: float
    volume_min: float
    volume_max: float
    volume_step: float
    stops_level: int = 0
    freeze_level: int = 0
    filling_mode: int = 0
    source: str = "defaults"

    @property
    def value_per_price_unit(self) -> float:
        """Account-currency P&L of a 1.0 price move on 1.0 lot."""
        if self.tick_value > 0 and self.tick_size > 0:
            return self.tick_value / self.tick_size
        return self.contract_size

    @classmethod
    def from_defaults(cls, symbol: str) -> "SymbolSpec":
        d = defaults_for(symbol)
        return cls(name=symbol, point=d.point, digits=d.digits, tick_size=d.tick_size,
                   tick_value=d.tick_value, contract_size=d.contract_size,
                   volume_min=d.volume_min, volume_max=d.volume_max,
                   volume_step=d.volume_step, stops_level=d.stops_level)

    def to_json(self) -> str:
        return json.dumps(self.__dict__, indent=2)

    @classmethod
    def from_json(cls, text: str) -> "SymbolSpec":
        return cls(**json.loads(text))


@dataclass
class CostConfig:
    commission_per_lot_side: float | None = None  # None -> symbol default
    extra_spread_price: float = 0.0               # added on top of the data spread
    slippage_price: float | None = None           # None -> symbol default (per side)
    latency_ms: int = 250                         # signal -> fill delay in the backtest


@dataclass
class RiskConfig:
    risk_per_trade_pct: float = 0.5
    max_daily_loss_pct: float = 2.0
    max_open_positions: int = 1
    max_drawdown_pct: float = 10.0
    max_trades_per_day: int = 10
    cooldown_after_losses: int = 3
    cooldown_minutes: int = 60


@dataclass
class FilterConfig:
    spread_max_mult: float = 2.0          # skip if spread > mult x recent median
    spread_median_bars: int = 60          # bars (minutes) in the rolling median
    rollover_tz: str = "America/New_York"
    rollover_start_local: str = "16:50"   # daily close / rollover spike window
    rollover_end_local: str = "18:10"
    news_minutes_before: int = 15         # defaults for rows that omit them
    news_minutes_after: int = 30


@dataclass
class ExecConfig:
    magic: int = 26111701
    deviation_points: int = 30
    loop_interval_ms: int = 200
    max_retries: int = 3
    retry_backoff_ms: int = 300
    tick_buffer_hours: int = 30
    reconnect_max_wait_s: int = 60


@dataclass
class TrailConfig:
    """Trailing-stop variant. Copied into the variant's params when it is logged."""
    activate_r: float = 1.0      # start trailing once open profit reaches 1.0 x initial risk
    lock_fraction: float = 0.5   # stop locks in 50% of the best open profit
    step_r: float = 0.1          # stop moves in steps of 0.1 x risk (limits modify requests)

    def as_params(self) -> dict:
        return {"trail": True, "trail_activate_r": self.activate_r,
                "trail_lock": self.lock_fraction, "trail_step_r": self.step_r}


@dataclass
class SplitConfig:
    train: float = 0.50
    validation: float = 0.25
    final: float = 0.25


@dataclass
class Config:
    symbol: str = "XAUUSD"                 # base name; broker resolves XAUUSDm etc.
    server_tz: str = "UTC"                 # Exness MT5 server time is GMT+0
    mt5_login: int | None = None
    mt5_password: str | None = None
    mt5_server: str | None = None
    mt5_path: str | None = None
    costs: CostConfig = field(default_factory=CostConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    filters: FilterConfig = field(default_factory=FilterConfig)
    execution: ExecConfig = field(default_factory=ExecConfig)
    splits: SplitConfig = field(default_factory=SplitConfig)
    trail: TrailConfig = field(default_factory=TrailConfig)
    starting_equity: float = 10_000.0      # backtest only

    def symbol_defaults(self) -> SymbolDefaults:
        return defaults_for(self.symbol)

    def commission(self) -> float:
        if self.costs.commission_per_lot_side is not None:
            return self.costs.commission_per_lot_side
        return self.symbol_defaults().commission_per_lot_side

    def slippage(self) -> float:
        if self.costs.slippage_price is not None:
            return self.costs.slippage_price
        return self.symbol_defaults().slippage_price


def load_config(env_path: Path | None = None, symbol: str | None = None) -> Config:
    load_env(env_path or ENV_FILE)
    cfg = Config()
    cfg.symbol = (symbol or _env("SYMBOL", cfg.symbol)).upper()
    cfg.server_tz = normalize_tz(_env("SERVER_TZ", cfg.server_tz))
    login = _env("MT5_LOGIN", None)
    cfg.mt5_login = int(login) if login else None
    cfg.mt5_password = _env("MT5_PASSWORD", None)
    cfg.mt5_server = _env("MT5_SERVER", None)
    cfg.mt5_path = _env("MT5_PATH", None)
    cfg.starting_equity = _env("STARTING_EQUITY", cfg.starting_equity, float)

    c = cfg.costs
    # per-symbol costs, read once here so code that sets cfg.costs later is never overridden
    c.commission_per_lot_side = _env(f"COMMISSION_{cfg.symbol}", c.commission_per_lot_side, float)
    c.slippage_price = _env(f"SLIPPAGE_{cfg.symbol}", c.slippage_price, float)
    c.extra_spread_price = _env("EXTRA_SPREAD_PRICE", c.extra_spread_price, float)
    c.latency_ms = _env("LATENCY_MS", c.latency_ms, int)

    r = cfg.risk
    r.risk_per_trade_pct = _env("RISK_PER_TRADE_PCT", r.risk_per_trade_pct, float)
    r.max_daily_loss_pct = _env("MAX_DAILY_LOSS_PCT", r.max_daily_loss_pct, float)
    r.max_open_positions = _env("MAX_OPEN_POSITIONS", r.max_open_positions, int)
    r.max_drawdown_pct = _env("MAX_DRAWDOWN_PCT", r.max_drawdown_pct, float)
    r.max_trades_per_day = _env("MAX_TRADES_PER_DAY", r.max_trades_per_day, int)
    r.cooldown_after_losses = _env("COOLDOWN_AFTER_LOSSES", r.cooldown_after_losses, int)
    r.cooldown_minutes = _env("COOLDOWN_MINUTES", r.cooldown_minutes, int)

    f = cfg.filters
    f.spread_max_mult = _env("SPREAD_MAX_MULT", f.spread_max_mult, float)
    f.spread_median_bars = _env("SPREAD_MEDIAN_BARS", f.spread_median_bars, int)

    t = cfg.trail
    t.activate_r = _env("TRAIL_ACTIVATE_R", t.activate_r, float)
    t.lock_fraction = _env("TRAIL_LOCK_FRACTION", t.lock_fraction, float)
    t.step_r = _env("TRAIL_STEP_R", t.step_r, float)

    e = cfg.execution
    e.magic = _env("MAGIC", e.magic, int)
    e.deviation_points = _env("DEVIATION_POINTS", e.deviation_points, int)
    e.loop_interval_ms = _env("LOOP_INTERVAL_MS", e.loop_interval_ms, int)
    return cfg


def load_chosen(path: Path | None = None) -> dict | None:
    path = path or CHOSEN_FILE
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
