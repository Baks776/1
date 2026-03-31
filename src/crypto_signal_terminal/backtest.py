from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .models import BacktestResult, BacktestStats, StrategyParameters, Trade


@dataclass
class Position:
    side: str
    entry_time: pd.Timestamp
    entry_price: float
    stop_price: float
    tp1_price: float
    trailing_stop: float
    risk_amount: float
    qty: float
    remainder_qty: float


class BacktestEngine:
    def __init__(self, params: StrategyParameters):
        self.params = params

    def run(self, analyzed: pd.DataFrame, symbol: str) -> BacktestResult:
        balance = self.params.initial_balance
        equity_curve = [balance]
        trades: list[Trade] = []
        position: Position | None = None
        trade_id = 1

        gross_profit = 0.0
        gross_loss = 0.0

        for ts, row in analyzed.iterrows():
            price_open = float(row["open"])
            high = float(row["high"])
            low = float(row["low"])
            close = float(row["close"])
            atr = float(row.get("atr", 0.0) or 0.0)

            if position is None:
                if bool(row.get("long_signal", False)):
                    entry = close
                    stop = entry - atr * self.params.stop_atr_multiplier
                    tp1 = entry + atr * self.params.tp1_atr_multiplier
                    risk_amount = balance * (self.params.risk_per_trade / 100)
                    risk_per_unit = max(entry - stop, 1e-9)
                    qty = risk_amount / risk_per_unit
                    position = Position(
                        side="LONG",
                        entry_time=ts,
                        entry_price=entry,
                        stop_price=stop,
                        tp1_price=tp1,
                        trailing_stop=stop,
                        risk_amount=risk_amount,
                        qty=qty,
                        remainder_qty=qty,
                    )
                elif bool(row.get("short_signal", False)):
                    entry = close
                    stop = entry + atr * self.params.stop_atr_multiplier
                    tp1 = entry - atr * self.params.tp1_atr_multiplier
                    risk_amount = balance * (self.params.risk_per_trade / 100)
                    risk_per_unit = max(stop - entry, 1e-9)
                    qty = risk_amount / risk_per_unit
                    position = Position(
                        side="SHORT",
                        entry_time=ts,
                        entry_price=entry,
                        stop_price=stop,
                        tp1_price=tp1,
                        trailing_stop=stop,
                        risk_amount=risk_amount,
                        qty=qty,
                        remainder_qty=qty,
                    )
                equity_curve.append(balance)
                continue

            realized = 0.0
            exit_reason = ""
            exit_price = close

            partial_qty = position.qty * (self.params.partial_tp_percent / 100)

            if position.side == "LONG":
                if high >= position.tp1_price and position.remainder_qty == position.qty:
                    realized += partial_qty * (position.tp1_price - position.entry_price)
                    position.remainder_qty -= partial_qty
                    position.trailing_stop = max(
                        position.trailing_stop,
                        close - atr * self.params.trailing_atr_multiplier,
                    )

                position.trailing_stop = max(position.trailing_stop, close - atr * self.params.trailing_atr_multiplier)

                stop_hit = low <= min(position.stop_price, position.trailing_stop)
                reverse_signal = bool(row.get("short_signal", False))

                if stop_hit:
                    exit_price = min(position.stop_price, position.trailing_stop)
                    realized += position.remainder_qty * (exit_price - position.entry_price)
                    exit_reason = "Stop/Trailing"
                    position.remainder_qty = 0.0
                elif reverse_signal:
                    exit_price = close
                    realized += position.remainder_qty * (exit_price - position.entry_price)
                    exit_reason = "Reverse signal"
                    position.remainder_qty = 0.0

            else:
                if low <= position.tp1_price and position.remainder_qty == position.qty:
                    realized += partial_qty * (position.entry_price - position.tp1_price)
                    position.remainder_qty -= partial_qty
                    position.trailing_stop = min(
                        position.trailing_stop,
                        close + atr * self.params.trailing_atr_multiplier,
                    )

                position.trailing_stop = min(position.trailing_stop, close + atr * self.params.trailing_atr_multiplier)

                stop_hit = high >= max(position.stop_price, position.trailing_stop)
                reverse_signal = bool(row.get("long_signal", False))

                if stop_hit:
                    exit_price = max(position.stop_price, position.trailing_stop)
                    realized += position.remainder_qty * (position.entry_price - exit_price)
                    exit_reason = "Stop/Trailing"
                    position.remainder_qty = 0.0
                elif reverse_signal:
                    exit_price = close
                    realized += position.remainder_qty * (position.entry_price - exit_price)
                    exit_reason = "Reverse signal"
                    position.remainder_qty = 0.0

            if position.remainder_qty == 0:
                balance += realized
                pnl_pct = (realized / position.risk_amount * 100) if position.risk_amount else 0.0
                trade = Trade(
                    trade_id=trade_id,
                    symbol=symbol,
                    side=position.side,
                    entry_time=position.entry_time.to_pydatetime(),
                    exit_time=ts.to_pydatetime(),
                    entry_price=position.entry_price,
                    stop_price=position.stop_price,
                    tp1_price=position.tp1_price,
                    exit_price=exit_price,
                    exit_reason=exit_reason,
                    pnl_usd=realized,
                    pnl_pct=pnl_pct,
                )
                trades.append(trade)
                trade_id += 1
                if realized >= 0:
                    gross_profit += realized
                else:
                    gross_loss += abs(realized)
                position = None

            equity_curve.append(balance)

        wins = sum(1 for t in trades if t.pnl_usd > 0)
        losses = sum(1 for t in trades if t.pnl_usd <= 0)
        total_trades = len(trades)
        avg_trade_pct = sum(t.pnl_pct for t in trades) / total_trades if total_trades else 0.0
        win_rate = (wins / total_trades * 100) if total_trades else 0.0
        profit_factor = (gross_profit / gross_loss) if gross_loss else (gross_profit if gross_profit else 0.0)

        peak = equity_curve[0]
        max_dd = 0.0
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100 if peak else 0.0
            max_dd = max(max_dd, dd)

        stats = BacktestStats(
            total_pnl=balance - self.params.initial_balance,
            final_balance=balance,
            total_trades=total_trades,
            wins=wins,
            losses=losses,
            win_rate=win_rate,
            avg_trade_pct=avg_trade_pct,
            profit_factor=profit_factor,
            max_drawdown_pct=max_dd,
        )
        return BacktestResult(trades=trades, equity_curve=equity_curve, stats=stats)
