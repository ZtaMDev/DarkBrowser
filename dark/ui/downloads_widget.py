from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt, QTimer, QSize

class DownloadItemWidget(QFrame):
    def __init__(self, item: dict, on_action, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("DownloadItem")
        self.setStyleSheet("""
            QFrame#DownloadItem {
                background: #1a1f29;
                border: 1px solid rgba(255,255,255,.08);
                border-radius: 12px;
                margin: 4px 0px;
            }
            QFrame#DownloadItem:hover {
                background: #232937;
                border-color: rgba(255,255,255,.12);
            }
        """)
        self.item = item
        self.on_action = on_action
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)
        
        # Title row
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        
        # File info
        file_info = QVBoxLayout()
        file_info.setContentsMargins(0, 0, 0, 0)
        file_info.setSpacing(2)
        
        self.title_label = QLabel(f"<b>{item.get('name', 'Unknown file')}</b>")
        self.title_label.setStyleSheet("""
            QLabel {
                color: #e5e7eb;
                font-size: 14px;
                font-weight: 600;
                background: transparent;
            }
        """)
        
        # URL link
        url_text = item.get('url', '')
        if len(url_text) > 50:
            url_text = url_text[:47] + "..."
        self.url_label = QLabel(f"<a href='{item.get('url', '')}' style='color: #3b82f6; text-decoration: none;'>{url_text}</a>")
        self.url_label.setStyleSheet("""
            QLabel {
                color: #3b82f6;
                font-size: 12px;
                background: transparent;
            }
        """)
        self.url_label.setOpenExternalLinks(False)
        self.url_label.setToolTip(item.get('url', ''))
        
        # Size info
        size_mb = (item.get('total', 0) / 1024 / 1024)
        self.size_label = QLabel(f"{size_mb:.2f} MB")
        self.size_label.setStyleSheet("""
            QLabel {
                color: #9ca3af;
                font-size: 12px;
                background: transparent;
            }
        """)
        
        file_info.addWidget(self.title_label)
        file_info.addWidget(self.url_label)
        file_info.addWidget(self.size_label)
        
        title_row.addLayout(file_info, 1)
        
        # Actions
        actions = QVBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(4)
        
        # Get icons path
        from pathlib import Path
        icon_base = str((Path(__file__).parent.parent / 'resources' / 'icons').resolve())
        
        btn_show = QPushButton("")
        btn_show.setIcon(QIcon(f"{icon_base}/folder.svg"))
        btn_show.setIconSize(QSize(16, 16))
        btn_show.setToolTip("Abrir carpeta")
        btn_show.setStyleSheet("""
            QPushButton {
                background: rgba(59, 130, 246, 0.1);
                color: #3b82f6;
                border: 1px solid rgba(59, 130, 246, 0.2);
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 14px;
                min-width: 35px;
                min-height: 30px;
            }
            QPushButton:hover {
                background: rgba(59, 130, 246, 0.2);
                border-color: rgba(59, 130, 246, 0.3);
            }
        """)
        btn_show.clicked.connect(lambda: on_action('show', item['id']))
        
        btn_remove = QPushButton("")
        btn_remove.setIcon(QIcon(f"{icon_base}/remove.svg"))
        btn_remove.setIconSize(QSize(16, 16))
        btn_remove.setToolTip("Eliminar")
        btn_remove.setStyleSheet("""
            QPushButton {
                background: rgba(107, 114, 128, 0.1);
                color: #6b7280;
                border: 1px solid rgba(107, 114, 128, 0.2);
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 14px;
                min-width: 35px;
                min-height: 30px;
            }
            QPushButton:hover {
                background: rgba(107, 114, 128, 0.2);
                border-color: rgba(107, 114, 128, 0.3);
            }
        """)
        btn_remove.clicked.connect(lambda: on_action('remove', item['id']))
        
        actions_row = QHBoxLayout()
        actions_row.setContentsMargins(0, 0, 0, 0)
        actions_row.setSpacing(4)
        actions_row.addWidget(btn_show)
        actions_row.addWidget(btn_remove)
        
        actions.addLayout(actions_row)
        title_row.addLayout(actions)
        
        lay.addLayout(title_row)
        
        # Status row
        status = QHBoxLayout()
        status.setContentsMargins(0, 0, 0, 0)
        self.state_lbl = QLabel(item.get('state', ''))
        self.state_lbl.setStyleSheet("""
            QLabel {
                color: #9ca3af;
                font-size: 12px;
                background: transparent;
            }
        """)
        status.addWidget(self.state_lbl)
        status.addStretch(1)
        lay.addLayout(status)
        
        self.update_progress(item)

    def update_progress(self, item: dict):
        import os
        from pathlib import Path
        
        state = item.get('state', '')
        path = item.get('path', '')
        
        # For completed downloads, show actual file size
        if state == 'completed' and path and os.path.exists(path):
            try:
                actual_size = os.path.getsize(path)
                size_str = self._format_size(actual_size)
                self.state_lbl.setText(f"Completado • {size_str}")
            except Exception:
                self.state_lbl.setText(state)
        else:
            self.state_lbl.setText(state)
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

class DownloadsWidget(QWidget):
    def __init__(self, downloads_manager, parent=None) -> None:
        super().__init__(parent)
        self.mgr = downloads_manager
        self._setup_ui()
        self.items: dict[str, DownloadItemWidget] = {}
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(800)
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("Historial de Descargas")
        title.setStyleSheet("""
            QLabel {
                color: #e5e7eb;
                font-size: 24px;
                font-weight: 700;
                background: transparent;
                padding: 0px 0px 16px 0px;
            }
        """)
        layout.addWidget(title)
        
        # Scroll area for downloads
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
        """)
        
        self.body = QWidget()
        self.body_l = QVBoxLayout(self.body)
        self.body_l.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.body_l.setContentsMargins(0, 0, 0, 0)
        self.body_l.setSpacing(8)
        
        # Empty state message
        self.empty_label = QLabel("No hay descargas en el historial")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("""
            QLabel {
                color: #6b7280;
                font-size: 16px;
                background: transparent;
                padding: 40px 20px;
                border: 2px dashed rgba(107, 114, 128, 0.3);
                border-radius: 12px;
                margin: 20px 0px;
            }
        """)
        self.body_l.addWidget(self.empty_label)
        
        self.scroll.setWidget(self.body)
        layout.addWidget(self.scroll)

    def refresh(self):
        data = self.mgr.list()
        seen = set()
        
        # Show/hide empty state
        has_downloads = len(data) > 0
        self.empty_label.setVisible(not has_downloads)
        
        for d in data:
            seen.add(d['id'])
            if d['id'] not in self.items:
                w = DownloadItemWidget(d, self.action, self)
                self.items[d['id']] = w
                # Insert before empty label if it exists
                if self.empty_label.isVisible():
                    self.body_l.insertWidget(self.body_l.count() - 1, w)
                else:
                    self.body_l.addWidget(w)
            else:
                self.items[d['id']].update_progress(d)
                
        # Remove deleted items
        for k in list(self.items.keys()):
            if k not in seen:
                w = self.items.pop(k)
                self.body_l.removeWidget(w)
                w.deleteLater()

    def action(self, kind: str, did: str):
        if kind == 'show':
            self.mgr.action('show', did)
        elif kind == 'cancel':
            self.mgr.action('cancel', did)
        elif kind == 'remove':
            self.mgr.action('remove', did)
        self.refresh()
    
    def download_image(self, image_url: str):
        """Download image using the download manager"""
        if self.mgr:
            self.mgr.download_image(image_url)
