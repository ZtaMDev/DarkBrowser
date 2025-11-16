from __future__ import annotations
from PyQt6.QtWebEngineCore import QWebEngineUrlScheme, QWebEngineUrlSchemeHandler, QWebEngineUrlRequestJob
from PyQt6.QtCore import QByteArray, QIODevice, QUrlQuery, QBuffer
from pathlib import Path
from typing import Optional

class DarkUrlSchemeHandler(QWebEngineUrlSchemeHandler):
    def __init__(self, pages_dir: Path, downloads_provider, settings_provider, settings_actions, downloads_actions, parent=None) -> None:
        super().__init__(parent)
        self._pages_dir = pages_dir
        self._downloads_provider = downloads_provider
        self._settings_provider = settings_provider
        self._settings_actions = settings_actions
        self._downloads_actions = downloads_actions
        self._devices: set[QBuffer] = set()

    def _respond(self, job: QWebEngineUrlRequestJob, mime: bytes, data: bytes):
        buf = QBuffer()
        buf.setData(data)
        buf.open(QIODevice.OpenModeFlag.ReadOnly)
        job.reply(mime, buf)
        self._devices.add(buf)

        def cleanup():
            self._devices.discard(buf)

        job.destroyed.connect(cleanup)

    def requestStarted(self, job: QWebEngineUrlRequestJob) -> None:  # type: ignore[override]
        url = job.requestUrl()
        host = url.host() or url.path().lstrip('/')
        q = QUrlQuery(url)

        if host == "settings":
            action = q.queryItemValue("action")
            if action == "get":
                import json
                data = json.dumps(self._settings_provider()).encode("utf-8")
                self._respond(job, b"application/json", data)
                return
            if action == "set":
                key = q.queryItemValue("key")
                value = q.queryItemValue("value")
                if key:
                    self._settings_actions("set", key, value)
            p = self._pages_dir / "settings.html"
            data = p.read_bytes() if p.exists() else b"<h1>Not found</h1>"
            self._respond(job, b"text/html", data)
            return

        if host == "home":
            p = self._pages_dir / "home.html"
            data = p.read_bytes() if p.exists() else b"<h1>Not found</h1>"
            self._respond(job, b"text/html", data)
            return

        if host == "downloads":
            action = q.queryItemValue("action")
            if action:
                idv = q.queryItemValue("id")
                self._downloads_actions(action, idv)
            items = self._downloads_provider()
            html = _render_downloads(items)
            self._respond(job, b"text/html", html.encode("utf-8"))
            return
        # default 404
        self._respond(job, b"text/html", b"<h1>Not found</h1>")


def register_dark_scheme():
    """Register the dark:// scheme if not already registered"""
    try:
        scheme = QWebEngineUrlScheme(b"dark")
        scheme.setFlags(QWebEngineUrlScheme.Flag.SecureScheme | QWebEngineUrlScheme.Flag.LocalScheme | QWebEngineUrlScheme.Flag.LocalAccessAllowed)
        scheme.setSyntax(QWebEngineUrlScheme.Syntax.HostAndPort)
        scheme.setDefaultPort(0)
        QWebEngineUrlScheme.registerScheme(scheme)
    except Exception as e:
        # Scheme already registered or other error, just continue
        pass


def _render_downloads(items: list[dict]) -> str:
    rows = []
    for d in items:
        size_mb = f"{(d.get('total',0)/1024/1024):.2f}"
        pct = int((d.get('received',0) / d.get('total',1)) * 100) if d.get('total') else 0
        rows.append("""
        <div class='item'>
          <div class='row'>
            <div><b>{name}</b> <span class='muted'>{size} MB</span></div>
            <div class='actions'>
              <button onclick="downloadAction('show','{id}')">Abrir carpeta</button>
              <button onclick="downloadAction('cancel','{id}')">Cancelar</button>
              <button onclick="downloadAction('remove','{id}')">Eliminar</button>
            </div>
          </div>
          <div class='progress'><div class='bar' style='width:{pct}%;'></div></div>
          <div class='row'><span>{state}</span><span>{pct}%</span></div>
        </div>
        """.format(name=d.get('name',''), size=size_mb, id=d.get('id',''), pct=pct, state=d.get('state','')))
    body = "\n".join(rows) or "<div class='muted'>No hay descargas</div>"
    template = """
<!doctype html>
<html>
<head>
<meta charset='utf-8'/>
<meta name='viewport' content='width=device-width,initial-scale=1'/>
<title>Dark · Descargas</title>
<style>
:root{{--bg:#0f1115;--fg:#e5e7eb;--muted:#9aa3af;--card:#141821;--accent:#3b82f6}}
body{{margin:0;background:var(--bg);color:var(--fg);font:14px system-ui,Segoe UI,Roboto,Arial,sans-serif}}
main{{max-width:900px;margin:40px auto;padding:0 20px}}
.item{{background:var(--card);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:12px;margin-bottom:12px}}
.row{{display:flex;gap:12px;align-items:center;justify-content:space-between}}
.progress{{height:8px;border-radius:8px;background:#0e131b;border:1px solid rgba(255,255,255,.06);overflow:hidden}}
.bar{{height:100%;background:var(--accent);width:0}}
.actions button{{background:#243b55;border:1px solid rgba(255,255,255,.1);color:#dbeafe;border-radius:8px;padding:6px 10px;margin-left:8px;cursor:pointer}}
.muted{{color:#9aa3af}}
</style>
</head>
<body>
<main>
  <h2>Descargas</h2>
  <div id='list'>
    {body}
  </div>
</main>
<script>
function downloadAction(k,id){
  if (k==='show') window.location.href = 'dark://downloads?action=show&id='+id;
  if (k==='cancel') window.location.href = 'dark://downloads?action=cancel&id='+id;
  if (k==='remove') window.location.href = 'dark://downloads?action=remove&id='+id;
}
</script>
</body>
</html>
"""
    return template.format(body=body)
