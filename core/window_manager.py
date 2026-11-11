"""Win32 window discovery and focusing for WEN.

WEN switches to windows that are already open; it never launches anything.
An assignment is a plain dict: {"title", "exe_path", "class_name"} plus an
optional runtime-only "hwnd" that is never written to disk.
"""

import ctypes
import os
from ctypes import wintypes
from dataclasses import dataclass

import pywintypes
import win32api
import win32con
import win32gui
import win32process

_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_DWMWA_CLOAKED = 14
_UWP_FRAME_CLASS = "ApplicationFrameWindow"
_IGNORED_CLASSES = {"Progman", "WorkerW", "Shell_TrayWnd", "Windows.UI.Core.CoreWindow"}

_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_kernel32.OpenProcess.restype = wintypes.HANDLE
_kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
_kernel32.QueryFullProcessImageNameW.argtypes = [
    wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)
]
_kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
_dwmapi = ctypes.WinDLL("dwmapi")


@dataclass(frozen=True)
class WindowInfo:
    hwnd: int
    title: str
    exe_path: str
    class_name: str


def _exe_path(pid: int) -> str:
    handle = _kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return ""  # elevated or protected process
    try:
        buf = ctypes.create_unicode_buffer(32768)
        size = wintypes.DWORD(len(buf))
        if _kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
            return buf.value
        return ""
    finally:
        _kernel32.CloseHandle(handle)


def _is_cloaked(hwnd: int) -> bool:
    cloaked = wintypes.DWORD(0)
    _dwmapi.DwmGetWindowAttribute(
        wintypes.HWND(hwnd), _DWMWA_CLOAKED, ctypes.byref(cloaked), ctypes.sizeof(cloaked)
    )
    return bool(cloaked.value)


def list_windows(exclude_pid=None):
    """Return the user-facing top-level windows, front-most first."""
    if exclude_pid is None:
        exclude_pid = os.getpid()
    results = []

    def callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return True
        title = win32gui.GetWindowText(hwnd)
        if not title or win32gui.GetWindow(hwnd, win32con.GW_OWNER):
            return True
        if win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) & win32con.WS_EX_TOOLWINDOW:
            return True
        class_name = win32gui.GetClassName(hwnd)
        if class_name in _IGNORED_CLASSES:
            return True
        # Suspended Store apps keep an invisible ("cloaked") frame window around.
        if class_name == _UWP_FRAME_CLASS and _is_cloaked(hwnd):
            return True
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if pid == exclude_pid:
            return True
        results.append(WindowInfo(hwnd, title, _exe_path(pid), class_name))
        return True

    win32gui.EnumWindows(callback, None)
    return results


def _same_exe(a: str, b: str) -> bool:
    return bool(a) and os.path.normcase(a) == os.path.normcase(b)


def find_window(assignment, windows=None):
    """Resolve an assignment to a live window handle, or None if it isn't open.

    Order of preference: the handle remembered from this session, then a
    window of the same program with the same title, then the front-most
    window of the same program.
    """
    if windows is None:
        windows = list_windows()
    exe = assignment.get("exe_path", "")
    candidates = [w for w in windows if _same_exe(w.exe_path, exe)]

    hwnd = assignment.get("hwnd")
    if hwnd and any(w.hwnd == hwnd for w in candidates):
        return hwnd

    title = assignment.get("title", "")
    for w in candidates:
        if w.title == title:
            return w.hwnd

    class_name = assignment.get("class_name", "")
    # Every Store app is hosted by the same exe, so only the title tells them apart.
    if class_name == _UWP_FRAME_CLASS:
        return None
    for w in candidates:
        if w.class_name == class_name:
            return w.hwnd
    return candidates[0].hwnd if candidates else None


def focus_window(hwnd: int) -> bool:
    """Restore the window if minimized and bring it to the foreground."""
    try:
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        try:
            win32gui.SetForegroundWindow(hwnd)
        except pywintypes.error:
            # Windows refuses focus changes from a background process; a
            # synthetic Alt key press lifts that restriction.
            win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
            win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
            win32gui.SetForegroundWindow(hwnd)
        return True
    except pywintypes.error:
        return False
