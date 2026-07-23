from __future__ import annotations

from collections import defaultdict

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.services.timetable_view import (
    TimetableLesson,
    TimetableViewType,
    cell_text,
    lessons_for_owner,
    owner_names,
)
from database.database import SessionLocal
from database.repository import Repository
from ui.pages.base_page import BasePage


DAY_NAMES = ("Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek")
LESSON_COLORS = (
    ("#E8F1FF", "#1D4ED8"),
    ("#EAF8EF", "#15803D"),
    ("#FFF4DE", "#B45309"),
    ("#F3E8FF", "#7E22CE"),
    ("#FFE9EE", "#BE123C"),
    ("#E6F7F7", "#0F766E"),
    ("#F1F5F9", "#334155"),
)

VIEW_LABELS = {
    TimetableViewType.CLASS: "Klasa",
    TimetableViewType.TEACHER: "Nauczyciel",
    TimetableViewType.ROOM: "Sala",
}


class PlanPage(BasePage):
    """Czytelna siatka planu oparta na tych samych lekcjach co pozostałe strony."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            "Plan",
            "Wybierz klasę, nauczyciela albo salę i przeglądaj lekcje w układzie tygodniowym.",
            parent,
        )
        self.lessons: list[TimetableLesson] = []
        self.current_lessons: tuple[TimetableLesson, ...] = ()

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_owner_panel())
        splitter.addWidget(self._build_grid_panel())
        splitter.addWidget(self._build_details_panel())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([220, 760, 280])

        self.root_layout.addWidget(splitter, 1)
        self.refresh_data()

    def _build_owner_panel(self) -> QWidget:
        card = QFrame()
        card.setObjectName("contentCard")
        card.setMinimumWidth(190)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("Typ planu")
        title.setObjectName("sectionTitle")
        self.view_combo = QComboBox()
        for view_type, label in VIEW_LABELS.items():
            self.view_combo.addItem(label, view_type.value)
        self.view_combo.currentIndexChanged.connect(self._reload_owner_list)

        list_title = QLabel("Wybierz pozycję")
        list_title.setObjectName("sectionTitle")
        self.owner_list = QListWidget()
        self.owner_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.owner_list.currentTextChanged.connect(self._render_selected_owner)

        layout.addWidget(title)
        layout.addWidget(self.view_combo)
        layout.addSpacing(8)
        layout.addWidget(list_title)
        layout.addWidget(self.owner_list, 1)
        return card

    def _build_grid_panel(self) -> QWidget:
        card = QFrame()
        card.setObjectName("contentCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)

        self.selection_label = QLabel("Nie wybrano planu")
        self.selection_label.setObjectName("sectionTitle")
        self.table = QTableWidget(0, len(DAY_NAMES))
        self._configure_day_columns()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setWordWrap(True)
        self.table.setShowGrid(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setMinimumSectionSize(72)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.itemSelectionChanged.connect(self._show_selected_cell)

        layout.addWidget(self.selection_label)
        layout.addWidget(self.table, 1)
        return card


    def _configure_day_columns(self) -> None:
        """Przywraca zawsze pięć widocznych kolumn od poniedziałku do piątku."""
        self.table.setColumnCount(len(DAY_NAMES))
        self.table.setHorizontalHeaderLabels(DAY_NAMES)
        for column in range(len(DAY_NAMES)):
            self.table.setColumnHidden(column, False)

    def _build_details_panel(self) -> QWidget:
        card = QFrame()
        card.setObjectName("contentCard")
        card.setMinimumWidth(240)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)

        title = QLabel("Szczegóły")
        title.setObjectName("sectionTitle")
        self.details_label = QLabel("Kliknij komórkę z lekcją, aby zobaczyć szczegóły.")
        self.details_label.setObjectName("mutedText")
        self.details_label.setWordWrap(True)
        self.details_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.details_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout.addWidget(title)
        layout.addWidget(self.details_label, 1)
        return card

    def refresh_data(self) -> None:
        previous_view = self.current_view_type
        previous_owner = self.owner_list.currentItem().text() if self.owner_list.currentItem() else ""
        with SessionLocal() as session:
            db_lessons = Repository(session).list_lessons()
            self.lessons = [self._snapshot_lesson(lesson) for lesson in db_lessons]
        self._reload_owner_list(previous_view=previous_view, preferred_owner=previous_owner)

    @property
    def current_view_type(self) -> TimetableViewType:
        value = self.view_combo.currentData() or TimetableViewType.CLASS.value
        return TimetableViewType(value)

    @staticmethod
    def _snapshot_lesson(lesson) -> TimetableLesson:
        participants = tuple(
            (group.school_class.name, group.name)
            for group in lesson.groups
        )
        if not participants and lesson.school_class:
            participants = ((lesson.school_class.name, lesson.group_name or ""),)
        return TimetableLesson(
            id=lesson.id,
            day_index=lesson.day_index,
            day_name=lesson.day_name,
            lesson_number=lesson.lesson_number,
            time_range=lesson.time_range or "",
            subject=lesson.subject,
            teacher_name=lesson.teacher.name,
            room_name=lesson.room.name if lesson.room else "",
            participants=participants,
        )

    def _reload_owner_list(
        self,
        _index: int | None = None,
        previous_view: TimetableViewType | None = None,
        preferred_owner: str = "",
    ) -> None:
        del previous_view
        names = owner_names(self.lessons, self.current_view_type)
        self.owner_list.blockSignals(True)
        self.owner_list.clear()
        for name in names:
            self.owner_list.addItem(QListWidgetItem(name))
        self.owner_list.blockSignals(False)

        if not names:
            self._clear_grid("Brak danych. Najpierw zaimportuj plan w zakładce Projekt.")
            return

        matches = self.owner_list.findItems(preferred_owner, Qt.MatchExactly) if preferred_owner else []
        self.owner_list.setCurrentItem(matches[0] if matches else self.owner_list.item(0))
        self._render_selected_owner(self.owner_list.currentItem().text())

    def _render_selected_owner(self, owner_name: str) -> None:
        if not owner_name:
            self._clear_grid("Nie wybrano planu")
            return

        view_type = self.current_view_type
        self.current_lessons = lessons_for_owner(self.lessons, view_type, owner_name)
        self.selection_label.setText(f"{VIEW_LABELS[view_type]}: {owner_name}")

        max_period = max((lesson.lesson_number for lesson in self.current_lessons), default=10)
        max_period = max(10, max_period)
        self._configure_day_columns()
        self.table.clearContents()
        self.table.setRowCount(max_period)
        self.table.setVerticalHeaderLabels([str(number) for number in range(1, max_period + 1)])
        for row in range(max_period):
            self.table.setRowHeight(row, 112)

        by_slot: dict[tuple[int, int], list[TimetableLesson]] = defaultdict(list)
        for lesson in self.current_lessons:
            day_column = self._day_column(lesson)
            if day_column is not None:
                by_slot[(day_column, lesson.lesson_number)].append(lesson)

        for (day_index, lesson_number), slot_lessons in by_slot.items():
            text = "\n\n".join(self._cell_text(lesson, view_type) for lesson in slot_lessons)
            item = QTableWidgetItem(text)
            item.setData(Qt.UserRole, tuple(lesson.id for lesson in slot_lessons))
            item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
            item.setToolTip("Kliknij, aby wyświetlić szczegóły")
            item.setFont(self._cell_font())

            background, foreground = self._lesson_colors(slot_lessons[0])
            item.setBackground(QBrush(QColor(background)))
            item.setForeground(QBrush(QColor(foreground)))
            self.table.setItem(lesson_number - 1, day_index, item)

        self.table.clearSelection()
        # Po odświeżeniu widok zawsze zaczyna się od poniedziałku.
        self.table.horizontalScrollBar().setValue(self.table.horizontalScrollBar().minimum())
        self.table.horizontalScrollBar().setValue(0)
        self.details_label.setText("Kliknij komórkę z lekcją, aby zobaczyć szczegóły.")



    @staticmethod
    def _day_column(lesson: TimetableLesson) -> int | None:
        """Zwraca kolumnę 0-4 dla danych zapisanych w formacie 0-4 lub 1-5."""
        normalized_name = lesson.day_name.strip().casefold()
        names = {name.casefold(): index for index, name in enumerate(DAY_NAMES)}
        if normalized_name in names:
            return names[normalized_name]

        if 0 <= lesson.day_index < 5:
            return lesson.day_index
        if 1 <= lesson.day_index <= 5:
            return lesson.day_index - 1
        return None

    @staticmethod
    def _cell_font() -> QFont:
        font = QFont("Segoe UI", 9)
        font.setWeight(QFont.DemiBold)
        return font

    @staticmethod
    def _lesson_colors(lesson: TimetableLesson) -> tuple[str, str]:
        index = sum(ord(character) for character in lesson.subject.casefold()) % len(LESSON_COLORS)
        return LESSON_COLORS[index]

    @staticmethod
    def _cell_text(lesson: TimetableLesson, view_type: TimetableViewType) -> str:
        lines = [lesson.subject.upper()]

        if view_type is TimetableViewType.TEACHER:
            participants = [
                " ".join(part for part in (class_name, group_name) if part)
                for class_name, group_name in lesson.participants
            ]
            if participants:
                lines.append("👥 " + "  •  ".join(participants))
        else:
            lines.append("👤 " + lesson.teacher_name)
            if view_type is TimetableViewType.CLASS and lesson.group_names:
                lines.append("GRUPY  " + "  •  ".join(lesson.group_names))

        if lesson.room_name:
            lines.append("🏫 Sala " + lesson.room_name)
        if lesson.time_range:
            lines.append("🕘 " + lesson.time_range)
        return "\n".join(line for line in lines if line)

    def _show_selected_cell(self) -> None:
        items = self.table.selectedItems()
        if not items:
            return
        ids = set(items[0].data(Qt.UserRole) or ())
        selected = [lesson for lesson in self.current_lessons if lesson.id in ids]
        if not selected:
            return
        self.details_label.setText("\n\n────────────\n\n".join(self._lesson_details(lesson) for lesson in selected))

    @staticmethod
    def _lesson_details(lesson: TimetableLesson) -> str:
        participants = "\n".join(
            f"• {class_name}{f' — {group_name}' if group_name else ''}"
            for class_name, group_name in lesson.participants
        ) or "—"
        day = lesson.day_name or (DAY_NAMES[lesson.day_index] if 0 <= lesson.day_index < 5 else str(lesson.day_index))
        time = f" ({lesson.time_range})" if lesson.time_range else ""
        return (
            f"{lesson.subject}\n\n"
            f"Nauczyciel\n{lesson.teacher_name}\n\n"
            f"Klasy i grupy\n{participants}\n\n"
            f"Sala\n{lesson.room_name or '—'}\n\n"
            f"Termin\n{day}, lekcja {lesson.lesson_number}{time}"
        )

    def _clear_grid(self, message: str) -> None:
        self.current_lessons = ()
        self.selection_label.setText(message)
        self._configure_day_columns()
        self.table.clearContents()
        self.table.setRowCount(10)
        self.table.setVerticalHeaderLabels([str(number) for number in range(1, 11)])
        self.details_label.setText("Kliknij komórkę z lekcją, aby zobaczyć szczegóły.")
