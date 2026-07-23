from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from core.entities import ClassGroup, Lesson, Room, SchoolClass, Teacher


class Timetable:
    """Plan lekcji w pamięci, niezależny od SQLAlchemy i PySide6."""

    def __init__(
        self,
        lessons: Iterable[Lesson] = (),
        *,
        teachers: Iterable[Teacher] = (),
        classes: Iterable[SchoolClass] = (),
        rooms: Iterable[Room] = (),
        groups: Iterable[ClassGroup] = (),
    ) -> None:
        self._lessons: list[Lesson] = list(lessons)
        self._teachers = _unique_by_name(teachers)
        self._classes = _unique_by_name(classes)
        self._rooms = _unique_by_name(rooms)
        self._groups = _unique_by_key(groups)
        self._rebuild_indexes()

    @property
    def lessons(self) -> tuple[Lesson, ...]:
        return tuple(sorted(self._lessons, key=lambda item: (item.day_index, item.lesson_number, item.teacher_name, item.class_name or "")))

    @property
    def teachers(self) -> tuple[Teacher, ...]:
        return tuple(sorted(self._teachers.values(), key=lambda item: item.name.casefold()))

    @property
    def classes(self) -> tuple[SchoolClass, ...]:
        return tuple(sorted(self._classes.values(), key=lambda item: item.name.casefold()))

    @property
    def rooms(self) -> tuple[Room, ...]:
        return tuple(sorted(self._rooms.values(), key=lambda item: item.name.casefold()))

    @property
    def groups(self) -> tuple[ClassGroup, ...]:
        return tuple(sorted(self._groups.values(), key=lambda item: (item.class_name.casefold(), item.name.casefold())))

    def teacher(self, name: str) -> Teacher:
        return self._get(self._teachers, name, "nauczyciela")

    def school_class(self, name: str) -> SchoolClass:
        return self._get(self._classes, name, "klasy")

    def class_(self, name: str) -> SchoolClass:
        return self.school_class(name)

    def room(self, name: str) -> Room:
        return self._get(self._rooms, name, "sali")

    def class_group(self, class_name: str, group_name: str) -> ClassGroup:
        return self._get(self._groups, (class_name, group_name), "grupy")

    def groups_for_class(self, class_name: str) -> tuple[ClassGroup, ...]:
        return tuple(group for group in self.groups if group.class_name == class_name)

    def lessons_at(self, day_index: int, lesson_number: int) -> tuple[Lesson, ...]:
        return tuple(lesson for lesson in self.lessons if lesson.day_index == day_index and lesson.lesson_number == lesson_number)

    def class_lessons_conflict(self, first: Lesson, second: Lesson) -> bool:
        """Sprawdza konflikt uczniów dla dwóch lekcji tej samej klasy."""
        if first.class_name != second.class_name or not first.class_name:
            return False
        if first.slot != second.slot:
            return False
        # Lekcja całej klasy koliduje z każdą grupą tej klasy.
        if not first.group_name or not second.group_name:
            return True
        return self.class_group(first.class_name, first.group_name).overlaps(
            self.class_group(second.class_name, second.group_name)
        )

    def add_lesson(self, lesson: Lesson) -> None:
        self._lessons.append(lesson)
        self._rebuild_indexes()

    def replace_lesson(self, old: Lesson, new: Lesson) -> None:
        try:
            index = self._lessons.index(old)
        except ValueError as exc:
            raise KeyError("Nie znaleziono lekcji do zastąpienia.") from exc
        self._lessons[index] = new
        self._rebuild_indexes()

    def remove_lesson(self, lesson: Lesson) -> None:
        try:
            self._lessons.remove(lesson)
        except ValueError as exc:
            raise KeyError("Nie znaleziono lekcji do usunięcia.") from exc
        self._rebuild_indexes()

    def counts(self) -> dict[str, int]:
        return {
            "teachers": len(self._teachers),
            "classes": len(self._classes),
            "groups": len(self._groups),
            "rooms": len(self._rooms),
            "lessons": len(self._lessons),
        }

    def _rebuild_indexes(self) -> None:
        by_teacher: dict[str, list[Lesson]] = defaultdict(list)
        by_class: dict[str, list[Lesson]] = defaultdict(list)
        by_room: dict[str, list[Lesson]] = defaultdict(list)

        for lesson in self._lessons:
            by_teacher[lesson.teacher_name].append(lesson)
            self._teachers.setdefault(lesson.teacher_name, Teacher(lesson.teacher_name))
            if lesson.class_name:
                by_class[lesson.class_name].append(lesson)
                self._classes.setdefault(lesson.class_name, SchoolClass(lesson.class_name))
            if lesson.group_key:
                self._groups.setdefault(lesson.group_key, ClassGroup(*lesson.group_key))
            if lesson.room_name:
                by_room[lesson.room_name].append(lesson)
                self._rooms.setdefault(lesson.room_name, Room(lesson.room_name))

        for name, teacher in self._teachers.items():
            teacher._replace_lessons(by_teacher.get(name, ()))
        for name, school_class in self._classes.items():
            school_class._replace_lessons(by_class.get(name, ()))
        for name, room in self._rooms.items():
            room._replace_lessons(by_room.get(name, ()))

    @staticmethod
    def _get(mapping: dict, key, label: str):
        try:
            return mapping[key]
        except KeyError as exc:
            raise KeyError(f"Nie znaleziono {label}: {key}") from exc


def _unique_by_name(items):
    result = {}
    for item in items:
        if item.name in result:
            raise ValueError(f"Powtarzająca się nazwa: {item.name}")
        result[item.name] = item
    return result


def _unique_by_key(items):
    result = {}
    for item in items:
        if item.key in result:
            raise ValueError(f"Powtarzająca się grupa: {item.class_name} {item.name}")
        result[item.key] = item
    return result
