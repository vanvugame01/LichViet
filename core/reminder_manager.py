import json
import sys
from copy import deepcopy
from pathlib import Path

def get_reminders_file():
    # Ban portable luu canh EXE, khong luu trong thu muc giai nen tam.
    directory = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
    return directory / "lunar_reminders.json"


REMINDERS_FILE = get_reminders_file()

class ReminderManager:
    def __init__(self):
        self.reminders = []
        self.last_error = ""
        self.load_failed = False
        self.load_reminders()

    def load_reminders(self):
        """Đọc danh sách nhắc lịch từ file JSON."""
        self.reminders = []
        self.load_failed = False
        self.last_error = ""
        if not REMINDERS_FILE.exists():
            return
        try:
            data = json.loads(REMINDERS_FILE.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                raise ValueError("Reminder data must be a list")
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
                            "is_leap": bool(item.get("is_leap", False)),
                            "enabled": bool(item.get("enabled", True)),
                            "last_triggered_date": item.get("last_triggered_date"),
                        }
                    )
        except Exception as e:
            self.last_error = str(e)
            self.load_failed = True
            self.reminders = []

    def save_reminders(self):
        """Lưu danh sách nhắc lịch vào file JSON an toàn (atomic write)."""
        if self.load_failed:
            return False
        try:
            tmp_file = REMINDERS_FILE.with_suffix('.tmp')
            tmp_file.write_text(json.dumps(self.reminders, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp_file.replace(REMINDERS_FILE)
            self.last_error = ""
            return True
        except Exception as e:
            self.last_error = str(e)
            return False

    def add_reminder(self, reminder):
        previous = deepcopy(self.reminders)
        self.reminders.append(dict(reminder))
        if self.save_reminders():
            return True
        self.reminders = previous
        return False

    def remove_reminder(self, index):
        if 0 <= index < len(self.reminders):
            previous = deepcopy(self.reminders)
            self.reminders.pop(index)
            if self.save_reminders():
                return True
            self.reminders = previous
        return False

    def toggle_reminder(self, index):
        if 0 <= index < len(self.reminders):
            previous = deepcopy(self.reminders)
            self.reminders[index]["enabled"] = not self.reminders[index].get("enabled", True)
            if self.save_reminders():
                return True
            self.reminders = previous
        return False

    def get_all(self):
        return self.reminders
