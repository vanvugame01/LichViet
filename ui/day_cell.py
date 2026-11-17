from datetime import date

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout


class DayCell(QFrame):
    clicked = pyqtSignal(object)
    navigate = pyqtSignal(object, int)

    def __init__(self):
        super().__init__()
        self._day = None
        self.setObjectName("dayCell")
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(42, 42)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        self.solar_label = QLabel()
        self.solar_label.setObjectName("solarDay")
        self.lunar_label = QLabel()
        self.lunar_label.setObjectName("lunarDay")
        self.dot_label = QLabel()
        self.dot_label.setObjectName("reminderDot")
        self.dot_label.setFixedHeight(5)
        for label in (self.solar_label, self.lunar_label, self.dot_label):
            label.setAlignment(Qt.AlignCenter)
            label.setAttribute(Qt.WA_TransparentForMouseEvents)
            layout.addWidget(label)

    def set_day(self, day: date, lunar_text: str, in_month: bool,
                is_sunday: bool, is_selected: bool, is_today=False,
                has_reminder=False, lunar_description=""):
        self._day = day
        self.solar_label.setText(str(day.day))
        self.lunar_label.setText(lunar_text)
        self.dot_label.setText("•" if has_reminder else "")
        for key, value in (("inMonth", in_month), ("sunday", is_sunday),
                           ("selected", is_selected), ("today", is_today)):
            self.setProperty(key, value)
        description = f"{day:%d/%m/%Y}, âm lịch {lunar_description or lunar_text}"
        if is_today:
            description += ", hôm nay"
        if is_selected:
            description += ", đang chọn"
        if has_reminder:
            description += ", có nhắc việc"
        self.setAccessibleName(description)
        self.setToolTip(description)
        self.style().unpolish(self)
        self.style().polish(self)
        for label in (self.solar_label, self.lunar_label, self.dot_label):
            label.style().unpolish(label)
            label.style().polish(label)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._day is not None:
            self.setFocus(Qt.MouseFocusReason)
            self.clicked.emit(self._day)
            event.accept()
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        offsets = {Qt.Key_Left: -1, Qt.Key_Right: 1, Qt.Key_Up: -7, Qt.Key_Down: 7}
        if self._day is not None and event.key() in offsets:
            self.navigate.emit(self._day, offsets[event.key()])
            event.accept()
        elif self._day is not None and event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.clicked.emit(self._day)
            event.accept()
        else:
            super().keyPressEvent(event)
