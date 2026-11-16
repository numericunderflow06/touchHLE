"""Capture a window of another process from the outside (Windows only).

This is a fallback for builds without the control interface, and a way to
double-check what is really on screen. Normal runs should use the control
interface's `screenshot` command instead.

usage: python winshot.py <pid> <out.png>
"""

import ctypes
import ctypes.wintypes as wt
import sys

from PIL import Image

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

PW_CLIENTONLY = 1
PW_RENDERFULLCONTENT = 2


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG),
        ("biPlanes", wt.WORD), ("biBitCount", wt.WORD), ("biCompression", wt.DWORD),
        ("biSizeImage", wt.DWORD), ("biXPelsPerMeter", wt.LONG), ("biYPelsPerMeter", wt.LONG),
        ("biClrUsed", wt.DWORD), ("biClrImportant", wt.DWORD),
    ]


def windows_of(pid):
    """Visible top-level windows of a process: [(hwnd, title, (w, h))]."""
    found = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def callback(hwnd, _):
        owner = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid and user32.IsWindowVisible(hwnd):
            title = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, title, 256)
            rect = wt.RECT()
            user32.GetClientRect(hwnd, ctypes.byref(rect))
            found.append((hwnd, title.value, (rect.right, rect.bottom)))
        return True

    user32.EnumWindows(callback, 0)
    return found


def capture(hwnd):
    rect = wt.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    width, height = rect.right, rect.bottom
    if width <= 0 or height <= 0:
        raise RuntimeError("window has no client area")
    window_dc = user32.GetDC(hwnd)
    mem_dc = gdi32.CreateCompatibleDC(window_dc)
    bitmap = gdi32.CreateCompatibleBitmap(window_dc, width, height)
    gdi32.SelectObject(mem_dc, bitmap)
    user32.PrintWindow(hwnd, mem_dc, PW_CLIENTONLY | PW_RENDERFULLCONTENT)
    header = BITMAPINFOHEADER()
    header.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    header.biWidth, header.biHeight = width, -height  # top-down
    header.biPlanes, header.biBitCount = 1, 32
    buffer = ctypes.create_string_buffer(width * height * 4)
    gdi32.GetDIBits(mem_dc, bitmap, 0, height, buffer, ctypes.byref(header), 0)
    gdi32.DeleteObject(bitmap)
    gdi32.DeleteDC(mem_dc)
    user32.ReleaseDC(hwnd, window_dc)
    return Image.frombuffer("RGBA", (width, height), buffer, "raw", "BGRA", 0, 1).convert("RGB")


def capture_pid(pid, out_path):
    windows = [w for w in windows_of(pid) if w[2][0] > 0]
    if not windows:
        raise RuntimeError(f"process {pid} has no visible window")
    # The game window is the largest one (a console or message box may exist).
    hwnd, title, size = max(windows, key=lambda w: w[2][0] * w[2][1])
    image = capture(hwnd)
    image.save(out_path)
    return {"title": title, "size": list(size), "path": str(out_path)}


if __name__ == "__main__":
    import json

    print(json.dumps(capture_pid(int(sys.argv[1]), sys.argv[2])))
