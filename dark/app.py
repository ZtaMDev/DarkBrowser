from __future__ import annotations
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
from PyQt6.QtCore import QStandardPaths
from .core.settings import Settings
from .core.scheme import register_dark_scheme, DarkUrlSchemeHandler
from .core.downloads import DownloadsManager
from .ui.main_window import MainWindow

class DarkApp:
    def __init__(self) -> None:
        self.settings = Settings()
        # Register custom scheme before profile usage
        register_dark_scheme()
        self.profile = QWebEngineProfile()
        self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        
        # Set proper user agent for better compatibility
        self.profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Set storage paths FIRST to ensure cookies are loaded
        data_dir = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)) / "Dark Browser"
        data_dir.mkdir(parents=True, exist_ok=True)
        self.profile.setCachePath(str(data_dir / "cache"))
        self.profile.setPersistentStoragePath(str(data_dir / "storage"))
        
        # Force loading of existing cookies
        self.profile.cookieStore().loadAllCookies()
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
