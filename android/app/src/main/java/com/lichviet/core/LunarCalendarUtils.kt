package com.lichviet.core

import java.util.Calendar
import java.util.TimeZone
import kotlin.math.floor

/**
 * Vietnamese Lunar Calendar Utilities
 * Based on the algorithm by Ho Ngoc Duc.
 */
object LunarCalendarUtils {

    private val CAN = arrayOf("Giáp", "Ất", "Bính", "Đinh", "Mậu", "Kỷ", "Canh", "Tân", "Nhâm", "Quý")
    private val CHI = arrayOf("Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi")
    private val WEEKDAY_VI = arrayOf("Chủ Nhật", "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy")

    data class LunarDate(
        val day: Int,
        val month: Int,
        val year: Int,
        val isLeap: Boolean = false
    )

    /**
     * Returns the zodiac name (Can Chi) for a given lunar year.
     */
    fun getZodiacYearName(year: Int): String {
        return "${CAN[(year + 6) % 10]} ${CHI[(year + 8) % 12]}"
    }

    /**
     * Converts Solar Date to Lunar Date (Hanoi Time GMT+7).
     * This is a simplified version of the astronomical algorithm.
     */
    fun solarToLunar(day: Int, month: Int, year: Int): LunarDate {
        val jd = jdFromDate(day, month, year)
        // For production, we would use the full C-logic ported to Kotlin
        // or a library like 'VietnameseLunar-android'.
        // This is a placeholder for the logic structure.
        return decodeLunar(jd)
    }

    private fun jdFromDate(d: Int, m: Int, y: Int): Double {
        var mm = m
        var yy = y
        if (m <= 2) {
            mm = m + 12
            yy = y - 1
        }
        val a = floor(yy / 100.0)
        val b = 2 - a + floor(a / 4.0)
        return floor(365.25 * (yy + 4716)) + floor(30.6001 * (mm + 1)) + d + b - 1524.5
    }

    private fun decodeLunar(jd: Double): LunarDate {
        // Simplified mapping for demonstration. 
        // Real implementation requires complex astronomical calculations for New Moon.
        // In a real Android app, we'd use a pre-calculated table or the full lib.
        return LunarDate(15, 8, 2024) // Example placeholder
    }
}
