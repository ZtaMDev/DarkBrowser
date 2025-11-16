from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QFont, QMovie, QPainter, QPen, QColor
from PyQt6.QtCore import QRect
import sys
import os

class LoadingSpinner(QWidget):
    """Custom loading spinner widget"""
    def __init__(self, size=40, parent=None):
        super().__init__(parent)
        self.size = size
        self._angle = 0
        self.animation = QPropertyAnimation(self, b"angle")
        self.animation.setDuration(1000)
        self.animation.setStartValue(0)
        self.animation.setEndValue(360)
        self.animation.setLoopCount(-1)
        self.animation.setEasingCurve(QEasingCurve.Type.Linear)
        
    def start(self):
        self.animation.start()
        
    def stop(self):
        self.animation.stop()
        
    def get_angle(self):
        return self._angle
        
    def set_angle(self, angle):
        self._angle = angle
        self.update()
        
    angle = pyqtProperty(int, get_angle, set_angle)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Always use white color for dark theme
        color = QColor("#ffffff")
        
        # Thicker pen for better visibility
        pen = QPen(color, 5)  # Increased from 3 to 5
        painter.setPen(pen)
        
        center = self.rect().center()
        radius = self.size // 2
        
        # Draw spinning arc - longer arc for better visibility
        start_angle = self._angle
        span_angle = 300  # Increased from 270 to 300
        
        rect = QRect(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
        painter.drawArc(rect, int(start_angle * 16), int(span_angle * 16))

class LoadingOverlay(QWidget):
    """Loading overlay widget with spinner and text"""
    def __init__(self, parent=None, text="Cargando..."):
        super().__init__(parent)
        self.parent_widget = parent
        self.text = text
        self._setup_ui()
        
    def _setup_ui(self):
        # Make overlay cover parent completely
        if self.parent_widget:
            self.setGeometry(self.parent_widget.rect())
            
        # Dark, solid background to cover white space
        self.setStyleSheet("""
            QWidget {
                background: #1a1a1a;
                border: none;
                border-radius: 0px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Loading spinner - larger and more prominent
        self.spinner = LoadingSpinner(60)  # Increased size
        self.spinner.start()
        layout.addWidget(self.spinner, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Loading text - larger and more visible
        self.label = QLabel(self.text)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: 600;
                margin-top: 20px;
                background: transparent;
            }
        """)
        layout.addWidget(self.label, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Add some spacing
        layout.addSpacing(20)
        
        # Initially hidden
        self.hide()
        
    def show_loading(self, text=None):
        """Show loading overlay"""
        if text:
            self.label.setText(text)
        
        # Update position to cover parent completely
        if self.parent_widget:
            self.setGeometry(self.parent_widget.rect())
            # Ensure we're on top
            self.raise_()
            # Make sure we're visible
            self.show()
            # Force update
            self.update()
        else:
            self.show()
        
    def hide_loading(self):
        """Hide loading overlay"""
        self.hide()
        
    def resizeEvent(self, event):
        """Maintain overlay size when parent resizes"""
        super().resizeEvent(event)
        if self.parent_widget:
            self.setGeometry(self.parent_widget.rect())

class WebLoadingOverlay(LoadingOverlay):
    """Specialized loading overlay for web views"""
    def __init__(self, web_view, parent=None):
        self.web_view = web_view
        super().__init__(parent, "Cargando página...")
        self._connect_signals()
        
    def _connect_signals(self):
        """Connect to web view loading signals"""
        if self.web_view:
            self.web_view.loadStarted.connect(self._on_load_started)
            self.web_view.loadFinished.connect(self._on_load_finished)
            self.web_view.renderProcessTerminated.connect(self._on_render_terminated)
            
    def _on_load_started(self):
        """Show loading when page starts loading"""
        self.show_loading("Cargando página...")
        
    def _on_load_finished(self, success):
        """Hide loading when page finishes loading"""
        # Small delay to ensure content is visible
        QTimer.singleShot(500, self.hide_loading)
        
    def _on_render_terminated(self, status, exit_code):
        """Handle render process termination"""
        self.hide_loading()

class SidebarLoadingOverlay(LoadingOverlay):
    """Specialized loading overlay for sidebar"""
    def __init__(self, sidebar_widget, parent=None):
        self.sidebar_widget = sidebar_widget
        super().__init__(parent, "Cargando ChatGPT...")
        
    def show_chatgpt_loading(self):
        """Show loading for ChatGPT sidebar"""
        self.show_loading("Cargando ChatGPT...")
        
    def show_loading(self, text=None):
        """Override to handle sidebar-specific positioning"""
        if text:
            self.label.setText(text)
            
        # Update position to cover sidebar
        if self.parent_widget:
            self.setGeometry(self.parent_widget.rect())
            
        self.raise_()
        self.show()
