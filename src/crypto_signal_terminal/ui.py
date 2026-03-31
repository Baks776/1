from __future__ import annotations

import pandas as pd
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QFileDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QComboBox,
)

from .backtest import BacktestEngine
from .charting import ChartWidget
from .data import ExchangeDataClient, load_csv
from .models import SignalStatus, StrategyParameters
from .notifications import Notifier
from .settings import SettingsStore
from .strategy import EmaAdxStrategy


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Crypto Signal Terminal")
        self.resize(1500, 900)

        self.settings_store = SettingsStore()
        self.params = self.settings_store.load()
        self.strategy = EmaAdxStrategy(self.params)
        self.backtester = BacktestEngine(self.params)
        self.notifier = Notifier(self)
        self.data_client = ExchangeDataClient()

        self.raw_candles: pd.DataFrame = pd.DataFrame()
        self.analyzed: pd.DataFrame = pd.DataFrame()
        self.last_status: SignalStatus = SignalStatus.NONE

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        controls = QHBoxLayout()
        self.exchange_box = QComboBox()
        self.exchange_box.addItems(["binance", "bybit"])
        self.symbol_box = QComboBox()
        self.symbol_box.addItems(["BTC/USDT:USDT", "ETH/USDT:USDT"])
        self.timeframe_box = QComboBox()
        self.timeframe_box.addItems(["5m", "15m", "1h", "4h", "1d"])

        self.btn_markets = QPushButton("Обновить пары")
        self.btn_api = QPushButton("Загрузить с биржи")
        self.btn_csv = QPushButton("Загрузить CSV")
        self.btn_backtest = QPushButton("Запустить бэктест")
        self.btn_monitor = QPushButton("Старт мониторинга")
        self.btn_stop = QPushButton("Стоп")

        for widget in [
            QLabel("Биржа"),
            self.exchange_box,
            QLabel("Инструмент"),
            self.symbol_box,
            QLabel("Таймфрейм"),
            self.timeframe_box,
            self.btn_markets,
            self.btn_api,
            self.btn_csv,
            self.btn_backtest,
            self.btn_monitor,
            self.btn_stop,
        ]:
            controls.addWidget(widget)
        controls.addStretch(1)
        layout.addLayout(controls)

        body = QGridLayout()
        layout.addLayout(body, 1)

        self.chart = ChartWidget()
        body.addWidget(self.chart, 0, 0, 2, 1)

        right = QWidget()
        right_layout = QVBoxLayout(right)

        signal_form = QFormLayout()
        self.signal_labels: dict[str, QLabel] = {}
        for key in ["status", "signal_time", "current_price", "entry_price", "stop_loss", "take_profit", "comment"]:
            label = QLabel("-")
            self.signal_labels[key] = label
            signal_form.addRow(key, label)
        right_layout.addLayout(signal_form)

        self.param_widgets = self._build_param_editor()
        right_layout.addWidget(QLabel("Параметры стратегии"))
        right_layout.addLayout(self.param_widgets)

        self.btn_save_settings = QPushButton("Сохранить настройки")
        right_layout.addWidget(self.btn_save_settings)
        body.addWidget(right, 0, 1)

        self.stats_label = QLabel("Статистика: -")
        body.addWidget(self.stats_label, 1, 1)

        self.trades_table = QTableWidget(0, 13)
        self.trades_table.setHorizontalHeaderLabels(
            [
                "#",
                "Entry Time",
                "Exit Time",
                "Symbol",
                "Side",
                "Entry",
                "Stop",
                "TP1",
                "Exit",
                "Reason",
                "PnL $",
                "PnL %",
                "Balance",
            ]
        )
        layout.addWidget(self.trades_table)

        self.timer = QTimer(self)
        self.timer.setInterval(10_000)
        self.timer.timeout.connect(self.load_from_api)

        self.btn_markets.clicked.connect(self.refresh_markets)
        self.btn_api.clicked.connect(self.load_from_api)
        self.btn_csv.clicked.connect(self.load_from_csv)
        self.btn_backtest.clicked.connect(self.run_backtest)
        self.btn_monitor.clicked.connect(self.timer.start)
        self.btn_stop.clicked.connect(self.timer.stop)
        self.btn_save_settings.clicked.connect(self.save_settings)

    def _build_param_editor(self) -> QFormLayout:
        form = QFormLayout()

        def spin_int(value: int, minv: int, maxv: int) -> QSpinBox:
            w = QSpinBox()
            w.setRange(minv, maxv)
            w.setValue(value)
            return w

        def spin_float(value: float, minv: float, maxv: float, step: float = 0.1) -> QDoubleSpinBox:
            w = QDoubleSpinBox()
            w.setRange(minv, maxv)
            w.setDecimals(4)
            w.setSingleStep(step)
            w.setValue(value)
            return w

        self.w_risk = spin_float(self.params.risk_per_trade, 0.01, 100)
        self.w_partial = spin_float(self.params.partial_tp_percent, 1, 100)
        self.w_di = spin_int(self.params.di_length, 2, 100)
        self.w_adx_sm = spin_int(self.params.adx_smoothing, 2, 100)
        self.w_adx_thr = spin_float(self.params.adx_threshold, 1, 100)
        self.w_ema_fast = spin_int(self.params.ema_fast, 2, 200)
        self.w_ema_mid = spin_int(self.params.ema_mid, 2, 300)
        self.w_ema_slow = spin_int(self.params.ema_slow, 2, 500)
        self.w_atr = spin_int(self.params.atr_length, 2, 200)
        self.w_stop_mult = spin_float(self.params.stop_atr_multiplier, 0.1, 20)
        self.w_tp1_mult = spin_float(self.params.tp1_atr_multiplier, 0.1, 20)
        self.w_trailing_mult = spin_float(self.params.trailing_atr_multiplier, 0.1, 20)
        self.w_balance = spin_float(self.params.initial_balance, 100, 10_000_000, 100)

        fields = [
            ("Risk % per trade", self.w_risk),
            ("Partial TP %", self.w_partial),
            ("DI Length", self.w_di),
            ("ADX Smoothing", self.w_adx_sm),
            ("ADX Threshold", self.w_adx_thr),
            ("EMA Fast", self.w_ema_fast),
            ("EMA Mid", self.w_ema_mid),
            ("EMA Slow", self.w_ema_slow),
            ("ATR Length", self.w_atr),
            ("Stop ATR Mult", self.w_stop_mult),
            ("TP1 ATR Mult", self.w_tp1_mult),
            ("Trailing ATR Mult", self.w_trailing_mult),
            ("Initial Balance", self.w_balance),
        ]
        for label, widget in fields:
            form.addRow(label, widget)
        return form

    def _update_params_from_ui(self) -> None:
        self.params = StrategyParameters(
            risk_per_trade=self.w_risk.value(),
            partial_tp_percent=self.w_partial.value(),
            di_length=self.w_di.value(),
            adx_smoothing=self.w_adx_sm.value(),
            adx_threshold=self.w_adx_thr.value(),
            ema_fast=self.w_ema_fast.value(),
            ema_mid=self.w_ema_mid.value(),
            ema_slow=self.w_ema_slow.value(),
            atr_length=self.w_atr.value(),
            stop_atr_multiplier=self.w_stop_mult.value(),
            tp1_atr_multiplier=self.w_tp1_mult.value(),
            trailing_atr_multiplier=self.w_trailing_mult.value(),
            initial_balance=self.w_balance.value(),
        )
        self.strategy = EmaAdxStrategy(self.params)
        self.backtester = BacktestEngine(self.params)

    def save_settings(self) -> None:
        self._update_params_from_ui()
        self.settings_store.save(self.params)
        QMessageBox.information(self, "OK", "Настройки сохранены")

    def refresh_markets(self) -> None:
        try:
            symbols = self.data_client.load_markets(self.exchange_box.currentText())
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Ошибка", str(exc))
            return
        if not symbols:
            QMessageBox.warning(self, "Нет данных", "Не удалось загрузить список рынков")
            return
        self.symbol_box.clear()
        self.symbol_box.addItems(symbols[:200])

    def _after_data_loaded(self) -> None:
        self._update_params_from_ui()
        self.analyzed = self.strategy.compute(self.raw_candles)
        self.chart.set_price_data(self.analyzed)
        self.refresh_signal(notify=True)

    def load_from_api(self) -> None:
        try:
            candles = self.data_client.fetch_ohlcv(
                exchange_name=self.exchange_box.currentText(),
                symbol=self.symbol_box.currentText(),
                timeframe=self.timeframe_box.currentText(),
                limit=500,
            )
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "API error", str(exc))
            return
        self.raw_candles = candles
        self._after_data_loaded()

    def load_from_csv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Выберите CSV", filter="CSV Files (*.csv)")
        if not path:
            return
        try:
            self.raw_candles = load_csv(path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "CSV error", str(exc))
            return
        self._after_data_loaded()

    def refresh_signal(self, notify: bool = False) -> None:
        snap = self.strategy.current_signal(self.analyzed)
        for key, label in self.signal_labels.items():
            value = getattr(snap, key)
            label.setText("-" if value is None else str(value))

        if notify and snap.status in (SignalStatus.LONG, SignalStatus.SHORT) and snap.status != self.last_status:
            self.notifier.notify_signal(
                "Новый сигнал",
                f"{snap.status.value} | {self.symbol_box.currentText()} {self.timeframe_box.currentText()} | {snap.current_price}",
            )
        self.last_status = snap.status

    def run_backtest(self) -> None:
        if self.analyzed.empty:
            QMessageBox.warning(self, "Нет данных", "Сначала загрузите данные")
            return

        result = self.backtester.run(self.analyzed, self.symbol_box.currentText())
        self.chart.set_equity_curve(result.equity_curve)

        self.trades_table.setRowCount(len(result.trades))
        running_balance = self.params.initial_balance
        for i, trade in enumerate(result.trades):
            running_balance += trade.pnl_usd
            values = [
                str(trade.trade_id),
                str(trade.entry_time),
                str(trade.exit_time),
                trade.symbol,
                trade.side,
                f"{trade.entry_price:.4f}",
                f"{trade.stop_price:.4f}",
                f"{trade.tp1_price:.4f}",
                f"{trade.exit_price:.4f}",
                trade.exit_reason,
                f"{trade.pnl_usd:.2f}",
                f"{trade.pnl_pct:.2f}",
                f"{running_balance:.2f}",
            ]
            for j, value in enumerate(values):
                self.trades_table.setItem(i, j, QTableWidgetItem(value))

        s = result.stats
        self.stats_label.setText(
            " | ".join(
                [
                    f"PnL: {s.total_pnl:.2f}",
                    f"Balance: {s.final_balance:.2f}",
                    f"Trades: {s.total_trades}",
                    f"Wins: {s.wins}",
                    f"Losses: {s.losses}",
                    f"Win Rate: {s.win_rate:.2f}%",
                    f"Avg: {s.avg_trade_pct:.2f}%",
                    f"PF: {s.profit_factor:.2f}",
                    f"Max DD: {s.max_drawdown_pct:.2f}%",
                ]
            )
        )
