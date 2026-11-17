from datetime import date, timedelta
from pathlib import Path

from PyQt5.QtCore import QDate, QPoint, QTime, QTimer, Qt
from PyQt5.QtGui import QColor, QCursor, QIcon, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (
    QAction, QApplication, QDialog, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QMenu, QMessageBox, QPushButton, QScrollArea, QSizeGrip,
    QSystemTrayIcon, QVBoxLayout, QWidget,
)

from core.lunar_utils import WEEKDAY_VI, zodiac_year_name
from core.reminder_manager import ReminderManager
from ui.day_cell import DayCell
from ui.dialogs import AddReminderDialog, ManageRemindersDialog, solar_to_lunar

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


def calendar_icon(color="#b45309"):
    pixmap = QPixmap(28, 28)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor(color), 2))
    painter.drawRoundedRect(4, 6, 20, 18, 3, 3)
    painter.drawLine(4, 12, 24, 12)
    painter.drawLine(9, 3, 9, 9)
    painter.drawLine(19, 3, 19, 9)
    painter.end()
    return QIcon(pixmap)


def line_icon(kind):
    pixmap = QPixmap(20, 20)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor("#334155"), 1.8))
    if kind == "left":
        painter.drawLine(12, 5, 7, 10)
        painter.drawLine(7, 10, 12, 15)
    elif kind == "right":
        painter.drawLine(8, 5, 13, 10)
        painter.drawLine(13, 10, 8, 15)
    elif kind == "close":
        painter.drawLine(5, 5, 15, 15)
        painter.drawLine(5, 15, 15, 5)
    else:
        painter.drawLine(5, 11, 15, 11)
    painter.end()
    return QIcon(pixmap)


class DashboardWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lịch Việt")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setWindowIcon(calendar_icon())
        self.setGeometry(260, 40, 460, 720)
        self.setMinimumSize(440, 680)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.drag_position = QPoint()
        self.current_month = QDate.currentDate().addDays(1 - QDate.currentDate().day())
        self.selected_date = date.today()
        self.reminder_manager = ReminderManager()
        self.last_checked_day = date.today()
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
        if self.reminder_manager.last_error:
            self.status_label.setText("Chưa đọc được dữ liệu nhắc việc. Kiểm tra tệp lưu trước khi thêm lịch mới.")
            self.status_label.show()

    def make_button(self, text, name, callback, accessible_name=None):
        button = QPushButton(text)
        button.setObjectName(name)
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(callback)
        button.setAccessibleName(accessible_name or text)
        button.setToolTip(accessible_name or text)
        return button

    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 6)
        root.setSpacing(10)
        top = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(calendar_icon().pixmap(26, 26))
        top.addWidget(icon)
        self.title_label = QLabel("Lịch Việt")
        self.title_label.setObjectName("titleLabel")
        top.addWidget(self.title_label)
        top.addStretch()
        self.menu_button = self.make_button("...", "iconButton", self.show_window_menu, "Mở menu ứng dụng")
        top.addWidget(self.menu_button)
        self.minimize_button = self.make_button("", "iconButton", self.showMinimized, "Thu nhỏ cửa sổ")
        self.minimize_button.setIcon(line_icon("minimize"))
        top.addWidget(self.minimize_button)
        self.close_button = self.make_button("", "iconButton", self.close, "Đóng cửa sổ; tiếp tục chạy dưới khay nếu có")
        self.close_button.setIcon(line_icon("close"))
        top.addWidget(self.close_button)
        root.addLayout(top)

        nav = QHBoxLayout()
        nav.setSpacing(8)
        self.prev_button = self.make_button("", "navButton", self.prev_month, "Tháng trước")
        self.prev_button.setIcon(line_icon("left"))
        self.next_button = self.make_button("", "navButton", self.next_month, "Tháng sau")
        self.next_button.setIcon(line_icon("right"))
        self.month_label = QLabel()
        self.month_label.setObjectName("monthTitle")
        self.month_label.setAlignment(Qt.AlignCenter)
        self.today_button = self.make_button("Hôm nay", "todayButton", self.go_today)
        nav.addWidget(self.prev_button)
        nav.addWidget(self.month_label, 1)
        nav.addWidget(self.next_button)
        nav.addWidget(self.today_button)
        root.addLayout(nav)

        calendar_frame = QFrame()
        calendar_frame.setObjectName("calendarFrame")
        calendar_layout = QVBoxLayout(calendar_frame)
        calendar_layout.setContentsMargins(4, 4, 4, 4)
        calendar_layout.setSpacing(2)
        weekdays = QHBoxLayout()
        weekdays.setSpacing(2)
        for index, weekday in enumerate(("T2", "T3", "T4", "T5", "T6", "T7", "CN")):
            label = QLabel(weekday)
            label.setAlignment(Qt.AlignCenter)
            label.setObjectName("sundayHeader" if index == 6 else "weekdayHeader")
            weekdays.addWidget(label, 1)
        calendar_layout.addLayout(weekdays)
        grid = QGridLayout()
        grid.setSpacing(2)
        self.cells = []
        for index in range(42):
            cell = DayCell()
            cell.clicked.connect(self.select_date)
            cell.navigate.connect(self.navigate_date)
            grid.addWidget(cell, index // 7, index % 7)
            self.cells.append(cell)
        for column in range(7):
            grid.setColumnStretch(column, 1)
        for row in range(6):
            grid.setRowStretch(row, 1)
        calendar_layout.addLayout(grid, 1)
        root.addWidget(calendar_frame, 5)

        details = QFrame()
        details.setObjectName("detailCard")
        details_layout = QHBoxLayout(details)
        details_layout.setContentsMargins(12, 10, 12, 10)
        detail_icon = QLabel()
        detail_icon.setPixmap(calendar_icon("#047857").pixmap(28, 28))
        details_layout.addWidget(detail_icon)
        detail_text = QVBoxLayout()
        detail_text.setSpacing(3)
        self.detail_main = QLabel()
        self.detail_main.setObjectName("detailMain")
        self.detail_main.setWordWrap(True)
        self.detail_sub = QLabel()
        self.detail_sub.setObjectName("secondaryText")
        self.detail_sub.setWordWrap(True)
        detail_text.addWidget(self.detail_main)
        detail_text.addWidget(self.detail_sub)
        details_layout.addLayout(detail_text, 1)
        root.addWidget(details)

        reminder_heading = QLabel("Nhắc việc trong ngày")
        reminder_heading.setObjectName("sectionTitle")
        root.addWidget(reminder_heading)
        self.daily_scroll = QScrollArea()
        self.daily_scroll.setWidgetResizable(True)
        self.daily_scroll.setObjectName("dailyScroll")
        self.daily_scroll.setMinimumHeight(62)
        self.daily_scroll.setMaximumHeight(150)
        self.daily_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.daily_container = QWidget()
        self.daily_container.setObjectName("dailyContainer")
        self.daily_layout = QVBoxLayout(self.daily_container)
        self.daily_layout.setContentsMargins(0, 0, 0, 0)
        self.daily_layout.setSpacing(6)
        self.daily_scroll.setWidget(self.daily_container)
        root.addWidget(self.daily_scroll, 1)
        self.status_label = QLabel()
        self.status_label.setObjectName("errorLabel")
        self.status_label.setWordWrap(True)
        self.status_label.hide()
        root.addWidget(self.status_label)
        footer = QHBoxLayout()
        footer.setSpacing(10)
        self.add_button = self.make_button("+ Thêm lịch âm", "primaryButton", self.add_reminder_dialog)
        self.manage_button = self.make_button("Quản lý", "secondaryButton", self.manage_reminders_dialog)
        footer.addWidget(self.add_button, 2)
        footer.addWidget(self.manage_button, 1)
        root.addLayout(footer)
        grip_row = QHBoxLayout()
        grip_row.setContentsMargins(0, 0, 0, 0)
        grip_row.addStretch()
        grip = QSizeGrip(self)
        grip.setFixedSize(12, 12)
        grip_row.addWidget(grip)
        root.addLayout(grip_row)

    def setup_tray(self):
        self.tray_icon = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self.windowIcon(), self)
            self.tray_icon.setToolTip("Lịch Việt")
            self.tray_icon.activated.connect(self.tray_icon_activated)
            menu = QMenu(self)
            for title, callback in (("Hiển thị", self.restore_window),
                                    ("Thêm lịch âm", self.add_reminder_dialog),
                                    ("Quản lý nhắc việc", self.manage_reminders_dialog)):
                action = QAction(title, self)
                action.triggered.connect(callback)
                menu.addAction(action)
            menu.addSeparator()
            exit_action = QAction("Thoát", self)
            exit_action.triggered.connect(self.quit_app)
            menu.addAction(exit_action)
            self.tray_icon.setContextMenu(menu)
            self.tray_icon.show()
            self.close_button.setToolTip("Ẩn xuống khay hệ thống; ứng dụng vẫn nhắc lịch")
            self.close_button.setAccessibleName("Ẩn xuống khay hệ thống")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.pos().y() < 52:
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
        else:
            self.reminder_timer.stop()
            event.accept()
            QApplication.instance().quit()

    def tray_icon_activated(self, reason):
        if reason in (QSystemTrayIcon.DoubleClick, QSystemTrayIcon.Trigger):
            self.restore_window()

    def restore_window(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def hide_to_tray(self, show_tip=True):
        if self.tray_icon is None:
            self.showMinimized()
            return
        self.hide()
        self.tray_icon.show()
        if show_tip:
            self.tray_icon.showMessage("Lịch Việt", "Ứng dụng vẫn chạy và nhắc lịch dưới khay hệ thống.", QSystemTrayIcon.Information, 3000)

    def show_window_menu(self):
        menu = QMenu(self)
        for title, callback in (("Về hôm nay", self.go_today),
                                ("Thêm lịch âm", self.add_reminder_dialog),
                                ("Quản lý nhắc việc", self.manage_reminders_dialog)):
            menu.addAction(title, callback)
        if self.tray_icon is not None:
            menu.addAction("Ẩn xuống khay hệ thống", self.hide_to_tray)
        menu.addSeparator()
        menu.addAction("Thoát", self.quit_app)
        menu.exec_(QCursor.pos())

    def quit_app(self):
        self.reminder_timer.stop()
        if self.tray_icon is not None:
            self.tray_icon.hide()
        QApplication.instance().quit()

    def go_today(self):
        self.select_date(date.today())

    def change_month(self, offset):
        month = self.current_month.addMonths(offset)
        if not 1900 <= month.year() <= 2199:
            return
        self.current_month = month
        self.selected_date = date(month.year(), month.month(), min(self.selected_date.day, month.daysInMonth()))
        self.update_calendar()

    def prev_month(self):
        self.change_month(-1)

    def next_month(self):
        self.change_month(1)

    def select_date(self, selected):
        if not 1900 <= selected.year <= 2199:
            return
        try:
            solar_to_lunar(selected)
        except (ValueError, IndexError):
            return
        self.selected_date = selected
        self.current_month = QDate(selected.year, selected.month, 1)
        self.update_calendar()

    def navigate_date(self, selected, offset):
        self.select_date(selected + timedelta(days=offset))
        for cell in self.cells:
            if cell._day == self.selected_date:
                cell.setFocus(Qt.OtherFocusReason)
                break

    def reminders_for_lunar(self, lunar):
        return sorted(
            [reminder for reminder in self.reminder_manager.get_all()
             if reminder.get("enabled", True)
             and reminder.get("lunar_day") == lunar.day
             and reminder.get("lunar_month") == lunar.month
             and bool(reminder.get("is_leap", False)) == bool(lunar.isleap)
             and (reminder.get("repeat_yearly", True) or reminder.get("lunar_year") == lunar.year)],
            key=lambda reminder: (reminder.get("hour", 8), reminder.get("minute", 0)),
        )

    def update_detail(self):
        try:
            lunar = solar_to_lunar(self.selected_date)
        except (ValueError, IndexError):
            self.detail_main.setText(f"{self.selected_date:%d/%m/%Y}")
            self.detail_sub.setText("Ngày nằm ngoài phạm vi lịch âm được hỗ trợ.")
            return
        self.detail_main.setText(f"{WEEKDAY_VI[self.selected_date.weekday()]}, {self.selected_date:%d/%m/%Y}")
        leap = " nhuận" if lunar.isleap else ""
        self.detail_sub.setText(f"Âm lịch · {lunar.day:02d}/{lunar.month:02d}{leap} · {zodiac_year_name(lunar.year)}")
        while self.daily_layout.count():
            item = self.daily_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        reminders = self.reminders_for_lunar(lunar)
        if not reminders:
            empty = QLabel("Chưa có nhắc việc trong ngày này.")
            empty.setObjectName("emptyState")
            empty.setWordWrap(True)
            self.daily_layout.addWidget(empty)
        for reminder in reminders:
            card = QFrame()
            card.setObjectName("dailyReminder")
            row = QHBoxLayout(card)
            row.setContentsMargins(12, 10, 12, 10)
            title = QLabel(reminder["title"])
            title.setObjectName("reminderTitle")
            title.setWordWrap(True)
            row.addWidget(title, 1)
            time = QLabel(f"{reminder.get('hour', 8):02d}:{reminder.get('minute', 0):02d}")
            time.setObjectName("timeBadge")
            row.addWidget(time)
            self.daily_layout.addWidget(card)
        self.daily_layout.addStretch()

    def update_calendar(self):
        self.month_label.setText(f"Tháng {self.current_month.month()}, {self.current_month.year()}")
        first = QDate(self.current_month.year(), self.current_month.month(), 1)
        start = first.addDays(1 - first.dayOfWeek())
        for index, cell in enumerate(self.cells):
            qd = start.addDays(index)
            day = qd.toPyDate()
            try:
                lunar = solar_to_lunar(day)
                lunar_text = f"{lunar.day:02d}/{lunar.month:02d}"
                has_reminder = bool(self.reminders_for_lunar(lunar))
                description = f"{lunar.day:02d}/{lunar.month:02d}/{lunar.year}" + (" nhuận" if lunar.isleap else "")
                cell.setEnabled(True)
            except (ValueError, IndexError):
                lunar_text, has_reminder, description = "—", False, "ngoài phạm vi hỗ trợ"
                cell.setEnabled(False)
            cell.set_day(day, lunar_text, qd.month() == first.month() and qd.year() == first.year(),
                         qd.dayOfWeek() == 7, day == self.selected_date, day == date.today(), has_reminder, description)
        self.prev_button.setEnabled((first.year(), first.month()) > (1900, 1))
        self.next_button.setEnabled((first.year(), first.month()) < (2199, 12))
        self.update_detail()

    def add_reminder_dialog(self):
        dlg = AddReminderDialog(self, self.reminder_manager, self.selected_date)
        if dlg.exec_() == QDialog.Accepted:
            self.update_calendar()
            self.check_reminders()

    def manage_reminders_dialog(self):
        dlg = ManageRemindersDialog(self, self.reminder_manager)
        dlg.exec_()
        self.update_calendar()
        self.check_reminders()

    def notify_reminder(self, reminder, lunar_today):
        message = (
            f"{reminder.get('title', 'Nhắc lịch âm')}\n"
            f"Hôm nay âm lịch {lunar_today.day:02d}/{lunar_today.month:02d}/{lunar_today.year}."
        )
        if self.tray_icon is not None:
            self.tray_icon.showMessage("Nhắc lịch âm", message, QSystemTrayIcon.Information, 10000)
        else:
            QMessageBox.information(self, "Nhắc lịch âm", message)

    def check_reminders(self):
        today = date.today()
        if self.last_checked_day != today:
            self.last_checked_day = today
            self.update_calendar()
        now = QTime.currentTime()
        lunar_today = solar_to_lunar(today)
        changed = False
        for reminder in self.reminders_for_lunar(lunar_today):
            if (now.hour(), now.minute()) < (reminder.get("hour", 8), reminder.get("minute", 0)):
                continue
            if reminder.get("last_triggered_date") == today.isoformat():
                continue
            self.notify_reminder(reminder, lunar_today)
            reminder["last_triggered_date"] = today.isoformat()
            if not reminder.get("repeat_yearly", True):
                reminder["enabled"] = False
            changed = True
        if changed:
            if not self.reminder_manager.save_reminders():
                self.status_label.setText("Đã nhắc việc nhưng chưa lưu được trạng thái. Kiểm tra quyền ghi thư mục.")
                self.status_label.show()
            self.update_calendar()
