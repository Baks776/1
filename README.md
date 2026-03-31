# Crypto Signal Terminal (Windows, V1)

Desktop-приложение для анализа крипто-фьючерсов, визуализации индикаторов и сигналов стратегии (без автоторговли в V1).

## Что уже реализовано

- Базовый desktop-каркас на **PySide6**.
- Загрузка **OHLCV** из CSV (`timestamp, open, high, low, close, volume`).
- Расчёт индикаторов:
  - EMA Fast / Mid / Slow
  - ATR
  - DMI / ADX
- Сигналы стратегии:
  - `Long`: EMA Fast пересекает EMA Mid снизу вверх + ADX выше порога
  - `Short`: EMA Fast пересекает EMA Mid сверху вниз + ADX выше порога
- Блок **текущего сигнала**:
  - статус (Long / Short / No signal)
  - цена, вход, стоп, тейк, комментарий
- Заготовка режима бэктеста (таблица сигналов/сделок V1).
- Режим мониторинга (таймер обновления статуса каждые 10 секунд).

## Быстрый старт

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
crypto-signal-terminal
```

## Структура

- `src/crypto_signal_terminal/data.py` — загрузка данных.
- `src/crypto_signal_terminal/indicators.py` — индикаторы.
- `src/crypto_signal_terminal/strategy.py` — правила сигналов и текущий сигнал.
- `src/crypto_signal_terminal/ui.py` — главное окно, таблица сделок, блок статуса.
- `src/crypto_signal_terminal/main.py` — точка входа.

## План следующего шага (V1.1)

1. Подключить API бирж (ccxt): Binance Futures / Bybit Futures.
2. Добавить реальный свечной график (pyqtgraph / lightweight charts).
3. Реализовать полноценный движок бэктеста: SL/TP1/Trailing, equity curve, max drawdown, profit factor.
4. Добавить сохранение настроек (JSON/SQLite).
5. Добавить уведомления о сигналах в UI.
