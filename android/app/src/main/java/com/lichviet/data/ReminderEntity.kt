package com.lichviet.data

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "reminders")
data class ReminderEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val title: String,
    val lunarDay: Int,
    val lunarMonth: Int,
    val lunarYear: Int?, // NULL if repeat yearly
    val hour: Int,
    val minute: Int,
    val isRepeatYearly: Boolean,
    val isEnabled: Boolean = true,
    val lastTriggeredDate: String? = null
)
