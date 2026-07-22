from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QHeaderView,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database.database import SessionLocal
from database.repository import Repository
from ui.pages.base_page import BasePage


class LessonsPage(BasePage):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            "Lekcje",
            "Przegląd wszystkich lekcji zapisanych w bazie danych.",
            parent,
        )
        self.lessons = []

        card = QFrame()
        card.setObjectName("contentCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Szukaj nauczyciela, klasy, przedmiotu lub sali…")
        self.search_box.setClearButtonEnabled(True)
        self.search_box.textChanged.connect(self.apply_filter)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["Dzień", "Lekcja", "Godzina", "Nauczyciel", "Klasa", "Grupa", "Przedmiot", "Sala"]
        )
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(self.search_box)
        layout.addWidget(self.table)
        self.root_layout.addWidget(card, 1)
        self.refresh_data()

    def refresh_data(self) -> None:
        with SessionLocal() as session:
            self.lessons = Repository(session).list_lessons()
            # Kopiujemy wartości, zanim sesja zostanie zamknięta.
            self.rows = [
                (
                    lesson.day_name,
                    str(lesson.lesson_number),
                    lesson.time_range or "",
                    lesson.teacher.name,
                    lesson.school_class.name if lesson.school_class else "",
                    lesson.group_name or "",
                    lesson.subject,
                    lesson.room.name if lesson.room else "",
                )
                for lesson in self.lessons
            ]
        self.apply_filter(self.search_box.text())

    def apply_filter(self, text: str) -> None:
        query = text.strip().casefold()
        rows = [row for row in self.rows if not query or any(query in value.casefold() for value in row)]
        self.table.setRowCount(len(rows))
        for row_index, values in enumerate(rows):
            for column_index, value in enumerate(values):
                self.table.setItem(row_index, column_index, QTableWidgetItem(value))
