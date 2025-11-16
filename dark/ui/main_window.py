from __future__ import annotations
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtGui import QIcon, QClipboard, QShortcut, QKeySequence
from PyQt6.QtWidgets import (
    QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QListWidget, QListWidgetItem, QApplication, QStackedLayout, QDockWidget, QMenu
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtCore import QStandardPaths
import os
import sys
import json
import time
import traceback
import shutil
from pathlib import Path
from .tabs import TabManager
from .home_widget import HomeWidget
from .settings_widget import SettingsWidget
from .downloads_widget import DownloadsWidget
from .notification_widget import NotificationManager


class MainWindow(QMainWindow):
    def __init__(self, profile: QWebEngineProfile, settings, downloads=None) -> None:
        super().__init__()
        self.setWindowTitle("Dark Browser")
        self.resize(1400, 900)
        self.profile = profile
        self.settings = settings
        self.downloads = downloads

        # Central widget (navbar + content stack)
        central = QWidget(self)
        self.setCentralWidget(central)
        root_v = QVBoxLayout(central)
        root_v.setContentsMargins(0, 0, 0, 0)
        root_v.setSpacing(0)

        # Navbar
        nav = QHBoxLayout()
        nav.setContentsMargins(8, 8, 8, 8)
        nav.setSpacing(8)
        nav_widget = QWidget(); nav_widget.setObjectName("NavBar"); nav_widget.setLayout(nav)
        root_v.addWidget(nav_widget)

        def btn(text: str, icon_path: str | None = None, tooltip: str | None = None):
            b = QPushButton()
            if icon_path:
                b.setIcon(QIcon(icon_path))
            else:
                b.setText(text)
            b.setFixedSize(32, 28)
            if tooltip:
                b.setToolTip(tooltip)
            return b

        icon_base = str((__import__('pathlib').Path(__file__).parent.parent / 'resources' / 'icons').resolve())
        self.toggle_tabs_btn = btn("", icon_base+"/tabs.svg", "Toggle Tabs")
        self.back_btn = btn("", icon_base+"/back.svg", "Atrás")
        self.fwd_btn = btn("", icon_base+"/forward.svg", "Adelante")
        self.reload_btn = btn("", icon_base+"/reload.svg", "Recargar")
        self.url_edit = QLineEdit(); self.url_edit.setPlaceholderText("Buscar o escribir dirección")
        self.home_btn = btn("", icon_base+"/home.svg", "Home")
        self.dl_btn = btn("", icon_base+"/downloads.svg", "Descargas")
        self.set_btn = btn("", icon_base+"/settings.svg", "Configuración")
        self.side_btn = btn("", icon_base+"/sidebar.svg", "Sidebar")

        nav.addWidget(self.toggle_tabs_btn); nav.addWidget(self.back_btn); nav.addWidget(self.fwd_btn); nav.addWidget(self.reload_btn)
        nav.addWidget(self.url_edit, 1)
        nav.addWidget(self.home_btn); nav.addWidget(self.dl_btn); nav.addWidget(self.set_btn); nav.addWidget(self.side_btn)

        # Favorites bar (initially hidden)
        self.favorites_bar = QWidget()
        self.favorites_bar.setObjectName("FavoritesBar")
        self.favorites_bar.setVisible(False)
        self.favorites_layout = QHBoxLayout(self.favorites_bar)
        self.favorites_layout.setContentsMargins(8, 2, 8, 2)
        self.favorites_layout.setSpacing(2)
        root_v.addWidget(self.favorites_bar)

        # Tabs dock (left)
        self.tabs_list = QListWidget()
        self.tabs_list.setMinimumWidth(196)
        self.tabs_list.setMaximumWidth(260)
        self.tabs_list.itemClicked.connect(self._on_tab_clicked)
        self.tabs_dock = QDockWidget("Tabs", self)
        self.tabs_dock.setObjectName("TabsDock")
        self.tabs_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        self.tabs_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetClosable)
        self.tabs_dock.setWidget(self.tabs_list)
        self.tabs_dock.closeEvent = lambda e: self._on_tabs_dock_closed()
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.tabs_dock)
        self.tabs_dock.setVisible(True)

        # Content stack (central)
        self.content = QWidget(); self.content.setStyleSheet("background:#0f1115")
        self.content_stack = QStackedLayout(self.content)
        self.content_stack.setContentsMargins(0, 0, 0, 0)
        self.content_stack.setStackingMode(QStackedLayout.StackingMode.StackOne)
        root_v.addWidget(self.content, 1)

        # Sidebar (ChatGPT)
        self.sidebar_view = QWebEngineView(self)
        self.sidebar_dock = QDockWidget("ChatGPT", self)
        self.sidebar_view.setMinimumWidth(400)
        self.sidebar_view.setMaximumWidth(700)
        self.sidebar_dock.setObjectName("SidebarDock")
        self.sidebar_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.sidebar_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetClosable)
        self.sidebar_dock.setWidget(self.sidebar_view)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.sidebar_dock)
        self.sidebar_dock.setVisible(False)

        # Initial dock sizes
        try:
            self.resizeDocks([self.tabs_dock, self.sidebar_dock], [110, 420], Qt.Orientation.Horizontal)
        except Exception:
            pass

        # Initialize favorites list
        self.favorites = []  # List of (url, title) tuples
        self.favorites_widgets = []  # List of favorite button widgets
        
        # Load favorites from settings
        self.load_favorites()

        # Main view stack manager
        self.tabman = TabManager(self.profile, self.tabs_list, self.url_edit, self.content, self.content_stack, settings=self.settings, downloads=self.downloads, main_window=self)
        self.side_open = False
        
        # Notification manager
        self.notification_manager = NotificationManager(self)
        self.notification_manager.hide()  # Initially hidden, shown when needed
        
        # Setup download notifications
        if self.downloads:
            self.downloads.set_notify_callback(self.show_notification)
            
        # Download icon update timer
        self.download_icon_timer = QTimer(self)
        self.download_icon_timer.timeout.connect(self._update_download_icon)
        self.download_icon_timer.start(1000)
        
        # Resume any paused downloads on startup
        if self.downloads:
            self.downloads.resume_all_downloads()

        # Restore state/geometry but force sidebar to start closed
        try:
            import base64
            geo = self.settings.get('win_geometry')
            state = self.settings.get('win_state')
            if geo:
                self.restoreGeometry(base64.b64decode(geo))
            if state:
                self.restoreState(base64.b64decode(state))
            # Force sidebar to start closed regardless of saved state
            self.side_open = False
            self.sidebar_dock.hide()
        except Exception:
            pass

        # Signals
        self.back_btn.clicked.connect(lambda: self.tabman.navigate("back"))
        self.fwd_btn.clicked.connect(lambda: self.tabman.navigate("forward"))
        self.reload_btn.clicked.connect(lambda: self.tabman.navigate("reload"))
        self.home_btn.clicked.connect(lambda: self.tabman.open_url(self.settings.get("home") or "dark://home"))
        self.dl_btn.clicked.connect(lambda: self.tabman.open_url("dark://downloads"))
        self.set_btn.clicked.connect(lambda: self.tabman.open_url("dark://settings"))
        self.side_btn.clicked.connect(lambda: self.toggle_sidebar())
        self.toggle_tabs_btn.clicked.connect(lambda: self.toggle_tabs_dock())
        self.url_edit.returnPressed.connect(self._on_enter_address)
        
        # Initially hide toggle tabs button (only show when tabs dock is hidden)
        self.toggle_tabs_btn.hide()
        
        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()
        
        # Welcome dialog system
        self._setup_welcome_dialog()

    def _setup_keyboard_shortcuts(self):
        """Setup all keyboard shortcuts"""
        # Ctrl+T: New tab
        shortcut_new_tab = QShortcut(QKeySequence("Ctrl+T"), self)
        shortcut_new_tab.activated.connect(lambda: self.tabman.create_tab())
        
        # Ctrl+W: Close current tab
        shortcut_close_tab = QShortcut(QKeySequence("Ctrl+W"), self)
        shortcut_close_tab.activated.connect(lambda: self.tabman.close_tab(self.tabman.active_index))
        
        # Ctrl+L: Focus URL bar
        shortcut_focus_url = QShortcut(QKeySequence("Ctrl+L"), self)
        shortcut_focus_url.activated.connect(self.url_edit.setFocus)
        
        # Ctrl+R: Reload page
        shortcut_reload = QShortcut(QKeySequence("Ctrl+R"), self)
        shortcut_reload.activated.connect(lambda: self.tabman.navigate("reload"))
        
        # F5: Reload page
        shortcut_f5_reload = QShortcut(QKeySequence("F5"), self)
        shortcut_f5_reload.activated.connect(lambda: self.tabman.navigate("reload"))
        
        # Ctrl+Shift+T: Reopen closed tab (placeholder - needs history)
        shortcut_reopen = QShortcut(QKeySequence("Ctrl+Shift+T"), self)
        shortcut_reopen.activated.connect(lambda: self.tabman.create_tab())  # Simple implementation
        
        # Ctrl+Tab: Next tab
        shortcut_next_tab = QShortcut(QKeySequence("Ctrl+Tab"), self)
        shortcut_next_tab.activated.connect(lambda: self._cycle_tab(1))
        
        # Ctrl+Shift+Tab: Previous tab
        shortcut_prev_tab = QShortcut(QKeySequence("Ctrl+Shift+Tab"), self)
        shortcut_prev_tab.activated.connect(lambda: self._cycle_tab(-1))
        
        # Ctrl+D: Add to favorites (removed - not implemented)
        # shortcut_favorite = QShortcut(QKeySequence("Ctrl+D"), self)
        # shortcut_favorite.activated.connect(self._toggle_favorite)
        
        # F11: Fullscreen
        shortcut_fullscreen = QShortcut(QKeySequence("F11"), self)
        shortcut_fullscreen.activated.connect(self._toggle_fullscreen)
        
        # Ctrl+H: History (removed - not implemented)
        # shortcut_history = QShortcut(QKeySequence("Ctrl+H"), self)
        # shortcut_history.activated.connect(lambda: self.tabman.open_url("dark://home"))
        
        # Ctrl+J: Downloads
        shortcut_downloads = QShortcut(QKeySequence("Ctrl+J"), self)
        shortcut_downloads.activated.connect(lambda: self.tabman.open_url("dark://downloads"))
        
        # Ctrl+Shift+L: Settings
        shortcut_settings = QShortcut(QKeySequence("Ctrl+,"), self)
        shortcut_settings.activated.connect(lambda: self.tabman.open_url("dark://settings"))

    def _setup_welcome_dialog(self):
        """Setup and show welcome dialog for first run or debug mode"""
        from PyQt6.QtCore import QTimer
        from .welcome_dialog import WelcomeDialog
        
        # Check if this is first run or debug mode
        first_run = not self.settings.get('welcome_shown')
        debug_always_show = self.settings.get('debug_welcome_always')
        
        if first_run or debug_always_show:
            # Show welcome dialog after window is fully loaded
            QTimer.singleShot(500, self._show_welcome_dialog)
            
            # Mark as shown (unless in debug mode)
            if not debug_always_show:
                self.settings.set('welcome_shown', True)
    
    def _show_welcome_dialog(self):
        """Show the welcome dialog"""
        from .welcome_dialog import WelcomeDialog
        
        welcome_dialog = WelcomeDialog(self)
        welcome_dialog.exec()

    def _cycle_tab(self, direction: int):
        """Cycle through tabs (1 for next, -1 for previous)"""
        if not self.tabman.tabs:
            return
        
        current = self.tabman.active_index
        if direction == 1:  # Next tab
            next_tab = current + 1
            if next_tab >= len(self.tabman.tabs):
                next_tab = 0
        else:  # Previous tab
            next_tab = current - 1
            if next_tab < 0:
                next_tab = len(self.tabman.tabs) - 1
        
        self.tabman.set_active(next_tab)
    
    def _toggle_favorite(self):
        """Toggle current page as favorite"""
        if 0 <= self.tabman.active_index < len(self.tabman.tabs):
            tab = self.tabman.tabs[self.tabman.active_index]
            if tab.view:
                url = tab.view.url().toString()
                title = tab.view.title() or "Untitled"
                if url and url.startswith("http"):
                    # Check if already favorited
                    if any(url == fav_url for fav_url, _ in self.favorites):
                        self.remove_favorite(url)
                    else:
                        self.add_favorite(url, title)
    
    def _toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _on_enter_address(self):
        text = self.url_edit.text().strip()
        if not text:
            return
        url = self.tabman.parse_url_or_search(text, self.settings.get("search") or "google")
        self.tabman.open_url(url)

    def _on_tab_clicked(self, item: QListWidgetItem):  # type: ignore[name-defined]
        idx = self.tabs_list.row(item)
        if idx == self.tabs_list.count() - 1:
            # Don't create Home tab automatically - create empty web tab instead
            self.tabman.create_tab()
            self.tabman.set_active(len(self.tabman.tabs) - 1)
        else:
            self.tabman.set_active(idx)

    def open_url(self, url: str):
        self.tabman.open_url(url)

    def toggle_tabs_dock(self):
        """Toggle tabs dock visibility and show/hide toggle button accordingly"""
        if self.tabs_dock.isVisible():
            # Hide tabs dock and show toggle button
            self.tabs_dock.hide()
            self.toggle_tabs_btn.show()
        else:
            # Show tabs dock and hide toggle button
            self.tabs_dock.show()
            self.toggle_tabs_btn.hide()
    
    def _on_tabs_dock_closed(self):
        """Handle tabs dock close event"""
        self.toggle_tabs_btn.show()

    def clear_data(self):
        """Clear all browser data including cache, cookies, and storage"""
        try:
            # Clear HTTP cache
            self.profile.clearHttpCache()
            
            # Clear all cookies with proper callback
            def cookies_deleted():
                # Clear localStorage and sessionStorage
                from PyQt6.QtCore import QTimer
                def clear_storage():
                    # Force clear storage paths
                    import shutil
                    from pathlib import Path
                    data_dir = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)) / "Dark Browser"
                    cache_dir = data_dir / "cache"
                    storage_dir = data_dir / "storage"
                    
                    try:
                        if cache_dir.exists():
                            shutil.rmtree(cache_dir)
                        if storage_dir.exists():
                            shutil.rmtree(storage_dir)
                    except Exception:
                        pass
                    
                    # Show notification
                    self.show_notification("All browser data cleared successfully", "success", 3000)
                
                QTimer.singleShot(200, clear_storage)
            
            # Delete cookies with callback
            self.profile.cookieStore().deleteAllCookies()
            QTimer.singleShot(100, cookies_deleted)
            
            self.show_notification("Clearing browser data...", "info", 2000)
            
        except Exception as e:
            self.show_notification(f"Error clearing data: {str(e)}", "error", 3000)

    def toggle_favorites_bar(self):
        """Toggle the visibility of the favorites bar"""
        current_visible = self.favorites_bar.isVisible()
        self.favorites_bar.setVisible(not current_visible)
        
    def show_favorites_bar(self):
        """Show the favorites bar"""
        self.favorites_bar.setVisible(True)
        
    def hide_favorites_bar(self):
        """Hide the favorites bar"""
        self.favorites_bar.setVisible(False)
    
    def _update_favorites_bar_visibility(self):
        """Update favorites bar visibility based on setting and current tab"""
        if not self.favorites:
            self.hide_favorites_bar()
            return
            
        favorites_bar_setting = self.settings.get('favorites_bar')
        if not favorites_bar_setting:
            favorites_bar_setting = 'show'
        
        if favorites_bar_setting == 'show':
            self.show_favorites_bar()
        else:  # hide
            self.hide_favorites_bar()
    
    def load_favorites(self):
        """Load favorites from settings"""
        saved_favorites = self.settings.get('favorites')
        self.favorites = saved_favorites if isinstance(saved_favorites, list) else []
        self.rebuild_favorites_bar()
        # Update visibility based on setting
        self._update_favorites_bar_visibility()
    
    def save_favorites(self):
        """Save favorites to settings"""
        self.settings.set('favorites', self.favorites)
    
    def add_favorite(self, url: str, title: str):
        """Add a favorite to the list and update UI"""
        # Remove if already exists
        self.favorites = [(u, t) for u, t in self.favorites if u != url]
        # Add to the end
        self.favorites.append((url, title))
        self.save_favorites()
        self.rebuild_favorites_bar()
        self._update_favorites_bar_visibility()
        # Update all tabs' favorite status
        if hasattr(self.tabman, '_update_all_tabs_favorite_status'):
            self.tabman._update_all_tabs_favorite_status()
    
    def remove_favorite(self, url: str):
        """Remove a favorite from the list and update UI"""
        self.favorites = [(u, t) for u, t in self.favorites if u != url]
        self.save_favorites()
        self.rebuild_favorites_bar()
        self._update_favorites_bar_visibility()
        # Update all tabs' favorite status
        if hasattr(self.tabman, '_update_all_tabs_favorite_status'):
            self.tabman._update_all_tabs_favorite_status()
    
    def rebuild_favorites_bar(self):
        """Rebuild the favorites bar UI with pre-loading for performance"""
        # Clear existing widgets
        for widget in self.favorites_widgets:
            widget.deleteLater()
        self.favorites_widgets.clear()
        
        # Clear layout
        while self.favorites_layout.count():
            item = self.favorites_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add favorite buttons with pre-loading
        for url, title in self.favorites:
            # Limit title length and add ellipsis if needed
            display_title = title[:15] + "..." if len(title) > 15 else title
            
            btn = QPushButton(display_title)
            btn.setObjectName("FavoriteButton")
            btn.setToolTip(f"{title}\n{url}")
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda pos, b=btn, u=url: self._favorite_context_menu(pos, b, u))
            
            # Pre-load the URL to avoid lag when clicked
            btn.setProperty("target_url", url)
            
            # Use a more efficient connection with pre-stored URL
            btn.clicked.connect(lambda checked=False, button=btn: self.open_url(button.property("target_url")))
            
            self.favorites_layout.addWidget(btn)
            self.favorites_widgets.append(btn)
        
        # Add stretch to push buttons to the left
        self.favorites_layout.addStretch()

    def _favorite_context_menu(self, pos, button, url):
        """Show context menu for favorite button"""
        menu = QMenu(self)
        remove_action = menu.addAction("Remove from Favorites")
        remove_action.triggered.connect(lambda: self.remove_favorite(url))
        
        # Show menu at button position
        global_pos = button.mapToGlobal(pos)
        menu.exec(global_pos)

    def toggle_sidebar(self, with_text: str | None = None):
        # Always open sidebar when sending text
        if with_text:
            # Open sidebar if closed, keep open if already open
            if not self.side_open:
                self.side_open = True
                self.sidebar_dock.show()
            
            # Load ChatGPT if not loaded
            if self.sidebar_view.url().isEmpty():
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(50, lambda: self.sidebar_view.load(QUrl("https://chatgpt.com")))
            
            # Copy text to clipboard
            from PyQt6.QtGui import QClipboard
            clipboard = QApplication.clipboard()
            clipboard.setText(with_text)
            
            # Show small notification
            self.show_notification("Text copied to clipboard", "info", 2000)
            
            # Focus the sidebar after a short delay to avoid UI conflicts
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, lambda: self.sidebar_view.setFocus())
        else:
            # Toggle sidebar behavior when no text
            if self.side_open:
                # Close sidebar
                self.side_open = False
                self.sidebar_dock.hide()
            else:
                # Open sidebar
                self.side_open = True
                self.sidebar_dock.show()
                # Load ChatGPT if not loaded
                if self.sidebar_view.url().isEmpty():
                    self.sidebar_view.load(QUrl("https://chatgpt.com"))

    def show_notification(self, message: str, notification_type: str = "info", duration: int = 3000):
        """Show a notification message"""
        # Check if notifications are disabled in settings
        notifications_setting = self.settings.get('notifications') or 'enable'
        if notifications_setting == 'disable':
            return
            
        if notification_type == "download_update":
            # Handle download state changes
            self._update_download_icon()
            return
        
        # Ensure notification manager is visible
        if self.notification_manager.isHidden():
            self.notification_manager.show()
            
        self.notification_manager.show_notification(message, notification_type, duration)
        
    def show_success(self, message: str, duration: int = 3000):
        """Show success notification"""
        self.notification_manager.show_success(message, duration)
        
    def show_error(self, message: str, duration: int = 3000):
        """Show error notification"""
        self.notification_manager.show_error(message, duration)
        
    def show_warning(self, message: str, duration: int = 3000):
        """Show warning notification"""
        self.notification_manager.show_warning(message, duration)
        
    def show_info(self, message: str, duration: int = 3000):
        """Show info notification"""
        self.notification_manager.show_info(message, duration)
        
    def _update_download_icon(self):
        """Update download icon based on download status"""
        if not self.downloads:
            return
            
        if self.downloads.has_active_downloads():
            # Change icon to downloading state
            icon_base = str((__import__('pathlib').Path(__file__).parent.parent / 'resources' / 'icons').resolve())
            self.dl_btn.setIcon(QIcon(f"{icon_base}/downloads_active.svg"))
            self.dl_btn.setToolTip("Descargas (descargando...)")
        else:
            # Normal icon
            icon_base = str((__import__('pathlib').Path(__file__).parent.parent / 'resources' / 'icons').resolve())
            self.dl_btn.setIcon(QIcon(f"{icon_base}/downloads.svg"))
            self.dl_btn.setToolTip("Descargas")

    # Persist session/layout
    def closeEvent(self, e):  # pragma: no cover
        # Check for active downloads before closing
        if self.downloads and self.downloads.has_active_downloads():
            from PyQt6.QtWidgets import QMessageBox, QApplication
            
            reply = QMessageBox.question(
                self, 
                "Descargas activas", 
                "Hay descargas en progreso. ¿Desea salir y pausar las descargas?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Pause all downloads
                self.downloads.pause_all_downloads()
                self.show_info("Descargas pausadas. Puede reanudarlas cuando vuelva a abrir la aplicación.", 5000)
            else:
                # Don't close
                e.ignore()
                return
        
        try:
            sess = self.tabman.export_session()
            self.settings.set('session', sess.get('tabs', []))
            # Save the actual active tab index instead of last tab
            self.settings.set('session_active', self.tabman.active_index if self.tabman.active_index >= 0 else 0)
            # Save favorites
            self.save_favorites()
            import base64
            self.settings.set('win_geometry', base64.b64encode(self.saveGeometry()).decode('ascii'))
            self.settings.set('win_state', base64.b64encode(self.saveState()).decode('ascii'))
        except Exception:
            pass
        return super().closeEvent(e)
