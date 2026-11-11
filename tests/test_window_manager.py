"""Matching rules for resolving a saved assignment to a live window.

Run from the repo root:  python -m pytest tests
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.window_manager import WindowInfo, find_window, list_windows

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
HOST = r"C:\Windows\System32\ApplicationFrameHost.exe"

WINDOWS = [
    WindowInfo(10, "Inbox - Google Chrome", CHROME, "Chrome_WidgetWin_1"),
    WindowInfo(11, "Docs - Google Chrome", CHROME, "Chrome_WidgetWin_1"),
    WindowInfo(20, "Calculator", HOST, "ApplicationFrameWindow"),
    WindowInfo(30, "notes.txt - Notepad", r"C:\Windows\notepad.exe", "Notepad"),
]


def test_exact_title_wins_over_window_order():
    a = {"title": "Docs - Google Chrome", "exe_path": CHROME, "class_name": "Chrome_WidgetWin_1"}
    assert find_window(a, WINDOWS) == 11


def test_remembered_handle_wins_over_title():
    a = {"title": "Inbox - Google Chrome", "exe_path": CHROME,
         "class_name": "Chrome_WidgetWin_1", "hwnd": 11}
    assert find_window(a, WINDOWS) == 11


def test_stale_handle_is_ignored():
    a = {"title": "Docs - Google Chrome", "exe_path": CHROME,
         "class_name": "Chrome_WidgetWin_1", "hwnd": 30}  # now belongs to Notepad
    assert find_window(a, WINDOWS) == 11


def test_changed_title_falls_back_to_front_most_window_of_same_program():
    a = {"title": "Old tab - Google Chrome", "exe_path": CHROME, "class_name": "Chrome_WidgetWin_1"}
    assert find_window(a, WINDOWS) == 10


def test_exe_path_comparison_ignores_case():
    a = {"title": "x", "exe_path": r"c:\windows\NOTEPAD.EXE", "class_name": "Notepad"}
    assert find_window(a, WINDOWS) == 30


def test_program_not_running():
    a = {"title": "x", "exe_path": r"C:\nope.exe", "class_name": "Nope"}
    assert find_window(a, WINDOWS) is None


def test_store_apps_match_on_title_only():
    settings = {"title": "Settings", "exe_path": HOST, "class_name": "ApplicationFrameWindow"}
    calculator = {"title": "Calculator", "exe_path": HOST, "class_name": "ApplicationFrameWindow"}
    assert find_window(settings, WINDOWS) is None
    assert find_window(calculator, WINDOWS) == 20


def test_list_windows_returns_usable_entries():
    windows = list_windows()
    assert all(w.title and w.hwnd for w in windows)
