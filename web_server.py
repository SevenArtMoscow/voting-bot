import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import config
from database import Database

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "disign.html"
WEB_ROOT = ROOT / "web"
db = Database()

PAGE_ROUTES = {"/1", "/2", "/3", "/1/", "/2/", "/3/"}

PAGES = {
    "1": {"title": "Матвей Петров — кандидат", "slug": "1", "boot": "Матвей Петров", "intro": "МАТВЕЙ ПЕТРОВ"},
    "2": {"title": "Валентин Пупликов — кандидат", "slug": "2", "boot": "Валентин Пупликов", "intro": "ВАЛЕНТИН ПУПЛИКОВ"},
    "3": {"title": "Дарина Мамедова — кандидат", "slug": "3", "boot": "Дарина Мамедова", "intro": "ДАРИНА МАМЕДОВА"},
}


def page_for(path):
    return PAGES[path.strip("/")]


def prepare_candidate_html(page, overlay_src="/overlay.js"):
    html = TEMPLATE.read_text(encoding="utf-8")
    html = html.replace(
        "<title>Ольга Спиркина — актриса, телеведущая, журналист</title>",
        f"<title>{page['title']}</title>",
        1,
    )
    html = html.replace(
        'content="Ольга Спиркина — актриса, телеведущая, журналист, режиссёр, художественный руководитель Медиа Школы Ольги Спиркиной."',
        f'content="{page["title"]}"',
        1,
    )
    html = html.replace("ОЛЬГА СПИРКИНА", page["intro"])
    html = html.replace("Ольга Спиркина", page["boot"])
    boot = (
        "<script>window.__PAGE__="
        + json.dumps(page["slug"])
        + ";document.title="
        + json.dumps(page["title"])
        + ";</script>"
    )
    html = html.replace("<head>", "<head>" + boot, 1)
    if "</body>" in html:
        html = html.replace("</body>", f'<script src="{overlay_src}"></script></body>', 1)
    return html


def public_payload():
    board = db.get_public_board(config.CANDIDATES, config.VOTING_ACTIVE)
    board["bot_url"] = f"https://t.me/{config.BOT_USERNAME}?start=vote"
    board["bot_username"] = config.BOT_USERNAME
    return board


class VotingSiteHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def log_message(self, format, *args):
        return

    def _send(self, status, content_type, body, cache="no-store"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", cache)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/status":
            self._send(200, "application/json; charset=utf-8", json.dumps(public_payload(), ensure_ascii=False))
            return
        if path == "/overlay.js":
            self._send(200, "application/javascript; charset=utf-8", (WEB_ROOT / "overlay.js").read_bytes(), "no-cache")
            return
        if path in ("/", "/index.html"):
            self._send(200, "text/html; charset=utf-8", (WEB_ROOT / "index.html").read_text(encoding="utf-8"))
            return
        if path in PAGE_ROUTES:
            page = page_for(path)
            html = prepare_candidate_html(page)
            self._send(200, "text/html; charset=utf-8", html)
            return
        return super().do_GET()


def start_web_server():
    server = ThreadingHTTPServer((config.WEB_HOST, config.WEB_PORT), VotingSiteHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True, name="voting-site")
    thread.start()
    print(f"Сайт витрины: http://127.0.0.1:{config.WEB_PORT}")
    return server
