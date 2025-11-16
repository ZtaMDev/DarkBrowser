import sys, traceback, os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication, Qt
from dark.app import DarkApp

def main():
    QCoreApplication.setApplicationName("Dark Browser")
    QCoreApplication.setOrganizationName("ZtaMDev")
    os.environ.setdefault("QT_LOGGING_RULES", "*.debug=false;qt.qpa.*=false;qt.core.plugin.*=false;qt.webengine.*=false")
    
    # Initialize QWebEngine BEFORE creating QApplication
    try:
        QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        print("QWebEngine initialized successfully")
        
        # Wait for QWebEngine to fully warm up
        import time
        print("Warming up QWebEngine...")
        time.sleep(0.5)  # 500ms warmup
    except Exception as e:
        print(f"Warning: QWebEngine initialization failed: {e}")
        traceback.print_exc()
        pass
    
    app = QApplication(sys.argv)
    
    # Set application icon
    try:
        from pathlib import Path
        icon_path = Path(__file__).parent / 'dark' / 'resources' / 'icons' / 'Dark_logo.png'
        if icon_path.exists():
            from PyQt6.QtGui import QIcon
            app.setWindowIcon(QIcon(str(icon_path)))
            print("Application icon set successfully")
    except Exception as e:
        print(f"Error setting application icon: {e}")
    
    # Load dark theme only
    try:
        from pathlib import Path
        qss_path = Path(__file__).parent / 'dark' / 'resources' / 'qss' / 'theme.qss'
        if qss_path.exists():
            app.setStyleSheet(qss_path.read_text(encoding='utf-8'))
            print("Dark theme loaded")
    except Exception as e:
        print(f"Error loading theme: {e}")
    
    # Keep a global reference
    global _dark_app
    _dark_app = DarkApp()
    
    def _excepthook(t, v, tb):
        print("\n===== Uncaught exception =====", file=sys.stderr)
        traceback.print_exception(t, v, tb)
    sys.excepthook = _excepthook
    
    _dark_app.run()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
