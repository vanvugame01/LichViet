from datetime import date
from PyQt5.QtCore import QTime
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
    QCheckBox
)
import lunarcalendar

def format_reminder_line(reminder):
    repeat = "Hằng năm" if reminder.get("repeat_yearly", True) else f"Năm {reminder.get('lunar_year', '-') }"
    state = "Bật" if reminder.get("enabled", True) else "Tắt"
    title = reminder.get('title', 'Nhắc lịch âm')
    # Truncate title if too long
    if len(title) > 20: title = title[:17] + "..."
    return (
        f"{title} | "
        f"Âm {reminder.get('lunar_day', 1):02d}/{reminder.get('lunar_month', 1):02d} | "
        f"{reminder.get('hour', 8):02d}:{reminder.get('minute', 0):02d} | {repeat} | {state}"
    )

class AddReminderDialog(QDialog):
    def __init__(self, parent=None, reminder_manager=None):
        super().__init__(parent)
        self.setWindowTitle("Hẹn lịch âm")
        self.setStyleSheet("font-size: 13px; font-family: 'Segoe UI';")
        self.reminder_manager = reminder_manager

        layout = QFormLayout(self)

        self.title_edit = QLineEdit("Nhắc việc")
        self.title_edit.setMinimumWidth(200)

        self.day_spin = QSpinBox()
        self.day_spin.setRange(1, 30)
        
        self.month_spin = QSpinBox()
        self.month_spin.setRange(1, 12)
        
        current_lunar = lunarcalendar.Lunar.from_date(date.today())
        self.day_spin.setValue(current_lunar.day)
        self.month_spin.setValue(current_lunar.month)

        self.year_spin = QSpinBox()
        self.year_spin.setRange(1900, 2200)
        self.year_spin.setValue(current_lunar.year)

        self.repeat_yearly = QCheckBox("Lặp hằng năm")
        self.repeat_yearly.setChecked(True)
        self.year_spin.setEnabled(False)
        self.repeat_yearly.toggled.connect(lambda checked: self.year_spin.setEnabled(not checked))

        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime(8, 0))

        layout.addRow("Tiêu đề", self.title_edit)
        layout.addRow("Ngày âm", self.day_spin)
        layout.addRow("Tháng âm", self.month_spin)
        layout.addRow("Năm âm", self.year_spin)
        layout.addRow("Nhắc lúc", self.time_edit)
        layout.addRow("", self.repeat_yearly)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addRow(buttons)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

    def get_reminder_data(self):
        title = self.title_edit.text().strip() or "Nhắc lịch âm"
        return {
            "title": title,
            "lunar_day": self.day_spin.value(),
            "lunar_month": self.month_spin.value(),
            "lunar_year": None if self.repeat_yearly.isChecked() else self.year_spin.value(),
            "hour": self.time_edit.time().hour(),
            "minute": self.time_edit.time().minute(),
            "repeat_yearly": self.repeat_yearly.isChecked(),
            "enabled": True,
            "last_triggered_date": None,
        }

class ManageRemindersDialog(QDialog):
    def __init__(self, parent=None, reminder_manager=None):
        super().__init__(parent)
        self.setWindowTitle("Quản lý nhắc lịch âm")
        self.resize(480, 280)
        self.setStyleSheet("font-size: 13px; font-family: 'Segoe UI';")
        self.reminder_manager = reminder_manager

        layout = QVBoxLayout(self)
        self.reminder_list = QListWidget()
        
        btn_row = QHBoxLayout()
        add_btn = QPushButton("Thêm")
        add_btn.setMinimumHeight(30)
        self.toggle_btn = QPushButton("Bật/Tắt")
        self.toggle_btn.setMinimumHeight(30)
        self.del_btn = QPushButton("Xóa")
        self.del_btn.setMinimumHeight(30)
        close_btn = QPushButton("Đóng")
        close_btn.setMinimumHeight(30)

        btn_row.addWidget(add_btn)
        btn_row.addWidget(self.toggle_btn)
        btn_row.addWidget(self.del_btn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)

        layout.addWidget(self.reminder_list)
        layout.addLayout(btn_row)

        self.refresh_list()

        add_btn.clicked.connect(self.add_item)
        self.toggle_btn.clicked.connect(self.toggle_item)
        self.del_btn.clicked.connect(self.del_item)
        close_btn.clicked.connect(self.accept)

    def refresh_list(self):
        self.reminder_list.clear()
        for rem in self.reminder_manager.get_all():
            self.reminder_list.addItem(QListWidgetItem(format_reminder_line(rem)))

    def add_item(self):
        dlg = AddReminderDialog(self, self.reminder_manager)
        if dlg.exec_() == QDialog.Accepted:
            self.reminder_manager.add_reminder(dlg.get_reminder_data())
            self.refresh_list()

    def toggle_item(self):
        row = self.reminder_list.currentRow()
        if row < 0:
            return
        self.reminder_manager.toggle_reminder(row)
        self.refresh_list()

    def del_item(self):
        row = self.reminder_list.currentRow()
        if row < 0:
            return
        self.reminder_manager.remove_reminder(row)
        self.refresh_list()
