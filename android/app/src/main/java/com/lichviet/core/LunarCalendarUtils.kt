package com.lichviet.core

import java.time.DateTimeException
import java.time.LocalDate
import kotlin.math.PI
import kotlin.math.floor
import kotlin.math.sin

/** Tinh ngay am theo soc va tiet khi tai mui gio Viet Nam UTC+7. */
object LunarCalendarUtils {

    private val CAN = arrayOf("Giáp", "Ất", "Bính", "Đinh", "Mậu", "Kỷ", "Canh", "Tân", "Nhâm", "Quý")
    private val CHI = arrayOf("Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi")
    private const val lunarEpoch = 2415021.076998695
    private const val synodicMonth = 29.530588853
    private const val timeZone = 7.0

    data class LunarDate(
        val day: Int,
        val month: Int,
        val year: Int,
        val isLeap: Boolean = false
    )

    fun getZodiacYearName(year: Int): String {
        return "${CAN[Math.floorMod(year + 6, 10)]} ${CHI[Math.floorMod(year + 8, 12)]}"
    }

    fun solarToLunar(day: Int, month: Int, year: Int): LunarDate {
        val julianDay = julianDay(LocalDate.of(year, month, day))
        var cycle = floor((julianDay - lunarEpoch) / synodicMonth).toInt()
        var start = newMoonDay(cycle)
        // Hieu chinh moc uoc luong de ngay luon nam giua hai lan soc.
        for (attempt in 0 until 3) {
            if (start > julianDay) cycle--
            else if (newMoonDay(cycle + 1) <= julianDay) cycle++
            else break
            start = newMoonDay(cycle)
        }
        check(start <= julianDay && newMoonDay(cycle + 1) > julianDay) { "Cannot locate lunar month" }
        var anchor = monthEleven(year)
        var end = anchor
        var lunarYear: Int
        if (anchor >= start) {
            lunarYear = year
            anchor = monthEleven(year - 1)
        } else {
            lunarYear = year + 1
            end = monthEleven(year + 1)
        }
        val lunarDay = julianDay - start + 1
        val offset = floor((start - anchor) / 29.0).toInt()
        var lunarMonth = offset + 11
        var leap = false
        if (end - anchor > 365) {
            val leapOffset = leapMonthOffset(anchor)
            if (offset >= leapOffset) {
                lunarMonth = offset + 10
                leap = offset == leapOffset
            }
        }
        if (lunarMonth > 12) lunarMonth -= 12
        if (lunarMonth >= 11 && offset < 4) lunarYear--
        return LunarDate(lunarDay, lunarMonth, lunarYear, leap)
    }

    fun lunarToSolar(day: Int, month: Int, year: Int, isLeap: Boolean = false): LocalDate? {
        if (day !in 1..30 || month !in 1..12 || year !in 1900..2199) return null
        val anchor = monthEleven(if (month < 11) year - 1 else year)
        val end = monthEleven(if (month < 11) year else year + 1)
        val cycle = floor(0.5 + (anchor - lunarEpoch) / synodicMonth).toInt()
        var offset = Math.floorMod(month - 11, 12)
        if (end - anchor > 365) {
            val leapOffset = leapMonthOffset(anchor)
            val leapMonth = Math.floorMod(leapOffset - 2, 12).let { if (it == 0) 12 else it }
            if (isLeap && month != leapMonth) return null
            if (isLeap || offset >= leapOffset) offset++
        } else if (isLeap) {
            return null
        }
        val result = try {
            LocalDate.ofEpochDay((newMoonDay(cycle + offset) + day - 1 - 2440588).toLong())
        } catch (_: DateTimeException) {
            return null
        }
        // Doi nguoc de loai ngay 30 cua thang chi co 29 ngay.
        return result.takeIf {
            solarToLunar(it.dayOfMonth, it.monthValue, it.year) == LunarDate(day, month, year, isLeap)
        }
    }

    private fun julianDay(date: LocalDate): Int = (date.toEpochDay() + 2440588).toInt()

    private fun newMoonDay(cycle: Int): Int {
        val t = cycle / 1236.85
        val t2 = t * t
        val t3 = t2 * t
        val radians = PI / 180
        val solarAnomaly = (359.2242 + 29.10535608 * cycle - 0.0000333 * t2 - 0.00000347 * t3) * radians
        val lunarAnomaly = (306.0253 + 385.81691806 * cycle + 0.0107306 * t2 + 0.00001236 * t3) * radians
        val latitude = (21.2964 + 390.67050646 * cycle - 0.0016528 * t2 - 0.00000239 * t3) * radians
        val base = 2415020.75933 + 29.53058868 * cycle + 0.0001178 * t2 - 0.000000155 * t3 +
            0.00033 * sin((166.56 + 132.87 * t - 0.009173 * t2) * radians)
        val correction = (0.1734 - 0.000393 * t) * sin(solarAnomaly) + 0.0021 * sin(2 * solarAnomaly) -
            0.4068 * sin(lunarAnomaly) + 0.0161 * sin(2 * lunarAnomaly) - 0.0004 * sin(3 * lunarAnomaly) +
            0.0104 * sin(2 * latitude) - 0.0051 * sin(solarAnomaly + lunarAnomaly) -
            0.0074 * sin(solarAnomaly - lunarAnomaly) + 0.0004 * sin(2 * latitude + solarAnomaly) -
            0.0004 * sin(2 * latitude - solarAnomaly) - 0.0006 * sin(2 * latitude + lunarAnomaly) +
            0.0010 * sin(2 * latitude - lunarAnomaly) + 0.0005 * sin(2 * lunarAnomaly + solarAnomaly)
        val delta = if (t < -11) {
            0.001 + 0.000839 * t + 0.0002261 * t2 - 0.00000845 * t3 - 0.000000081 * t * t3
        } else {
            -0.000278 + 0.000265 * t + 0.000262 * t2
        }
        return floor(base + correction - delta + 0.5 + timeZone / 24).toInt()
    }

    private fun solarSector(day: Int): Int {
        val t = (day - 2451545.5 - timeZone / 24) / 36525
        val radians = PI / 180
        val anomaly = (357.52910 + 35999.05030 * t - 0.0001559 * t * t - 0.00000048 * t * t * t) * radians
        val mean = 280.46645 + 36000.76983 * t + 0.0003032 * t * t
        val correction = (1.914600 - 0.004817 * t - 0.000014 * t * t) * sin(anomaly) +
            (0.019993 - 0.000101 * t) * sin(2 * anomaly) + 0.000290 * sin(3 * anomaly)
        val longitude = (mean + correction) * radians
        val normalized = longitude - 2 * PI * floor(longitude / (2 * PI))
        return floor(normalized / PI * 6).toInt()
    }

    private fun monthEleven(year: Int): Int {
        val offset = julianDay(LocalDate.of(year, 12, 31)) - 2415021
        val cycle = floor(offset / synodicMonth).toInt()
        val day = newMoonDay(cycle)
        return if (solarSector(day) >= 9) newMoonDay(cycle - 1) else day
    }

    private fun leapMonthOffset(anchor: Int): Int {
        val cycle = floor(0.5 + (anchor - lunarEpoch) / synodicMonth).toInt()
        var offset = 1
        var sector = solarSector(newMoonDay(cycle + offset))
        do {
            val previous = sector
            offset++
            sector = solarSector(newMoonDay(cycle + offset))
        } while (sector != previous && offset < 14)
        return offset - 1
    }
}
