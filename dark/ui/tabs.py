from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
from PyQt6.QtCore import Qt, QUrl, QPoint
from PyQt6.QtWidgets import QWidget, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout, QStackedLayout, QLabel, QMenu, QApplication
from PyQt6.QtGui import QClipboard
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEnginePage as Page
from .web import WebPage
from .home_widget import HomeWidget
from .tab_item import TabItemWidget

SEARCH_ENGINES = {
    "google": "https://www.google.com/search?q={q}",
    "duckduckgo": "https://duckduckgo.com/?q={q}",
    "bing": "https://www.bing.com/search?q={q}",
    "brave": "https://search.brave.com/search?q={q}",
}

@dataclass
class Tab:
    view: QWebEngineView | None
    widget: QWidget | None
    title: str = "New Tab"
    url: str = ""
    pinned: bool = False

class TabManager:
    def __init__(self, profile: QWebEngineProfile, tabs_list: QListWidget, url_edit, content_container: QWidget, content_stack: QStackedLayout, settings=None, downloads=None, main_window=None) -> None:
        self.profile = profile
        self.tabs_list = tabs_list
        self.url_edit = url_edit
        self.container = content_container
        self.stack = content_stack
        self.settings = settings
        self.downloads = downloads
        self.main_window = main_window
        self.tabs: List[Tab] = []
        self.active_index: int = -1
        self._restoring_session = False  # Flag to prevent redundant set_active calls

        # Pre-warm QWebEngine with a lightweight page to prevent first-search restart
        self._prewarm_qwebengine()

        # Restore session or open single Home tab
        restored = False
        if self.settings:
            try:
                sess = self.settings.get('session') or []
                active = int(self.settings.get('session_active') or 0)
                #print(f"DEBUG: Restoring session with {len(sess)} tabs, active index: {active}")
                if sess:
                    # Set flag to prevent redundant set_active calls during restore
                    self._restoring_session = True
                    
                    # Create tabs without immediately setting active
                    for i, t in enumerate(sess):
                        ttype = t.get('type')
                        #print(f"DEBUG: Tab {i}: type={ttype}, url={t.get('url')}, title={t.get('title')}")
                        if ttype == 'web':
                            self.create_tab(t.get('url') or 'https://www.google.com')
                            # Set the saved title after creation
                            saved_title = t.get('title')
                            if saved_title and self.tabs:
                                self.tabs[-1].title = saved_title
                        elif ttype == 'home':
                            title = t.get('title') or 'Home'
                            self.create_tab_native(HomeWidget(self.settings, tab_manager=self), title)
                        elif ttype == 'settings':
                            from .settings_widget import SettingsWidget
                            title = t.get('title') or 'Settings'
                            self.create_tab_native(SettingsWidget(self.settings, self.container.window()), title)
                        elif ttype == 'downloads':
                            from .downloads_widget import DownloadsWidget
                            title = t.get('title') or 'Descargas'
                            self.create_tab_native(DownloadsWidget(self.downloads), title)
                    
                    # Clear flag and set the final active tab
                    self._restoring_session = False
                    last_active = int(self.settings.get('session_active') or 0)
                    #print(f"DEBUG: Setting final active tab to index {last_active}, total tabs: {len(self.tabs)}")
                    if 0 <= last_active < len(self.tabs):
                        self.set_active(last_active)
                    else:
                        self.set_active(len(self.tabs) - 1)
                    
                    # Reload all web tabs to ensure they're fully loaded after session restore
                    # Use QTimer to ensure tabs are fully loaded before reloading
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(500, self._reload_all_tabs_for_restore)
                    
                    restored = True
            except Exception:
                restored = False
        if not restored:
            self.create_tab_native(HomeWidget(self.settings, tab_manager=self), 'Home')
            self.set_active(0)

    def _reload_all_tabs_for_restore(self):
        """Reload all web tabs after session restore to ensure full loading"""
        #print(f"DEBUG: Reloading {len(self.tabs)} tabs after session restore")
        for i, tab in enumerate(self.tabs):
            if tab.view and tab.view.url().toString():
                #print(f"DEBUG: Reloading tab {i}: {tab.view.url().toString()}")
                tab.view.reload()
    
    def _reload_all_tabs_for_theme(self):
        """Reload all web tabs to apply dark theme"""
        for tab in self.tabs:
            if tab.view and tab.view.url().toString():
                tab.view.reload()

    def parse_url_or_search(self, text: str, engine: str) -> str:
        text = (text or "").strip()
        try:
            u = QUrl(text)
            if u.scheme() and u.host():
                return u.toString()
        except Exception:
            pass
        if "." in text and " " not in text and not text.startswith("dark://"):
            return "https://" + text
        from urllib.parse import quote_plus
        return SEARCH_ENGINES.get(engine, SEARCH_ENGINES["google"]).format(q=quote_plus(text))

    def _attach_view(self, view: QWebEngineView):
        # Ensure the new view is parented and sized
        view.setParent(self.container)
        self.stack.addWidget(view)
        
        # Connect signals safely
        try:
            view.titleChanged.connect(lambda title: self._sync_title(title, view))
            view.iconChanged.connect(lambda *_: self._refresh_tabs_ui())
            view.urlChanged.connect(lambda url: self._on_url_changed(url, view))
            # Removed selectionChanged to prevent floating button
            view.loadFinished.connect(lambda *_: self._update_all_tabs_favorite_status())
            
            # Setup custom context menu for web view
            view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            view.customContextMenuRequested.connect(lambda pos: self._web_context_menu(pos, view))
        except Exception:
            pass
        
        # Enable prudent features
        s = view.settings()
        try:
            s.setAttribute(s.WebAttribute.JavascriptEnabled, True)
            s.setAttribute(s.WebAttribute.JavascriptCanOpenWindows, True)
            s.setAttribute(s.WebAttribute.LocalStorageEnabled, True)
            s.setAttribute(s.WebAttribute.LocalContentCanAccessFileUrls, True)
            s.setAttribute(s.WebAttribute.LocalContentCanAccessRemoteUrls, True)
            s.setAttribute(s.WebAttribute.PluginsEnabled, True)
            s.setAttribute(s.WebAttribute.FullScreenSupportEnabled, True)
            s.setAttribute(s.WebAttribute.Accelerated2dCanvasEnabled, True)
            s.setAttribute(s.WebAttribute.WebGLEnabled, True)
            s.setAttribute(s.WebAttribute.JavascriptCanAccessClipboard, True)
            s.setAttribute(s.WebAttribute.AllowGeolocationOnInsecureOrigins, True)
            s.setAttribute(s.WebAttribute.AllowWindowActivationFromJavaScript, True)
        except Exception:
            pass

        # Auto-grant runtime permissions prudently
        def on_perm(origin, feature):
            try:
                view.page().setFeaturePermission(origin, feature, Page.PermissionPolicy.PermissionGrantedByUser)
            except Exception:
                pass
        try:
            view.page().featurePermissionRequested.connect(on_perm)
        except Exception:
            pass

    def resize(self):
        pass

    def create_tab(self, url: Optional[str] = None):
        if url:
            # Create web tab with URL
            view = QWebEngineView(self.container)
            page = WebPage(self.profile, view)
            view.setPage(page)
            # Set view reference in page for createWindow to access
            page.view = view
            self._attach_view(view)
            t = Tab(view=view, widget=None, title="Loading...")
            self.tabs.append(t)
            self._rebuild_list()
            self.set_active(len(self.tabs)-1)
            view.load(QUrl(url))
            # Update URL bar immediately
            self.url_edit.setText(url)
            # Update favorite status for the new tab
            self._update_tab_favorite_status(len(self.tabs)-1)
        else:
            # Create Home tab
            from .home_widget import HomeWidget
            home_widget = HomeWidget(self.settings, tab_manager=self)
            home_widget.setParent(self.container)
            self.stack.addWidget(home_widget)
            t = Tab(view=None, widget=home_widget, title="Home")
            self.tabs.append(t)
            self._rebuild_list()
            self.set_active(len(self.tabs)-1)

    def create_tab_native(self, widget: QWidget, title: str = ""):
        widget.setParent(self.container)
        self.stack.addWidget(widget)
        t = Tab(view=None, widget=widget, title=title or "New Tab")
        self.tabs.append(t)
        self._rebuild_list()
        self.set_active(len(self.tabs)-1)

    def set_active(self, index: int):
        #print(f"DEBUG: set_active called with index {index}, current active_index: {self.active_index}, restoring: {self._restoring_session}")
        if index < 0 or index >= len(self.tabs):
            #print(f"DEBUG: Invalid index {index}, returning")
            return
        
        # Skip if we're restoring session and this isn't the final call
        if self._restoring_session and index != self.active_index:
            print(f"DEBUG: Skipping set_active during session restore")
            return
        
        # Update active index
        self.active_index = index
        #print(f"DEBUG: Updated active_index to {self.active_index}")
        
        # Save session immediately when tab changes (but not during restore)
        if not self._restoring_session:
            self._save_session_immediately()
        
        # Remove active class from all tabs
        for i in range(self.tabs_list.count()):
            item = self.tabs_list.item(i)
            widget = self.tabs_list.itemWidget(item)
            if widget and widget.objectName() == "TabItem":
                widget.setProperty("class", "")
                widget.style().unpolish(widget)
                widget.style().polish(widget)
        
        # Add active class to selected tab
        item = self.tabs_list.item(index)
        widget = self.tabs_list.itemWidget(item)
        if widget and widget.objectName() == "TabItem":
            widget.setProperty("class", "active")
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        
        # Select the item in the list
        self.tabs_list.setCurrentItem(item)
        
        # Show the selected tab content
        self._show_only(index)
        
        # Update URL bar to match the active tab
        if 0 <= index < len(self.tabs):
            tab = self.tabs[index]
            if tab.view and not tab.widget:
                # Web tab - update URL bar with current URL
                try:
                    url = tab.view.url().toString()
                    if url:
                        self.url_edit.setText(url)
                except Exception:
                    pass
            elif tab.widget:
                # Native tab - set appropriate URL
                if hasattr(tab.widget, '__class__'):
                    class_name = tab.widget.__class__.__name__
                    if 'HomeWidget' in class_name:
                        self.url_edit.setText("dark://home")
                    elif 'SettingsWidget' in class_name:
                        self.url_edit.setText("dark://settings")
                    elif 'DownloadsWidget' in class_name:
                        self.url_edit.setText("dark://downloads")
        
        # Setup context menu only once
        if not hasattr(self, '_ctx_init'):
            self._refresh_tabs_ui()
        
        # Update favorites bar visibility if main_window supports it
        if self.main_window and hasattr(self.main_window, '_update_favorites_bar_visibility'):
            self.main_window._update_favorites_bar_visibility()

    def _show_only(self, index: int):
        if 0 <= index < len(self.tabs):
            tab = self.tabs[index]
            target = tab.view if tab.view is not None else tab.widget
            if target is not None:
                if tab.view:
                    #print(f"DEBUG: Switching to web view at index {index}")
                    self.stack.setCurrentWidget(tab.view)
                elif tab.widget:
                    #print(f"DEBUG: Switching to native widget at index {index}")
                    self.stack.setCurrentWidget(tab.widget)
                else:
                    print(f"DEBUG: No widget found for tab at index {index}")
                #print(f"DEBUG: set_active completed, current stack widget: {self.stack.currentWidget()}")
                target.show()  # Ensure widget is visible
                target.setFocus()
                # Update URL bar
                if tab.view:
                    # Web view - show actual URL
                    try:
                        url = tab.view.url().toString()
                        if url:
                            self.url_edit.setText(url)
                    except Exception:
                        pass
                elif tab.widget:
                    # Native widget - show corresponding dark:// URL
                    if hasattr(tab.widget, '__class__'):
                        class_name = tab.widget.__class__.__name__
                        if 'HomeWidget' in class_name:
                            self.url_edit.setText("dark://home")
                        elif 'SettingsWidget' in class_name:
                            self.url_edit.setText("dark://settings")
                        elif 'DownloadsWidget' in class_name:
                            self.url_edit.setText("dark://downloads")
                        else:
                            self.url_edit.setText("")

    def close_tab(self, index: int):
        if index < 0 or index >= len(self.tabs):
            return
        t = self.tabs.pop(index)
        if t.view:
            self.stack.removeWidget(t.view)
            t.view.deleteLater()
        if t.widget:
            self.stack.removeWidget(t.widget)
            t.widget.deleteLater()
        self._rebuild_list()
        if self.tabs:
            self.set_active(min(index, len(self.tabs)-1))
        else:
            # No tabs left: close the app window
            try:
                self.container.window().close()
            except Exception:
                pass

    def duplicate_tab(self, index: int):
        if index < 0 or index >= len(self.tabs):
            return
        if self.tabs[index].view:
            url = self.tabs[index].view.url().toString()
            self.create_tab(url)
            # URL bar is already updated in create_tab
        else:
            # Duplicate native tabs as a new home tab
            self.create_tab_native(HomeWidget(self.settings, tab_manager=self), "Home")

    def toggle_pin(self, index: int):
        if index < 0 or index >= len(self.tabs):
            return
        
        tab = self.tabs[index]
        if tab.view:
            # Get current page info
            url = tab.view.url().toString()
            title = tab.view.title() or "Untitled"
            
            # Get current pins
            pins = self.settings.get("pinned") or []
            
            # Check if already pinned
            for pin in pins:
                if pin.get("url") == url:
                    # Unpin - remove from pins
                    pins.remove(pin)
                    self.settings.set("pinned", pins)
                    self._refresh_tabs_ui()
                    # Refresh home widget if exists
                    self._refresh_home_widget()
                    return
            
            # Add to pins (max 9)
            if len(pins) < 9:
                pins.append({"title": title, "url": url})
                self.settings.set("pinned", pins)
                tab.pinned = True
            else:
                # Show message that pins are full
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self.container, "Pin Limit", "Maximum 9 pins allowed")
            
            self._refresh_tabs_ui()
            self._refresh_home_widget()
    
    def _refresh_home_widget(self):
        """Refresh the home widget to show updated pins"""
        for tab in self.tabs:
            if tab.widget and hasattr(tab.widget, '__class__') and 'HomeWidget' in tab.widget.__class__.__name__:
                tab.widget._render_pins()
                break

    def navigate(self, kind: str):
        v = self.current_view()
        if not v:
            return
        if kind == "back" and v.history().canGoBack():
            v.back()
        elif kind == "forward" and v.history().canGoForward():
            v.forward()
        elif kind == "reload":
            # Show loading overlay for reload
            if hasattr(v, 'loading_overlay'):
                v.loading_overlay.show_loading("Reloading page...")
            v.reload()

    def open_url(self, url: str):
        # Prevent recursion during conversion
        if hasattr(self, '_converting') and self._converting:
            return
        
        # internal routing
        if url.startswith("dark://"):
            host = url.replace("dark://", "").split("?")[0]
            if host == "home":
                # Check if Home tab already exists
                for i, tab in enumerate(self.tabs):
                    if tab.widget and hasattr(tab.widget, '__class__') and 'HomeWidget' in tab.widget.__class__.__name__:
                        self.set_active(i)
                        return
                self.create_tab_native(HomeWidget(self.settings, tab_manager=self), "Home")
                # Update URL bar for home page
                self.url_edit.setText("dark://home")
                return
            if host == "settings":
                # Check if Settings tab already exists
                for i, tab in enumerate(self.tabs):
                    if tab.widget and hasattr(tab.widget, '__class__') and 'SettingsWidget' in tab.widget.__class__.__name__:
                        self.set_active(i)
                        return
                from .settings_widget import SettingsWidget
                self.create_tab_native(SettingsWidget(self.settings, self.container.window()), "Settings")
                # Update URL bar for settings page
                self.url_edit.setText("dark://settings")
                return
            if host == "downloads":
                # Check if Downloads tab already exists
                for i, tab in enumerate(self.tabs):
                    if tab.widget and hasattr(tab.widget, '__class__') and 'DownloadsWidget' in tab.widget.__class__.__name__:
                        self.set_active(i)
                        return
                from .downloads_widget import DownloadsWidget
                self.create_tab_native(DownloadsWidget(self.downloads), "Descargas")
                # Update URL bar for downloads page
                self.url_edit.setText("dark://downloads")
                return
            return
        
        # Smart tab management: decide whether to use current tab or create new one
        current_tab = self.tabs[self.active_index] if 0 <= self.active_index < len(self.tabs) else None
        
        if current_tab and current_tab.widget and not current_tab.view:
            # Current tab is native - check if we should convert it or create new
            class_name = current_tab.widget.__class__.__name__
            
            # Convert Home tab to web tab if it's the first navigation (common pattern)
            if 'HomeWidget' in class_name:
                self._convert_current_to_web(url)
                return
            
            # For Settings and Downloads, always create new tab to preserve functionality
            if 'SettingsWidget' in class_name or 'DownloadsWidget' in class_name:
                self.create_tab(url)
                self.set_active(len(self.tabs) - 1)
                # Update URL bar immediately since create_tab won't do it for existing tabs
                self.url_edit.setText(url)
                return
        
        # Current tab is web or doesn't exist
        v = self.current_view()
        if v:
            # Use existing web tab
            v.load(QUrl(url))
            # Update URL bar immediately
            self.url_edit.setText(url)
        else:
            # Fallback: create new tab
            self.create_tab(url)
            self.set_active(len(self.tabs) - 1)
            # URL bar is already updated in create_tab

    def _convert_current_to_web(self, url: str):
        if not (0 <= self.active_index < len(self.tabs)):
            self.create_tab(url)
            # URL bar is already updated in create_tab
            return
        
        tab = self.tabs[self.active_index]
        
        # Block signals during conversion to prevent recursion
        self.tabs_list.blockSignals(True)
        
        try:
            # Remove native widget from stack if present
            if tab.widget:
                try:
                    self.stack.removeWidget(tab.widget)
                    tab.widget.hide()
                    # Set parent to None to ensure proper cleanup
                    tab.widget.setParent(None)
                except Exception:
                    pass
            
            # Create web view
            view = QWebEngineView(self.container)
            page = WebPage(self.profile, view)
            view.setPage(page)
            # Set view reference in page for createWindow to access
            page.view = view
            
            # Update tab to be web tab
            tab.view = view
            tab.widget = None
            tab.title = "Loading..."
            
            # Attach view and load URL
            self._attach_view(view)
            
            # Load URL immediately after attachment
            view.load(QUrl(url))
            # Update URL bar immediately
            self.url_edit.setText(url)
            
            # Update UI
            self._rebuild_list()
            # Show the new view immediately
            self._show_only(self.active_index)
            
        finally:
            # Unblock signals
            self.tabs_list.blockSignals(False)

    def current_view(self) -> Optional[QWebEngineView]:
        if 0 <= self.active_index < len(self.tabs):
            return self.tabs[self.active_index].view
        return None

    def _web_context_menu(self, pos, view):
        """Custom context menu for web views"""
        if not view:
            return
            
        menu = QMenu(view)
        
        # Get selected text
        selected_text = view.selectedText()
        
        # Get link and image under cursor if any
        link_url = ""
        image_url = ""
        try:
            page_point = view.mapToScene(pos)
            hit_result = view.page().hitTestContent(page_point)
            link_url = hit_result.linkUrl().toString()
            image_url = hit_result.imageUrl().toString()
        except Exception:
            pass
        
        # Navigation options for links
        if link_url:
            open_link = menu.addAction("Open Link")
            open_link.triggered.connect(lambda: self.open_url(link_url))
            
            open_new_tab = menu.addAction("Open in New Tab")
            open_new_tab.triggered.connect(lambda: self.create_tab(link_url))
            
            open_new_window = menu.addAction("Open in New Window")
            open_new_window.triggered.connect(lambda: self._open_link_in_new_window(link_url))
            
            # Download link
            download_link = menu.addAction("Download Link")
            download_link.triggered.connect(lambda: self._download_link(link_url))
            
            copy_link_address = menu.addAction("Copy Link Address")
            copy_link_address.triggered.connect(lambda: self._copy_text(link_url))
            
            menu.addSeparator()
        
        # Image operations using native WebEngine actions
        if hasattr(view.page(), 'action'):
            # Add native copy image action
            copy_image_action = view.page().action(QWebEnginePage.WebAction.CopyImageToClipboard)
            if copy_image_action.isEnabled():
                menu.addAction(copy_image_action)
            
            # Add copy image address
            copy_image_addr_action = view.page().action(QWebEnginePage.WebAction.CopyImageUrlToClipboard)
            if copy_image_addr_action.isEnabled():
                menu.addAction(copy_image_addr_action)
            
            # Add save image using download action
            save_image_action = view.page().action(QWebEnginePage.WebAction.DownloadImageToDisk)
            if save_image_action.isEnabled():
                menu.addAction(save_image_action)
            
            menu.addSeparator()
        
        # Fallback to custom implementations if native actions don't work
        if image_url:
            if not (hasattr(view.page(), 'action') and 
                   view.page().action(QWebEnginePage.WebAction.CopyImageUrlToClipboard).isEnabled()):
                copy_image_url = menu.addAction("Copy Image Address")
                copy_image_url.triggered.connect(lambda: self._copy_text(image_url))
            
            open_image_tab = menu.addAction("Open Image in New Tab")
            open_image_tab.triggered.connect(lambda: self.create_tab(image_url))
            
            menu.addSeparator()
        
        # If both link and image exist (image is a link)
        if link_url and image_url:
            copy_link = menu.addAction("Copy Link Address")
            copy_link.triggered.connect(lambda: self._copy_text(link_url))
            menu.addSeparator()
        
        # Text operations
        if selected_text:
            send_to_chatgpt = menu.addAction("Send to ChatGPT")
            send_to_chatgpt.triggered.connect(lambda: self._send_text_to_chatgpt(selected_text))
            
            copy_text = menu.addAction("Copy")
            copy_text.triggered.connect(lambda: self._copy_text(selected_text))
            
            menu.addSeparator()
        
        # Standard operations using WebEngine actions
        select_all = menu.addAction("Select All")
        select_all.triggered.connect(lambda: view.triggerPageAction(QWebEnginePage.WebAction.SelectAll))
        
        # Add copy/paste using WebEngine actions when available
        if hasattr(view.page(), 'action'):
            copy_action = view.page().action(QWebEnginePage.WebAction.Copy)
            if copy_action.isEnabled():
                menu.addAction(copy_action)
            
            paste_action = view.page().action(QWebEnginePage.WebAction.Paste)
            if paste_action.isEnabled():
                menu.addAction(paste_action)
            
            cut_action = view.page().action(QWebEnginePage.WebAction.Cut)
            if cut_action.isEnabled():
                menu.addAction(cut_action)
        else:
            # Fallback to manual implementation
            if selected_text:
                cut_text = menu.addAction("Cut")
                cut_text.triggered.connect(lambda: view.triggerPageAction(QWebEnginePage.WebAction.Cut))
                
            paste_text = menu.addAction("Paste")
            paste_text.triggered.connect(lambda: view.triggerPageAction(QWebEnginePage.WebAction.Paste))
        
        menu.addSeparator()
        
        # Page navigation actions
        back = menu.addAction("Back")
        back.setEnabled(view.history().canGoBack())
        back.triggered.connect(lambda: view.triggerPageAction(QWebEnginePage.WebAction.Back))
        
        forward = menu.addAction("Forward")
        forward.setEnabled(view.history().canGoForward())
        forward.triggered.connect(lambda: view.triggerPageAction(QWebEnginePage.WebAction.Forward))
        
        reload = menu.addAction("Reload")
        reload.triggered.connect(lambda: view.triggerPageAction(QWebEnginePage.WebAction.Reload))
        
        # Add WebEngine view source action
        # Note: View Source and Inspect Element removed from context menu
        
        menu.addSeparator()
        
        # Show menu at cursor position
        menu.exec(view.mapToGlobal(pos))
    
    def _send_text_to_chatgpt(self, text: str):
        """Send selected text to ChatGPT with full JavaScript integration"""
        # Signal to main window through a simple method call
        w = self.container.window()
        if hasattr(w, 'toggle_sidebar'):
            w.toggle_sidebar(text)
    
    def _copy_text(self, text: str):
        """Copy text to clipboard"""
        cb = QApplication.clipboard()
        cb.setText(text, mode=QClipboard.Mode.Clipboard)
    
    def _open_link_in_new_window(self, link_url: str):
        """Open link in new window"""
        # Reuse the new window creation logic from context menu
        from .main_window import MainWindow
        from PyQt6.QtWebEngineCore import QWebEngineProfile
        from ..core.downloads import DownloadsManager
        from ..core.scheme import register_dark_scheme, DarkUrlSchemeHandler
        from pathlib import Path
        
        # Use the SAME profile for shared cookies and sessions
        new_profile = self.profile
        
        # Create new downloads manager
        new_downloads = DownloadsManager(new_profile)
        
        # Create scheme handler
        pages_dir = Path(__file__).parent.parent / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)
        new_scheme_handler = DarkUrlSchemeHandler(
            pages_dir,
            downloads_provider=new_downloads.list,
            settings_provider=self.settings.all if self.settings else {},
            settings_actions=lambda action, value: None,
            downloads_actions=new_downloads.action,
        )
        new_profile.setUrlSchemeHandler("dark", new_scheme_handler)
        
        # Create new window with shared profile
        new_window = MainWindow(new_profile, self.settings, new_downloads)
        new_window.tabman.create_tab(link_url)
        new_window.show()
        
        # Clear all default tabs and create only the specific tab
        new_window.tabman.tabs.clear()
        new_window.tabman.tabs_list.clear()
        
        # Clear the content stack properly
        while new_window.tabman.stack.count() > 0:
            widget = new_window.tabman.stack.widget(0)
            new_window.tabman.stack.removeWidget(widget)
            widget.deleteLater()
        
        # Create the specific tab for the new window
        new_window.tabman.create_tab(link_url)
        
        # Ensure the window is fully initialized before showing
        new_window.show()
        # Force a reload after a short delay to ensure page loads
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, lambda: new_window.tabman.current_view().reload() if new_window.tabman.current_view() else None)
    
    def _download_link(self, link_url: str):
        """Download link using download system"""
        # Use direct download to avoid creating temporary QWebEngineView instances
        self._download_link_direct(link_url)
    
    def _download_link_direct(self, link_url: str):
        """Direct download fallback for links"""
        import requests
        from urllib.parse import urlparse
        import os
        
        try:
            parsed = urlparse(link_url)
            filename = os.path.basename(parsed.path) or "download"
            
            # Download to Downloads folder
            save_dir = Path.home() / "Downloads"
            save_dir.mkdir(parents=True, exist_ok=True)
            filepath = save_dir / filename
            
            response = requests.get(link_url, timeout=10)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                print(f"Downloaded to: {filepath}")
        except Exception as e:
            print(f"Error downloading link: {e}")

    def _sync_title(self, title: str, view=None):
        """Sync title from web view to tab"""
        try:
            # Use provided view or try to get sender
            sender_view = view
            if not sender_view:
                try:
                    sender_view = self.sender()
                except AttributeError:
                    return
            
            if not sender_view:
                return
            
            # Find which tab this view belongs to and update its title
            for i, tab in enumerate(self.tabs):
                if tab.view and tab.view == sender_view:
                    # Update stored title
                    tab.title = title or "New Tab"
                    # Update the tab item widget
                    self._update_tab_title(i, tab.title)
                    break
        except Exception as e:
            print(f"Error syncing title: {e}")
            pass

    def _update_all_tabs_favorite_status(self):
        """Update favorite status for all tabs"""
        for i in range(len(self.tabs)):
            self._update_tab_favorite_status(i)

    def _update_tab_favorite_status(self, index: int):
        """Update favorite status for a specific tab"""
        if index < 0 or index >= self.tabs_list.count() - 1:  # -1 for the + New Tab item
            return
        
        item = self.tabs_list.item(index)
        widget = self.tabs_list.itemWidget(item)
        if widget and hasattr(widget, 'set_favorite_status') and self.main_window:
            tab = self.tabs[index] if index < len(self.tabs) else None
            if tab and tab.view:
                url = tab.view.url().toString()
                # Check if this URL is in favorites
                is_fav = any(url == fav_url for fav_url, _ in self.main_window.favorites)
                widget.set_favorite_status(is_fav)
                # Also update the URL
                if hasattr(widget, 'set_url'):
                    widget.set_url(url)

    def _update_tab_title(self, index: int, title: str):
        """Update only a specific tab's title without rebuilding the entire list"""
        if index < 0 or index >= self.tabs_list.count() - 1:  # -1 for the + New Tab item
            return
        
        item = self.tabs_list.item(index)
        widget = self.tabs_list.itemWidget(item)
        if widget and hasattr(widget, 'set_title'):
            widget.set_title(title)
            
            # Update URL and favorite status for web tabs
            if index < len(self.tabs):
                tab = self.tabs[index]
                if tab.view and hasattr(widget, 'set_url'):
                    widget.set_url(tab.view.url().toString())
                    if hasattr(widget, 'set_favorite_status') and self.main_window:
                        url = tab.view.url().toString()
                        is_fav = any(url == fav_url for fav_url, _ in self.main_window.favorites)
                        widget.set_favorite_status(is_fav)

    def _refresh_tabs_ui(self):
        # Setup context menu for tabs list (once)
        if not hasattr(self, '_ctx_init'):
            self.tabs_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.tabs_list.customContextMenuRequested.connect(self._open_ctx_menu)
            self._ctx_init = True

    def _open_ctx_menu(self, pos):
        idx = self.tabs_list.currentRow()
        if idx < 0 or idx == self.tabs_list.count()-1:
            return
        m = QMenu(self.tabs_list)
        a_close = m.addAction("Close Tab")
        a_dup = m.addAction("Duplicate Tab")
        a_pin = m.addAction("Pin/Unpin")
        a_newwin = m.addAction("Open in New Window")
        act = m.exec(self.tabs_list.mapToGlobal(pos))
        if act == a_close:
            self.close_tab(idx)
        elif act == a_dup:
            self.duplicate_tab(idx)
        elif act == a_pin:
            self.toggle_pin(idx)
        elif act == a_newwin:
            url = (self.tabs[idx].view.url().toString() if self.tabs[idx].view else "dark://home")
            # Create new window instance with proper arguments
            from .main_window import MainWindow
            from PyQt6.QtWebEngineCore import QWebEngineProfile
            from ..core.downloads import DownloadsManager
            from ..core.scheme import register_dark_scheme, DarkUrlSchemeHandler
            from pathlib import Path
            
            # Use the SAME profile for shared cookies and sessions
            new_profile = self.profile
            
            # Ensure profile has proper configuration
            from PyQt6.QtCore import QStandardPaths
            from pathlib import Path
            data_dir = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)) / "Dark Browser"
            data_dir.mkdir(parents=True, exist_ok=True)
            new_profile.setCachePath(str(data_dir / "cache"))
            new_profile.setPersistentStoragePath(str(data_dir / "storage"))
            
            # Register custom scheme for new window (check if already registered)
            try:
                register_dark_scheme()
            except:
                pass  # Already registered
            
            new_downloads = DownloadsManager(new_profile)
            pages_dir = Path(__file__).parent.parent / "pages"
            pages_dir.mkdir(parents=True, exist_ok=True)
            scheme_handler = DarkUrlSchemeHandler(
                pages_dir,
                downloads_provider=new_downloads.list,
                settings_provider=self.settings.all,
                settings_actions=lambda k, v: None,
                downloads_actions=new_downloads.action,
            )
            new_profile.installUrlSchemeHandler(b"dark", scheme_handler)
            
            new_window = MainWindow(new_profile, self.settings, new_downloads)
            
            # Clear all default tabs and create only the specific tab
            new_window.tabman.tabs.clear()
            new_window.tabman.tabs_list.clear()
            
            # Clear the content stack properly
            while new_window.tabman.stack.count() > 0:
                widget = new_window.tabman.stack.widget(0)
                new_window.tabman.stack.removeWidget(widget)
                widget.deleteLater()
            
            # Create the specific tab for the new window
            new_window.tabman.create_tab(url)
            
            # Ensure the window is fully initialized before showing
            new_window.show()
            # Force a reload after a short delay to ensure page loads
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, lambda: new_window.tabman.current_view().reload() if new_window.tabman.current_view() else None)

    def _rebuild_list(self):
        self.tabs_list.clear()
        from pathlib import Path
        close_path = str((Path(__file__).parent.parent / 'resources' / 'icons' / 'close.svg').resolve())
        for i, t in enumerate(self.tabs):
            item = QListWidgetItem()
            self.tabs_list.addItem(item)
            # Get title safely - use stored title first, then try view title
            title = t.title or "New Tab"
            if t.view and not t.title:
                try:
                    view_title = t.view.title()
                    title = view_title or "Loading..."
                except Exception:
                    title = "Loading..."
            w = TabItemWidget(title, None, close_path, is_web_tab=bool(t.view))
            # capture index by default arg
            w.close_btn.clicked.connect(lambda _=False, idx=i: self.close_tab(idx))
            # Set main_window reference
            if hasattr(self, 'main_window'):
                w.main_window = self.main_window
            # Set URL and favorite status for web tabs
            if t.view and hasattr(w, 'set_url'):
                w.set_url(t.view.url().toString())
                if hasattr(w, 'set_favorite_status') and self.main_window:
                    url = t.view.url().toString()
                    is_fav = any(url == fav_url for fav_url, _ in self.main_window.favorites)
                    w.set_favorite_status(is_fav)
            self.tabs_list.setItemWidget(item, w)
        # plus item
        plus = QListWidgetItem()
        plus_widget = QWidget()
        plus_widget.setObjectName("TabItem")
        plus_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        plus_layout = QHBoxLayout(plus_widget)
        plus_layout.setContentsMargins(8, 6, 8, 8)
        plus_layout.setSpacing(6)
        
        plus_label = QLabel("+ New Tab")
        plus_label.setStyleSheet("background: transparent; color: #9ca3af; font-size: 13px;")
        plus_layout.addWidget(plus_label, 1)
        
        self.tabs_list.addItem(plus)
        self.tabs_list.setItemWidget(plus, plus_widget)

    # Session export
    def export_session(self) -> dict:
        tabs = []
        for t in self.tabs:
            if t.view:
                tabs.append({ 
                    'type': 'web', 
                    'url': t.view.url().toString(),
                    'title': t.title or t.view.title() or "New Tab"
                })
            else:
                # Check widget class to determine type accurately
                widget = t.widget
                if widget and hasattr(widget, '__class__'):
                    class_name = widget.__class__.__name__
                    if 'SettingsWidget' in class_name:
                        tabs.append({ 'type': 'settings', 'title': t.title or 'Settings' })
                    elif 'DownloadsWidget' in class_name:
                        tabs.append({ 'type': 'downloads', 'title': t.title or 'Descargas' })
                    elif 'HomeWidget' in class_name:
                        tabs.append({ 'type': 'home', 'title': t.title or 'Home' })
                    else:
                        # Fallback to title-based detection
                        title = (t.title or '').lower()
                        if 'settings' in title:
                            tabs.append({ 'type': 'settings', 'title': 'Settings' })
                        elif 'descarga' in title or 'download' in title:
                            tabs.append({ 'type': 'downloads', 'title': 'Descargas' })
                        else:
                            tabs.append({ 'type': 'home', 'title': 'Home' })
                else:
                    # Fallback if no widget
                    title = (t.title or '').lower()
                    if 'settings' in title:
                        tabs.append({ 'type': 'settings', 'title': 'Settings' })
                    elif 'descarga' in title or 'download' in title:
                        tabs.append({ 'type': 'downloads', 'title': 'Descargas' })
                    else:
                        tabs.append({ 'type': 'home', 'title': 'Home' })
        return { 'tabs': tabs, 'active': max(0, self.active_index) }

    def _on_url_changed(self, url, view=None):
        """Handle URL changes - update favorite status when URL changes"""
        try:
            if url and url.toString():
                # Use provided view or try to get sender
                sender_view = view
                if not sender_view:
                    try:
                        sender_view = self.sender()
                    except AttributeError:
                        return
                
                if not sender_view:
                    return
                
                # Update favorite status for the tab that changed URL
                for i, tab in enumerate(self.tabs):
                    if tab.view and tab.view == sender_view:
                        # Update tab title when URL changes
                        tab.title = sender_view.title() or "New Tab"
                        self._update_tab_favorite_status(i)
                        break
                        
                # Save session immediately when URL changes
                self._save_session_immediately()
        except Exception:
            pass

    def _save_session_immediately(self):
        """Save session immediately when active tab changes"""
        if self.settings:
            try:
                sess = self.export_session()
                #print(f"DEBUG: Saving session with {len(sess.get('tabs', []))} tabs, active index: {self.active_index}")
                self.settings.set('session', sess.get('tabs', []))
                self.settings.set('session_active', self.active_index if self.active_index >= 0 else 0)
                #print(f"DEBUG: Session saved successfully")
            except Exception as e:
                print(f"DEBUG: Error saving session: {e}")
                pass

    def _prewarm_qwebengine(self):
        """Pre-warm QWebEngine with a lightweight page to prevent first-search restart"""
        try:
            # Create a minimal web view in the background
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            from PyQt6.QtCore import QUrl, QTimer
            
            # Create a hidden web view for pre-warming
            prewarm_view = QWebEngineView()
            prewarm_view.setParent(self.container)
            prewarm_view.hide()  # Keep it hidden
            
            # Load a lightweight page (about:blank is perfect)
            prewarm_view.load(QUrl("about:blank"))
            
            # Clean up after a short delay to free resources
            def cleanup():
                try:
                    prewarm_view.setParent(None)
                    prewarm_view.deleteLater()
                except:
                    pass
            
            QTimer.singleShot(2000, cleanup)  # Clean up after 2 seconds
            
        except Exception as e:
            # If pre-warming fails, continue normally
            print(f"Warning: QWebEngine pre-warming failed: {e}")
            pass
