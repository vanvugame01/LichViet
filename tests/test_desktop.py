import json
import os
import tempfile
import sys
import unittest
from copy import deepcopy
from datetime import date
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import QTime, Qt
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QCheckBox, QDialog, QPushButton

import core.reminder_manager as storage
from ui.dashboard import DashboardWidget
from ui.dialogs import AddReminderDialog, ManageRemindersDialog, solar_to_lunar


def reminder(**changes):
    value = dict(title="Giỗ gia đình", lunar_day=9, lunar_month=10,
                 lunar_year=None, hour=8, minute=0, repeat_yearly=True,
                 enabled=True, is_leap=False, last_triggered_date=None)
    value.update(changes)
    return value


class DesktopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)
        font = Path("C:/Windows/Fonts/segoeui.ttf")
        if font.exists():
            QFontDatabase.addApplicationFont(str(font))

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temporary.name) / "reminders.json"
        self.file_patch = patch.object(storage, "REMINDERS_FILE", self.data_file)
        self.file_patch.start()
        self.manager = storage.ReminderManager()
        self.widgets = []

    def tearDown(self):
        for widget in self.widgets:
            if hasattr(widget, "reminder_timer"):
                widget.reminder_timer.stop()
            if getattr(widget, "tray_icon", None) is not None:
                widget.tray_icon.hide()
            widget.hide()
            widget.deleteLater()
        self.app.processEvents()
        self.file_patch.stop()
        self.temporary.cleanup()

    def dashboard(self):
        with patch("ui.dashboard.QSystemTrayIcon.isSystemTrayAvailable", return_value=False), \
             patch.object(DashboardWidget, "notify_reminder"):
            widget = DashboardWidget()
        widget.reminder_timer.stop()
        self.widgets.append(widget)
        return widget

    def test_legacy_data_defaults_to_regular_month(self):
        legacy = reminder()
        del legacy["is_leap"]
        self.data_file.write_text(json.dumps([legacy]), encoding="utf-8")
        loaded = storage.ReminderManager()
        self.assertFalse(loaded.get_all()[0]["is_leap"])

    def test_portable_data_is_beside_executable(self):
        executable = Path(self.temporary.name) / "portable" / "LichViet.exe"
        with patch.object(sys, "frozen", True, create=True), patch.object(sys, "executable", str(executable)):
            self.assertEqual(executable.parent / "lunar_reminders.json", storage.get_reminders_file())

    def test_source_data_is_in_project_directory(self):
        with patch.object(sys, "frozen", False, create=True):
            self.assertEqual(Path(storage.__file__).resolve().parent.parent / "lunar_reminders.json", storage.get_reminders_file())

    def test_persist_unicode_and_leap_month(self):
        self.assertTrue(self.manager.add_reminder(reminder(is_leap=True)))
        loaded = storage.ReminderManager()
        self.assertEqual("Giỗ gia đình", loaded.get_all()[0]["title"])
        self.assertTrue(loaded.get_all()[0]["is_leap"])

    def test_corrupted_file_is_not_overwritten(self):
        self.data_file.write_text("{broken", encoding="utf-8")
        manager = storage.ReminderManager()
        self.assertTrue(manager.load_failed)
        self.assertFalse(manager.add_reminder(reminder()))
        self.assertEqual("{broken", self.data_file.read_text(encoding="utf-8"))

    def test_failed_mutations_roll_back(self):
        self.manager.add_reminder(reminder())
        previous = deepcopy(self.manager.get_all())
        with patch.object(self.manager, "save_reminders", return_value=False):
            self.assertFalse(self.manager.add_reminder(reminder(title="Lịch mới")))
            self.assertEqual(previous, self.manager.get_all())
            self.assertFalse(self.manager.toggle_reminder(0))
            self.assertEqual(previous, self.manager.get_all())
            self.assertFalse(self.manager.remove_reminder(0))
            self.assertEqual(previous, self.manager.get_all())

    def test_keyboard_crosses_month_and_lunar_labels_have_no_prefix(self):
        widget = self.dashboard()
        widget.select_date(date(2026, 1, 31))
        selected = next(cell for cell in widget.cells if cell._day == widget.selected_date)
        QTest.keyClick(selected, Qt.Key_Right)
        self.assertEqual(date(2026, 2, 1), widget.selected_date)
        self.assertEqual(42, len(widget.cells))
        for cell in widget.cells:
            self.assertNotIn("âm", cell.lunar_label.text().lower())
        selected = next(cell for cell in widget.cells if cell._day == widget.selected_date)
        self.assertIn("đang chọn", selected.accessibleName())

    def test_invalid_lunar_date_retains_form(self):
        dialog = AddReminderDialog(reminder_manager=self.manager, initial_date=date(2025, 2, 28))
        self.widgets.append(dialog)
        dialog.title_edit.setText("Ngày không tồn tại")
        dialog.repeat_yearly.setChecked(False)
        dialog.year_spin.setValue(2025)
        dialog.month_spin.setValue(2)
        dialog.day_spin.setValue(30)
        dialog.accept()
        self.assertNotEqual(QDialog.Accepted, dialog.result())
        self.assertIn("không tồn tại", dialog.error_label.text())
        self.assertEqual([], self.manager.get_all())

    def test_save_failure_retains_title_and_shows_error(self):
        dialog = AddReminderDialog(reminder_manager=self.manager, initial_date=date(2026, 11, 17))
        self.widgets.append(dialog)
        dialog.title_edit.setText("Lịch cần giữ")
        with patch.object(self.manager, "save_reminders", return_value=False):
            dialog.accept()
        self.assertNotEqual(QDialog.Accepted, dialog.result())
        self.assertEqual("Lịch cần giữ", dialog.title_edit.text())
        self.assertIn("Chưa lưu", dialog.error_label.text())
        self.assertEqual([], self.manager.get_all())

    def test_delete_can_be_undone(self):
        self.manager.add_reminder(reminder())
        dialog = ManageRemindersDialog(reminder_manager=self.manager)
        self.widgets.append(dialog)
        dialog.del_item(0)
        self.assertEqual([], self.manager.get_all())
        dialog.undo_delete()
        self.assertEqual("Giỗ gia đình", self.manager.get_all()[0]["title"])
        self.assertEqual(1, len(storage.ReminderManager().get_all()))

    def test_long_title_keeps_management_controls_in_view(self):
        self.manager.add_reminder(reminder(title="Long reminder title " * 12))
        dashboard = self.dashboard()
        dialog = ManageRemindersDialog(dashboard, self.manager)
        self.widgets.append(dialog)
        dialog.resize(420, 490)
        dialog.show()
        for _ in range(3):
            self.app.processEvents()
        listing = dialog.reminder_list
        card = listing.itemWidget(listing.item(0))
        viewport = listing.viewport()
        self.assertLessEqual(card.width(), viewport.width())
        for control in card.findChildren(QCheckBox) + card.findChildren(QPushButton):
            position = control.mapTo(viewport, control.rect().topRight())
            self.assertLess(position.x(), viewport.width())
            self.assertGreaterEqual(position.x() - control.width() + 1, 0)

    def test_notification_fires_once_and_distinguishes_leap_month(self):
        widget = self.dashboard()
        lunar = solar_to_lunar(date.today())
        widget.reminder_manager.reminders = [
            reminder(lunar_day=lunar.day, lunar_month=lunar.month, is_leap=lunar.isleap),
            reminder(lunar_day=lunar.day, lunar_month=lunar.month, is_leap=not lunar.isleap),
        ]
        with patch("ui.dashboard.QTime") as clock, patch.object(widget, "notify_reminder") as notify:
            clock.currentTime.return_value = QTime(23, 59)
            widget.check_reminders()
            widget.check_reminders()
        self.assertEqual(1, notify.call_count)
        self.assertEqual(date.today().isoformat(), widget.reminder_manager.get_all()[0]["last_triggered_date"])
        self.assertIsNone(widget.reminder_manager.get_all()[1]["last_triggered_date"])


if __name__ == "__main__":
    unittest.main()
