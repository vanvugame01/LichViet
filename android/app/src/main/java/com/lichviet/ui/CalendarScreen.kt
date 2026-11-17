package com.lichviet.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.DateRange
import androidx.compose.material.icons.filled.KeyboardArrowLeft
import androidx.compose.material.icons.filled.KeyboardArrowRight
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material.icons.filled.Notifications
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.lichviet.core.LunarCalendarUtils
import com.lichviet.data.ReminderEntity
import com.lichviet.data.ReminderRepository
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.time.LocalDate
import java.time.YearMonth
import java.time.format.DateTimeFormatter
import java.util.Locale

private val Vietnamese = Locale.forLanguageTag("vi-VN")
private val DateFormat = DateTimeFormatter.ofPattern("EEEE, dd/MM/yyyy", Vietnamese)
private val LightColors = lightColorScheme(
    primary = Color(0xFF9C4700), onPrimary = Color.White,
    primaryContainer = Color(0xFFFFEBC7), onPrimaryContainer = Color(0xFF643100),
    secondary = Color(0xFF006C4C), onSecondary = Color.White,
    secondaryContainer = Color(0xFFD6F5E6), onSecondaryContainer = Color(0xFF004D36),
    background = Color(0xFFF8FAFC), onBackground = Color(0xFF0F172A),
    surface = Color(0xFFF8FAFC), onSurface = Color(0xFF0F172A),
    surfaceVariant = Color(0xFFEFF2F6), onSurfaceVariant = Color(0xFF475569),
    outline = Color(0xFF64748B), outlineVariant = Color(0xFFCBD5E1)
)
private val DarkColors = darkColorScheme(
    primary = Color(0xFFFFB874), onPrimary = Color(0xFF4C2500),
    primaryContainer = Color(0xFF663300), onPrimaryContainer = Color(0xFFFFDDBB),
    secondary = Color(0xFF83DCB4), onSecondary = Color(0xFF003825),
    secondaryContainer = Color(0xFF005138), onSecondaryContainer = Color(0xFFACF2CE),
    background = Color(0xFF101820), onBackground = Color(0xFFE7EDF5),
    surface = Color(0xFF101820), onSurface = Color(0xFFE7EDF5),
    surfaceVariant = Color(0xFF25313E), onSurfaceVariant = Color(0xFFC2CDD9),
    outline = Color(0xFFA2ADBB), outlineVariant = Color(0xFF475569)
)

@Composable
fun LichVietTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = if (isSystemInDarkTheme()) DarkColors else LightColors,
        shapes = Shapes(
            small = RoundedCornerShape(8.dp), medium = RoundedCornerShape(12.dp),
            large = RoundedCornerShape(16.dp)
        ),
        content = content
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LichVietApp(repository: ReminderRepository) {
    LichVietTheme {
        var activeTab by rememberSaveable { mutableStateOf(0) }
        var selectedDay by rememberSaveable { mutableStateOf(LocalDate.now().toEpochDay()) }
        var monthText by rememberSaveable { mutableStateOf(YearMonth.now().toString()) }
        var showAddDialog by rememberSaveable { mutableStateOf(false) }
        var isSaving by remember { mutableStateOf(false) }
        var saveError by remember { mutableStateOf<String?>(null) }
        val snackbar = remember { SnackbarHostState() }
        val scope = rememberCoroutineScope()
        val reminderFlow = remember(repository) {
            repository.allReminders.catch { error ->
                if (error is CancellationException) throw error
                snackbar.showSnackbar("Không đọc được lịch đã lưu. Hãy đóng và mở lại ứng dụng.")
                emit(emptyList())
            }
        }
        val reminders by reminderFlow.collectAsStateWithLifecycle(initialValue = emptyList())
        val selectedDate = LocalDate.ofEpochDay(selectedDay)
        val month = YearMonth.parse(monthText)

        fun changeReminder(reminder: ReminderEntity, enabled: Boolean) {
            scope.launch {
                try {
                    repository.updateReminder(reminder.copy(isEnabled = enabled))
                } catch (error: Exception) {
                    if (error is CancellationException) throw error
                    snackbar.showSnackbar("Không lưu được thay đổi. Vui lòng thử lại.")
                }
            }
        }

        fun deleteReminder(reminder: ReminderEntity) {
            scope.launch {
                try {
                    repository.deleteReminder(reminder.id)
                    val result = snackbar.showSnackbar(
                        "Đã xóa ${reminder.title}", actionLabel = "Hoàn tác",
                        withDismissAction = true, duration = SnackbarDuration.Long
                    )
                    if (result == SnackbarResult.ActionPerformed) repository.addReminder(reminder)
                } catch (error: Exception) {
                    if (error is CancellationException) throw error
                    snackbar.showSnackbar("Không thực hiện được thao tác. Vui lòng thử lại.")
                }
            }
        }

        Scaffold(
            containerColor = MaterialTheme.colorScheme.background,
            contentWindowInsets = WindowInsets.safeDrawing,
            topBar = {
                TopAppBar(
                    title = { Text(if (activeTab == 0) "Lịch Việt" else "Nhắc việc", fontWeight = FontWeight.Bold) },
                    navigationIcon = {
                        Icon(Icons.Default.DateRange, null, Modifier.padding(start = 16.dp), tint = MaterialTheme.colorScheme.primary)
                    },
                    colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background)
                )
            },
            bottomBar = {
                NavigationBar(containerColor = MaterialTheme.colorScheme.surface) {
                    NavigationBarItem(
                        selected = activeTab == 0, onClick = { activeTab = 0 },
                        icon = { Icon(Icons.Default.DateRange, null) }, label = { Text("Lịch") }
                    )
                    NavigationBarItem(
                        selected = activeTab == 1, onClick = { activeTab = 1 },
                        icon = { Icon(Icons.Default.Notifications, null) }, label = { Text("Nhắc việc") }
                    )
                }
            },
            floatingActionButton = {
                if (activeTab == 0) FloatingActionButton(
                    onClick = { saveError = null; showAddDialog = true },
                    containerColor = MaterialTheme.colorScheme.primary,
                    contentColor = MaterialTheme.colorScheme.onPrimary
                ) { Icon(Icons.Default.Add, contentDescription = "Thêm lịch âm") }
            },
            snackbarHost = { SnackbarHost(snackbar) }
        ) { insets ->
            if (activeTab == 0) {
                CalendarScreen(
                    month = month, selectedDate = selectedDate, reminders = reminders,
                    modifier = Modifier.padding(insets),
                    onMonthChange = { offset ->
                        val next = month.plusMonths(offset.toLong())
                        if (next.year in 1900..2199) monthText = next.toString()
                    },
                    onToday = {
                        selectedDay = LocalDate.now().toEpochDay()
                        monthText = YearMonth.now().toString()
                    },
                    onDateSelect = { date ->
                        selectedDay = date.toEpochDay()
                        monthText = YearMonth.from(date).toString()
                    }
                )
            } else {
                RemindersScreen(
                    reminders = reminders, modifier = Modifier.padding(insets),
                    onAdd = { saveError = null; showAddDialog = true },
                    onToggle = ::changeReminder, onDelete = ::deleteReminder
                )
            }
        }

        if (showAddDialog) AddReminderDialog(
            initialDate = selectedDate, isSaving = isSaving, errorMessage = saveError,
            onDismiss = { if (!isSaving) showAddDialog = false },
            onSave = { reminder ->
                isSaving = true
                saveError = null
                scope.launch {
                    try {
                        val valid = reminder.isRepeatYearly || withContext(Dispatchers.Default) {
                            LunarCalendarUtils.lunarToSolar(
                                reminder.lunarDay, reminder.lunarMonth, reminder.lunarYear!!, reminder.isLeap
                            ) != null
                        }
                        if (!valid) {
                            saveError = "Ngày âm này không tồn tại trong năm đã chọn. Hãy kiểm tra ngày và tháng nhuận."
                        } else {
                            repository.addReminder(reminder)
                            showAddDialog = false
                            isSaving = false
                            snackbar.showSnackbar("Đã lưu lịch")
                        }
                    } catch (error: Exception) {
                        if (error is CancellationException) throw error
                        saveError = "Không lưu được lịch. Thông tin vẫn được giữ lại; vui lòng thử lại."
                    } finally {
                        isSaving = false
                    }
                }
            }
        )
    }
}

@Composable
fun CalendarScreen(
    month: YearMonth, selectedDate: LocalDate, reminders: List<ReminderEntity>,
    modifier: Modifier = Modifier, onMonthChange: (Int) -> Unit,
    onToday: () -> Unit, onDateSelect: (LocalDate) -> Unit
) {
    val selectedLunar = remember(selectedDate) { lunarDate(selectedDate) }
    val dayReminders = reminders.filter { it.isEnabled && matchesLunarDate(it, selectedLunar) }
    Column(
        modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 16.dp).padding(bottom = 88.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Column {
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                IconButton(onClick = { onMonthChange(-1) }, enabled = month > YearMonth.of(1900, 1)) {
                    Icon(Icons.Default.KeyboardArrowLeft, "Tháng trước")
                }
                Text(
                    "Tháng ${month.monthValue}, ${month.year}", Modifier.weight(1f),
                    style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold
                )
                IconButton(onClick = { onMonthChange(1) }, enabled = month < YearMonth.of(2199, 12)) {
                    Icon(Icons.Default.KeyboardArrowRight, "Tháng sau")
                }
            }
            TextButton(onClick = onToday, modifier = Modifier.align(Alignment.End)) { Text("Hôm nay") }
        }
        CalendarGrid(month, selectedDate, reminders, onDateSelect)
        DateDetail(selectedDate)
        Text("Nhắc việc trong ngày", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
        if (dayReminders.isEmpty()) {
            Text("Chưa có nhắc việc cho ngày này.", color = MaterialTheme.colorScheme.onSurfaceVariant)
        } else {
            dayReminders.forEach { reminder ->
                OutlinedCard(Modifier.fillMaxWidth()) {
                    Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                        Box(Modifier.width(4.dp).height(32.dp).background(MaterialTheme.colorScheme.primary, CircleShape))
                        Column(Modifier.padding(start = 12.dp).weight(1f)) {
                            Text(reminder.title, fontWeight = FontWeight.SemiBold)
                            Text(
                                "${formatTime(reminder)} · ${if (reminder.isRepeatYearly) "Lặp hằng năm" else "Một lần"}",
                                style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun CalendarGrid(
    month: YearMonth, selectedDate: LocalDate, reminders: List<ReminderEntity>, onDateSelect: (LocalDate) -> Unit
) {
    val start = remember(month) { month.atDay(1).minusDays((month.atDay(1).dayOfWeek.value - 1).toLong()) }
    val today = LocalDate.now()
    OutlinedCard(Modifier.fillMaxWidth()) {
        Row(Modifier.fillMaxWidth().padding(vertical = 8.dp)) {
            listOf("T2", "T3", "T4", "T5", "T6", "T7", "CN").forEachIndexed { index, text ->
                Box(Modifier.weight(1f), contentAlignment = Alignment.Center) {
                    Text(text, style = MaterialTheme.typography.labelLarge,
                        color = if (index == 6) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
        repeat(6) { row ->
            Row(Modifier.fillMaxWidth()) {
                repeat(7) { column ->
                    val day = start.plusDays((row * 7 + column).toLong())
                    val lunar = remember(day) { lunarDate(day) }
                    val hasReminder = reminders.any { it.isEnabled && matchesLunarDate(it, lunar) }
                    DayCell(day, lunar, selectedDate, month, day == today, hasReminder, Modifier.weight(1f)) {
                        if (day.year in 1900..2199) onDateSelect(day)
                    }
                }
            }
        }
    }
}

@Composable
private fun DayCell(
    date: LocalDate, lunar: LunarCalendarUtils.LunarDate, selectedDate: LocalDate,
    currentMonth: YearMonth, isToday: Boolean, hasReminder: Boolean,
    modifier: Modifier, onClick: () -> Unit
) {
    val isSelected = date == selectedDate
    val colors = MaterialTheme.colorScheme
    val background = if (isSelected) colors.primaryContainer else colors.surface
    val foreground = when {
        isSelected -> colors.onPrimaryContainer
        YearMonth.from(date) != currentMonth -> colors.onSurfaceVariant
        isToday -> colors.secondary
        else -> colors.onSurface
    }
    val label = buildString {
        append(date.format(DateFormat))
        append(", âm lịch ${lunar.day}/${lunar.month}/${lunar.year}")
        if (lunar.isLeap) append(", tháng nhuận")
        if (isToday) append(", hôm nay")
        if (hasReminder) append(", có nhắc việc")
    }
    Column(
        modifier.padding(2.dp).heightIn(min = 58.dp)
            .background(background, MaterialTheme.shapes.small)
            .then(if (isSelected || isToday) Modifier.border(
                1.dp, if (isSelected) colors.primary else colors.secondary, MaterialTheme.shapes.small
            ) else Modifier)
            .selectable(selected = isSelected, role = Role.Button, enabled = date.year in 1900..2199, onClick = onClick)
            .semantics(mergeDescendants = true) { contentDescription = label; selected = isSelected }
            .padding(vertical = 6.dp),
        horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center
    ) {
        Text(date.dayOfMonth.toString(), fontWeight = FontWeight.Bold, color = foreground,
            style = MaterialTheme.typography.bodyLarge)
        Text("${lunar.day}/${lunar.month}", style = MaterialTheme.typography.labelSmall,
            color = if (isSelected) colors.onPrimaryContainer else colors.onSurfaceVariant)
        Box(Modifier.size(4.dp).background(if (hasReminder) colors.primary else Color.Transparent, CircleShape))
    }
}

@Composable
private fun DateDetail(date: LocalDate) {
    val lunar = remember(date) { lunarDate(date) }
    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
        Row(Modifier.fillMaxWidth().padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
            Icon(Icons.Default.DateRange, null, tint = MaterialTheme.colorScheme.secondary)
            Column(Modifier.padding(start = 12.dp)) {
                Text(date.format(DateFormat).replaceFirstChar { it.titlecase(Vietnamese) }, fontWeight = FontWeight.Bold)
                Text(
                    "Âm lịch · ${lunar.day}/${lunar.month}${if (lunar.isLeap) " nhuận" else ""} · ${LunarCalendarUtils.getZodiacYearName(lunar.year)}",
                    style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

@Composable
private fun RemindersScreen(
    reminders: List<ReminderEntity>, modifier: Modifier = Modifier, onAdd: () -> Unit,
    onToggle: (ReminderEntity, Boolean) -> Unit, onDelete: (ReminderEntity) -> Unit
) {
    LazyColumn(
        modifier.fillMaxSize(), contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item { Text("${reminders.size} lịch đã lưu", color = MaterialTheme.colorScheme.onSurfaceVariant) }
        if (reminders.isEmpty()) {
            item {
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("Chưa có lịch âm", style = MaterialTheme.typography.titleMedium)
                        Text("Thêm ngày giỗ hoặc việc cần nhớ theo âm lịch.")
                    }
                }
            }
        }
        items(reminders, key = { it.id }) { reminder ->
            ReminderCard(reminder, onToggle, onDelete)
        }
        item {
            Button(onClick = onAdd, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) {
                Icon(Icons.Default.Add, null)
                Spacer(Modifier.width(8.dp))
                Text("Thêm lịch âm")
            }
        }
        item {
            Text(
                "Android hiện lưu và quản lý lịch. Thông báo nhắc việc chạy nền chưa được hỗ trợ.",
                style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
private fun ReminderCard(
    reminder: ReminderEntity, onToggle: (ReminderEntity, Boolean) -> Unit, onDelete: (ReminderEntity) -> Unit
) {
    var showMenu by remember { mutableStateOf(false) }
    OutlinedCard(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(reminder.title, Modifier.weight(1f), fontWeight = FontWeight.Bold)
                Switch(
                    checked = reminder.isEnabled, onCheckedChange = { onToggle(reminder, it) },
                    modifier = Modifier.semantics { contentDescription = "Nhắc việc ${reminder.title}" }
                )
                Box {
                    IconButton(onClick = { showMenu = true }) { Icon(Icons.Default.MoreVert, "Thao tác với ${reminder.title}") }
                    DropdownMenu(expanded = showMenu, onDismissRequest = { showMenu = false }) {
                        DropdownMenuItem(
                            text = { Text("Xóa lịch", color = MaterialTheme.colorScheme.error) },
                            onClick = { showMenu = false; onDelete(reminder) }
                        )
                    }
                }
            }
            Text(
                "${reminder.lunarDay}/${reminder.lunarMonth}${if (reminder.isLeap) " nhuận" else ""} âm lịch · ${formatTime(reminder)}",
                style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Text(
                "${if (reminder.isRepeatYearly) "Hằng năm" else "Năm ${reminder.lunarYear}"} · ${if (reminder.isEnabled) "Đang bật" else "Đang tắt"}",
                style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
private fun AddReminderDialog(
    initialDate: LocalDate, isSaving: Boolean, errorMessage: String?,
    onDismiss: () -> Unit, onSave: (ReminderEntity) -> Unit
) {
    val initialLunar = remember(initialDate) { lunarDate(initialDate) }
    var title by rememberSaveable { mutableStateOf("") }
    var day by rememberSaveable { mutableStateOf(initialLunar.day.toString()) }
    var month by rememberSaveable { mutableStateOf(initialLunar.month.toString()) }
    var year by rememberSaveable { mutableStateOf(initialLunar.year.toString()) }
    var hour by rememberSaveable { mutableStateOf("08") }
    var minute by rememberSaveable { mutableStateOf("00") }
    var repeatYearly by rememberSaveable { mutableStateOf(true) }
    var leapMonth by rememberSaveable { mutableStateOf(initialLunar.isLeap) }
    var attempted by rememberSaveable { mutableStateOf(false) }
    val validTitle = title.isNotBlank()
    val validDay = day.toIntOrNull() in 1..30
    val validMonth = month.toIntOrNull() in 1..12
    val validYear = repeatYearly || year.toIntOrNull() in 1900..2199
    val validHour = hour.toIntOrNull() in 0..23
    val validMinute = minute.toIntOrNull() in 0..59
    val valid = validTitle && validDay && validMonth && validYear && validHour && validMinute
    Dialog(onDismissRequest = onDismiss) {
        Surface(shape = MaterialTheme.shapes.large, tonalElevation = 6.dp) {
            Column(
                Modifier.fillMaxWidth().imePadding().verticalScroll(rememberScrollState()).padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Text("Thêm lịch âm", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
                OutlinedTextField(
                    value = title, onValueChange = { title = it }, label = { Text("Tiêu đề") },
                    singleLine = true, enabled = !isSaving, modifier = Modifier.fillMaxWidth(),
                    isError = attempted && !validTitle,
                    supportingText = { if (attempted && !validTitle) Text("Nhập tên việc cần nhớ.") }
                )
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    NumberField("Ngày âm", day, { day = it }, !isSaving, attempted && !validDay, "Từ 1 đến 30", Modifier.weight(1f))
                    NumberField("Tháng âm", month, { month = it }, !isSaving, attempted && !validMonth, "Từ 1 đến 12", Modifier.weight(1f))
                }
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Lặp hằng năm", Modifier.weight(1f))
                    Switch(checked = repeatYearly, onCheckedChange = { repeatYearly = it }, enabled = !isSaving,
                        modifier = Modifier.semantics { contentDescription = "Lặp hằng năm" })
                }
                if (!repeatYearly) NumberField(
                    "Năm âm", year, { year = it }, !isSaving, attempted && !validYear, "Từ 1900 đến 2199", Modifier.fillMaxWidth()
                )
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Tháng nhuận", Modifier.weight(1f))
                    Switch(checked = leapMonth, onCheckedChange = { leapMonth = it }, enabled = !isSaving,
                        modifier = Modifier.semantics { contentDescription = "Tháng nhuận" })
                }
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    NumberField("Giờ", hour, { hour = it }, !isSaving, attempted && !validHour, "Từ 0 đến 23", Modifier.weight(1f))
                    NumberField("Phút", minute, { minute = it }, !isSaving, attempted && !validMinute, "Từ 0 đến 59", Modifier.weight(1f))
                }
                Text(
                    "Lịch lặp chỉ áp dụng khi ngày âm và tháng nhuận đã chọn tồn tại trong năm đó.",
                    style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Text(
                    "Android chưa hỗ trợ thông báo nhắc việc chạy nền.",
                    style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                if (errorMessage != null) Text(
                    errorMessage, color = MaterialTheme.colorScheme.error,
                    modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite }
                )
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp, Alignment.End)) {
                    OutlinedButton(onClick = onDismiss, enabled = !isSaving) { Text("Hủy") }
                    Button(onClick = {
                        attempted = true
                        if (valid) onSave(ReminderEntity(
                            title = title.trim(), lunarDay = day.toInt(), lunarMonth = month.toInt(),
                            lunarYear = if (repeatYearly) null else year.toInt(),
                            hour = hour.toInt(), minute = minute.toInt(),
                            isRepeatYearly = repeatYearly, isLeap = leapMonth
                        ))
                    }, enabled = !isSaving) { Text(if (isSaving) "Đang lưu…" else "Lưu lịch") }
                }
            }
        }
    }
}

@Composable
private fun NumberField(
    label: String, value: String, onValueChange: (String) -> Unit, enabled: Boolean,
    isError: Boolean, hint: String, modifier: Modifier
) {
    OutlinedTextField(
        value = value, onValueChange = { text ->
            if (text.length <= 4 && text.all { it in '0'..'9' }) onValueChange(text)
        },
        label = { Text(label) }, singleLine = true, enabled = enabled,
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
        modifier = modifier, isError = isError, supportingText = { if (isError) Text(hint) }
    )
}

private fun lunarDate(date: LocalDate): LunarCalendarUtils.LunarDate =
    LunarCalendarUtils.solarToLunar(date.dayOfMonth, date.monthValue, date.year)

private fun matchesLunarDate(reminder: ReminderEntity, lunar: LunarCalendarUtils.LunarDate): Boolean =
    reminder.lunarDay == lunar.day && reminder.lunarMonth == lunar.month && reminder.isLeap == lunar.isLeap &&
        (reminder.isRepeatYearly || reminder.lunarYear == lunar.year)

private fun formatTime(reminder: ReminderEntity): String =
    String.format(Locale.ROOT, "%02d:%02d", reminder.hour, reminder.minute)
