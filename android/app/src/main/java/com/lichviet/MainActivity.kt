package com.lichviet

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.room.Room
import com.lichviet.data.AppDatabase
import com.lichviet.data.ReminderRepository
import com.lichviet.ui.LichVietApp

class MainActivity : ComponentActivity() {
    private val database by lazy {
        Room.databaseBuilder(applicationContext, AppDatabase::class.java, "lichviet.db")
            .addMigrations(AppDatabase.MIGRATION_1_2)
            .build()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val repository = ReminderRepository(database.reminderDao())
        setContent { LichVietApp(repository) }
    }
}
