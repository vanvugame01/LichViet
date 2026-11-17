from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from math import floor, pi, sin


WEEKDAY_VI = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
CAN = ["Giáp", "Ất", "Bính", "Đinh", "Mậu", "Kỷ", "Canh", "Tân", "Nhâm", "Quý"]
CHI = ["Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]
LUNAR_EPOCH = 2415021.076998695
SYNODIC_MONTH = 29.530588853
TIME_ZONE = 7.0


@dataclass(frozen=True)
class LunarDate:
    day: int
    month: int
    year: int
    isleap: bool = False

def zodiac_year_name(year: int) -> str:
    """Returns the celestial stem and terrestrial branch for a lunar year."""
    return f"{CAN[(year + 6) % 10]} {CHI[(year + 8) % 12]}"


def _julian_day(day: date) -> int:
    return day.toordinal() + 1721425


@lru_cache(maxsize=4096)
def _new_moon_day(cycle: int) -> int:
    t = cycle / 1236.85
    t2 = t * t
    t3 = t2 * t
    radians = pi / 180
    solar_anomaly = (359.2242 + 29.10535608 * cycle - 0.0000333 * t2 - 0.00000347 * t3) * radians
    lunar_anomaly = (306.0253 + 385.81691806 * cycle + 0.0107306 * t2 + 0.00001236 * t3) * radians
    latitude = (21.2964 + 390.67050646 * cycle - 0.0016528 * t2 - 0.00000239 * t3) * radians
    base = (2415020.75933 + 29.53058868 * cycle + 0.0001178 * t2 - 0.000000155 * t3
            + 0.00033 * sin((166.56 + 132.87 * t - 0.009173 * t2) * radians))
    correction = (
        (0.1734 - 0.000393 * t) * sin(solar_anomaly) + 0.0021 * sin(2 * solar_anomaly)
        - 0.4068 * sin(lunar_anomaly) + 0.0161 * sin(2 * lunar_anomaly)
        - 0.0004 * sin(3 * lunar_anomaly) + 0.0104 * sin(2 * latitude)
        - 0.0051 * sin(solar_anomaly + lunar_anomaly)
        - 0.0074 * sin(solar_anomaly - lunar_anomaly)
        + 0.0004 * sin(2 * latitude + solar_anomaly)
        - 0.0004 * sin(2 * latitude - solar_anomaly)
        - 0.0006 * sin(2 * latitude + lunar_anomaly)
        + 0.0010 * sin(2 * latitude - lunar_anomaly)
        + 0.0005 * sin(2 * lunar_anomaly + solar_anomaly)
    )
    if t < -11:
        delta = 0.001 + 0.000839 * t + 0.0002261 * t2 - 0.00000845 * t3 - 0.000000081 * t * t3
    else:
        delta = -0.000278 + 0.000265 * t + 0.000262 * t2
    return floor(base + correction - delta + 0.5 + TIME_ZONE / 24)


def _solar_sector(day: int) -> int:
    t = (day - 2451545.5 - TIME_ZONE / 24) / 36525
    radians = pi / 180
    anomaly = (357.52910 + 35999.05030 * t - 0.0001559 * t * t - 0.00000048 * t * t * t) * radians
    mean = 280.46645 + 36000.76983 * t + 0.0003032 * t * t
    correction = (
        (1.914600 - 0.004817 * t - 0.000014 * t * t) * sin(anomaly)
        + (0.019993 - 0.000101 * t) * sin(2 * anomaly)
        + 0.000290 * sin(3 * anomaly)
    )
    longitude = (mean + correction) * radians
    normalized = longitude - 2 * pi * floor(longitude / (2 * pi))
    return floor(normalized / pi * 6)


@lru_cache(maxsize=512)
def _month_eleven(year: int) -> int:
    offset = _julian_day(date(year, 12, 31)) - 2415021
    cycle = floor(offset / SYNODIC_MONTH)
    day = _new_moon_day(cycle)
    return _new_moon_day(cycle - 1) if _solar_sector(day) >= 9 else day


@lru_cache(maxsize=512)
def _leap_month_offset(anchor: int) -> int:
    cycle = floor(0.5 + (anchor - LUNAR_EPOCH) / SYNODIC_MONTH)
    offset = 1
    sector = _solar_sector(_new_moon_day(cycle + offset))
    while True:
        previous = sector
        offset += 1
        sector = _solar_sector(_new_moon_day(cycle + offset))
        if sector == previous or offset >= 14:
            return offset - 1


def solar_to_lunar(day: date) -> LunarDate:
    """Tinh ngay am tai mui gio Viet Nam UTC+7."""
    julian_day = _julian_day(day)
    cycle = floor((julian_day - LUNAR_EPOCH) / SYNODIC_MONTH) + 1
    # Hieu chinh uoc luong de ngay luon nam giua hai soc lien tiep.
    for _ in range(3):
        start = _new_moon_day(cycle)
        if start > julian_day:
            cycle -= 1
        elif _new_moon_day(cycle + 1) <= julian_day:
            cycle += 1
        else:
            break
    else:
        raise ValueError("Unable to locate lunar month")
    anchor = _month_eleven(day.year)
    end = anchor
    if anchor >= start:
        lunar_year = day.year
        anchor = _month_eleven(day.year - 1)
    else:
        lunar_year = day.year + 1
        end = _month_eleven(day.year + 1)
    lunar_day = julian_day - start + 1
    offset = floor((start - anchor) / 29.0)
    lunar_month = offset + 11
    leap = False
    if end - anchor > 365:
        leap_offset = _leap_month_offset(anchor)
        if offset >= leap_offset:
            lunar_month = offset + 10
            leap = offset == leap_offset
    if lunar_month > 12:
        lunar_month -= 12
    if lunar_month >= 11 and offset < 4:
        lunar_year -= 1
    return LunarDate(lunar_day, lunar_month, lunar_year, leap)


def lunar_to_solar(day: int, month: int, year: int, is_leap: bool = False) -> date | None:
    """Doi ngay am hop le sang duong lich, tra None neu ngay khong ton tai."""
    if not 1 <= day <= 30 or not 1 <= month <= 12 or not 1900 <= year <= 2199:
        return None
    anchor = _month_eleven(year - 1 if month < 11 else year)
    end = _month_eleven(year if month < 11 else year + 1)
    cycle = floor(0.5 + (anchor - LUNAR_EPOCH) / SYNODIC_MONTH)
    offset = (month - 11) % 12
    if end - anchor > 365:
        leap_offset = _leap_month_offset(anchor)
        leap_month = (leap_offset - 2) % 12 or 12
        if is_leap and month != leap_month:
            return None
        if is_leap or offset >= leap_offset:
            offset += 1
    elif is_leap:
        return None
    try:
        result = date.fromordinal(_new_moon_day(cycle + offset) + day - 1 - 1721425)
    except (ValueError, OverflowError):
        return None
    # Doi nguoc de loai ngay 30 cua thang chi co 29 ngay.
    return result if solar_to_lunar(result) == LunarDate(day, month, year, is_leap) else None
