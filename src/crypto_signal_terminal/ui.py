from __future__ import annotations

from dataclasses import asdict

import pandas as pd
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .data import load_csv
from .models import StrategyParameters
from .strategy import EmaAdxStrategy


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Crypto Signal Terminal")
        self.resize(1300, 800)

        self.params = StrategyParameters()
        self.strategy = EmaAdxStrategy(self.params)
        self.analyzed: pd.DataFrame = pd.DataFrame()

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        top = QHBoxLayout()
        self.btn_load = QPushButton("Загрузить CSV")
        self.btn_backtest = QPushButton("Запустить бэктест")
        self.btn_monitor = QPushButton("Старт мониторинга")
        self.btn_stop = QPushButton("Стоп")

        top.addWidget(self.btn_load)
        top.addWidget(self.btn_backtest)
        top.addWidget(self.btn_monitor)
        top.addWidget(self.btn_stop)
        top.addStretch(1)
        layout.addLayout(top)

        splitter = QSplitter()
        layout.addWidget(splitter, 1)

        self.chart_stub = QLabel("График (stub): для V1 подключите pyqtgraph/lightweight charts")
        self.chart_stub.setStyleSheet("background:#141414;color:#ddd;padding:16px;")
        splitter.addWidget(self.chart_stub)

        right_panel = QWidget()
        right_layout = QFormLayout(right_panel)
        self.signal_labels = {}
        for key in ["status", "signal_time", "current_price", "entry_price", "stop_loss", "take_profit", "comment"]:
            label = QLabel("-")
            right_layout.addRow(key, label)
            self.signal_labels[key] = label

        params_label = QLabel("Параметры стратегии")
        right_layout.addRow(params_label)
        for k, v in asdict(self.params).items():
            right_layout.addRow(k, QLabel(str(v)))
        splitter.addWidget(right_panel)

        self.trades_table = QTableWidget(0, 8)
        self.trades_table.setHorizontalHeaderLabels(
            ["#", "Entry", "Exit", "Side", "Entry Price", "Exit Price", "PnL $", "Reason"]
        )
        layout.addWidget(self.trades_table)

        self.timer = QTimer(self)
        self.timer.setInterval(10_000)
        self.timer.timeout.connect(self.refresh_signal)

        self.btn_load.clicked.connect(self.load_data)
        self.btn_backtest.clicked.connect(self.run_backtest)
        self.btn_monitor.clicked.connect(self.timer.start)
        self.btn_stop.clicked.connect(self.timer.stop)

    def load_data(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Выберите CSV", filter="CSV Files (*.csv)")
        if not path:
            return
        try:
            candles = load_csv(path)
            self.analyzed = self.strategy.compute(candles)
            self.refresh_signal()
            QMessageBox.information(self, "OK", f"Загружено свечей: {len(self.analyzed)}")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Ошибка", str(exc))

    def refresh_signal(self) -> None:
        snap = self.strategy.current_signal(self.analyzed)
        for key, label in self.signal_labels.items():
            value = getattr(snap, key)
            label.setText("-" if value is None else str(value))

    def run_backtest(self) -> None:
        if self.analyzed.empty:
            QMessageBox.warning(self, "Нет данных", "Сначала загрузите данные")
            return

        rows = []
        for idx, row in self.analyzed.iterrows():
            if row.get("long_signal"):
                rows.append((idx, "LONG", row["close"]))
            elif row.get("short_signal"):
                rows.append((idx, "SHORT", row["close"]))

        self.trades_table.setRowCount(len(rows))
        for i, (time, side, price) in enumerate(rows):
            values = [
                str(i + 1),
                str(time),
                "-",
                side,
                f"{price:.2f}",
                "-",
                "0.00",
                "Signal only (V1 stub)",
            ]
            for j, value in enumerate(values):
                self.trades_table.setItem(i, j, QTableWidgetItem(value))
