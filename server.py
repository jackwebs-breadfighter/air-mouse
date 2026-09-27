"""
AirMouse server: serves the mobile web UI and turns WebSocket messages
into real mouse/keyboard input via winput.py (Win32 SendInput).
"""

import ctypes
import datetime
import ipaddress
import json
import os
import secrets
import socket
import ssl
import sys
import threading
from pathlib import Path

from aiohttp import web, WSMsgType

import traymenu
import winput

FROZEN = getattr(sys, "frozen", False)

if FROZEN:
    # PyInstaller onefile: bundled read-only assets (static/) live in the
    # temp extraction dir (sys._MEIPASS), but writable/persistent files
    # (config, cert) must live next to the actual .exe, not in that temp dir.
    BASE_DIR = Path(sys.executable).resolve().parent
    RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", BASE_DIR))
else:
    BASE_DIR = Path(__file__).resolve().parent
    RESOURCE_DIR = BASE_DIR

STATIC_DIR = RESOURCE_DIR / "static"
CONFIG_PATH = BASE_DIR / "config.json"
CERT_PATH = BASE_DIR / "cert.pem"
KEY_PATH = BASE_DIR / "key.pem"

DEFAULT_CONFIG = {
    "port": 8765,
    "token": "",
    "sensitivity": 1.0,
    "scroll_speed": 1.0,
    "invert_scroll": False,
    "tray_lang": "en",
}

TRAY_STRINGS = {
    "en": {
        "tooltip": "AirMouse",
        "show_qr": "Show QR Code",
        "exit": "Exit AirMouse",
        "switch_to": "中文",
        "heading": "Scan with your iPhone's Camera app,",
        "subheading": "or open this link in Safari:",
    },
    "zh": {
        "tooltip": "AirMouse",
        "show_qr": "顯示 QR Code",
        "exit": "結束 AirMouse",
        "switch_to": "English",
        "heading": "用 iPhone 相機 App 掃描,",
        "subheading": "或者喺 Safari 開啟以下連結:",
    },
}

MOUSE_BUTTONS = {"left", "right", "middle"}


def load_config() -> dict:
    cfg = {}
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            cfg = {}
    changed = False
    for key, value in DEFAULT_CONFIG.items():
        if key not in cfg:
            cfg[key] = value
            changed = True
    if not cfg.get("token"):
        cfg["token"] = secrets.token_urlsafe(24)
        changed = True
    if changed:
        save_config(cfg)
    return cfg


def save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def get_lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def _cert_covers_ip(cert_path: Path, ip: str) -> bool:
    from cryptography import x509

    cert = x509.load_pem_x509_certificate(cert_path.read_bytes())
    if cert.not_valid_after_utc < datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30):
        return False
    san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    covered = {str(v) for v in san.get_values_for_type(x509.IPAddress)}
    return ip in covered


def ensure_tls_cert(ip: str) -> None:
    """Generate a self-signed cert for the LAN IP if missing, expiring soon, or stale."""
    if CERT_PATH.exists() and KEY_PATH.exists():
        try:
            if _cert_covers_ip(CERT_PATH, ip):
                return
        except Exception:
            pass  # fall through and regenerate

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "AirMouse")])
    san = [x509.DNSName("localhost"), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]
    try:
        san.append(x509.IPAddress(ipaddress.ip_address(ip)))
    except ValueError:
        pass

    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=825))
        .add_extension(x509.SubjectAlternativeName(san), critical=False)
        .sign(key, hashes.SHA256())
    )

    KEY_PATH.write_bytes(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ))
    CERT_PATH.write_bytes(cert.public_bytes(serialization.Encoding.PEM))


def check_token(request: web.Request, cfg: dict) -> bool:
    token = request.query.get("token", "")
    return bool(token) and secrets.compare_digest(token, cfg["token"])


def handle_message(msg: dict, cfg: dict) -> None:
    """Apply one client message. Never raises: bad/unknown input is ignored."""
    t = msg.get("t")
    try:
        if t == "move":
            dx = float(msg.get("dx", 0)) * cfg.get("sensitivity", 1.0)
            dy = float(msg.get("dy", 0)) * cfg.get("sensitivity", 1.0)
            winput.mouse_move(dx, dy)
        elif t == "click":
            b = msg.get("b", "left")
            if b in MOUSE_BUTTONS:
                winput.mouse_click(b)
        elif t == "down":
            b = msg.get("b", "left")
            if b in MOUSE_BUTTONS:
                winput.mouse_down(b)
        elif t == "up":
            b = msg.get("b", "left")
            if b in MOUSE_BUTTONS:
                winput.mouse_up(b)
        elif t == "scroll":
            dx = float(msg.get("dx", 0)) * cfg.get("scroll_speed", 1.0)
            dy = float(msg.get("dy", 0)) * cfg.get("scroll_speed", 1.0)
            if cfg.get("invert_scroll"):
                dx, dy = -dx, -dy
            winput.scroll(dx, dy)
        elif t == "text":
            s = msg.get("s", "")
            if isinstance(s, str):
                winput.type_text(s)
        elif t == "key":
            k = msg.get("k")
            if isinstance(k, str):
                winput.press_key(k)
        elif t == "combo":
            keys = msg.get("k")
            if isinstance(keys, list):
                winput.key_combo([str(k) for k in keys])
        elif t == "media":
            k = msg.get("k")
            if isinstance(k, str):
                winput.media_key(k)
        # any other/unknown "t" is silently ignored by design
    except Exception:
        pass


async def index_handler(request: web.Request) -> web.StreamResponse:
    cfg = request.app["config"]
    if not check_token(request, cfg):
        return web.Response(status=403, text="Forbidden: missing or invalid token")
    return web.FileResponse(STATIC_DIR / "index.html")


async def settings_handler(request: web.Request) -> web.Response:
    cfg = request.app["config"]
    if not check_token(request, cfg):
        return web.json_response({"error": "forbidden"}, status=403)
    if request.method == "GET":
        return web.json_response({
            "sensitivity": cfg["sensitivity"],
            "scroll_speed": cfg["scroll_speed"],
            "invert_scroll": cfg["invert_scroll"],
        })
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "bad json"}, status=400)
    for key in ("sensitivity", "scroll_speed"):
        if key in body:
            try:
                cfg[key] = float(body[key])
            except (TypeError, ValueError):
                pass
    if "invert_scroll" in body:
        cfg["invert_scroll"] = bool(body["invert_scroll"])
    save_config(cfg)
    return web.json_response({"ok": True})


async def ws_handler(request: web.Request) -> web.WebSocketResponse:
    cfg = request.app["config"]
    ws = web.WebSocketResponse(heartbeat=20)
    await ws.prepare(request)

    if not check_token(request, cfg):
        await ws.close(code=4001, message=b"bad token")
        return ws

    on_first_connection()

    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            try:
                data = json.loads(msg.data)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict):
                handle_message(data, cfg)
        elif msg.type in (WSMsgType.ERROR, WSMsgType.CLOSE, WSMsgType.CLOSING):
            break
    return ws


def build_app(cfg: dict) -> web.Application:
    app = web.Application()
    app["config"] = cfg
    app.router.add_get("/", index_handler)
    app.router.add_get("/ws", ws_handler)
    app.router.add_route("*", "/api/settings", settings_handler)
    app.router.add_static("/static/", STATIC_DIR, show_index=False)
    return app


def print_qr(url: str) -> None:
    try:
        import qrcode
        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.make()
        qr.print_ascii(invert=True)
    except Exception as exc:
        print(f"(無法產生 QR code: {exc})")


_qr_window_lock = threading.Lock()
_qr_window = None  # the currently-open QrWindow, if any


def show_qr_now(cfg: dict) -> None:
    """Regenerate the QR (IP may have changed since startup, e.g. new Wi-Fi)
    and pop up our own window for it - closing any previous one first. Used
    by both the startup banner and the tray icon's "show QR" action."""
    global _qr_window
    try:
        import qrwindow
        import qrcode

        ip = get_lan_ip()
        url = f"https://{ip}:{cfg['port']}/?token={cfg['token']}"
        # Manually break the URL across two lines at the path separator:
        # DrawTextW's word-wrap can't find a break point in a token with no
        # spaces, so left unbroken it just gets clipped at both edges instead
        # of wrapping.
        display_url = f"https://{ip}:{cfg['port']}/\n?token={cfg['token']}"

        qr = qrcode.QRCode(border=4)
        qr.add_data(url)
        qr.make()
        matrix = qr.get_matrix()

        strings = TRAY_STRINGS[cfg.get("tray_lang", "en")]
        win = qrwindow.QrWindow(
            "AirMouse", strings["heading"], strings["subheading"], display_url, matrix,
        )

        with _qr_window_lock:
            if _qr_window is not None:
                _qr_window.close()
            _qr_window = win

        def _run():
            global _qr_window
            win.show()
            with _qr_window_lock:
                if _qr_window is win:
                    _qr_window = None

        threading.Thread(target=_run, daemon=True).start()
    except Exception:
        pass


_console_hidden = False


def on_first_connection() -> None:
    """Called on the first authenticated connection: the interactive/console
    launch (and any QR window still open) has served its purpose and can now
    get out of the way, leaving just the tray icon. No-op on repeat calls, or
    if there was never a console to begin with (--background/frozen-headless)."""
    global _console_hidden, _qr_window
    if _console_hidden:
        return
    _console_hidden = True
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE
    except Exception:
        pass
    with _qr_window_lock:
        if _qr_window is not None:
            _qr_window.close()
            _qr_window = None


def start_tray_icon(cfg: dict) -> None:
    icon_path = STATIC_DIR / "tray.ico"
    if not icon_path.exists():
        return

    def _strings():
        return TRAY_STRINGS[cfg.get("tray_lang", "en")]

    def _toggle_language():
        cfg["tray_lang"] = "zh" if cfg.get("tray_lang", "en") == "en" else "en"
        save_config(cfg)

    def _on_exit():
        tray.remove_icon()
        os._exit(0)

    tray = traymenu.TrayIcon(
        icon_path,
        "AirMouse",
        lambda: show_qr_now(cfg),
        [
            (lambda: _strings()["show_qr"], lambda: show_qr_now(cfg)),
            (lambda: _strings()["switch_to"], _toggle_language),
            (lambda: _strings()["exit"], _on_exit),
        ],
    )
    threading.Thread(target=tray.run, daemon=True).start()


def run_server(cfg: dict) -> None:
    start_tray_icon(cfg)
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_ctx.load_cert_chain(str(CERT_PATH), str(KEY_PATH))
    app = build_app(cfg)
    web.run_app(app, host="0.0.0.0", port=cfg["port"], ssl_context=ssl_ctx, print=None)


def main() -> None:
    # Console codepage varies by system locale; force UTF-8 so Chinese text
    # and the QR code's block characters print correctly regardless.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    background = "--background" in sys.argv[1:]

    if background:
        # Launched by the auto-start task - no banner, no console at all.
        # In source form this runs via pythonw.exe, which never has a
        # console. The frozen exe has no such windowless variant, and a Task
        # Scheduler "Interactive" action shows a real console regardless of
        # the task's own "Hidden" setting (that only hides it from the Task
        # Scheduler list, not the process's window) - so explicitly release
        # whatever console got allocated.
        try:
            ctypes.windll.kernel32.FreeConsole()
        except Exception:
            pass

    cfg = load_config()
    ip = get_lan_ip()
    ensure_tls_cert(ip)

    if not background:
        # Interactive launch (start.bat / double-clicking the exe): show the
        # welcome banner + QR so the phone can connect, and also pop up our
        # own QR window (easier to scan than the console's ASCII art). A tray
        # icon appears immediately - once the phone connects, this console
        # window and the QR window both close themselves automatically
        # (on_first_connection, called from ws_handler); until then it's fine
        # to leave them open, and closing early just means "never mind, don't
        # start" since no phone has connected yet. From then on, right-click
        # the AirMouse tray icon any time to see the QR again or to exit.
        url = f"https://{ip}:{cfg['port']}/?token={cfg['token']}"
        print("=" * 60)
        print("AirMouse server 啟動中...")
        print("手機同電腦要連同一個 Wi-Fi,然後用 Safari 開啟:")
        print(f"  {url}")
        print("(第一次連接 Safari 會顯示「連線並非私人連線」,呢個係自簽")
        print(" 證書嘅正常現象,撳「顯示詳細資料」→「前往此網頁」一次就得)")
        print("=" * 60)
        print_qr(url)
        print()
        print("已經幫你開埋一張大嘅 QR code 圖,掃嗰張會方便啲。")
        print("手機連接成功之後,呢個視窗會自動收埋去工作列(tray)。")
        print("之後想再睇 QR code,去工作列右下角搵 AirMouse 圖示撳一下就得。")
        show_qr_now(cfg)

    run_server(cfg)


if __name__ == "__main__":
    main()
