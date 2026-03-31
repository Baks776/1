from __future__ import annotations

import pandas as pd

from .indicators import atr, dmi_adx, ema
from .models import SignalSnapshot, SignalStatus, StrategyParameters


class EmaAdxStrategy:
    def __init__(self, params: StrategyParameters):
        self.params = params

    def compute(self, candles: pd.DataFrame) -> pd.DataFrame:
        df = candles.copy()
        df["ema_fast"] = ema(df["close"], self.params.ema_fast)
        df["ema_mid"] = ema(df["close"], self.params.ema_mid)
        df["ema_slow"] = ema(df["close"], self.params.ema_slow)
        df["atr"] = atr(df, self.params.atr_length)

        dmi = dmi_adx(df, self.params.di_length, self.params.adx_smoothing)
        df = df.join(dmi)

        cross_up = (df["ema_fast"].shift(1) <= df["ema_mid"].shift(1)) & (df["ema_fast"] > df["ema_mid"])
        cross_down = (df["ema_fast"].shift(1) >= df["ema_mid"].shift(1)) & (df["ema_fast"] < df["ema_mid"])
        adx_ok = df["adx"] > self.params.adx_threshold

        df["long_signal"] = cross_up & adx_ok
        df["short_signal"] = cross_down & adx_ok
        return df

    def current_signal(self, analyzed: pd.DataFrame) -> SignalSnapshot:
        if analyzed.empty:
            return SignalSnapshot(SignalStatus.NONE, None, None, None, None, None, "No candles loaded")

        row = analyzed.iloc[-1]
        status = SignalStatus.NONE
        if bool(row.get("long_signal", False)):
            status = SignalStatus.LONG
        elif bool(row.get("short_signal", False)):
            status = SignalStatus.SHORT

        price = float(row["close"])
        atr_value = float(row.get("atr", 0.0) or 0.0)

        if status is SignalStatus.LONG:
            stop = price - atr_value * self.params.stop_atr_multiplier
            take = price + atr_value * self.params.tp1_atr_multiplier
            comment = "EMA crossover confirmed, ADX above threshold"
        elif status is SignalStatus.SHORT:
            stop = price + atr_value * self.params.stop_atr_multiplier
            take = price - atr_value * self.params.tp1_atr_multiplier
            comment = "EMA crossover confirmed, ADX above threshold"
        else:
            stop = None
            take = None
            comment = "Trend weak / no entry"

        signal_time = row.name.to_pydatetime() if hasattr(row.name, "to_pydatetime") else None
        return SignalSnapshot(
            status=status,
            signal_time=signal_time,
            current_price=price,
            entry_price=price if status is not SignalStatus.NONE else None,
            stop_loss=stop,
            take_profit=take,
            comment=comment,
        )
