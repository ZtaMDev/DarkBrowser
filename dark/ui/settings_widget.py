from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QFrame, QScrollArea
from PyQt6.QtCore import Qt, QTimer

class SettingsWidget(QWidget):
    def __init__(self, settings, main_window=None, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.main_window = main_window
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("QScrollArea{background:transparent;border:none;} QScrollArea>QWidget>QWidget{background:#1a1d26;}")
        
        # Create content widget to hold all settings
        content_widget = QWidget()
        lay = QVBoxLayout(content_widget)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(16)
        
        card = QFrame(); card.setStyleSheet("QFrame{background:#141821;border:1px solid rgba(255,255,255,.06);border-radius:16px}")
        inner = QVBoxLayout(card)
        # Search engine
        row1 = _row("Default Search Engine")
        self.engine = QComboBox(); self.engine.addItems(["google","duckduckgo","bing","brave"]) 
        row1.addWidget(self.engine, 1)
        inner.addLayout(row1)
        # Home
        row2 = _row("Home page")
        self.home = QLineEdit(); self.home.setPlaceholderText("dark://home")
        row2.addWidget(self.home, 1)
        inner.addLayout(row2)
        # Favorites bar
        row3 = _row("Favorites Bar")
        self.favorites_bar = QComboBox()
        self.favorites_bar.addItems(["show", "hide"])
        row3.addWidget(self.favorites_bar, 1)
        inner.addLayout(row3)
        # Notifications
        row4 = _row("Notifications")
        self.notifications = QComboBox()
        self.notifications.addItems(["enable", "disable"])
        row4.addWidget(self.notifications, 1)
        inner.addLayout(row4)
        # Debug & Welcome
        row5 = _row("Debug & Welcome")
        welcome_btn = QPushButton("See Welcome Page")
        welcome_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #2563eb;
            }
        """)
        welcome_btn.clicked.connect(self._show_welcome_page)
        row5.addWidget(welcome_btn, 1)
        inner.addLayout(row5)
        
        # Data Management
        row6 = _row("Data Management")
        clear_cache_btn = QPushButton("Clear Cache & Cookies")
        clear_cache_btn.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #dc2626;
            }
        """)
        clear_cache_btn.clicked.connect(self._clear_data)
        row6.addWidget(clear_cache_btn, 1)
        inner.addLayout(row6)
        # Keyboard Shortcuts
        shortcuts_frame = QFrame()
        shortcuts_frame.setStyleSheet("QFrame{background:#141821;border:1px solid rgba(255,255,255,.06);border-radius:16px}")
        shortcuts_layout = QVBoxLayout(shortcuts_frame)
        
        shortcuts_title = QLabel("Keyboard Shortcuts")
        shortcuts_title.setStyleSheet("QLabel{font-size:14px;font-weight:600;color:#fff;margin:8px}")
        shortcuts_layout.addWidget(shortcuts_title)
        
        shortcuts_content = QWidget()
        shortcuts_content_layout = QVBoxLayout(shortcuts_content)
        shortcuts_content_layout.setContentsMargins(16, 8, 16, 16)
        
        # Create shortcuts list
        shortcuts = [
            ("Ctrl+T", "New Tab"),
            ("Ctrl+W", "Close Current Tab"),
            ("Ctrl+L", "Focus URL Bar"),
            ("Ctrl+R", "Reload Page"),
            ("F5", "Reload Page"),
            ("Ctrl+Shift+T", "Reopen Closed Tab"),
            ("Ctrl+Tab", "Next Tab"),
            ("Ctrl+Shift+Tab", "Previous Tab"),
            ("F11", "Toggle Fullscreen"),
            ("Ctrl+J", "Downloads"),
            ("Ctrl+,", "Settings")
        ]
        
        for shortcut, description in shortcuts:
            row = QHBoxLayout()
            row.setContentsMargins(0, 2, 0, 2)
            
            shortcut_label = QLabel(shortcut)
            shortcut_label.setStyleSheet("QLabel{color:#4a9eff;font-weight:500;min-width:80px}")
            
            desc_label = QLabel(description)
            desc_label.setStyleSheet("QLabel{color:#aaa}")
            
            row.addWidget(shortcut_label)
            row.addWidget(desc_label, 1)
            shortcuts_content_layout.addLayout(row)
        
        shortcuts_layout.addWidget(shortcuts_content)
        lay.addWidget(shortcuts_frame)
        
        lay.addWidget(card)
        self._load()
        self.engine.currentTextChanged.connect(lambda v: self.settings.set("search", v))
        self.home.editingFinished.connect(lambda: self.settings.set("home", self.home.text().strip() or "dark://home"))
        self.favorites_bar.currentTextChanged.connect(self._on_favorites_bar_changed)
        self.notifications.currentTextChanged.connect(lambda v: self.settings.set("notifications", v))
        
        # Set the content widget for scroll area
        scroll.setWidget(content_widget)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll)

    def _load(self):
        cfg = self.settings.all()
        self.engine.setCurrentText(cfg.get("search","google"))
        self.home.setText(cfg.get("home","dark://home"))
        favorites_bar_setting = cfg.get("favorites_bar")
        if not favorites_bar_setting:
            favorites_bar_setting = "show"
        self.favorites_bar.setCurrentText(favorites_bar_setting)
        notifications_setting = cfg.get("notifications")
        if not notifications_setting:
            notifications_setting = "enable"
        self.notifications.setCurrentText(notifications_setting)

    def _on_favorites_bar_changed(self, value):
        """Handle favorites bar setting change with instant feedback"""
        # Save the setting
        self.settings.set("favorites_bar", value)
        
        # Apply instantly if main_window is available
        if self.main_window and hasattr(self.main_window, '_update_favorites_bar_visibility'):
            # Use QTimer.singleShot to apply in the next event loop iteration
            # This prevents UI blocking and makes it feel instant
            QTimer.singleShot(0, self.main_window._update_favorites_bar_visibility)

    def _show_welcome_page(self):
        """Show the welcome dialog"""
        if self.main_window and hasattr(self.main_window, '_show_welcome_dialog'):
            self.main_window._show_welcome_dialog()

    def _clear_data(self):
        if self.main_window and hasattr(self.main_window, 'clear_data'):
            self.main_window.clear_data()

def _row(label: str):
    box = QHBoxLayout(); box.setContentsMargins(8,8,8,8)
    box.addWidget(QLabel(label))
    return box
