from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class SignalStatus(str, Enum):
    LONG = "Long signal"
    SHORT = "Short signal"
    NONE = "No signal"


@dataclass(slots=True)
class SignalSnapshot:
    status: SignalStatus
    signal_time: datetime | None
    current_price: float | None
    entry_price: float | None
    stop_loss: float | None
    take_profit: float | None
    comment: str


@dataclass(slots=True)
class StrategyParameters:
    risk_per_trade: float = 1.0
    partial_tp_percent: float = 50.0
    di_length: int = 14
    adx_smoothing: int = 14
    adx_threshold: float = 20.0
    ema_fast: int = 9
    ema_mid: int = 21
    ema_slow: int = 55
    atr_length: int = 14
    stop_atr_multiplier: float = 1.5
    tp1_atr_multiplier: float = 1.0
    trailing_atr_multiplier: float = 2.0
    initial_balance: float = 10_000.0


@dataclass(slots=True)
class Trade:
    trade_id: int
    symbol: str
    side: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    stop_price: float
    tp1_price: float
    exit_price: float
    exit_reason: str
    pnl_usd: float
    pnl_pct: float


@dataclass(slots=True)
class BacktestStats:
    total_pnl: float
    final_balance: float
    total_trades: int
    wins: int
    losses: int
    win_rate: float
    avg_trade_pct: float
    profit_factor: float
    max_drawdown_pct: float


@dataclass(slots=True)
class BacktestResult:
    trades: list[Trade]
    equity_curve: list[float]
    stats: BacktestStats
