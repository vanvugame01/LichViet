import json
import os
import sys
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import QApplication

import core.reminder_manager as storage
from ui.dashboard import DashboardWidget
from ui.dialogs import AddReminderDialog, ManageRemindersDialog


def main():
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    font = Path("C:/Windows/Fonts/segoeui.ttf")
    if font.exists():
        QFontDatabase.addApplicationFont(str(font))
    output = Path(__file__).resolve().parent.parent / "output" / "desktop"
    output.mkdir(parents=True, exist_ok=True)
    sample = dict(title="Giỗ gia đình", lunar_day=9, lunar_month=10,
                  lunar_year=None, hour=8, minute=0, repeat_yearly=True,
                  enabled=True, is_leap=False, last_triggered_date=None)
    # Chi dung tep tam; khong doc/ghi du lieu nhac viec that khi dung anh.
    with tempfile.TemporaryDirectory() as directory:
        data_file = Path(directory) / "reminders.json"
        data_file.write_text(json.dumps([sample], ensure_ascii=False), encoding="utf-8")
        with patch.object(storage, "REMINDERS_FILE", data_file), \
             patch.object(DashboardWidget, "setup_tray", lambda self: setattr(self, "tray_icon", None)), \
             patch.object(DashboardWidget, "notify_reminder"):
            dashboard = DashboardWidget()
            dashboard.reminder_timer.stop()
            dashboard.select_date(date(2026, 11, 17))
            dashboard.show()
            app.processEvents()
            dashboard.grab().save(str(output / "calendar.png"))
            dashboard.resize(dashboard.minimumSize())
            app.processEvents()
            dashboard.grab().save(str(output / "calendar-minimum.png"))
            add = AddReminderDialog(dashboard, dashboard.reminder_manager, date(2026, 11, 17))
            add.title_edit.setText("Giỗ gia đình")
            add.show()
            app.processEvents()
            add.grab().save(str(output / "add-reminder.png"))
            manage = ManageRemindersDialog(dashboard, dashboard.reminder_manager)
            manage.show()
            app.processEvents()
            manage.grab().save(str(output / "manage-reminders.png"))
            for widget in (manage, add, dashboard):
                widget.hide()
                widget.deleteLater()
            app.processEvents()
    print(output)


if __name__ == "__main__":
    main()
