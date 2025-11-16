from __future__ import annotations
import json
from pathlib import Path
from PyQt6.QtCore import QStandardPaths

DEFAULTS = {
    "version": "0.1.0",
    "theme": "system",
    "home": "dark://home",
    "search": "google",
    "pinned": [
        {"title": "ChatGPT", "url": "https://chatgpt.com", "icon": "https://chat.openai.com/favicon.ico"},
        {"title": "GitHub", "url": "https://github.com", "icon": "https://github.githubassets.com/favicons/favicon.png"},
        {"title": "MDN", "url": "https://developer.mozilla.org", "icon": "https://developer.mozilla.org/favicon-48x48.cbbd161b.png"},
    ],
}

class Settings:
    def __init__(self) -> None:
        data_dir = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
        data_dir.mkdir(parents=True, exist_ok=True)
        self._file = data_dir / "settings.json"
        self._cache = self._load()

    def _load(self) -> dict:
        if not self._file.exists():
            self._file.write_text(json.dumps(DEFAULTS, indent=2), encoding="utf-8")
            return dict(DEFAULTS)
        try:
            data = json.loads(self._file.read_text(encoding="utf-8"))
            merged = dict(DEFAULTS)
            merged.update(data)
            return merged
        except Exception:
            return dict(DEFAULTS)

    def all(self) -> dict:
        return self._cache

    def get(self, key: str):
        return self._cache.get(key)

    def set(self, key: str, value):
        self._cache[key] = value
        self._file.write_text(json.dumps(self._cache, indent=2), encoding="utf-8")
        return True
