package com.lichviet.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.lichviet.core.LunarCalendarUtils
import java.util.*

@Composable
fun CalendarScreen() {
    var currentMonth by remember { mutableStateOf(Calendar.getInstance()) }
    var selectedDate by remember { mutableStateOf(Calendar.getInstance()) }

    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        MonthHeader(currentMonth) { offset ->
            val newMonth = currentMonth.clone() as Calendar
            newMonth.add(Calendar.MONTH, offset)
            currentMonth = newMonth
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        WeekdayHeader()
        
        CalendarGrid(currentMonth, selectedDate) { date ->
            selectedDate = date
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        DateDetail(selectedDate)
    }
}

@Composable
fun MonthHeader(month: Calendar, onMonthChange: (Int) -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        IconButton(onClick = { onMonthChange(-1) }) {
            Text("‹", fontSize = 24.sp)
        }
        Text(
            text = "THÁNG ${month.get(Calendar.MONTH) + 1}, ${month.get(Calendar.YEAR)}",
            style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.Bold
        )
        IconButton(onClick = { onMonthChange(1) }) {
            Text("›", fontSize = 24.sp)
        }
    }
}

@Composable
fun WeekdayHeader() {
    val days = listOf("T2", "T3", "T4", "T5", "T6", "T7", "CN")
    Row(modifier = Modifier.fillMaxWidth()) {
        days.forEachIndexed { index, day ->
            Text(
                text = day,
                modifier = Modifier.weight(1f),
                textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                color = if (index == 6) Color.Red else Color.Unspecified,
                fontWeight = FontWeight.SemiBold
            )
        }
    }
}

@Composable
fun CalendarGrid(month: Calendar, selectedDate: Calendar, onDateClick: (Calendar) -> Unit) {
    val days = remember(month) { getDaysInMonth(month) }
    
    LazyVerticalGrid(
        columns = GridCells.Fixed(7),
        modifier = Modifier.height(300.dp)
    ) {
        items(days) { date ->
            DayCell(date, selectedDate, month) {
                onDateClick(date)
            }
        }
    }
}

@Composable
fun DayCell(date: Calendar, selectedDate: Calendar, currentMonth: Calendar, onClick: () -> Unit) {
    val isSelected = isSameDay(date, selectedDate)
    val isInMonth = date.get(Calendar.MONTH) == currentMonth.get(Calendar.MONTH)
    val lunarDate = LunarCalendarUtils.solarToLunar(
        date.get(Calendar.DAY_OF_MONTH),
        date.get(Calendar.MONTH) + 1,
        date.get(Calendar.YEAR)
    )

    Column(
        modifier = Modifier
            .aspectRatio(1f)
            .padding(2.dp)
            .background(
                if (isSelected) Color(0xFFFFF8EE) else Color.Transparent,
                shape = MaterialTheme.shapes.small
            )
            .clickable { onClick() },
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = date.get(Calendar.DAY_OF_MONTH).toString(),
            color = if (isInMonth) Color.Black else Color.LightGray,
            fontWeight = FontWeight.Bold
        )
        Text(
            text = if (lunarDate.day == 1) "1/${lunarDate.month}" else lunarDate.day.toString(),
            fontSize = 10.sp,
            color = if (lunarDate.day == 1) Color.Red else Color.Gray
        )
    }
}

@Composable
fun DateDetail(date: Calendar) {
    val lunar = LunarCalendarUtils.solarToLunar(
        date.get(Calendar.DAY_OF_MONTH),
        date.get(Calendar.MONTH) + 1,
        date.get(Calendar.YEAR)
    )
    
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text("Âm lịch", style = MaterialTheme.typography.labelSmall)
            Text(
                "Ngày ${lunar.day} Tháng ${lunar.month}",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold
            )
            Text(
                "Năm ${LunarCalendarUtils.getZodiacYearName(lunar.year)}",
                style = MaterialTheme.typography.bodyMedium
            )
        }
    }
}

// Helper functions (simplified)
fun getDaysInMonth(month: Calendar): List<Calendar> {
    val calendar = month.clone() as Calendar
    calendar.set(Calendar.DAY_OF_MONTH, 1)
    val firstDayOfWeek = (calendar.get(Calendar.DAY_OF_WEEK) + 5) % 7 // Align with Monday
    calendar.add(Calendar.DAY_OF_MONTH, -firstDayOfWeek)
    
    return List(42) {
        val day = calendar.clone() as Calendar
        calendar.add(Calendar.DAY_OF_MONTH, 1)
        day
    }
}

fun isSameDay(c1: Calendar, c2: Calendar): Boolean {
    return c1.get(Calendar.YEAR) == c2.get(Calendar.YEAR) &&
           c1.get(Calendar.DAY_OF_YEAR) == c2.get(Calendar.DAY_OF_YEAR)
}
