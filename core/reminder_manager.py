import json
from pathlib import Path

# Thư mục lưu file reminders: d:\MyProject\LichViet\lunar_reminders.json
REMINDERS_FILE = Path(__file__).parent.parent / "lunar_reminders.json"

class ReminderManager:
    def __init__(self):
        self.reminders = []
        self.load_reminders()

    def load_reminders(self):
        """Đọc danh sách nhắc lịch từ file JSON."""
        self.reminders = []
        if not REMINDERS_FILE.exists():
            return
        try:
            data = json.loads(REMINDERS_FILE.read_text(encoding="utf-8"))
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
        except Exception as e:
            print(f"Lỗi khi đọc reminders: {e}")
            self.reminders = []

    def save_reminders(self):
        """Lưu danh sách nhắc lịch vào file JSON an toàn (atomic write)."""
        try:
            tmp_file = REMINDERS_FILE.with_suffix('.tmp')
            tmp_file.write_text(json.dumps(self.reminders, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp_file.replace(REMINDERS_FILE)
            return True
        except Exception as e:
            print(f"Lỗi khi lưu reminders: {e}")
            return False

    def add_reminder(self, reminder):
        self.reminders.append(reminder)
        self.save_reminders()

    def remove_reminder(self, index):
        if 0 <= index < len(self.reminders):
            self.reminders.pop(index)
            self.save_reminders()

    def toggle_reminder(self, index):
        if 0 <= index < len(self.reminders):
            self.reminders[index]["enabled"] = not self.reminders[index].get("enabled", True)
            self.save_reminders()

    def get_all(self):
        return self.reminders
