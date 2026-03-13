package com.lichviet.data

import kotlinx.coroutines.flow.Flow

class ReminderRepository(private val reminderDao: ReminderDao) {
    val allReminders: Flow<List<ReminderEntity>> = reminderDao.getAllReminders()

    suspend fun addReminder(reminder: ReminderEntity) {
        reminderDao.insertReminder(reminder)
    }

    suspend fun updateReminder(reminder: ReminderEntity) {
        reminderDao.updateReminder(reminder)
    }

    suspend fun deleteReminder(id: Long) {
        reminderDao.deleteReminderById(id)
    }

    suspend fun getActiveReminders(): List<ReminderEntity> {
        return reminderDao.getActiveReminders()
    }
}
