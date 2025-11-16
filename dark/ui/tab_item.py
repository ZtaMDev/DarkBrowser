from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt

class TabItemWidget(QWidget):
    def __init__(self, title: str, icon, close_icon_path: str, is_web_tab: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("TabItem")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.is_web_tab = is_web_tab
        self.is_favorite = False
        self.tab_url = ""
        
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 6, 8, 8)
        lay.setSpacing(6)
        self.title_lbl = QLabel(title or "New Tab")
        self.close_btn = QPushButton()
        self.close_btn.setObjectName("CloseBtn")
        from PyQt6.QtGui import QIcon
        self.close_btn.setIcon(QIcon(close_icon_path))
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.setVisible(False)
        
        # Star button for favorites (only for web tabs)
        self.star_btn = QPushButton()
        self.star_btn.setObjectName("StarBtn")
        from pathlib import Path
        icon_base = str((Path(__file__).parent.parent / 'resources' / 'icons').resolve())
        self.star_icon_path = icon_base + "/star.svg"
        self.star_filled_icon_path = icon_base + "/star_filled.svg"
        self.star_btn.setIcon(QIcon(self.star_icon_path))
        self.star_btn.setFixedSize(20, 20)
        self.star_btn.setVisible(False)
        self.star_btn.clicked.connect(self.toggle_favorite)
        
        lay.addWidget(self.title_lbl, 1)
        if self.is_web_tab:
            lay.addWidget(self.star_btn)
        lay.addWidget(self.close_btn)

    def enterEvent(self, e):  # pragma: no cover
        self.close_btn.setVisible(True)
        if self.is_web_tab:
            self.star_btn.setVisible(True)
        return super().enterEvent(e)

    def leaveEvent(self, e):  # pragma: no cover
        self.close_btn.setVisible(False)
        if self.is_web_tab:
            self.star_btn.setVisible(False)
        return super().leaveEvent(e)
    
    def toggle_favorite(self):
        """Toggle favorite status and update icon"""
        self.is_favorite = not self.is_favorite
        from PyQt6.QtGui import QIcon
        if self.is_favorite:
            self.star_btn.setIcon(QIcon(self.star_filled_icon_path))
            self.add_to_favorites()
        else:
            self.star_btn.setIcon(QIcon(self.star_icon_path))
            self.remove_from_favorites()
    
    def add_to_favorites(self):
        """Add current tab to favorites"""
        if self.tab_url and hasattr(self, 'main_window') and self.main_window:
            self.main_window.add_favorite(self.tab_url, self.title_lbl.text())
    
    def remove_from_favorites(self):
        """Remove current tab from favorites"""
        if self.tab_url and hasattr(self, 'main_window') and self.main_window:
            self.main_window.remove_favorite(self.tab_url)
    
    def set_url(self, url: str):
        """Set the tab URL for favorites functionality"""
        self.tab_url = url
    
    def set_favorite_status(self, is_favorite: bool):
        """Set favorite status and update icon"""
        self.is_favorite = is_favorite
        from PyQt6.QtGui import QIcon
        if is_favorite:
            self.star_btn.setIcon(QIcon(self.star_filled_icon_path))
        else:
            self.star_btn.setIcon(QIcon(self.star_icon_path))

    def set_title(self, title: str):
        self.title_lbl.setText(title or "New Tab")

    def set_icon(self, icon):
        pass
