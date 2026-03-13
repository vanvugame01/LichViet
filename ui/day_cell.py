from datetime import date
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout

class DayCell(QFrame):
    clicked = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self._day = None
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMinimumHeight(38)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        self.solar_label = QLabel("1")
        self.solar_label.setAlignment(Qt.AlignCenter)

        self.lunar_label = QLabel("1")
        self.lunar_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.solar_label)
        layout.addWidget(self.lunar_label)

    def set_day(self, day: date, lunar_text: str, in_month: bool, is_sunday: bool, is_selected: bool):
        self._day = day
        self.solar_label.setText(str(day.day))
        self.lunar_label.setText(lunar_text)

        solar_color = "#0f172a"
        lunar_color = "#475569"
        border = "transparent"
        bg = "transparent"
        
        # Style logic
        if not in_month:
            solar_color = "#cbd5e1"
            lunar_color = "#94a3b8"
        else:
            if is_sunday:
                solar_color = "#e11d48"
            if lunar_text.startswith("1/"):
                lunar_color = "#ea580c"

        if is_selected:
            border = "#f59e0b"
            bg = "#fef3c7"
            if in_month:
                solar_color = "#b45309"

        self.setStyleSheet(
            f"QFrame {{border: 1px solid {border}; border-radius: 8px; background-color: {bg};}}"
        )
        self.solar_label.setStyleSheet(
            f"border: none; font-size: 13px; font-weight: 700; color: {solar_color}; background: transparent;"
        )
        self.lunar_label.setStyleSheet(
            f"border: none; font-size: 10px; font-weight: 500; color: {lunar_color}; background: transparent;"
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._day is not None:
            self.clicked.emit(self._day)
        super().mousePressEvent(event)
