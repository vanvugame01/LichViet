import os
import subprocess
import sys
import zipfile
from pathlib import Path

from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QColor, QImage, QPainter, QPen


ROOT = Path(__file__).resolve().parent.parent


def create_portable_archive(destination, archive):
    temporary = archive.with_suffix(".tmp")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as package:
        for name in ("LichViet.exe", "HUONG-DAN.txt"):
            package.write(destination / name, arcname=f"LichViet/{name}")
        # Goi phan phoi luon rong, khong dua lich ca nhan vao ban public.
        package.writestr("LichViet/lunar_reminders.json", "[]\n")
    temporary.replace(archive)


def create_icon(path):
    image = QImage(256, 256, QImage.Format_ARGB32)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor("#fff7ed"))
    painter.drawRoundedRect(QRectF(4, 4, 248, 248), 48, 48)
    painter.setBrush(Qt.NoBrush)
    pen = QPen(QColor("#b45309"), 13)
    pen.setCapStyle(Qt.RoundCap)
    painter.setPen(pen)
    painter.drawRoundedRect(QRectF(48, 66, 160, 144), 20, 20)
    painter.drawLine(48, 110, 208, 110)
    painter.drawLine(88, 46, 88, 84)
    painter.drawLine(168, 46, 168, 84)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor("#b45309"))
    for x, y in [(85, 146), (128, 146), (171, 146), (85, 181), (128, 181)]:
        painter.drawRoundedRect(QRectF(x - 8, y - 8, 16, 16), 4, 4)
    painter.end()
    if not image.save(str(path), "ICO"):
        raise RuntimeError("Cannot create Windows icon")


def main():
    if sys.platform != "win32":
        raise SystemExit("Build the Windows executable on Windows.")
    build = ROOT / "output" / "build-portable"
    destination = ROOT / "output" / "portable"
    build.mkdir(parents=True, exist_ok=True)
    destination.mkdir(parents=True, exist_ok=True)
    icon = build / "LichViet.ico"
    create_icon(icon)
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    command = [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--onefile", "--windowed",
        "--name", "LichViet", "--icon", str(icon),
        "--add-data", f"{ROOT / 'assets'}:assets",
        "--distpath", str(destination), "--workpath", str(build / "work"),
        "--specpath", str(build), "--noupx", str(ROOT / "main.py"),
    ]
    subprocess.run(command, cwd=ROOT, env=environment, check=True, timeout=600)
    data_file = destination / "lunar_reminders.json"
    if not data_file.exists():
        # Giu nguyen du lieu portable da co; lan dau tao danh sach rong.
        data_file.write_text("[]\n", encoding="utf-8")
    guide = destination / "HUONG-DAN.txt"
    guide.write_text(
        "LỊCH VIỆT — BẢN PORTABLE WINDOWS 64-BIT\n\n"
        "Chạy LichViet.exe, không cần cài Python.\n"
        "Đặt chương trình trong thư mục có quyền ghi, ví dụ Documents hoặc USB.\n"
        "Nhắc việc được lưu ở lunar_reminders.json cạnh LichViet.exe.\n"
        "Khi chuyển máy, chép cả thư mục để giữ nhắc việc.\n"
        "Đóng cửa sổ sẽ ẩn xuống khay hệ thống nếu được hỗ trợ.\n"
        "Chọn menu Thoát để kết thúc; ứng dụng cần đang chạy để nhắc lịch.\n"
        "Khi cập nhật, giữ lại lunar_reminders.json của bạn và chỉ thay file EXE.\n",
        encoding="utf-8-sig",
    )
    archive = ROOT / "output" / "LichViet-Portable-Windows-x64.zip"
    create_portable_archive(destination, archive)
    print(f"Executable: {destination / 'LichViet.exe'}")
    print(f"Archive: {archive}")


if __name__ == "__main__":
    main()
