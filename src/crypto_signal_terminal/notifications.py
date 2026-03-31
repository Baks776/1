from __future__ import annotations

from PySide6.QtWidgets import QApplication, QMessageBox, QWidget


class Notifier:
    def __init__(self, parent: QWidget):
        self.parent = parent

    def notify_signal(self, title: str, message: str) -> None:
        QApplication.beep()
        QMessageBox.information(self.parent, title, message)
