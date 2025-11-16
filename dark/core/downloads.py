from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Dict
from pathlib import Path
from PyQt6.QtCore import QObject
from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest, QWebEngineProfile
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl
import time
import json

@dataclass
class DownloadItem:
    id: str
    name: str
    total: int
    received: int = 0
    state: str = "downloading"
    path: str = ""
    _req: QWebEngineDownloadRequest | None = field(default=None, repr=False)
    
    def to_dict(self):
        """Convert to dict without unpickleable fields"""
        return {
            'id': self.id,
            'name': self.name,
            'total': self.total,
            'received': self.received,
            'state': self.state,
            'path': self.path
        }

class DownloadsManager(QObject):
    def __init__(self, profile: QWebEngineProfile, parent=None) -> None:
        super().__init__(parent)
        self._profile = profile
        self._items: List[DownloadItem] = []
        self._map: Dict[str, QWebEngineDownloadRequest] = {}
        profile.downloadRequested.connect(self._on_download)
        
        # Load download history on startup
        self._load_history()

    def _on_download(self, req: QWebEngineDownloadRequest):
        save_dir = Path.home() / "Downloads"
        save_dir.mkdir(parents=True, exist_ok=True)
        filename = req.downloadFileName()
        dest = save_dir / filename
        req.setDownloadDirectory(str(save_dir))
        req.accept()
        did = f"{int(time.time()*1000)}"
        item = DownloadItem(id=did, name=filename, total=int(req.totalBytes()), received=0, state="downloading", path=str(dest), _req=req)
        self._items.insert(0, item)
        self._map[did] = req
        req.receivedBytesChanged.connect(lambda: self._update_progress(did))
        req.stateChanged.connect(lambda: self._check_finished(did, req))
        
        # Notify download started and update UI
        if hasattr(self, '_notify_callback'):
            self._notify_callback(f"Descarga iniciada: {filename}", "success")
        # Also notify for UI update
        if hasattr(self, '_notify_callback'):
            self._notify_callback("download_started", "download_update")

    def _update_progress(self, did: str):
        req = self._map.get(did)
        item = next((x for x in self._items if x.id == did), None)
        if not req or not item:
            return
        item.received = int(req.receivedBytes())

    def _check_finished(self, did: str, req: QWebEngineDownloadRequest):
        """Check if download is finished and handle accordingly"""
        if req.isFinished() or req.state() == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
            self._finish(did, req)
        elif req.state() == QWebEngineDownloadRequest.DownloadState.DownloadInterrupted:
            item = next((x for x in self._items if x.id == did), None)
            if item:
                item.state = "interrupted"
                if hasattr(self, '_notify_callback'):
                    self._notify_callback(f"Descarga interrumpida: {item.name}", "error")

    def _finish(self, did: str, req: QWebEngineDownloadRequest):
        item = next((x for x in self._items if x.id == did), None)
        if not item:
            return
        item.state = "completed" if req.state() == QWebEngineDownloadRequest.DownloadState.DownloadCompleted else ("cancelled" if req.state() == QWebEngineDownloadRequest.DownloadState.DownloadCancelled else "failed")
        self._map.pop(did, None)
        
        # Save download history when download finishes
        self._save_history()
        
        # Notify download finished
        if hasattr(self, '_notify_callback'):
            if item.state == "completed":
                self._notify_callback(f"Descarga completada: {item.name}", "success")
            elif item.state == "cancelled":
                self._notify_callback(f"Descarga cancelada: {item.name}", "warning")
            else:
                self._notify_callback(f"Descarga fallida: {item.name}", "error")
        # Also notify for UI update
        if hasattr(self, '_notify_callback'):
            self._notify_callback("download_finished", "download_update")

    def set_notify_callback(self, callback):
        """Set callback for notifications"""
        self._notify_callback = callback

    def has_active_downloads(self) -> bool:
        """Check if there are any active downloads"""
        return any(item.state == "downloading" for item in self._items)

    def pause_all_downloads(self):
        """Pause all active downloads"""
        for item in self._items:
            if item.state == "downloading" and hasattr(item, '_req') and item._req:
                try:
                    item._req.pause()
                    item.state = "paused"
                except:
                    pass

    def resume_all_downloads(self):
        """Resume all paused downloads"""
        for item in self._items:
            if item.state == "paused" and hasattr(item, '_req') and item._req:
                try:
                    item._req.resume()
                    item.state = "downloading"
                except:
                    pass
    
    def download_image(self, image_url: str):
        """Download image from URL using QWebEngine download system - DISABLED to avoid floating button"""
        # This method is disabled because it creates temporary QWebEngineView instances
        # that cause the floating blue button issue
        print("Image download disabled to prevent UI glitches")
        return
    
    def _download_image_direct(self, image_url: str):
        """Direct download fallback for images"""
        import requests
        from urllib.parse import urlparse
        import os
        from PyQt6.QtCore import QUrl
        
        try:
            # Get filename from URL
            parsed = urlparse(image_url)
            filename = os.path.basename(parsed.path) or "image.jpg"
            
            # Download to Downloads folder
            save_dir = Path.home() / "Downloads"
            save_dir.mkdir(parents=True, exist_ok=True)
            filepath = save_dir / filename
            
            # Download image
            response = requests.get(image_url, timeout=10)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                # Create download item for tracking
                did = f"{int(time.time()*1000)}"
                item = DownloadItem(id=did, name=filename, total=len(response.content), received=len(response.content), state="completed", path=str(filepath))
                self._items.insert(0, item)
                
                # Notify download completed
                if hasattr(self, '_notify_callback'):
                    self._notify_callback(f"Imagen descargada: {filename}", "success")
                
                return True
        except Exception as e:
            print(f"Error downloading image: {e}")
            # Notify download error
            if hasattr(self, '_notify_callback'):
                self._notify_callback(f"Error al descargar imagen: {str(e)}", "error")
            return False

    # Provider for scheme
    def list(self) -> list[dict]:
        return [dict(id=i.id, name=i.name, total=i.total, received=i.received, state=i.state, path=i.path) for i in self._items]

    # Actions for scheme
    def action(self, k: str, did: str | None):
        if not did:
            return
        if k == "remove":
            self._items = [x for x in self._items if x.id != did]
            self._map.pop(did, None)
            # Save history after removing an item
            self._save_history()
        elif k == "cancel":
            req = self._map.get(did)
            if req:
                req.cancel()
        elif k == "show":
            item = next((x for x in self._items if x.id == did), None)
            if item:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(item.path).parent)))
    
    def _load_history(self):
        """Load download history from JSON file"""
        try:
            history_file = Path.home() / ".dark_downloads.json"
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Load completed downloads only (no active downloads needed)
                    for item_data in data:
                        if item_data.get('state') in ['completed', 'failed', 'cancelled', 'interrupted']:
                            item = DownloadItem(
                                id=item_data['id'],
                                name=item_data['name'],
                                total=item_data['total'],
                                received=item_data['received'],
                                state=item_data['state'],
                                path=item_data['path']
                            )
                            self._items.append(item)
        except Exception as e:
            print(f"Error loading download history: {e}")
    
    def _save_history(self):
        """Save download history to JSON file"""
        try:
            history_file = Path.home() / ".dark_downloads.json"
            # Save only completed/failed/cancelled downloads (not active ones)
            history_data = []
            for item in self._items:
                if item.state in ['completed', 'failed', 'cancelled', 'interrupted']:
                    # Use to_dict method to avoid unpickleable fields
                    history_data.append(item.to_dict())
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving download history: {e}")
