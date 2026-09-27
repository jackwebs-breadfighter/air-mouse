"""
Minimal Windows system tray icon, built directly on ctypes (Shell_NotifyIcon +
a message-only window) rather than pulling in pystray/Pillow - consistent with
winput.py's approach of wrapping the Win32 APIs we actually need.
"""

import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
shell32 = ctypes.WinDLL("shell32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

LRESULT = ctypes.c_ssize_t
UINT_PTR = ctypes.c_size_t
WNDPROCTYPE = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

HWND_MESSAGE = wintypes.HWND(-3)

WM_DESTROY = 0x0002
WM_COMMAND = 0x0111
WM_APP = 0x8000
WM_LBUTTONUP = 0x0202
WM_LBUTTONDBLCLK = 0x0203
WM_RBUTTONUP = 0x0205
WM_NULL = 0x0000

NIM_ADD = 0x00000000
NIM_MODIFY = 0x00000001
NIM_DELETE = 0x00000002
NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004

IMAGE_ICON = 1
LR_LOADFROMFILE = 0x00000010

MF_STRING = 0x00000000
TPM_RIGHTBUTTON = 0x0002


class WNDCLASSEXW(ctypes.Structure):
    _fields_ = (
        ("cbSize", wintypes.UINT),
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROCTYPE),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
        ("hIconSm", wintypes.HICON),
    )


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = (
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", wintypes.HICON),
        ("szTip", wintypes.WCHAR * 128),
        ("dwState", wintypes.DWORD),
        ("dwStateMask", wintypes.DWORD),
        ("szInfo", wintypes.WCHAR * 256),
        ("uTimeoutOrVersion", wintypes.UINT),
        ("szInfoTitle", wintypes.WCHAR * 64),
        ("dwInfoFlags", wintypes.DWORD),
        ("guidItem", ctypes.c_byte * 16),
        ("hBalloonIcon", wintypes.HICON),
    )


user32.RegisterClassExW.restype = wintypes.ATOM
user32.RegisterClassExW.argtypes = (ctypes.POINTER(WNDCLASSEXW),)

user32.CreateWindowExW.restype = wintypes.HWND
user32.CreateWindowExW.argtypes = (
    wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID,
)

user32.DefWindowProcW.restype = LRESULT
user32.DefWindowProcW.argtypes = (wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

user32.GetMessageW.restype = ctypes.c_int
user32.GetMessageW.argtypes = (ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT)

user32.TranslateMessage.restype = wintypes.BOOL
user32.TranslateMessage.argtypes = (ctypes.POINTER(wintypes.MSG),)

user32.DispatchMessageW.restype = LRESULT
user32.DispatchMessageW.argtypes = (ctypes.POINTER(wintypes.MSG),)

user32.PostQuitMessage.restype = None
user32.PostQuitMessage.argtypes = (ctypes.c_int,)

user32.DestroyWindow.restype = wintypes.BOOL
user32.DestroyWindow.argtypes = (wintypes.HWND,)

user32.PostMessageW.restype = wintypes.BOOL
user32.PostMessageW.argtypes = (wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

user32.LoadImageW.restype = wintypes.HANDLE
user32.LoadImageW.argtypes = (wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT, ctypes.c_int, ctypes.c_int, wintypes.UINT)

user32.GetCursorPos.restype = wintypes.BOOL
user32.GetCursorPos.argtypes = (ctypes.POINTER(wintypes.POINT),)

user32.SetForegroundWindow.restype = wintypes.BOOL
user32.SetForegroundWindow.argtypes = (wintypes.HWND,)

user32.CreatePopupMenu.restype = wintypes.HMENU
user32.CreatePopupMenu.argtypes = ()

user32.AppendMenuW.restype = wintypes.BOOL
user32.AppendMenuW.argtypes = (wintypes.HMENU, wintypes.UINT, UINT_PTR, wintypes.LPCWSTR)

user32.TrackPopupMenu.restype = wintypes.BOOL
user32.TrackPopupMenu.argtypes = (
    wintypes.HMENU, wintypes.UINT, ctypes.c_int, ctypes.c_int,
    ctypes.c_int, wintypes.HWND, ctypes.c_void_p,
)

user32.DestroyMenu.restype = wintypes.BOOL
user32.DestroyMenu.argtypes = (wintypes.HMENU,)

kernel32.GetModuleHandleW.restype = wintypes.HMODULE
kernel32.GetModuleHandleW.argtypes = (wintypes.LPCWSTR,)

shell32.Shell_NotifyIconW.restype = wintypes.BOOL
shell32.Shell_NotifyIconW.argtypes = (wintypes.DWORD, ctypes.POINTER(NOTIFYICONDATAW))


class TrayIcon:
    """A tray icon with a right-click menu of arbitrary items. Call run() on
    a dedicated thread (it blocks pumping messages); left-click/double-click
    triggers on_primary.

    menu_items: list of (label_getter, callback) pairs. label_getter is a
    zero-arg callable returning the current text - re-invoked fresh every
    time the menu opens, so an item's label can change dynamically (e.g. a
    language toggle) without re-registering anything."""

    WM_TRAYICON = WM_APP + 1
    _FIRST_ITEM_ID = 2001

    def __init__(self, icon_path, tooltip, on_primary, menu_items):
        self.icon_path = str(icon_path)
        self.tooltip = tooltip[:127]
        self.on_primary = on_primary
        self.menu_items = list(menu_items)
        self.hwnd = None
        self._nid = None
        # Keep a reference alive for the window's lifetime - ctypes doesn't
        # otherwise stop this callback trampoline from being garbage collected.
        self._wndproc_ref = WNDPROCTYPE(self._wndproc)

    def _wndproc(self, hwnd, msg, wparam, lparam):
        if msg == self.WM_TRAYICON:
            event = lparam & 0xFFFF
            if event in (WM_LBUTTONUP, WM_LBUTTONDBLCLK):
                self._fire(self.on_primary)
            elif event == WM_RBUTTONUP:
                self._show_menu(hwnd)
            return 0
        if msg == WM_COMMAND:
            index = (wparam & 0xFFFF) - self._FIRST_ITEM_ID
            if 0 <= index < len(self.menu_items):
                self._fire(self.menu_items[index][1])
            return 0
        if msg == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    @staticmethod
    def _fire(callback):
        if callback is None:
            return
        try:
            callback()
        except Exception:
            pass

    def _show_menu(self, hwnd):
        pt = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        menu = user32.CreatePopupMenu()
        if not menu:
            return
        try:
            for i, (label_getter, _callback) in enumerate(self.menu_items):
                try:
                    label = label_getter()
                except Exception:
                    label = ""
                user32.AppendMenuW(menu, MF_STRING, self._FIRST_ITEM_ID + i, label)
            user32.SetForegroundWindow(hwnd)
            user32.TrackPopupMenu(menu, TPM_RIGHTBUTTON, pt.x, pt.y, 0, hwnd, None)
            user32.PostMessageW(hwnd, WM_NULL, 0, 0)
        finally:
            user32.DestroyMenu(menu)

    def remove_icon(self):
        if self._nid is not None:
            try:
                shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(self._nid))
            except Exception:
                pass

    def run(self):
        """Blocking - call on a dedicated thread."""
        hinstance = kernel32.GetModuleHandleW(None)
        class_name = "AirMouseTrayWndClass"

        wc = WNDCLASSEXW()
        wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wc.lpfnWndProc = self._wndproc_ref
        wc.hInstance = hinstance
        wc.lpszClassName = class_name
        user32.RegisterClassExW(ctypes.byref(wc))

        self.hwnd = user32.CreateWindowExW(
            0, class_name, "AirMouse", 0, 0, 0, 0, 0,
            HWND_MESSAGE, None, hinstance, None,
        )
        if not self.hwnd:
            return

        hicon = user32.LoadImageW(None, self.icon_path, IMAGE_ICON, 0, 0, LR_LOADFROMFILE)

        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self.hwnd
        nid.uID = 1
        nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        nid.uCallbackMessage = self.WM_TRAYICON
        nid.hIcon = hicon
        nid.szTip = self.tooltip
        shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid))
        self._nid = nid

        msg = wintypes.MSG()
        while True:
            ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret <= 0:
                break
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        self.remove_icon()
