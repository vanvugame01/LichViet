import json
import sys
from datetime import date
from pathlib import Path

import lunarcalendar
from PyQt5.QtCore import QDate, QPoint, QTime, QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QCursor, QIcon
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSystemTrayIcon,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)


WEEKDAY_VI = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
CAN = ["Giáp", "Ất", "Bính", "Đinh", "Mậu", "Kỷ", "Canh", "Tân", "Nhâm", "Quý"]
CHI = ["Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]


class DayCell(QFrame):
    clicked = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self._day = None
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMinimumHeight(38)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        self.solar_label = QLabel("1")
        self.solar_label.setAlignment(Qt.AlignCenter)

        self.lunar_label = QLabel("1")
        self.lunar_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.solar_label)
        layout.addWidget(self.lunar_label)

    def set_day(self, day: date, lunar_text: str, in_month: bool, is_sunday: bool, is_selected: bool):
        self._day = day
        self.solar_label.setText(str(day.day))
        self.lunar_label.setText(lunar_text)

        solar_color = "#111827"
        lunar_color = "#111827"
        border = "transparent"
        bg = "transparent"

        if not in_month:
            solar_color = "#c9ced6"
            lunar_color = "#d5d8de"
        else:
            if is_sunday:
                solar_color = "#c25a12"
            if lunar_text.startswith("1/"):
                lunar_color = "#c25a12"
            else:
                lunar_color = "#20242a"

        if is_selected:
            border = "#d97706"
            bg = "#fff8ee"

        self.setStyleSheet(
            f"QFrame {{border: 1px solid {border}; border-radius: 8px; background-color: {bg};}}"
        )
        self.solar_label.setStyleSheet(
            f"border: none; font-size: 12px; font-weight: 600; color: {solar_color}; background: transparent;"
        )
        self.lunar_label.setStyleSheet(
            f"border: none; font-size: 9px; color: {lunar_color}; background: transparent;"
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._day is not None:
            self.clicked.emit(self._day)
        super().mousePressEvent(event)


class DashboardWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lịch Việt")
        self.setGeometry(260, 40, 300, 400)
        self.setFixedSize(300, 400)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)

        self.drag_position = QPoint()
        self.current_month = QDate.currentDate().addDays(1 - QDate.currentDate().day())
        self.selected_date = QDate.currentDate().toPyDate()

        self.reminders_file = Path(__file__).with_name("lunar_reminders.json")
        self.reminders = []

        self.setStyleSheet(
            """
            QWidget {
                background-color: #f3f4f6;
                color: #111827;
                font-family: Segoe UI;
            }
            QLabel {
                background: transparent;
            }
            #monthTitle {
                font-size: 14px;
                font-weight: 700;
                color: #111827;
            }
            #weekdayHeader {
                font-size: 10px;
                color: #0f172a;
                font-weight: 500;
            }
            #sundayHeader {
                color: #c25a12;
            }
            #titleLabel {
                font-size: 13px;
                font-weight: 700;
                color: #5b5146;
                letter-spacing: 1px;
            }
            #navButton {
                font-size: 18px;
                min-width: 28px;
                max-width: 28px;
                min-height: 28px;
                max-height: 28px;
                border-radius: 9px;
                border: 1px solid #111827;
                background-color: #ffffff;
            }
            #navButton:hover {
                background-color: #f8fafc;
            }
            #capsuleBox {
                border: 1px solid #d1d5db;
                border-radius: 14px;
                background: #ffffff;
            }
            #capsuleButton {
                font-size: 12px;
                font-weight: 600;
                border: none;
                background: transparent;
                min-width: 22px;
                min-height: 20px;
                color: #0f172a;
            }
            #capsuleButton:hover {
                color: #000000;
            }
            #divider {
                background-color: #e5e7eb;
            }
            #bottomWeekday {
                font-size: 11px;
                font-weight: 600;
                color: #111827;
            }
            #bottomDay {
                font-size: 38px;
                font-weight: 700;
                color: #046c4e;
            }
            #bottomMonth {
                font-size: 11px;
                font-weight: 600;
                color: #111827;
            }
            #bottomType {
                font-size: 10px;
                color: #374151;
                font-weight: 600;
            }
            #badge {
                border: 1px solid #6b7280;
                border-radius: 8px;
                padding: 3px 6px;
                font-size: 10px;
                color: #4b5563;
                background-color: #ffffff;
            }
            #detailMain {
                font-size: 12px;
                font-weight: 700;
                color: #111827;
            }
            #detailSub {
                font-size: 10px;
                color: #1f2937;
                font-weight: 600;
            }
            #detailFoot {
                font-size: 9px;
                color: #374151;
                font-weight: 500;
            }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(5)

        top_row = QHBoxLayout()
        top_row.setSpacing(5)

        self.title_label = QLabel("LỊCH VIỆT")
        self.title_label.setObjectName("titleLabel")

        capsule = QFrame()
        capsule.setObjectName("capsuleBox")
        capsule_layout = QHBoxLayout(capsule)
        capsule_layout.setContentsMargins(3, 3, 3, 3)
        capsule_layout.setSpacing(0)

        self.menu_button = QPushButton("•••")
        self.menu_button.setObjectName("capsuleButton")
        self.menu_button.clicked.connect(self.show_window_menu)

        line = QFrame()
        line.setObjectName("divider")
        line.setFixedWidth(1)

        self.close_button = QPushButton("×")
        self.close_button.setObjectName("capsuleButton")
        self.close_button.clicked.connect(self.hide_to_tray)

        capsule_layout.addWidget(self.menu_button)
        capsule_layout.addWidget(line)
        capsule_layout.addWidget(self.close_button)

        top_row.addWidget(self.title_label)
        top_row.addStretch()
        top_row.addWidget(capsule)

        nav_row = QHBoxLayout()
        nav_row.setSpacing(6)

        self.prev_button = QPushButton("‹")
        self.prev_button.setObjectName("navButton")
        self.prev_button.clicked.connect(self.prev_month)

        self.month_label = QLabel()
        self.month_label.setObjectName("monthTitle")
        self.month_label.setAlignment(Qt.AlignCenter)

        self.next_button = QPushButton("›")
        self.next_button.setObjectName("navButton")
        self.next_button.clicked.connect(self.next_month)

        nav_row.addWidget(self.prev_button)
        nav_row.addStretch()
        nav_row.addWidget(self.month_label)
        nav_row.addStretch()
        nav_row.addWidget(self.next_button)

        weekday_row = QHBoxLayout()
        weekday_row.setSpacing(2)
        for idx, wd in enumerate(["T2", "T3", "T4", "T5", "T6", "T7", "CN"]):
            wd_label = QLabel(wd)
            wd_label.setAlignment(Qt.AlignCenter)
            wd_label.setObjectName("weekdayHeader")
            if idx == 6:
                wd_label.setObjectName("sundayHeader")
                wd_label.setStyleSheet("font-size: 10px; color: #c25a12; font-weight: 500;")
            weekday_row.addWidget(wd_label)

        grid_wrap = QFrame()
        grid = QGridLayout(grid_wrap)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(2)
        grid.setVerticalSpacing(2)

        self.cells = []
        for row in range(6):
            for col in range(7):
                cell = DayCell()
                cell.clicked.connect(self.select_date)
                self.cells.append(cell)
                grid.addWidget(cell, row, col)

        top_divider = QFrame()
        top_divider.setObjectName("divider")
        top_divider.setFixedHeight(1)

        bottom = QHBoxLayout()
        bottom.setSpacing(6)

        left_col = QVBoxLayout()
        left_col.setSpacing(2)
        self.left_weekday = QLabel()
        self.left_weekday.setObjectName("bottomWeekday")
        self.left_weekday.setAlignment(Qt.AlignCenter)

        self.left_day = QLabel()
        self.left_day.setObjectName("bottomDay")
        self.left_day.setAlignment(Qt.AlignCenter)

        self.left_month = QLabel()
        self.left_month.setObjectName("bottomMonth")
        self.left_month.setAlignment(Qt.AlignCenter)

        self.left_type = QLabel("Dương lịch")
        self.left_type.setObjectName("bottomType")
        self.left_type.setAlignment(Qt.AlignCenter)

        left_col.addWidget(self.left_weekday)
        left_col.addWidget(self.left_day)
        left_col.addWidget(self.left_month)
        left_col.addWidget(self.left_type)

        vline = QFrame()
        vline.setObjectName("divider")
        vline.setFixedWidth(1)

        right_col = QVBoxLayout()
        right_col.setSpacing(2)

        self.badge = QLabel("Âm lịch")
        self.badge.setObjectName("badge")
        self.badge.setAlignment(Qt.AlignCenter)

        self.detail_main = QLabel()
        self.detail_main.setObjectName("detailMain")
        self.detail_sub = QLabel()
        self.detail_sub.setObjectName("detailSub")

        detail_divider = QFrame()
        detail_divider.setObjectName("divider")
        detail_divider.setFixedHeight(1)

        self.detail_foot = QLabel()
        self.detail_foot.setWordWrap(True)
        self.detail_foot.setObjectName("detailFoot")

        right_col.addWidget(self.badge, alignment=Qt.AlignLeft)
        right_col.addWidget(self.detail_main)
        right_col.addWidget(self.detail_sub)
        right_col.addWidget(detail_divider)
        right_col.addWidget(self.detail_foot)
        right_col.addStretch()

        bottom.addLayout(left_col, 2)
        bottom.addWidget(vline)
        bottom.addLayout(right_col, 3)

        root.addLayout(top_row)
        root.addLayout(nav_row)
        root.addLayout(weekday_row)
        root.addWidget(grid_wrap)
        root.addWidget(top_divider)
        root.addLayout(bottom)

        self.tray_icon = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(QIcon("icon.png"))
            self.tray_icon.activated.connect(self.tray_icon_activated)

            tray_menu = QMenu()
            restore_action = QAction("Hiển thị", self)
            restore_action.triggered.connect(self.restore_window)
            add_action = QAction("Hẹn lịch âm", self)
            add_action.triggered.connect(self.add_reminder_dialog)
            exit_action = QAction("Thoát", self)
            exit_action.triggered.connect(self.quit_app)
            tray_menu.addAction(restore_action)
            tray_menu.addAction(add_action)
            tray_menu.addAction(exit_action)
            self.tray_icon.setContextMenu(tray_menu)

        self.load_reminders()
        self.reminder_timer = QTimer(self)
        self.reminder_timer.setInterval(30_000)
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start()

        self.update_calendar()
        self.check_reminders()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and not self.drag_position.isNull():
            self.move(event.globalPos() - self.drag_position)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.drag_position = QPoint()
        super().mouseReleaseEvent(event)

    def closeEvent(self, event):
        if self.tray_icon is not None:
            event.ignore()
            self.hide_to_tray(show_tip=False)
            return
        super().closeEvent(event)

    def tray_icon_activated(self, reason):
        if reason in (QSystemTrayIcon.DoubleClick, QSystemTrayIcon.Trigger):
            self.restore_window()

    def restore_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def hide_to_tray(self, show_tip=True):
        if self.tray_icon is None:
            self.showMinimized()
            return
        self.hide()
        if not self.tray_icon.isVisible():
            self.tray_icon.show()
        if show_tip:
            self.tray_icon.showMessage("Lịch Việt", "Ứng dụng đã ẩn xuống khay hệ thống.", QSystemTrayIcon.Information, 3000)

    def show_window_menu(self):
        menu = QMenu(self)
        reset_today = menu.addAction("Về hôm nay")
        add_reminder = menu.addAction("Hẹn lịch âm")
        manage_reminders = menu.addAction("Quản lý nhắc lịch")
        if self.tray_icon is not None:
            to_tray = menu.addAction("Ẩn xuống khay hệ thống")
        else:
            to_tray = None
        quit_action = menu.addAction("Thoát")

        chosen = menu.exec_(QCursor.pos())
        if chosen == reset_today:
            self.current_month = QDate.currentDate().addDays(1 - QDate.currentDate().day())
            self.selected_date = QDate.currentDate().toPyDate()
            self.update_calendar()
        elif chosen == add_reminder:
            self.add_reminder_dialog()
        elif chosen == manage_reminders:
            self.manage_reminders_dialog()
        elif to_tray is not None and chosen == to_tray:
            self.hide_to_tray()
        elif chosen == quit_action:
            self.quit_app()

    def quit_app(self):
        if self.tray_icon is not None:
            self.tray_icon.hide()
        QApplication.instance().quit()

    def prev_month(self):
        self.current_month = self.current_month.addMonths(-1)
        if self.selected_date.month != self.current_month.month() or self.selected_date.year != self.current_month.year():
            self.selected_date = date(self.current_month.year(), self.current_month.month(), 1)
        self.update_calendar()

    def next_month(self):
        self.current_month = self.current_month.addMonths(1)
        if self.selected_date.month != self.current_month.month() or self.selected_date.year != self.current_month.year():
            self.selected_date = date(self.current_month.year(), self.current_month.month(), 1)
        self.update_calendar()

    def select_date(self, selected: date):
        self.selected_date = selected
        self.current_month = QDate(selected.year, selected.month, 1)
        self.update_calendar()

    @staticmethod
    def zodiac_year_name(year: int) -> str:
        return f"{CAN[(year + 6) % 10]} {CHI[(year + 8) % 12]}"

    def update_detail(self):
        lunar = lunarcalendar.Lunar.from_date(self.selected_date)
        weekday_name = WEEKDAY_VI[self.selected_date.weekday()]

        self.left_weekday.setText(weekday_name)
        self.left_day.setText(str(self.selected_date.day))
        self.left_month.setText(f"Tháng {self.selected_date.month} {self.selected_date.year}")

        self.detail_main.setText(f"Ngày {lunar.day} Tháng {lunar.month}")
        self.detail_sub.setText(f"Năm {self.zodiac_year_name(lunar.year)} Âm lịch")
        self.detail_foot.setText(
            f"Dương lịch: {self.selected_date.day:02d}/{self.selected_date.month:02d}/{self.selected_date.year}\n"
            f"Âm lịch: {lunar.day:02d}/{lunar.month:02d}/{lunar.year}"
        )

    def update_calendar(self):
        self.month_label.setText(f"THÁNG {self.current_month.month()}, {self.current_month.year()}")

        first_day = QDate(self.current_month.year(), self.current_month.month(), 1)
        start = first_day.addDays(-(first_day.dayOfWeek() - 1))

        for idx, cell in enumerate(self.cells):
            qd = start.addDays(idx)
            dt = qd.toPyDate()
            lunar = lunarcalendar.Lunar.from_date(dt)

            if lunar.day == 1:
                lunar_text = f"1/{lunar.month}"
            else:
                lunar_text = str(lunar.day)

            in_month = qd.month() == self.current_month.month() and qd.year() == self.current_month.year()
            is_sunday = qd.dayOfWeek() == 7
            is_selected = dt == self.selected_date
            cell.set_day(dt, lunar_text, in_month, is_sunday, is_selected)

        self.update_detail()

    def load_reminders(self):
        self.reminders = []
        if not self.reminders_file.exists():
            return
        try:
            data = json.loads(self.reminders_file.read_text(encoding="utf-8"))
            if isinstance(data, list):
                for item in data:
                    if not isinstance(item, dict):
                        continue
                    self.reminders.append(
                        {
                            "title": str(item.get("title", "Nhắc lịch âm")),
                            "lunar_day": int(item.get("lunar_day", 1)),
                            "lunar_month": int(item.get("lunar_month", 1)),
                            "lunar_year": item.get("lunar_year"),
                            "hour": int(item.get("hour", 8)),
                            "minute": int(item.get("minute", 0)),
                            "repeat_yearly": bool(item.get("repeat_yearly", True)),
                            "enabled": bool(item.get("enabled", True)),
                            "last_triggered_date": item.get("last_triggered_date"),
                        }
                    )
        except Exception:
            self.reminders = []

    def save_reminders(self):
        try:
            self.reminders_file.write_text(json.dumps(self.reminders, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def add_reminder_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Hẹn lịch âm")
        dialog.setStyleSheet("font-size: 12px;")

        layout = QFormLayout(dialog)

        title_edit = QLineEdit("Nhắc việc")

        day_spin = QSpinBox()
        day_spin.setRange(1, 30)
        day_spin.setValue(1)

        month_spin = QSpinBox()
        month_spin.setRange(1, 12)
        month_spin.setValue(1)

        current_lunar = lunarcalendar.Lunar.from_date(date.today())
        year_spin = QSpinBox()
        year_spin.setRange(1900, 2200)
        year_spin.setValue(current_lunar.year)

        repeat_yearly = QCheckBox("Lặp hằng năm")
        repeat_yearly.setChecked(True)
        year_spin.setEnabled(False)
        repeat_yearly.toggled.connect(lambda checked: year_spin.setEnabled(not checked))

        time_edit = QTimeEdit()
        time_edit.setDisplayFormat("HH:mm")
        time_edit.setTime(QTime(8, 0))

        layout.addRow("Tiêu đề", title_edit)
        layout.addRow("Ngày âm", day_spin)
        layout.addRow("Tháng âm", month_spin)
        layout.addRow("Năm âm", year_spin)
        layout.addRow("Nhắc lúc", time_edit)
        layout.addRow("", repeat_yearly)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addRow(buttons)

        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        if dialog.exec_() != QDialog.Accepted:
            return

        title = title_edit.text().strip() or "Nhắc lịch âm"
        reminder = {
            "title": title,
            "lunar_day": day_spin.value(),
            "lunar_month": month_spin.value(),
            "lunar_year": None if repeat_yearly.isChecked() else year_spin.value(),
            "hour": time_edit.time().hour(),
            "minute": time_edit.time().minute(),
            "repeat_yearly": repeat_yearly.isChecked(),
            "enabled": True,
            "last_triggered_date": None,
        }
        self.reminders.append(reminder)
        self.save_reminders()
        self.check_reminders()

    def _reminder_line(self, reminder):
        repeat = "Hằng năm" if reminder.get("repeat_yearly", True) else f"Năm {reminder.get('lunar_year', '-') }"
        state = "Bật" if reminder.get("enabled", True) else "Tắt"
        return (
            f"{reminder.get('title', 'Nhắc lịch âm')} | "
            f"Âm {reminder.get('lunar_day', 1):02d}/{reminder.get('lunar_month', 1):02d} | "
            f"{reminder.get('hour', 8):02d}:{reminder.get('minute', 0):02d} | {repeat} | {state}"
        )

    def manage_reminders_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Quản lý nhắc lịch âm")
        dialog.resize(420, 260)

        layout = QVBoxLayout(dialog)
        reminder_list = QListWidget()

        for reminder in self.reminders:
            reminder_list.addItem(QListWidgetItem(self._reminder_line(reminder)))

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Thêm")
        toggle_btn = QPushButton("Bật/Tắt")
        del_btn = QPushButton("Xóa")
        close_btn = QPushButton("Đóng")

        btn_row.addWidget(add_btn)
        btn_row.addWidget(toggle_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)

        layout.addWidget(reminder_list)
        layout.addLayout(btn_row)

        def refresh_list():
            reminder_list.clear()
            for rem in self.reminders:
                reminder_list.addItem(QListWidgetItem(self._reminder_line(rem)))

        def add_item():
            self.add_reminder_dialog()
            refresh_list()

        def toggle_item():
            row = reminder_list.currentRow()
            if row < 0 or row >= len(self.reminders):
                return
            self.reminders[row]["enabled"] = not self.reminders[row].get("enabled", True)
            self.save_reminders()
            refresh_list()

        def del_item():
            row = reminder_list.currentRow()
            if row < 0 or row >= len(self.reminders):
                return
            self.reminders.pop(row)
            self.save_reminders()
            refresh_list()

        add_btn.clicked.connect(add_item)
        toggle_btn.clicked.connect(toggle_item)
        del_btn.clicked.connect(del_item)
        close_btn.clicked.connect(dialog.accept)

        dialog.exec_()

    def notify_reminder(self, reminder, lunar_today):
        message = (
            f"{reminder.get('title', 'Nhắc lịch âm')}\n"
            f"Hôm nay âm lịch {lunar_today.day:02d}/{lunar_today.month:02d}/{lunar_today.year}."
        )
        if self.tray_icon is not None:
            if not self.tray_icon.isVisible():
                self.tray_icon.show()
            self.tray_icon.showMessage("Nhắc lịch âm", message, QSystemTrayIcon.Information, 10000)
        QMessageBox.information(self, "Nhắc lịch âm", message)

    def check_reminders(self):
        if not self.reminders:
            return

        today = date.today()
        now = QTime.currentTime()
        lunar_today = lunarcalendar.Converter.Solar2Lunar(lunarcalendar.Solar(today.year, today.month, today.day))
        today_key = today.isoformat()

        changed = False
        for reminder in self.reminders:
            if not reminder.get("enabled", True):
                continue
            if reminder.get("lunar_day") != lunar_today.day or reminder.get("lunar_month") != lunar_today.month:
                continue
            if (not reminder.get("repeat_yearly", True)) and reminder.get("lunar_year") != lunar_today.year:
                continue

            target_hour = int(reminder.get("hour", 8))
            target_minute = int(reminder.get("minute", 0))
            if (now.hour(), now.minute()) < (target_hour, target_minute):
                continue
            if reminder.get("last_triggered_date") == today_key:
                continue

            self.notify_reminder(reminder, lunar_today)
            reminder["last_triggered_date"] = today_key
            if not reminder.get("repeat_yearly", True):
                reminder["enabled"] = False
            changed = True

        if changed:
            self.save_reminders()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    widget = DashboardWidget()
    widget.show()
    if widget.tray_icon is not None:
        widget.tray_icon.show()
    sys.exit(app.exec_())
