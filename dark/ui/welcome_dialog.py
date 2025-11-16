from __future__ import annotations
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QScrollArea, QWidget, QFrame, QGraphicsOpacityEffect)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QPoint
from PyQt6.QtGui import QPixmap, QFont, QIcon
from pathlib import Path


class WelcomeDialog(QDialog):
    """Beautiful welcome dialog with animations and feature showcase"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to Dark Browser")
        self.setFixedSize(800, 700)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Setup UI
        self._setup_ui()
        self._setup_animations()
        
        # Start animations after dialog is shown
        QTimer.singleShot(100, self._start_animations)
    
    def _setup_ui(self):
        """Setup the welcome dialog UI"""
        # Main container with rounded corners
        self.main_widget = QFrame()
        self.main_widget.setObjectName("WelcomeDialog")
        self.main_widget.setStyleSheet("""
            QFrame#WelcomeDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1d26, stop:1 #141821);
                border: 2px solid rgba(59, 130, 246, 0.3);
                border-radius: 20px;
                color: #e5e7eb;
            }
        """)
        
        # Layout for main widget
        layout = QVBoxLayout(self.main_widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Logo section
        logo_container = QHBoxLayout()
        logo_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.logo_label = QLabel()
        logo_path = Path(__file__).parent.parent / 'resources' / 'icons' / 'Dark_logo.png'
        if logo_path.exists():
            logo_pixmap = QPixmap(str(logo_path))
            if not logo_pixmap.isNull():
                scaled_logo = logo_pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, 
                                               Qt.TransformationMode.SmoothTransformation)
                self.logo_label.setPixmap(scaled_logo)
            else:
                # Fallback if pixmap is null
                self.logo_label.setText("🌙")
                self.logo_label.setStyleSheet("font-size: 60px; color: #3b82f6; background: transparent;")
        else:
            # Placeholder if image doesn't exist
            self.logo_label.setText("🌙")
            self.logo_label.setStyleSheet("font-size: 60px; color: #3b82f6; background: transparent;")
        
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setStyleSheet("background: transparent;")
        logo_container.addWidget(self.logo_label)
        
        layout.addLayout(logo_container)
        
        # Welcome title
        self.title_label = QLabel("Welcome to Dark Browser")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 28px;
                font-weight: bold;
                margin: 10px 0;
                background: transparent;
            }
        """)
        layout.addWidget(self.title_label)
        
        # Subtitle
        self.subtitle_label = QLabel("Your modern and elegant browser")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setStyleSheet("""
            QLabel {
                color: #9ca3af;
                font-size: 16px;
                margin-bottom: 20px;
                background: transparent;
            }
        """)
        layout.addWidget(self.subtitle_label)
        
        # Features section
        features_scroll = QScrollArea()
        features_scroll.setWidgetResizable(True)
        features_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        features_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        features_scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 4px;
            }
        """)
        
        features_widget = QWidget()
        features_layout = QVBoxLayout(features_widget)
        features_layout.setSpacing(20)
        
        # Feature 1: Vertical Tabs
        feature1 = self._create_feature_widget(
            "Vertical Tabs", 
            "Navigate with vertically organized tabs for better visibility and organization.",
            "vertical_tabs.png"
        )
        features_layout.addWidget(feature1)
        
        # Feature 2: ChatGPT Sidebar
        feature2 = self._create_feature_widget(
            "ChatGPT Sidebar", 
            "Access ChatGPT directly from the sidebar without interrupting your browsing.",
            "chatgpt_sidebar.png"
        )
        features_layout.addWidget(feature2)
        
        features_scroll.setWidget(features_widget)
        layout.addWidget(features_scroll)
        
        # Buttons section
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        # Start browsing button
        self.start_button = QPushButton("Start Browsing")
        self.start_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3b82f6, stop:1 #2563eb);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563eb, stop:1 #1d4ed8);
            }
            QPushButton:pressed {
                background: #1d4ed8;
            }
        """)
        self.start_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.start_button)
        
        layout.addLayout(buttons_layout)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.main_widget, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def _create_feature_widget(self, title: str, description: str, image_name: str) -> QFrame:
        """Create a feature widget with image and description"""
        feature = QFrame()
        feature.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        layout = QHBoxLayout(feature)
        layout.setSpacing(20)
        
        # Feature image
        image_label = QLabel()
        image_path = Path(__file__).parent.parent / 'resources' / 'icons' / image_name
        if image_path.exists():
            image_pixmap = QPixmap(str(image_path))
            if not image_pixmap.isNull():
                scaled_image = image_pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, 
                                                  Qt.TransformationMode.SmoothTransformation)
                image_label.setPixmap(scaled_image)
            else:
                # Fallback if pixmap is null
                image_label.setText("📱")
                image_label.setStyleSheet("font-size: 80px; color: #3b82f6; background: transparent;")
        else:
            # Placeholder if image doesn't exist
            image_label.setText("📱")
            image_label.setStyleSheet("font-size: 80px; color: #3b82f6; background: transparent;")
        
        image_label.setFixedSize(150, 150)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(image_label)
        
        # Feature text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
            }
        """)
        text_layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            QLabel {
                color: #9ca3af;
                font-size: 14px;
                line-height: 1.4;
                background: transparent;
            }
        """)
        desc_label.setWordWrap(True)
        text_layout.addWidget(desc_label)
        
        layout.addLayout(text_layout)
        
        return feature
    
    def _setup_animations(self):
        """Setup fade-in animations for elements"""
        self.opacity_effect = QGraphicsOpacityEffect(self.main_widget)
        self.main_widget.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)
        
        # Create individual animations for different elements
        self.animations = []
        
        # Logo animation
        logo_anim = QPropertyAnimation(self.logo_label, b"geometry")
        logo_anim.setDuration(800)
        logo_anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self.animations.append(logo_anim)
        
        # Title animation
        title_anim = QPropertyAnimation(self.title_label, b"geometry")
        title_anim.setDuration(600)
        title_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animations.append(title_anim)
        
        # Overall fade animation
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(1000)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
    
    def _start_animations(self):
        """Start all animations with delays"""
        # Start fade animation immediately
        self.fade_animation.start()
        
        # Start logo animation after 200ms
        QTimer.singleShot(200, self._animate_logo)
        
        # Start title animation after 400ms
        QTimer.singleShot(400, self._animate_title)
    
    def _animate_logo(self):
        """Animate logo with a subtle scale effect"""
        original_geometry = self.logo_label.geometry()
        scaled_geometry = original_geometry.adjusted(-10, -10, 10, 10)
        
        self.logo_animation = QPropertyAnimation(self.logo_label, b"geometry")
        self.logo_animation.setDuration(800)
        self.logo_animation.setEasingCurve(QEasingCurve.Type.OutBack)
        self.logo_animation.setStartValue(scaled_geometry)
        self.logo_animation.setEndValue(original_geometry)
        self.logo_animation.start()
    
    def _animate_title(self):
        """Animate title with slide-in effect"""
        self.title_animation = QPropertyAnimation(self.title_label, b"pos")
        self.title_animation.setDuration(600)
        self.title_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        original_pos = self.title_label.pos()
        self.title_animation.setStartValue(original_pos + QPoint(0, -20))
        self.title_animation.setEndValue(original_pos)
        self.title_animation.start()
    
    def showEvent(self, event):
        """Override show event to start animations"""
        super().showEvent(event)
        # Center the dialog on parent
        if self.parent():
            parent_rect = self.parent().geometry()
            dialog_rect = self.geometry()
            x = parent_rect.center().x() - dialog_rect.width() // 2
            y = parent_rect.center().y() - dialog_rect.height() // 2
            self.move(x, y)
