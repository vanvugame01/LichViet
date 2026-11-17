package com.lichviet.core

import java.time.LocalDate
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class LunarCalendarUtilsTest {
    @Test
    fun lunarNewYearDates() {
        assertEquals(LunarCalendarUtils.LunarDate(1, 1, 2007), LunarCalendarUtils.solarToLunar(17, 2, 2007))
        assertEquals(LunarCalendarUtils.LunarDate(1, 1, 2024), LunarCalendarUtils.solarToLunar(10, 2, 2024))
        assertEquals(LunarCalendarUtils.LunarDate(1, 1, 2025), LunarCalendarUtils.solarToLunar(29, 1, 2025))
        assertEquals(LunarCalendarUtils.LunarDate(1, 1, 2026), LunarCalendarUtils.solarToLunar(17, 2, 2026))
        assertEquals(LunarCalendarUtils.LunarDate(9, 10, 2026), LunarCalendarUtils.solarToLunar(17, 11, 2026))
    }

    @Test
    fun leapMonthIsDistinctFromRegularMonth() {
        assertEquals(LunarCalendarUtils.LunarDate(1, 2, 2023, true), LunarCalendarUtils.solarToLunar(22, 3, 2023))
        assertEquals(LocalDate.of(2023, 3, 22), LunarCalendarUtils.lunarToSolar(1, 2, 2023, true))
        assertEquals(LocalDate.of(2023, 2, 20), LunarCalendarUtils.lunarToSolar(1, 2, 2023, false))
        assertNull(LunarCalendarUtils.lunarToSolar(1, 2, 2026, true))
    }

    @Test
    fun impossibleDatesAreRejected() {
        assertNull(LunarCalendarUtils.lunarToSolar(0, 1, 2026))
        assertNull(LunarCalendarUtils.lunarToSolar(31, 1, 2026))
        assertNull(LunarCalendarUtils.lunarToSolar(1, 13, 2026))
        assertNull(LunarCalendarUtils.lunarToSolar(30, 2, 2025))
    }

    @Test
    fun roundTripAcrossLeapYearsAndCenturyBoundaries() {
        var solar = LocalDate.of(1900, 1, 1)
        while (solar.year < 2200) {
            val lunar = LunarCalendarUtils.solarToLunar(solar.dayOfMonth, solar.monthValue, solar.year)
            org.junit.Assert.assertTrue(solar.toString(), lunar.day in 1..30)
            org.junit.Assert.assertTrue(solar.toString(), lunar.month in 1..12)
            if (lunar.year >= 1900) {
                assertEquals(solar.toString(), solar, LunarCalendarUtils.lunarToSolar(lunar.day, lunar.month, lunar.year, lunar.isLeap))
            }
            solar = solar.plusDays(1)
        }
    }
}
