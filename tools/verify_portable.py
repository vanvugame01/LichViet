import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parent.parent


def find_window(executable):
    user = ctypes.WinDLL("user32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user.GetWindowThreadProcessId.restype = wintypes.DWORD
    user.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    found = []

    @callback_type
    def visit(handle, _):
        title = ctypes.create_unicode_buffer(256)
        user.GetWindowTextW(handle, title, 256)
        if title.value != "Lịch Việt":
            return True
        process_id = wintypes.DWORD()
        thread_id = user.GetWindowThreadProcessId(handle, ctypes.byref(process_id))
        process = kernel.OpenProcess(0x1000, False, process_id.value)
        if not process:
            return True
        try:
            path = ctypes.create_unicode_buffer(32768)
            length = wintypes.DWORD(len(path))
            if kernel.QueryFullProcessImageNameW(process, 0, path, ctypes.byref(length)) and Path(path.value) == executable:
                rectangle = wintypes.RECT()
                user.GetWindowRect(handle, ctypes.byref(rectangle))
                found.append(dict(title=title.value, process_id=process_id.value, thread_id=thread_id,
                                  width=rectangle.right - rectangle.left, height=rectangle.bottom - rectangle.top))
        finally:
            kernel.CloseHandle(process)
        return True

    user.EnumWindows(callback_type(visit), 0)
    return found


def main():
    if os.name != "nt":
        raise SystemExit("This verification requires Windows.")
    output = ROOT / "output"
    with tempfile.TemporaryDirectory(prefix="lichviet-portable-") as temporary:
        directory = Path(temporary) / "Lịch Việt portable"
        directory.mkdir()
        executable = directory / "LichViet.exe"
        shutil.copy2(output / "portable" / "LichViet.exe", executable)
        # Thu EXE rieng, khong dua Python, QSS hoac du lieu that vao thu muc nay.
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        environment = os.environ.copy()
        for key in ("PYTHONHOME", "PYTHONPATH", "QT_QPA_PLATFORM", "QT_PLUGIN_PATH"):
            environment.pop(key, None)
        process = subprocess.Popen([str(executable)], cwd=temporary, env=environment, startupinfo=startup)
        window = None
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError(f"Executable exited early: {process.returncode}")
                windows = find_window(executable)
                if windows:
                    window = windows[0]
                    break
                time.sleep(0.25)
            if window is None:
                raise RuntimeError("Main application window did not initialize within 30 seconds")
            time.sleep(1)
            if process.poll() is not None:
                raise RuntimeError("Executable stopped after startup")
            # Gui ket thuc vong lap chi den luong cua tien trinh thu nghiem.
            ctypes.windll.user32.PostThreadMessageW(window["thread_id"], 0x0012, 0, 0)
            code = process.wait(timeout=10)
            if code != 0:
                raise RuntimeError(f"Executable did not exit cleanly: {code}")
            report = dict(executable_started=True, standalone_exe_only=True,
                          unicode_path=True, different_working_directory=True,
                          window=window, exit_code=code)
            (output / "portable-verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps(report, ensure_ascii=True))
        finally:
            if process.poll() is None:
                if window is not None:
                    subprocess.run(["taskkill", "/PID", str(window["process_id"]), "/T", "/F"], capture_output=True, timeout=10)
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=10)


if __name__ == "__main__":
    main()
