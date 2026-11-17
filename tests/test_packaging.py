import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from tools.build_portable import create_portable_archive


class PortablePackagingTests(unittest.TestCase):
    def test_public_archive_uses_empty_data_and_preserves_local_reminders(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "LichViet.exe").write_bytes(b"test executable")
            (folder / "HUONG-DAN.txt").write_text("test guide", encoding="utf-8")
            personal_file = folder / "lunar_reminders.json"
            personal_contents = json.dumps([{"title": "private reminder"}])
            personal_file.write_text(personal_contents, encoding="utf-8")
            archive = folder / "portable.zip"
            create_portable_archive(folder, archive)
            with zipfile.ZipFile(archive) as package:
                self.assertEqual([], json.loads(package.read("LichViet/lunar_reminders.json")))
                self.assertEqual({"LichViet/LichViet.exe", "LichViet/HUONG-DAN.txt", "LichViet/lunar_reminders.json"}, set(package.namelist()))
                self.assertIsNone(package.testzip())
            self.assertEqual(personal_contents, personal_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
