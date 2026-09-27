"""
A small native window that shows a QR code plus explanatory text, drawn
directly with GDI (no image files, no external viewer). We own the window,
so it can be closed programmatically the moment a phone connects - something
an externally-opened photo viewer wouldn't let us do.
"""

import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

LRESULT = ctypes.c_ssize_t
WNDPROCTYPE = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

WM_DESTROY = 0x0002
WM_CLOSE = 0x0010
WM_PAINT = 0x000F

WS_OVERLAPPED = 0x00000000
WS_CAPTION = 0x00C00000
WS_SYSMENU = 0x00080000
WS_MINIMIZEBOX = 0x00020000
WS_VISIBLE = 0x10000000
WS_WINDOW = WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX

SW_SHOW = 5
SM_CXSCREEN = 0
SM_CYSCREEN = 1

DT_CENTER = 0x00000001
DT_WORDBREAK = 0x00000010
DT_NOPREFIX = 0x00000800

BI_RGB = 0
DIB_RGB_COLORS = 0
SRCCOPY = 0x00CC0020
TRANSPARENT_BKMODE = 1


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


class PAINTSTRUCT(ctypes.Structure):
    _fields_ = (
        ("hdc", wintypes.HDC),
        ("fErase", wintypes.BOOL),
        ("rcPaint", wintypes.RECT),
        ("fRestore", wintypes.BOOL),
        ("fIncUpdate", wintypes.BOOL),
        ("rgbReserved", ctypes.c_byte * 32),
    )


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = (
        ("biSize", wintypes.DWORD),
        ("biWidth", ctypes.c_long),
        ("biHeight", ctypes.c_long),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", ctypes.c_long),
        ("biYPelsPerMeter", ctypes.c_long),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
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

user32.ShowWindow.restype = wintypes.BOOL
user32.ShowWindow.argtypes = (wintypes.HWND, ctypes.c_int)

user32.SetForegroundWindow.restype = wintypes.BOOL
user32.SetForegroundWindow.argtypes = (wintypes.HWND,)

user32.GetSystemMetrics.restype = ctypes.c_int
user32.GetSystemMetrics.argtypes = (ctypes.c_int,)

user32.AdjustWindowRectEx.restype = wintypes.BOOL
user32.AdjustWindowRectEx.argtypes = (ctypes.POINTER(wintypes.RECT), wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)

user32.BeginPaint.restype = wintypes.HDC
user32.BeginPaint.argtypes = (wintypes.HWND, ctypes.POINTER(PAINTSTRUCT))

user32.EndPaint.restype = wintypes.BOOL
user32.EndPaint.argtypes = (wintypes.HWND, ctypes.POINTER(PAINTSTRUCT))

user32.GetClientRect.restype = wintypes.BOOL
user32.GetClientRect.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.RECT))

user32.FillRect.restype = ctypes.c_int
user32.FillRect.argtypes = (wintypes.HDC, ctypes.POINTER(wintypes.RECT), wintypes.HBRUSH)

user32.DrawTextW.restype = ctypes.c_int
user32.DrawTextW.argtypes = (wintypes.HDC, wintypes.LPCWSTR, ctypes.c_int, ctypes.POINTER(wintypes.RECT), wintypes.UINT)

kernel32.GetModuleHandleW.restype = wintypes.HMODULE
kernel32.GetModuleHandleW.argtypes = (wintypes.LPCWSTR,)

gdi32.CreateSolidBrush.restype = wintypes.HBRUSH
gdi32.CreateSolidBrush.argtypes = (wintypes.DWORD,)

gdi32.DeleteObject.restype = wintypes.BOOL
gdi32.DeleteObject.argtypes = (wintypes.HGDIOBJ,)

gdi32.SetBkMode.restype = ctypes.c_int
gdi32.SetBkMode.argtypes = (wintypes.HDC, ctypes.c_int)

gdi32.StretchDIBits.restype = ctypes.c_int
gdi32.StretchDIBits.argtypes = (
    wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    ctypes.c_void_p, ctypes.c_void_p, wintypes.UINT, wintypes.DWORD,
)


def _build_dib(matrix, scale):
    """Build a top-down 24bpp BGR pixel buffer (row-padded to 4 bytes) from a
    QR module matrix, plus its matching BITMAPINFOHEADER."""
    n = len(matrix)
    w = h = n * scale
    stride = ((w * 3 + 3) // 4) * 4
    buf = bytearray(stride * h)
    for y in range(h):
        row = matrix[y // scale]
        off = y * stride
        for x in range(w):
            if row[x // scale]:
                buf[off:off + 3] = (0, 0, 0)
            else:
                buf[off:off + 3] = (255, 255, 255)
            off += 3

    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = -h  # negative = top-down
    bmi.biPlanes = 1
    bmi.biBitCount = 24
    bmi.biCompression = BI_RGB
    return bytes(buf), bmi, w, h


class QrWindow:
    PADDING = 24
    TOP_TEXT_H = 56
    BOTTOM_TEXT_H = 66

    def __init__(self, title, heading, subheading, url, matrix, scale=8):
        self.title = title
        self.heading = heading
        self.subheading = subheading
        self.url = url
        self.bits, self.bmi, self.image_w, self.image_h = _build_dib(matrix, scale)
        self.hwnd = None
        self._wndproc_ref = WNDPROCTYPE(self._wndproc)

    def _wndproc(self, hwnd, msg, wparam, lparam):
        if msg == WM_PAINT:
            self._paint(hwnd)
            return 0
        if msg == WM_CLOSE:
            user32.DestroyWindow(hwnd)
            return 0
        if msg == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _paint(self, hwnd):
        ps = PAINTSTRUCT()
        hdc = user32.BeginPaint(hwnd, ctypes.byref(ps))
        try:
            client = wintypes.RECT()
            user32.GetClientRect(hwnd, ctypes.byref(client))

            brush = gdi32.CreateSolidBrush(0x00FFFFFF)
            user32.FillRect(hdc, ctypes.byref(client), brush)
            gdi32.DeleteObject(brush)
            gdi32.SetBkMode(hdc, TRANSPARENT_BKMODE)

            top_rect = wintypes.RECT(self.PADDING, 10, client.right - self.PADDING, 10 + self.TOP_TEXT_H)
            text = self.heading + "\n" + self.subheading
            user32.DrawTextW(hdc, text, -1, ctypes.byref(top_rect), DT_CENTER | DT_WORDBREAK | DT_NOPREFIX)

            img_x = (client.right - self.image_w) // 2
            img_y = self.TOP_TEXT_H + 16
            gdi32.StretchDIBits(
                hdc, img_x, img_y, self.image_w, self.image_h,
                0, 0, self.image_w, self.image_h,
                self.bits, ctypes.byref(self.bmi), DIB_RGB_COLORS, SRCCOPY,
            )

            bottom_rect = wintypes.RECT(
                self.PADDING, img_y + self.image_h + 14,
                client.right - self.PADDING, client.bottom - 8,
            )
            user32.DrawTextW(hdc, self.url, -1, ctypes.byref(bottom_rect), DT_CENTER | DT_WORDBREAK | DT_NOPREFIX)
        finally:
            user32.EndPaint(hwnd, ctypes.byref(ps))

    def close(self):
        if self.hwnd:
            user32.PostMessageW(self.hwnd, WM_CLOSE, 0, 0)

    def show(self):
        """Blocking - call on a dedicated thread."""
        hinstance = kernel32.GetModuleHandleW(None)
        class_name = "AirMouseQrWndClass"

        wc = WNDCLASSEXW()
        wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wc.lpfnWndProc = self._wndproc_ref
        wc.hInstance = hinstance
        wc.lpszClassName = class_name
        wc.hbrBackground = gdi32.CreateSolidBrush(0x00FFFFFF)
        user32.RegisterClassExW(ctypes.byref(wc))

        client_w = self.image_w + self.PADDING * 2
        client_h = self.TOP_TEXT_H + self.image_h + self.BOTTOM_TEXT_H + 16

        rect = wintypes.RECT(0, 0, client_w, client_h)
        user32.AdjustWindowRectEx(ctypes.byref(rect), WS_WINDOW, False, 0)
        win_w = rect.right - rect.left
        win_h = rect.bottom - rect.top

        screen_w = user32.GetSystemMetrics(SM_CXSCREEN)
        screen_h = user32.GetSystemMetrics(SM_CYSCREEN)
        x = max(0, (screen_w - win_w) // 2)
        y = max(0, (screen_h - win_h) // 2)

        self.hwnd = user32.CreateWindowExW(
            0, class_name, self.title, WS_WINDOW | WS_VISIBLE,
            x, y, win_w, win_h, None, None, hinstance, None,
        )
        if not self.hwnd:
            return

        user32.ShowWindow(self.hwnd, SW_SHOW)
        user32.SetForegroundWindow(self.hwnd)

        msg = wintypes.MSG()
        while True:
            ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret <= 0:
                break
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
