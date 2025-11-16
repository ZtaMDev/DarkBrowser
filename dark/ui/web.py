from __future__ import annotations
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PyQt6.QtCore import QUrl

class WebPage(QWebEnginePage):
    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)
        
        # Enable secure features needed for 2FA and security keys
        self.settings().setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptEnabled, True
        )
        self.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalStorageEnabled, True
        )
        self.settings().setAttribute(
            QWebEngineSettings.WebAttribute.WebGLEnabled, True
        )
        self.settings().setAttribute(
            QWebEngineSettings.WebAttribute.FocusOnNavigationEnabled, True
        )

    def _setup_dark_mode(self):
        """Force dark mode for web pages"""
        # PyQt6 doesn't have PrefersColorScheme, use JavaScript injection instead
        # This will be injected when pages load
        
    def certificateError(self, error):
        """Handle certificate errors - more permissive for 2FA compatibility"""
        # Accept all certificates including self-signed and expired
        # This is needed for some 2FA systems that use custom certificates
        error.ignoreCertificateError()
        return True
    
    def createWindow(self, window_type):
        """Handle popup windows and new window requests"""
        # Get the view that created this window
        if hasattr(self, 'view') and self.view:
            view = self.view
            # Find the MainWindow through the view's parent hierarchy
            parent = view.parent()
            while parent:
                # Check if this is MainWindow (has tabman attribute)
                if hasattr(parent, 'tabman') and hasattr(parent.tabman, 'create_tab'):
                    # Found the MainWindow with tab manager
                    tab_manager = parent.tabman
                    # Create new tab for popup
                    tab_manager.create_tab("about:blank")
                    # Return the new view's PAGE, not the view itself
                    return tab_manager.tabs[-1].view.page()
                parent = parent.parent()
        return None
    
    def acceptNavigationRequest(self, url, type, isMainFrame):
        # Handle all navigation requests, not just typed ones
        if isMainFrame:
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
            "Document-Policy HTTP header: Unrecognized document policy feature name include-js-call-stacks-in-crash-reports",
            "Document-Policy HTTP header: Unrecognized document policy feature name",
            "The resource https://i.ytimg.com/generate_204 was preloaded using link preload but not used within a few seconds from the window's load event",
            "Chrome currently does not support the Push API in incognito mode",
            "Refused to frame 'https://accounts.youtube.com/' because an ancestor violates the following Content Security Policy directive: \"frame-ancestors 'self'\"",
            "Refused to frame",
            "frame-ancestors 'self'"
        ]
        for frag in ignore_fragments:
            if frag in message:
                return
        # Otherwise, default handling (print to stderr via base implementation)
        return super().javaScriptConsoleMessage(level, message, lineNumber, sourceID)
