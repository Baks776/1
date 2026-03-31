# Crypto Signal Terminal (Windows)

Desktop-приложение для анализа крипто-фьючерсов, сигналов стратегии и бэктеста.

## Реализовано

- Загрузка OHLCV из CSV.
- Получение OHLCV через **ccxt**:
  - Binance Futures
  - Bybit Futures
- Реальный свечной график на **pyqtgraph** + EMA Fast/Mid/Slow + маркеры Long/Short.
- Индикаторы: EMA, ATR, DMI/ADX.
- Полноценный backtest-движок:
  - входы Long/Short по стратегии EMA crossover + ADX;
  - stop-loss по ATR;
  - partial TP по ATR;
  - trailing stop для остатка;
  - выход по reverse signal;
  - equity curve;
  - статистика: PnL, баланс, win rate, profit factor, max drawdown и др.
- Таблица сделок с ключевыми полями (вход/выход/стоп/TP1/PnL/причина).
- Блок “Текущий сигнал” (Long/Short/No signal, вход, стоп, тейк, комментарий).
- Онлайн-мониторинг (таймер обновления данных).
- Сохранение параметров стратегии в JSON (`~/.crypto_signal_terminal.json`).
- Внутренние уведомления о новых сигналах (popup + beep).

## Запуск

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
crypto-signal-terminal
```

## Структура

- `data.py` — CSV + ccxt источники данных.
- `indicators.py` — индикаторы.
- `strategy.py` — логика сигналов и текущего сигнала.
- `backtest.py` — движок бэктеста и метрики.
- `charting.py` — свечной график + график капитала.
- `settings.py` — хранение настроек JSON.
- `notifications.py` — уведомления в UI.
- `ui.py` — главное окно и orchestration модулей.
