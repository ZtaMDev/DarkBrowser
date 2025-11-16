from __future__ import annotations
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
                            QLabel, QGridLayout, QFrame, QDialog, QVBoxLayout as QDialogLayout,
                            QHBoxLayout as QDialogHBoxLayout, QLineEdit as QDialogLineEdit, 
                            QPushButton as QDialogButton, QMessageBox, QMenu)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QIcon, QPixmap

class HomeWidget(QWidget):
    def __init__(self, settings, parent=None, tab_manager=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.tab_manager = tab_manager  # Reference to the TabManager
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Logo section - centered above search
        logo_container = QHBoxLayout()
        logo_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_container.setContentsMargins(0, 0, 0, 20)
        
        # Logo
        try:
            from pathlib import Path
            
            logo_path = Path(__file__).parent.parent / 'resources' / 'icons' / 'Dark_logo.png'
            if logo_path.exists():
                logo_label = QLabel()
                logo_pixmap = QPixmap(str(logo_path))
                # Scale logo to reasonable size (150x150)
                scaled_pixmap = logo_pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                logo_label.setPixmap(scaled_pixmap)
                logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                logo_label.setStyleSheet("margin: 0px; padding: 0px;")
                logo_container.addWidget(logo_label)
                print("Logo loaded successfully in home page")
            else:
                print(f"Logo file not found at {logo_path}")
        except Exception as e:
            print(f"Error loading logo in home page: {e}")
        
        lay.addLayout(logo_container)
        
        # Search section - no container, centered
        search_container = QHBoxLayout()
        search_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        search_container.setContentsMargins(0, 20, 0, 30)
        
        self.search = QLineEdit(); self.search.setPlaceholderText("Buscar en la web")
        self.search.setFixedHeight(50)  # Much larger height
        self.search.setFixedWidth(400)  # Fixed width instead of minimum
        self.search.setStyleSheet("""
            QLineEdit {
                background: #0e131b;
                color: #e5e7eb;
                border: 1px solid rgba(255,255,255,.08);
                border-radius: 25px;
                padding: 0 20px;
                font-size: 16px;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
            }
        """)
        
        search_container.addWidget(self.search)
        lay.addLayout(search_container)
        
        # Pins container - below search
        pins_card = QFrame(); pins_card.setObjectName("Card")
        pins_layout = QVBoxLayout(pins_card)
        pins_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pins_layout.setContentsMargins(20, 20, 20, 20)
        
        self.grid = QGridLayout(); self.grid.setHorizontalSpacing(14); self.grid.setVerticalSpacing(14)
        pins_layout.addLayout(self.grid)
        
        # Enable context menu on the pins card
        pins_card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        pins_card.customContextMenuRequested.connect(self._show_container_context_menu)
        
        lay.addWidget(pins_card, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.search.returnPressed.connect(self._go)
        self._render_pins()

    def _go(self):
        txt = self.search.text().strip()
        if not txt:
            return
        from urllib.parse import quote_plus
        engine = (self.settings.get("search") or "google").lower()
        urls = {
            "google": f"https://www.google.com/search?q={quote_plus(txt)}",
            "duckduckgo": f"https://duckduckgo.com/?q={quote_plus(txt)}",
            "bing": f"https://www.bing.com/search?q={quote_plus(txt)}",
            "brave": f"https://search.brave.com/search?q={quote_plus(txt)}",
        }
        target = urls.get(engine, urls["google"])
        # Use the TabManager directly if available, otherwise fallback to window
        if self.tab_manager:
            self.tab_manager.open_url(target)
        elif hasattr(self.window(), 'open_url'):
            self.window().open_url(target)

    def _render_pins(self):
        # Clear existing pins
        for i in reversed(range(self.grid.count())):
            child = self.grid.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Default pins if none exist
        pins = self.settings.get("pinned") or []
        if not pins:
            pins = [
                {"title": "GitHub", "url": "https://github.com"},
                {"title": "ChatGPT", "url": "https://chat.openai.com"},
                {"title": "Stack Overflow", "url": "https://stackoverflow.com"}
            ]
            self.settings.set("pinned", pins)
        
        # Render existing pins
        for i, pin in enumerate(pins):
            title = pin.get("title", "")
            # Truncate long titles
            if len(title) > 15:
                title = title[:12] + "..."
            
            btn = QPushButton(title)
            btn.setProperty("class","PinnedTile")
            url = pin.get("url", "")
            
            # Create context menu for editing
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda pos, idx=i: self._show_pin_context_menu(pos, idx))
            
            # Use TabManager if available, otherwise fallback to window
            if self.tab_manager:
                btn.clicked.connect(lambda _=False, u=url: self.tab_manager.open_url(u))
            elif hasattr(self.window(), 'open_url'):
                btn.clicked.connect(lambda _=False, u=url: self.window().open_url(u))
            
            self.grid.addWidget(btn, i // 3, i % 3)
        
        # Add + button if there's space
        if len(pins) < 9:
            add_btn = QPushButton("+")
            add_btn.setProperty("class","PinnedTile")
            add_btn.setStyleSheet("""
                QPushButton.PinnedTile {
                    background: rgba(255,255,255,.05);
                    color: #9ca3af;
                    border: 2px dashed rgba(255,255,255,.2);
                    font-size: 24px;
                    font-weight: bold;
                }
                QPushButton.PinnedTile:hover {
                    background: rgba(255,255,255,.1);
                    border-color: rgba(255,255,255,.3);
                    color: #e5e7eb;
                }
            """)
            add_btn.clicked.connect(self._add_pin)
            
            # Position the + button in the next available spot
            add_pos = len(pins)
            self.grid.addWidget(add_btn, add_pos // 3, add_pos % 3)

    def _show_pin_context_menu(self, pos, pin_index):
        """Show context menu for pin editing"""
        menu = QMenu(self)
        
        edit_action = menu.addAction("Editar")
        edit_action.triggered.connect(lambda: self._edit_pin(pin_index))
        
        delete_action = menu.addAction("Eliminar")
        delete_action.triggered.connect(lambda: self._delete_pin(pin_index))
        
        pins = self.settings.get("pinned") or []
        if len(pins) < 9:
            add_action = menu.addAction("Añadir nuevo")
            add_action.triggered.connect(lambda: self._add_pin())
        
        # Get the button widget that triggered the context menu
        button = self.sender()
        if button:
            global_pos = button.mapToGlobal(pos)
        else:
            global_pos = self.mapToGlobal(pos)
        
        menu.exec(global_pos)

    def _show_container_context_menu(self, pos):
        """Show context menu for pins container"""
        pins = self.settings.get("pinned") or []
        if len(pins) >= 9:
            return  # Don't show menu if pins are full
        
        menu = QMenu(self)
        add_action = menu.addAction("Añadir nuevo pin")
        add_action.triggered.connect(self._add_pin)
        
        global_pos = self.mapToGlobal(pos)
        menu.exec(global_pos)

    def _edit_pin(self, pin_index):
        """Edit an existing pin"""
        pins = self.settings.get("pinned") or []
        if pin_index >= len(pins):
            return
        
        pin = pins[pin_index]
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Pin")
        dialog.setFixedSize(300, 150)
        
        layout = QDialogLayout(dialog)
        
        title_edit = QDialogLineEdit(pin.get("title", ""))
        title_edit.setPlaceholderText("Título")
        url_edit = QDialogLineEdit(pin.get("url", ""))
        url_edit.setPlaceholderText("URL")
        
        layout.addWidget(QLabel("Título:"))
        layout.addWidget(title_edit)
        layout.addWidget(QLabel("URL:"))
        layout.addWidget(url_edit)
        
        buttons_layout = QDialogHBoxLayout()
        save_btn = QDialogButton("Guardar")
        cancel_btn = QDialogButton("Cancelar")
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)
        
        save_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            pins[pin_index] = {"title": title_edit.text(), "url": url_edit.text()}
            self.settings.set("pinned", pins)
            self._render_pins()

    def _delete_pin(self, pin_index):
        """Delete a pin"""
        reply = QMessageBox.question(self, 'Confirmar', '¿Eliminar este pin?',
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            pins = self.settings.get("pinned") or []
            if pin_index < len(pins):
                pins.pop(pin_index)
                self.settings.set("pinned", pins)
                self._render_pins()

    def _add_pin(self):
        """Add a new pin"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Añadir Pin")
        dialog.setFixedSize(300, 150)
        
        layout = QDialogLayout(dialog)
        
        title_edit = QDialogLineEdit()
        title_edit.setPlaceholderText("Título")
        url_edit = QDialogLineEdit()
        url_edit.setPlaceholderText("URL")
        
        layout.addWidget(QLabel("Título:"))
        layout.addWidget(title_edit)
        layout.addWidget(QLabel("URL:"))
        layout.addWidget(url_edit)
        
        buttons_layout = QDialogHBoxLayout()
        save_btn = QDialogButton("Añadir")
        cancel_btn = QDialogButton("Cancelar")
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)
        
        save_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            title = title_edit.text().strip()
            url = url_edit.text().strip()
            if title and url:
                pins = self.settings.get("pinned") or []
                if len(pins) < 9:
                    pins.append({"title": title, "url": url})
                    self.settings.set("pinned", pins)
                    self._render_pins()
