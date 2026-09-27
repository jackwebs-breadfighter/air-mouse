"""
Low-level Windows input simulation via the Win32 SendInput API.

Uses ctypes directly (no pyautogui) to avoid its fail-safe corner-abort
behavior and its polling-based delays, which are unnecessary overhead
for a low-latency remote trackpad.
"""

import ctypes
from ctypes import wintypes
import struct

user32 = ctypes.WinDLL("user32", use_last_error=True)

ULONG_PTR = wintypes.WPARAM  # same width as ULONG_PTR on both 32/64-bit


class MOUSEINPUT(ctypes.Structure):
    _fields_ = (
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    )


class KEYBDINPUT(ctypes.Structure):
    _fields_ = (
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    )


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = (
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    )


class _INPUTUNION(ctypes.Union):
    _fields_ = (
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    )


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = (
        ("type", wintypes.DWORD),
        ("u", _INPUTUNION),
    )


SendInput = user32.SendInput
SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
SendInput.restype = wintypes.UINT

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_HWHEEL = 0x1000

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004

WHEEL_DELTA = 120

_BUTTON_DOWN = {
    "left": MOUSEEVENTF_LEFTDOWN,
    "right": MOUSEEVENTF_RIGHTDOWN,
    "middle": MOUSEEVENTF_MIDDLEDOWN,
}
_BUTTON_UP = {
    "left": MOUSEEVENTF_LEFTUP,
    "right": MOUSEEVENTF_RIGHTUP,
    "middle": MOUSEEVENTF_MIDDLEUP,
}

# Keys whose scan code lives on the extended keypad (per SendInput docs).
_EXTENDED_KEYS = {
    "left", "right", "up", "down", "home", "end", "pageup", "pagedown",
    "insert", "delete", "numlock", "rctrl", "ralt",
}

VK_CODES = {
    "enter": 0x0D,
    "backspace": 0x08,
    "esc": 0x1B,
    "escape": 0x1B,
    "tab": 0x09,
    "space": 0x20,
    "delete": 0x2E,
    "insert": 0x2D,
    "home": 0x24,
    "end": 0x23,
    "pageup": 0x21,
    "pagedown": 0x22,
    "up": 0x26,
    "down": 0x28,
    "left": 0x25,
    "right": 0x27,
    "win": 0x5B,
    "lwin": 0x5B,
    "rwin": 0x5C,
    "ctrl": 0x11,
    "control": 0x11,
    "rctrl": 0xA3,
    "alt": 0x12,
    "ralt": 0xA5,
    "shift": 0x10,
    "capslock": 0x14,
    "numlock": 0x90,
    "printscreen": 0x2C,
}
for _i in range(1, 13):
    VK_CODES[f"f{_i}"] = 0x6F + _i  # F1 = 0x70 ... F12 = 0x7B

_MEDIA_VK = {
    "vol_up": 0xAF,
    "vol_down": 0xAE,
    "mute": 0xAD,
    "next": 0xB0,
    "prev": 0xB1,
    "play_pause": 0xB3,
}


def _send(inp: INPUT) -> None:
    SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def _vk_for(key: str):
    key = key.lower()
    if key in VK_CODES:
        return VK_CODES[key]
    if len(key) == 1:
        c = key.upper()
        if ("A" <= c <= "Z") or ("0" <= c <= "9"):
            return ord(c)
    return None


def _key_event(vk: int, key_up: bool) -> None:
    flags = KEYEVENTF_KEYUP if key_up else 0
    name = next((n for n, v in VK_CODES.items() if v == vk), "")
    if name in _EXTENDED_KEYS:
        flags |= KEYEVENTF_EXTENDEDKEY
    ki = KEYBDINPUT(vk, 0, flags, 0, 0)
    _send(INPUT(type=INPUT_KEYBOARD, ki=ki))


# ---- Mouse -----------------------------------------------------------------

def mouse_move(dx: float, dy: float) -> None:
    dx, dy = int(round(dx)), int(round(dy))
    if dx == 0 and dy == 0:
        return
    mi = MOUSEINPUT(dx, dy, 0, MOUSEEVENTF_MOVE, 0, 0)
    _send(INPUT(type=INPUT_MOUSE, mi=mi))


def mouse_down(button: str = "left") -> None:
    flag = _BUTTON_DOWN.get(button)
    if flag is None:
        return
    _send(INPUT(type=INPUT_MOUSE, mi=MOUSEINPUT(0, 0, 0, flag, 0, 0)))


def mouse_up(button: str = "left") -> None:
    flag = _BUTTON_UP.get(button)
    if flag is None:
        return
    _send(INPUT(type=INPUT_MOUSE, mi=MOUSEINPUT(0, 0, 0, flag, 0, 0)))


def mouse_click(button: str = "left") -> None:
    mouse_down(button)
    mouse_up(button)


def scroll(dx: float = 0, dy: float = 0) -> None:
    if dy:
        amount = int(round(dy * WHEEL_DELTA))
        _send(INPUT(type=INPUT_MOUSE, mi=MOUSEINPUT(0, 0, amount, MOUSEEVENTF_WHEEL, 0, 0)))
    if dx:
        amount = int(round(dx * WHEEL_DELTA))
        _send(INPUT(type=INPUT_MOUSE, mi=MOUSEINPUT(0, 0, amount, MOUSEEVENTF_HWHEEL, 0, 0)))


# ---- Keyboard ----------------------------------------------------------------

def type_text(text: str) -> None:
    """Type arbitrary text (including CJK and emoji) via Unicode key events."""
    if not text:
        return
    encoded = text.encode("utf-16-le")
    units = struct.unpack(f"<{len(encoded) // 2}H", encoded)
    for unit in units:
        down = KEYBDINPUT(0, unit, KEYEVENTF_UNICODE, 0, 0)
        up = KEYBDINPUT(0, unit, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, 0)
        _send(INPUT(type=INPUT_KEYBOARD, ki=down))
        _send(INPUT(type=INPUT_KEYBOARD, ki=up))


def press_key(name: str) -> None:
    """Press and release a single named key (see VK_CODES / single chars)."""
    vk = _vk_for(name)
    if vk is None:
        return
    _key_event(vk, False)
    _key_event(vk, True)


def key_combo(names) -> None:
    """Hold a list of keys in order, then release in reverse order."""
    vks = [v for v in (_vk_for(n) for n in names) if v is not None]
    for vk in vks:
        _key_event(vk, False)
    for vk in reversed(vks):
        _key_event(vk, True)


def media_key(name: str) -> None:
    vk = _MEDIA_VK.get(name)
    if vk is None:
        return
    _key_event(vk, False)
    _key_event(vk, True)


if __name__ == "__main__":
    import time

    print("Moving mouse in a small square...")
    for dx, dy in ((80, 0), (0, 80), (-80, 0), (0, -80)):
        mouse_move(dx, dy)
        time.sleep(0.2)

    print("Typing test text (open Notepad now)...")
    time.sleep(3)
    type_text("測試ABC 123 🎉\n")
    key_combo(["ctrl", "a"])
