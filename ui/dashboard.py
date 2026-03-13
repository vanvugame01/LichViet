import sys
from datetime import date
from pathlib import Path

import lunarcalendar
from PyQt5.QtCore import QDate, QPoint, QTime, QTimer, Qt
from PyQt5.QtGui import QCursor, QIcon
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from core.lunar_utils import zodiac_year_name, WEEKDAY_VI
from core.reminder_manager import ReminderManager
from ui.day_cell import DayCell
from ui.dialogs import AddReminderDialog, ManageRemindersDialog

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

class DashboardWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lịch Việt")
        # Main geometry
        self.setGeometry(260, 40, 320, 430)
        self.setFixedSize(320, 430)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)

        self.drag_position = QPoint()
        self.current_month = QDate.currentDate().addDays(1 - QDate.currentDate().day())
        self.selected_date = QDate.currentDate().toPyDate()

        self.reminder_manager = ReminderManager()

        # Load Stylesheet
        qss_file = ASSETS_DIR / "style.qss"
        if qss_file.exists():
            self.setStyleSheet(qss_file.read_text(encoding="utf-8"))

        self.setup_ui()
        self.setup_tray()

        self.reminder_timer = QTimer(self)
        self.reminder_timer.setInterval(30_000)
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start()

        self.update_calendar()
        self.check_reminders()

    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # Top row
        top_row = QHBoxLayout()
        top_row.setSpacing(5)

        self.title_label = QLabel("LỊCH VIỆT")
        self.title_label.setObjectName("titleLabel")

        capsule = QFrame()
        capsule.setObjectName("capsuleBox")
        capsule_layout = QHBoxLayout(capsule)
        capsule_layout.setContentsMargins(2, 2, 2, 2)
        capsule_layout.setSpacing(0)

        self.menu_button = QPushButton("•••")
        self.menu_button.setObjectName("capsuleButton")
        self.menu_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.menu_button.clicked.connect(self.show_window_menu)

        line = QFrame()
        line.setObjectName("divider")
        line.setFixedWidth(1)

        self.close_button = QPushButton("×")
        self.close_button.setObjectName("capsuleButton")
        self.close_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.close_button.clicked.connect(self.hide_to_tray)

        capsule_layout.addWidget(self.menu_button)
        capsule_layout.addWidget(line)
        capsule_layout.addWidget(self.close_button)

        top_row.addWidget(self.title_label)
        top_row.addStretch()
        top_row.addWidget(capsule)

        # Navigation row
        nav_row = QHBoxLayout()
        nav_row.setSpacing(6)

        self.prev_button = QPushButton("‹")
        self.prev_button.setObjectName("navButton")
        self.prev_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.prev_button.clicked.connect(self.prev_month)

        self.month_label = QLabel()
        self.month_label.setObjectName("monthTitle")
        self.month_label.setAlignment(Qt.AlignCenter)

        self.next_button = QPushButton("›")
        self.next_button.setObjectName("navButton")
        self.next_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.next_button.clicked.connect(self.next_month)

        nav_row.addWidget(self.prev_button)
        nav_row.addStretch()
        nav_row.addWidget(self.month_label)
        nav_row.addStretch()
        nav_row.addWidget(self.next_button)

        # Weekdays header
        weekday_row = QHBoxLayout()
        weekday_row.setSpacing(2)
        for idx, wd in enumerate(["T2", "T3", "T4", "T5", "T6", "T7", "CN"]):
            wd_label = QLabel(wd)
            wd_label.setAlignment(Qt.AlignCenter)
            wd_label.setObjectName("weekdayHeader")
            if idx == 6:
                wd_label.setObjectName("sundayHeader")
            weekday_row.addWidget(wd_label)

        # Grid
        grid_wrap = QFrame()
        grid = QGridLayout(grid_wrap)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(4)
        grid.setVerticalSpacing(4)

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

        # Bottom section
        bottom = QHBoxLayout()
        bottom.setSpacing(10)

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
        right_col.setSpacing(3)

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
        detail_divider.setStyleSheet("margin: 2px 0;")

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

    def setup_tray(self):
        self.tray_icon = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            icon_path = str(ASSETS_DIR / "icon.png")
            if Path(icon_path).exists():
                self.tray_icon.setIcon(QIcon(icon_path))
            else:
                # Dùng một icon mặc định lấy từ phong bì sẵn của thư viện nếu ko tìm thấy file
                self.tray_icon.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))
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
            self.tray_icon.showMessage("Lịch Việt", "Ứng dụng đã ẩn xuống khay.", QSystemTrayIcon.Information, 3000)

    def show_window_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("font-size: 13px; font-family: 'Segoe UI';")
        reset_today = menu.addAction("Về hôm nay")
        add_reminder = menu.addAction("Hẹn lịch âm")
        manage_reminders = menu.addAction("Quản lý nhắc lịch")
        
        to_tray = None
        if self.tray_icon is not None:
            to_tray = menu.addAction("Ẩn xuống khay hệ thống")
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

    def update_detail(self):
        lunar = lunarcalendar.Lunar.from_date(self.selected_date)
        weekday_name = WEEKDAY_VI[self.selected_date.weekday()]

        self.left_weekday.setText(weekday_name)
        self.left_day.setText(str(self.selected_date.day))
        self.left_month.setText(f"Tháng {self.selected_date.month} {self.selected_date.year}")

        self.detail_main.setText(f"Ngày {lunar.day} Tháng {lunar.month}")
        self.detail_sub.setText(f"Năm {zodiac_year_name(lunar.year)} Âm lịch")
        self.detail_foot.setText(
            f"Dương: {self.selected_date.day:02d}/{self.selected_date.month:02d}/{self.selected_date.year}\n"
            f"Âm: {lunar.day:02d}/{lunar.month:02d}/{lunar.year}"
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

    def add_reminder_dialog(self):
        dlg = AddReminderDialog(self, self.reminder_manager)
        if dlg.exec_() == QDialog.Accepted:
            self.reminder_manager.add_reminder(dlg.get_reminder_data())
            self.check_reminders()

    def manage_reminders_dialog(self):
        dlg = ManageRemindersDialog(self, self.reminder_manager)
        dlg.exec_()

    def notify_reminder(self, reminder, lunar_today):
        message = (
            f"{reminder.get('title', 'Nhắc lịch âm')}\n"
            f"Hôm nay âm lịch {lunar_today.day:02d}/{lunar_today.month:02d}/{lunar_today.year}."
        )
        if self.tray_icon is not None:
            if not self.tray_icon.isVisible():
                self.tray_icon.show()
            self.tray_icon.showMessage("Nhắc lịch âm", message, QSystemTrayIcon.Information, 10000)
        else:
            QMessageBox.information(self, "Nhắc lịch âm", message)

    def check_reminders(self):
        reminders = self.reminder_manager.get_all()
        if not reminders:
            return

        today = date.today()
        now = QTime.currentTime()
        lunar_today = lunarcalendar.Converter.Solar2Lunar(lunarcalendar.Solar(today.year, today.month, today.day))
        today_key = today.isoformat()

        changed = False
        for reminder in reminders:
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
            self.reminder_manager.save_reminders()
