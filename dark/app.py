from __future__ import annotations
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineCore import QWebEngineProfile
from .core.settings import Settings
from .core.scheme import register_dark_scheme, DarkUrlSchemeHandler
from .core.downloads import DownloadsManager
from .ui.main_window import MainWindow

class DarkApp:
    def __init__(self) -> None:
        self.settings = Settings()
        # Register custom scheme before profile usage
        register_dark_scheme()
        self.profile = QWebEngineProfile.defaultProfile()
        self.downloads = DownloadsManager(self.profile)
        pages_dir = Path(__file__).parent / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)
        self.scheme_handler = DarkUrlSchemeHandler(
            pages_dir,
            downloads_provider=self.downloads.list,
            settings_provider=self.settings.all,
            settings_actions=self._settings_action,
            downloads_actions=self.downloads.action,
        )
        self.profile.installUrlSchemeHandler(b"dark", self.scheme_handler)
        self.window = MainWindow(self.profile, self.settings, self.downloads)

    def _settings_action(self, key: str, value):
        """Handle settings changes"""
        if key == "search":
            self.window.tab_manager.search_engine = value
        elif key == "home":
            self.window.tab_manager.home_url = value

    def run(self):
        self.window.show()
        # Don't open initial tab here - TabManager already handles it
