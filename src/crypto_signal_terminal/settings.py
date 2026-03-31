from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import StrategyParameters


class SettingsStore:
    def __init__(self, file_path: Path | None = None):
        self.file_path = file_path or Path.home() / ".crypto_signal_terminal.json"

    def load(self) -> StrategyParameters:
        if not self.file_path.exists():
            return StrategyParameters()
        data = json.loads(self.file_path.read_text(encoding="utf-8"))
        return StrategyParameters(**data)

    def save(self, params: StrategyParameters) -> None:
        payload = asdict(params)
        self.file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
