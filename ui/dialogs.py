from datetime import date

from PyQt5.QtCore import QEvent, QSize, QTime, QTimer, Qt
from PyQt5.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QFormLayout, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMenu, QPushButton, QSpinBox, QTimeEdit, QVBoxLayout, QWidget,
)
from core.lunar_utils import lunar_to_solar, solar_to_lunar


def format_reminder_line(reminder):
    repeat = "Hằng năm" if reminder.get("repeat_yearly", True) else f"Năm {reminder.get('lunar_year', '-')}"
    leap = " nhuận" if reminder.get("is_leap", False) else ""
    return (
        f"{reminder.get('lunar_day', 1):02d}/{reminder.get('lunar_month', 1):02d}{leap} âm lịch"
        f" · {reminder.get('hour', 8):02d}:{reminder.get('minute', 0):02d} · {repeat}"
    )


class AddReminderDialog(QDialog):
    def __init__(self, parent=None, reminder_manager=None, initial_date=None):
        super().__init__(parent)
        self.setWindowTitle("Thêm lịch âm")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumWidth(360)
        self.resize(400, 470)
        self.reminder_manager = reminder_manager

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)
        heading = QLabel("Thêm lịch âm")
        heading.setObjectName("dialogTitle")
        layout.addWidget(heading)
        form = QFormLayout()
        form.setVerticalSpacing(12)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Ví dụ: Giỗ gia đình")
        self.title_edit.setAccessibleName("Tiêu đề nhắc việc")
        form.addRow("Tiêu đề", self.title_edit)
        self.day_spin = QSpinBox()
        self.day_spin.setRange(1, 30)
        self.day_spin.setAccessibleName("Ngày âm")
        self.month_spin = QSpinBox()
        self.month_spin.setRange(1, 12)
        self.month_spin.setAccessibleName("Tháng âm")
        current_lunar = solar_to_lunar(initial_date or date.today())
        self.day_spin.setValue(current_lunar.day)
        self.month_spin.setValue(current_lunar.month)
        form.addRow("Ngày âm", self.day_spin)
        form.addRow("Tháng âm", self.month_spin)
        self.repeat_yearly = QCheckBox("Lặp hằng năm")
        self.repeat_yearly.setChecked(True)
        self.year_spin = QSpinBox()
        self.year_spin.setRange(1900, 2199)
        self.year_spin.setValue(current_lunar.year)
        self.year_spin.setEnabled(False)
        self.year_spin.setAccessibleName("Năm âm")
        self.repeat_yearly.toggled.connect(lambda checked: self.year_spin.setEnabled(not checked))
        form.addRow("", self.repeat_yearly)
        form.addRow("Năm âm", self.year_spin)
        self.leap_check = QCheckBox("Tháng nhuận")
        self.leap_check.setChecked(bool(current_lunar.isleap))
        form.addRow("", self.leap_check)
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime(8, 0))
        self.time_edit.setAccessibleName("Giờ nhắc")
        form.addRow("Giờ nhắc", self.time_edit)
        layout.addLayout(form)
        note = QLabel("Ứng dụng cần đang chạy để nhắc lịch.\nNgày 30 hoặc tháng nhuận chỉ nhắc trong năm có ngày đó.")
        note.setObjectName("infoNote")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.error_label = QLabel()
        self.error_label.setObjectName("errorLabel")
        self.error_label.setWordWrap(True)
        self.error_label.setAccessibleName("Lỗi lưu lịch")
        self.error_label.hide()
        layout.addWidget(self.error_label)
        layout.addStretch()
        buttons = QDialogButtonBox()
        self.cancel_button = buttons.addButton("Hủy", QDialogButtonBox.RejectRole)
        self.save_button = buttons.addButton("Lưu lịch", QDialogButtonBox.AcceptRole)
        self.save_button.setObjectName("primaryButton")
        self.save_button.setDefault(True)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.title_edit.setFocus()

    def get_reminder_data(self):
        return {
            "title": self.title_edit.text().strip() or "Nhắc lịch âm",
            "lunar_day": self.day_spin.value(),
            "lunar_month": self.month_spin.value(),
            "lunar_year": None if self.repeat_yearly.isChecked() else self.year_spin.value(),
            "hour": self.time_edit.time().hour(),
            "minute": self.time_edit.time().minute(),
            "repeat_yearly": self.repeat_yearly.isChecked(),
            "is_leap": self.leap_check.isChecked(),
            "enabled": True,
            "last_triggered_date": None,
        }

    def accept(self):
        self.error_label.hide()
        data = self.get_reminder_data()
        if not self.title_edit.text().strip():
            self.show_error("Nhập tiêu đề để dễ nhận biết lịch nhắc việc.", self.title_edit)
            return
        years = range(date.today().year, 2200) if data["repeat_yearly"] else [data["lunar_year"]]
        valid = any(lunar_to_solar(data["lunar_day"], data["lunar_month"], year, data["is_leap"]) is not None
                    for year in years)
        if not valid:
            self.show_error("Ngày âm không tồn tại trong năm đã chọn. Kiểm tra ngày, tháng và tháng nhuận.", self.day_spin)
            return
        if self.reminder_manager is not None and not self.reminder_manager.add_reminder(data):
            self.show_error("Chưa lưu được lịch. Kiểm tra quyền ghi thư mục và thử lại.", self.save_button)
            return
        super().accept()

    def show_error(self, message, field):
        self.error_label.setText(message)
        self.error_label.show()
        field.setFocus()


class ManageRemindersDialog(QDialog):
    def __init__(self, parent=None, reminder_manager=None):
        super().__init__(parent)
        self.setWindowTitle("Quản lý nhắc việc")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumSize(420, 350)
        self.resize(500, 490)
        self.reminder_manager = reminder_manager
        self.deleted_reminder = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        heading = QLabel("Quản lý nhắc việc")
        heading.setObjectName("dialogTitle")
        layout.addWidget(heading)
        self.count_label = QLabel()
        self.count_label.setObjectName("secondaryText")
        layout.addWidget(self.count_label)
        self.empty_label = QLabel("Chưa có lịch nhắc việc.\nChọn Thêm lịch âm để tạo lịch đầu tiên.")
        self.empty_label.setObjectName("emptyState")
        self.empty_label.setWordWrap(True)
        self.empty_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.empty_label)
        self.reminder_list = QListWidget()
        self.reminder_list.setObjectName("reminderList")
        self.reminder_list.setSpacing(6)
        self.reminder_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.reminder_list.viewport().installEventFilter(self)
        self.reminder_list.setAccessibleName("Danh sách nhắc việc")
        layout.addWidget(self.reminder_list, 1)
        self.error_label = QLabel()
        self.error_label.setObjectName("errorLabel")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        self.undo_frame = QFrame()
        self.undo_frame.setObjectName("undoBar")
        undo_layout = QHBoxLayout(self.undo_frame)
        undo_layout.addWidget(QLabel("Đã xóa lịch"))
        undo_layout.addStretch()
        self.undo_button = QPushButton("Hoàn tác")
        self.undo_button.setObjectName("textButton")
        self.undo_button.clicked.connect(self.undo_delete)
        undo_layout.addWidget(self.undo_button)
        self.undo_frame.hide()
        layout.addWidget(self.undo_frame)
        self.undo_timer = QTimer(self)
        self.undo_timer.setSingleShot(True)
        self.undo_timer.timeout.connect(self.clear_undo)
        buttons = QHBoxLayout()
        self.add_button = QPushButton("+ Thêm lịch âm")
        self.add_button.setObjectName("primaryButton")
        self.add_button.clicked.connect(self.add_item)
        close_button = QPushButton("Đóng")
        close_button.clicked.connect(self.accept)
        buttons.addWidget(self.add_button, 1)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)
        self.refresh_list()

    def refresh_list(self):
        self.reminder_list.clear()
        reminders = self.reminder_manager.get_all()
        self.count_label.setText(f"{len(reminders)} lịch đã lưu")
        self.empty_label.setVisible(not reminders)
        self.reminder_list.setVisible(bool(reminders))
        for index, reminder in enumerate(reminders):
            item = QListWidgetItem()
            item.setData(Qt.UserRole, index)
            item.setTextAlignment(Qt.AlignLeft)
            item.setToolTip(f"{reminder['title']}\n{format_reminder_line(reminder)}")
            card = QFrame()
            card.setObjectName("reminderCard")
            row = QHBoxLayout(card)
            row.setContentsMargins(12, 10, 10, 10)
            text = QVBoxLayout()
            title = QLabel(reminder["title"])
            title.setObjectName("reminderTitle")
            title.setWordWrap(True)
            title.setMinimumWidth(0)
            detail = QLabel(format_reminder_line(reminder))
            detail.setObjectName("secondaryText")
            detail.setWordWrap(True)
            detail.setMinimumWidth(0)
            text.addWidget(title)
            text.addWidget(detail)
            row.addLayout(text, 1)
            toggle = QCheckBox("Bật")
            toggle.setChecked(reminder.get("enabled", True))
            toggle.setAccessibleName(f"Bật nhắc việc {reminder['title']}")
            toggle.toggled.connect(lambda checked, i=index: self.toggle_item(i))
            row.addWidget(toggle)
            more = QPushButton("...")
            more.setObjectName("iconButton")
            more.setAccessibleName(f"Thao tác với {reminder['title']}")
            more.setToolTip("Thao tác với lịch")
            more.clicked.connect(lambda checked=False, i=index, button=more: self.show_item_menu(i, button))
            row.addWidget(more)
            self.reminder_list.addItem(item)
            self.reminder_list.setItemWidget(item, card)
        self.update_card_sizes()

    def update_card_sizes(self):
        width = max(1, self.reminder_list.viewport().width() - 2 * self.reminder_list.spacing())
        for row in range(self.reminder_list.count()):
            item = self.reminder_list.item(row)
            card = self.reminder_list.itemWidget(item)
            if card is None:
                continue
            card.ensurePolished()
            card.setFixedWidth(width)
            height = max(80, card.layout().totalHeightForWidth(width))
            item.setSizeHint(QSize(width, height))

    def eventFilter(self, watched, event):
        if watched is self.reminder_list.viewport() and event.type() == QEvent.Resize:
            QTimer.singleShot(0, self.update_card_sizes)
        return super().eventFilter(watched, event)

    def add_item(self):
        dlg = AddReminderDialog(self, self.reminder_manager)
        if dlg.exec_() == QDialog.Accepted:
            self.refresh_list()

    def show_item_menu(self, index, button):
        menu = QMenu(self)
        delete = menu.addAction("Xóa lịch")
        if menu.exec_(button.mapToGlobal(button.rect().bottomLeft())) == delete:
            self.del_item(index)

    def toggle_item(self, index=None):
        row = self.reminder_list.currentRow() if index is None else index
        if row < 0:
            return
        self.error_label.hide()
        if not self.reminder_manager.toggle_reminder(row):
            self.show_error()
        QTimer.singleShot(0, self.refresh_list)

    def del_item(self, index=None):
        row = self.reminder_list.currentRow() if index is None else index
        if row < 0:
            return
        reminder = dict(self.reminder_manager.get_all()[row])
        self.error_label.hide()
        if not self.reminder_manager.remove_reminder(row):
            self.show_error()
            return
        self.deleted_reminder = reminder
        self.undo_frame.show()
        self.undo_timer.start(10_000)
        self.refresh_list()
        self.undo_button.setFocus()

    def undo_delete(self):
        if self.deleted_reminder is None:
            return
        if not self.reminder_manager.add_reminder(self.deleted_reminder):
            self.show_error()
            return
        self.clear_undo()
        self.refresh_list()

    def clear_undo(self):
        self.undo_timer.stop()
        self.deleted_reminder = None
        self.undo_frame.hide()

    def show_error(self):
        self.error_label.setText("Chưa lưu được thay đổi. Kiểm tra quyền ghi thư mục và thử lại.")
        self.error_label.show()
