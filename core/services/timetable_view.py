from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TimetableViewType(str, Enum):
    CLASS = "class"
    TEACHER = "teacher"
    ROOM = "room"


@dataclass(frozen=True, slots=True)
class TimetableLesson:
    """Niezależny od bazy danych opis lekcji używany przez widok planu."""

    id: int
    day_index: int
    day_name: str
    lesson_number: int
    time_range: str
    subject: str
    teacher_name: str
    room_name: str
    participants: tuple[tuple[str, str], ...]

    @property
    def class_names(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(class_name for class_name, _ in self.participants if class_name))

    @property
    def group_names(self) -> tuple[str, ...]:
        return tuple(group_name for _, group_name in self.participants if group_name)

    def belongs_to(self, view_type: TimetableViewType, owner_name: str) -> bool:
        if view_type is TimetableViewType.TEACHER:
            return self.teacher_name == owner_name
        if view_type is TimetableViewType.ROOM:
            return self.room_name == owner_name
        return owner_name in self.class_names


def owner_names(
    lessons: list[TimetableLesson] | tuple[TimetableLesson, ...],
    view_type: TimetableViewType,
) -> tuple[str, ...]:
    if view_type is TimetableViewType.TEACHER:
        values = (lesson.teacher_name for lesson in lessons)
    elif view_type is TimetableViewType.ROOM:
        values = (lesson.room_name for lesson in lessons)
    else:
        values = (class_name for lesson in lessons for class_name in lesson.class_names)
    return tuple(sorted({value for value in values if value}, key=str.casefold))


def lessons_for_owner(
    lessons: list[TimetableLesson] | tuple[TimetableLesson, ...],
    view_type: TimetableViewType,
    owner_name: str,
) -> tuple[TimetableLesson, ...]:
    return tuple(
        sorted(
            (lesson for lesson in lessons if lesson.belongs_to(view_type, owner_name)),
            key=lambda lesson: (lesson.day_index, lesson.lesson_number, lesson.subject.casefold()),
        )
    )


def cell_text(lesson: TimetableLesson, view_type: TimetableViewType) -> str:
    lines = [lesson.subject]
    if view_type is TimetableViewType.TEACHER:
        participants = []
        for class_name, group_name in lesson.participants:
            participants.append(" ".join(part for part in (class_name, group_name) if part))
        if participants:
            lines.append(", ".join(participants))
    else:
        lines.append(lesson.teacher_name)
        if view_type is TimetableViewType.CLASS and lesson.group_names:
            lines.append(", ".join(lesson.group_names))
    if lesson.room_name:
        lines.append(lesson.room_name)
    return "\n".join(line for line in lines if line)
