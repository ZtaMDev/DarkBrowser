from __future__ import annotations
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PyQt6.QtCore import QUrl

class WebPage(QWebEnginePage):
    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)

    def _setup_dark_mode(self):
        """Force dark mode for web pages"""
        # PyQt6 doesn't have PrefersColorScheme, use JavaScript injection instead
        # This will be injected when pages load
        
    def certificateError(self, error):
        """Handle certificate errors"""
        # Accept all certificates for development
        error.ignoreCertificateError()
        return True
    
    def acceptNavigationRequest(self, url, type, isMainFrame):
        # Add dark mode parameters to URLs that support it
        if isMainFrame and type == QWebEnginePage.NavigationType.NavigationTypeTyped:
            url_str = url.toString()
            
            # Add dark mode parameters for common sites
            if 'youtube.com' in url_str:
                url = QUrl(url_str + ('&' if '?' in url_str else '?') + 'theme=dark')
            elif 'twitter.com' in url_str or 'x.com' in url_str:
                url = QUrl(url_str + ('&' if '?' in url_str else '?') + 'theme=dark')
            elif 'reddit.com' in url_str:
                url = QUrl(url_str + ('&' if '?' in url_str else '?') + 'theme=dark')
            elif 'github.com' in url_str:
                # GitHub uses system preference, but we can try
                pass
        
        return super().acceptNavigationRequest(url, type, isMainFrame)
    
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):  # type: ignore[override]
        # Filter noisy site messages that don't affect functionality
        ignore_fragments = [
            'While parsing speculation rules: A rule must have a source',
            "Unrecognized feature: 'ch-ua-form-factors'",
            "Error with Permissions-Policy header: Origin trial controlled feature not enabled: 'interest-cohort'",
            "interest-cohort",
        ]
        for frag in ignore_fragments:
            if frag in message:
                return
        # Otherwise, default handling (print to stderr via base implementation)
        return super().javaScriptConsoleMessage(level, message, lineNumber, sourceID)
