from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QFont
import time

class NotificationWidget(QFrame):
    """Individual notification widget"""
    def __init__(self, message: str, notification_type: str = "info", parent=None):
        super().__init__(parent)
        self.setObjectName("Notification")
        self.notification_type = notification_type
        self._opacity = 0.0
        
        self._setup_ui(message)
        self._setup_animation()
        
    def _setup_ui(self, message: str):
        from PyQt6.QtCore import Qt
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)
        
        # Make notification widgets non-interfering
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setWindowFlags(Qt.WindowType.NoDropShadowWindowHint)
        
        # Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(14, 14)
        
        # Message
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("""
            QLabel {
                color: #e5e7eb;
                font-size: 12px;
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.message_label, 1)
        
        # Set style based on type
        self._apply_type_style()
        
    def _apply_type_style(self):
        colors = {
            "success": ("#059669", "#047857"),
            "error": ("#dc2626", "#b91c1c"),
            "warning": ("#d97706", "#b45309"),
            "info": ("#2563eb", "#1d4ed8")
        }
        
        bg_color, border_color = colors.get(self.notification_type, colors["info"])
        
        self.setStyleSheet(f"""
            QFrame#Notification {{
                background: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
                margin: 0px;
            }}
        """)
        
        # Set icon (simple text for now)
        icons = {
            "success": "✓",
            "error": "✕", 
            "warning": "⚠",
            "info": "ℹ"
        }
        
        self.icon_label.setText(icons.get(self.notification_type, "ℹ"))
        self.icon_label.setStyleSheet(f"""
            QLabel {{
                color: #ffffff;
                font-size: 12px;
                font-weight: normal;
                background: transparent;
            }}
        """)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
    def _setup_animation(self):
        self.fade_animation = QPropertyAnimation(self, b"opacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
    def get_opacity(self):
        return self._opacity
        
    def set_opacity(self, value):
        self._opacity = value
        self.setStyleSheet(self.styleSheet() + f" opacity: {value};")
        
    opacity = pyqtProperty(float, get_opacity, set_opacity)
    
    def show_notification(self):
        """Show notification with fade in"""
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
        self.show()
        
    def hide_notification(self):
        """Hide notification with fade out"""
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self.deleteLater)
        self.fade_animation.start()

class NotificationManager(QWidget):
    """Manages all notifications in the application"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NotificationManager")
        self.notifications = []
        self._setup_ui()
        
    def _setup_ui(self):
        from PyQt6.QtCore import Qt
        
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        # Remove transparent background and floating window flags
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        # self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(6)
        
        self.setLayout(layout)
        
        # Position at bottom-left of parent and ensure visibility
        if self.parent():
            self.resize(300, 150)  # Smaller size
            parent_height = self.parent().height()
            parent_width = self.parent().width()
            self.move(20, parent_height - 170)  # Bottom-left with margin
            self.raise_()  # Bring to front
            
    def show_notification(self, message: str, notification_type: str = "info", duration: int = 3000):
        """Show a notification message"""
        notification = NotificationWidget(message, notification_type, self)
        self.layout().addWidget(notification)
        
        # Ensure we're positioned correctly
        if self.parent():
            parent_height = self.parent().height()
            self.move(20, parent_height - 170)
            self.raise_()
        
        notification.show_notification()
        self.notifications.append(notification)
        
        # Auto-hide after duration
        QTimer.singleShot(duration, lambda: self._hide_notification(notification))
        
        # Clean up layout
        QTimer.singleShot(duration + 500, self._cleanup_layout)
        
    def _hide_notification(self, notification):
        """Hide a specific notification"""
        if notification in self.notifications:
            notification.hide_notification()
            self.notifications.remove(notification)
            
    def _cleanup_layout(self):
        """Remove hidden notifications from layout"""
        for i in reversed(range(self.layout().count())):
            widget = self.layout().itemAt(i).widget()
            if widget and not widget.isVisible():
                self.layout().removeWidget(widget)
                
    def show_success(self, message: str, duration: int = 3000):
        """Show success notification"""
        self.show_notification(message, "success", duration)
        
    def show_error(self, message: str, duration: int = 3000):
        """Show error notification"""
        self.show_notification(message, "error", duration)
        
    def show_warning(self, message: str, duration: int = 3000):
        """Show warning notification"""
        self.show_notification(message, "warning", duration)
        
    def show_info(self, message: str, duration: int = 3000):
        """Show info notification"""
        self.show_notification(message, "info", duration)
