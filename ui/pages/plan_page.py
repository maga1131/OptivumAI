from __future__ import annotations

from collections import defaultdict

from PySide6.QtCore import QByteArray, QMimeData, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QDrag, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QPushButton,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.services.timetable_analysis import (
    analyze_timetable,
    introduced_conflicts,
    preview_positions,
)
from core.services.timetable_suggestions import (
    TimetableSuggestion,
    find_best_suggestions,
    lesson_diagnosis,
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


class TimetableGrid(QTableWidget):
    """Tabela emitująca docelowy termin podczas przeciągania komórki."""

    lesson_dropped = Signal(tuple, int, int)
    MIME_TYPE = "application/x-optivumai-lessons"

    def __init__(self, rows: int, columns: int, parent: QWidget | None = None) -> None:
        super().__init__(rows, columns, parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)

    def startDrag(self, supported_actions) -> None:
        item = self.currentItem()
        lesson_ids = tuple(item.data(Qt.UserRole) or ()) if item else ()
        if not lesson_ids:
            return

        mime_data = QMimeData()
        mime_data.setData(self.MIME_TYPE, QByteArray(",".join(map(str, lesson_ids)).encode("ascii")))
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec(Qt.MoveAction)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasFormat(self.MIME_TYPE):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        index = self.indexAt(event.position().toPoint())
        if event.mimeData().hasFormat(self.MIME_TYPE) and index.isValid():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        index = self.indexAt(event.position().toPoint())
        if not index.isValid() or not event.mimeData().hasFormat(self.MIME_TYPE):
            event.ignore()
            return

        raw_ids = bytes(event.mimeData().data(self.MIME_TYPE)).decode("ascii")
        lesson_ids = tuple(int(value) for value in raw_ids.split(",") if value)
        if lesson_ids:
            self.lesson_dropped.emit(lesson_ids, index.row(), index.column())
            event.acceptProposedAction()
        else:
            event.ignore()


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
        self.current_suggestions: tuple[TimetableSuggestion, ...] = ()
        self.selected_lesson_ids: tuple[int, ...] = ()

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

        score_row = QHBoxLayout()
        self.selection_label = QLabel("Nie wybrano planu")
        self.score_label = QLabel("Ocena planu: —")
        self.score_label.setObjectName("sectionTitle")
        self.score_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        score_row.addWidget(self.selection_label, 1)
        score_row.addWidget(self.score_label)
        self.selection_label.setObjectName("sectionTitle")
        self.table = TimetableGrid(0, len(DAY_NAMES))
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
        self.table.lesson_dropped.connect(self._move_lessons)

        self.metrics_label = QLabel("")
        self.metrics_label.setObjectName("mutedText")
        self.metrics_label.setWordWrap(True)

        drag_hint = QLabel("Przeciągnij lekcję na inny dzień lub godzinę, aby zmienić termin.")
        drag_hint.setObjectName("mutedText")

        layout.addLayout(score_row)
        layout.addWidget(self.metrics_label)
        layout.addWidget(drag_hint)
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

        title = QLabel("Szczegóły i podpowiedzi")
        title.setObjectName("sectionTitle")
        self.details_label = QLabel("Kliknij komórkę z lekcją, aby zobaczyć szczegóły.")
        self.details_label.setObjectName("mutedText")
        self.details_label.setWordWrap(True)
        self.details_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.details_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        diagnosis_title = QLabel("Dlaczego?")
        diagnosis_title.setObjectName("sectionTitle")
        self.diagnosis_label = QLabel("Wybierz lekcję, aby ją przeanalizować.")
        self.diagnosis_label.setObjectName("mutedText")
        self.diagnosis_label.setWordWrap(True)

        self.suggest_button = QPushButton("Zaproponuj poprawę")
        self.suggest_button.setEnabled(False)
        self.suggest_button.clicked.connect(self._generate_suggestions)
        self.suggestions_list = QListWidget()
        self.suggestions_list.setMinimumHeight(150)
        self.suggestions_list.currentRowChanged.connect(self._show_suggestion_details)
        self.apply_suggestion_button = QPushButton("Zastosuj wybraną zmianę")
        self.apply_suggestion_button.setEnabled(False)
        self.apply_suggestion_button.clicked.connect(self._apply_selected_suggestion)

        layout.addWidget(title)
        layout.addWidget(self.details_label)
        layout.addSpacing(8)
        layout.addWidget(diagnosis_title)
        layout.addWidget(self.diagnosis_label)
        layout.addSpacing(8)
        layout.addWidget(self.suggest_button)
        layout.addWidget(self.suggestions_list, 1)
        layout.addWidget(self.apply_suggestion_button)
        return card

    def refresh_data(self) -> None:
        previous_view = self.current_view_type
        previous_owner = self.owner_list.currentItem().text() if self.owner_list.currentItem() else ""
        with SessionLocal() as session:
            db_lessons = Repository(session).list_lessons()
            self.lessons = [self._snapshot_lesson(lesson) for lesson in db_lessons]
        self._update_metrics()
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
        self._reset_suggestions()
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

    def _move_lessons(self, lesson_ids: tuple[int, ...], target_row: int, target_column: int) -> None:
        target_lesson_number = target_row + 1
        target_day_name = DAY_NAMES[target_column]
        lesson_id_set = set(lesson_ids)
        moving = [lesson for lesson in self.current_lessons if lesson.id in lesson_id_set]
        if not moving:
            return

        source_column = self._day_column(moving[0])
        source_lesson_number = moving[0].lesson_number
        source_day_name = DAY_NAMES[source_column]

        if all(
            self._day_column(lesson) == target_column
            and lesson.lesson_number == target_lesson_number
            for lesson in moving
        ):
            return

        target_item = self.table.item(target_row, target_column)
        target_ids = tuple(
            lesson_id
            for lesson_id in (target_item.data(Qt.UserRole) or ())
            if lesson_id not in lesson_id_set
        ) if target_item else ()

        positions = {
            lesson.id: (target_column + 1, target_day_name, target_lesson_number)
            for lesson in moving
        }
        if target_ids:
            positions.update({
                lesson_id: (source_column + 1, source_day_name, source_lesson_number)
                for lesson_id in target_ids
            })
        preview = preview_positions(self.lessons, positions)
        conflicts = introduced_conflicts(self.lessons, preview, set(positions))
        if conflicts:
            details = "\n".join(f"• {item.describe(DAY_NAMES)}" for item in conflicts[:8])
            QMessageBox.warning(
                self,
                "Konflikt planu",
                "Ta operacja utworzyłaby nowy konflikt:\n\n" + details +
                "\n\nZmiana nie została zapisana.",
            )
            return

        try:
            with SessionLocal() as session:
                repository = Repository(session)
                if target_ids:
                    answer = QMessageBox.question(
                        self,
                        "Zamiana lekcji",
                        f"Termin {target_day_name}, lekcja {target_lesson_number} jest zajęty.\n\n"
                        f"Czy zamienić lekcje miejscami z terminem "
                        f"{source_day_name}, lekcja {source_lesson_number}?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No,
                    )
                    if answer != QMessageBox.Yes:
                        return

                    repository.swap_lessons(
                        source_lesson_ids=lesson_ids,
                        target_lesson_ids=target_ids,
                        source_day_index=source_column + 1,
                        source_day_name=source_day_name,
                        source_lesson_number=source_lesson_number,
                        target_day_index=target_column + 1,
                        target_day_name=target_day_name,
                        target_lesson_number=target_lesson_number,
                    )
                    action_text = (
                        f"Zamieniono lekcje: {source_day_name}, lekcja {source_lesson_number} "
                        f"↔ {target_day_name}, lekcja {target_lesson_number}."
                    )
                else:
                    repository.move_lessons(
                        lesson_ids=lesson_ids,
                        day_index=target_column + 1,
                        day_name=target_day_name,
                        lesson_number=target_lesson_number,
                    )
                    action_text = (
                        f"Przeniesiono lekcję: {target_day_name}, lekcja {target_lesson_number}."
                    )
        except Exception as error:
            QMessageBox.critical(self, "Nie udało się zmienić terminu lekcji", str(error))
            return

        self.refresh_data()
        self.details_label.setText(action_text)


    def _update_metrics(self) -> None:
        metrics = analyze_timetable(self.lessons)
        stars = "★" * max(0, min(5, round(metrics.score / 20)))
        empty_stars = "☆" * (5 - len(stars))
        self.score_label.setText(f"{stars}{empty_stars}  {metrics.score}/100")
        self.metrics_label.setText(
            f"Konflikty: {metrics.conflicts}   •   "
            f"Okienka nauczycieli: {metrics.teacher_gaps}   •   "
            f"Okienka klas: {metrics.class_gaps}   •   "
            f"Przepełnione dni: {metrics.overloaded_days}"
        )

    def _show_selected_cell(self) -> None:
        items = self.table.selectedItems()
        if not items:
            return
        ids = set(items[0].data(Qt.UserRole) or ())
        selected = [lesson for lesson in self.current_lessons if lesson.id in ids]
        if not selected:
            return
        self.selected_lesson_ids = tuple(sorted(ids))
        self.details_label.setText("\n\n────────────\n\n".join(self._lesson_details(lesson) for lesson in selected))
        self.diagnosis_label.setText("\n".join(lesson_diagnosis(self.lessons, ids)))
        self.suggest_button.setEnabled(True)
        self.suggestions_list.clear()
        self.current_suggestions = ()
        self.apply_suggestion_button.setEnabled(False)


    def _generate_suggestions(self) -> None:
        if not self.selected_lesson_ids:
            return
        max_period = max(10, max((lesson.lesson_number for lesson in self.lessons), default=10))
        self.current_suggestions = find_best_suggestions(
            self.lessons,
            self.selected_lesson_ids,
            self.current_lessons,
            DAY_NAMES,
            max_period=max_period,
            limit=5,
        )
        self.suggestions_list.clear()
        if not self.current_suggestions:
            self.suggestions_list.addItem("Brak bezkonfliktowej zmiany poprawiającej ocenę.")
            self.apply_suggestion_button.setEnabled(False)
            return
        for suggestion in self.current_suggestions:
            item = QListWidgetItem(suggestion.description)
            item.setToolTip("\n".join(suggestion.reasons))
            self.suggestions_list.addItem(item)
        self.suggestions_list.setCurrentRow(0)
        self.apply_suggestion_button.setEnabled(True)

    def _show_suggestion_details(self, row: int) -> None:
        if not 0 <= row < len(self.current_suggestions):
            return
        suggestion = self.current_suggestions[row]
        reasons = "\n".join(f"• {reason}" for reason in suggestion.reasons)
        self.diagnosis_label.setText(
            f"Proponowana ocena: {suggestion.score_before} → {suggestion.score_after} "
            f"(+{suggestion.improvement})\n\n{reasons}"
        )

    def _apply_selected_suggestion(self) -> None:
        row = self.suggestions_list.currentRow()
        if not 0 <= row < len(self.current_suggestions):
            return
        suggestion = self.current_suggestions[row]
        answer = QMessageBox.question(
            self,
            "Zastosowanie podpowiedzi",
            f"{suggestion.description}\n\nCzy zastosować tę zmianę?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        try:
            with SessionLocal() as session:
                repository = Repository(session)
                if suggestion.is_swap:
                    repository.swap_lessons(
                        source_lesson_ids=suggestion.source_ids,
                        target_lesson_ids=suggestion.target_ids,
                        source_day_index=suggestion.source_day_index,
                        source_day_name=suggestion.source_day_name,
                        source_lesson_number=suggestion.source_lesson_number,
                        target_day_index=suggestion.target_day_index,
                        target_day_name=suggestion.target_day_name,
                        target_lesson_number=suggestion.target_lesson_number,
                    )
                else:
                    repository.move_lessons(
                        lesson_ids=suggestion.source_ids,
                        day_index=suggestion.target_day_index,
                        day_name=suggestion.target_day_name,
                        lesson_number=suggestion.target_lesson_number,
                    )
        except Exception as error:
            QMessageBox.critical(self, "Nie udało się zastosować podpowiedzi", str(error))
            return
        self.refresh_data()
        self.details_label.setText(
            f"Zastosowano podpowiedź. Ocena planu wzrosła z "
            f"{suggestion.score_before} do {suggestion.score_after}."
        )

    def _reset_suggestions(self) -> None:
        self.selected_lesson_ids = ()
        self.current_suggestions = ()
        if hasattr(self, "suggestions_list"):
            self.suggestions_list.clear()
            self.suggest_button.setEnabled(False)
            self.apply_suggestion_button.setEnabled(False)
            self.diagnosis_label.setText("Wybierz lekcję, aby ją przeanalizować.")

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
        self._reset_suggestions()
        self.details_label.setText("Kliknij komórkę z lekcją, aby zobaczyć szczegóły.")
