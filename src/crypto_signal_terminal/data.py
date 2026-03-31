from __future__ import annotations

from pathlib import Path

import pandas as pd


class ExchangeDataClient:
    def __init__(self) -> None:
        self._instances: dict[str, object] = {}

    def _get_exchange(self, exchange_name: str):
        try:
            import ccxt  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("ccxt is not installed. Install with: pip install ccxt") from exc

        key = exchange_name.lower()
        if key in self._instances:
            return self._instances[key]

        if key == "binance":
            ex = ccxt.binance({"options": {"defaultType": "future"}, "enableRateLimit": True})
        elif key == "bybit":
            ex = ccxt.bybit({"options": {"defaultType": "linear"}, "enableRateLimit": True})
        else:
            raise ValueError(f"Unsupported exchange: {exchange_name}")

        self._instances[key] = ex
        return ex

    def load_markets(self, exchange_name: str) -> list[str]:
        ex = self._get_exchange(exchange_name)
        markets = ex.load_markets()
        symbols = [sym for sym, meta in markets.items() if meta.get("swap") and "USDT" in sym]
        return sorted(symbols)

    def fetch_ohlcv(self, exchange_name: str, symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame:
        ex = self._get_exchange(exchange_name)
        rows = ex.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
        if not rows:
            raise RuntimeError("No OHLCV data returned")

        df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        df = df.set_index("timestamp").sort_index()
        return df


def load_csv(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"timestamp", "open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV must contain columns: {sorted(required)}; missing={sorted(missing)}")

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.set_index("timestamp").sort_index()
    return df[["open", "high", "low", "close", "volume"]]
