from __future__ import annotations

import pandas as pd


def ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def atr(df: pd.DataFrame, length: int) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift(1)).abs()
    low_close = (df["low"] - df["close"].shift(1)).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=length, min_periods=length).mean()


def dmi_adx(df: pd.DataFrame, length: int, smoothing: int) -> pd.DataFrame:
    up_move = df["high"].diff()
    down_move = -df["low"].diff()

    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)

    tr_components = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - df["close"].shift(1)).abs(),
            (df["low"] - df["close"].shift(1)).abs(),
        ],
        axis=1,
    )
    tr = tr_components.max(axis=1)
    atr_value = tr.rolling(length, min_periods=length).mean()

    plus_di = 100 * (plus_dm.rolling(length, min_periods=length).mean() / atr_value)
    minus_di = 100 * (minus_dm.rolling(length, min_periods=length).mean() / atr_value)

    dx = ((plus_di - minus_di).abs() / (plus_di + minus_di)).fillna(0) * 100
    adx = dx.rolling(smoothing, min_periods=smoothing).mean()

    return pd.DataFrame({"plus_di": plus_di, "minus_di": minus_di, "adx": adx})
