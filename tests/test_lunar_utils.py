import unittest
from datetime import date, timedelta

from core.lunar_utils import lunar_to_solar, solar_to_lunar


class LunarUtilsTests(unittest.TestCase):
    def test_vietnamese_new_year_and_utc_seven_boundary(self):
        for solar in [date(2007, 2, 17), date(2024, 2, 10), date(2025, 1, 29), date(2026, 2, 17)]:
            lunar = solar_to_lunar(solar)
            self.assertEqual((1, 1, solar.year, False), (lunar.day, lunar.month, lunar.year, lunar.isleap))

    def test_leap_month_and_invalid_dates(self):
        lunar = solar_to_lunar(date(2023, 3, 22))
        self.assertEqual((1, 2, 2023, True), (lunar.day, lunar.month, lunar.year, lunar.isleap))
        self.assertEqual(date(2023, 3, 22), lunar_to_solar(1, 2, 2023, True))
        self.assertEqual(date(2023, 2, 20), lunar_to_solar(1, 2, 2023, False))
        self.assertIsNone(lunar_to_solar(1, 2, 2026, True))
        self.assertIsNone(lunar_to_solar(30, 2, 2025))

    def test_daily_round_trips(self):
        solar = date(1900, 1, 1)
        while solar.year < 2200:
            lunar = solar_to_lunar(solar)
            self.assertTrue(1 <= lunar.day <= 30, str(solar))
            self.assertTrue(1 <= lunar.month <= 12, str(solar))
            if lunar.year >= 1900:
                self.assertEqual(solar, lunar_to_solar(lunar.day, lunar.month, lunar.year, lunar.isleap))
            solar += timedelta(days=1)


if __name__ == "__main__":
    unittest.main()
