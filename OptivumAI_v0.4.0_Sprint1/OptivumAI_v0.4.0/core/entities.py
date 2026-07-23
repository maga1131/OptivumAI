from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from core.groups import parse_group_code


@dataclass(frozen=True, slots=True)
class Lesson:
    """Pojedyncza lekcja w planie przechowywanym w pamięci."""

    id: int | None
    teacher_name: str
    day_index: int
    lesson_number: int
    subject: str
    day_name: str = ""
    time_range: str | None = None
    class_name: str | None = None
    group_name: str | None = None
    room_name: str | None = None

    def __post_init__(self) -> None:
        if not self.teacher_name.strip():
            raise ValueError("Lekcja musi mieć nauczyciela.")
        if self.day_index < 0:
            raise ValueError("Indeks dnia nie może być ujemny.")
        if self.lesson_number < 1:
            raise ValueError("Numer lekcji musi być większy od zera.")
        if not self.subject.strip():
            raise ValueError("Lekcja musi mieć przedmiot.")
        if self.group_name and not self.class_name:
            raise ValueError("Grupa lekcyjna musi należeć do klasy.")

    @property
    def slot(self) -> tuple[int, int]:
        return self.day_index, self.lesson_number

    @property
    def group_key(self) -> tuple[str, str] | None:
        if not self.class_name or not self.group_name:
            return None
        return self.class_name, self.group_name


@dataclass(frozen=True, slots=True)
class ClassGroup:
    """Grupa należąca do konkretnej klasy.

    Ta sama klasa może równolegle używać wielu podziałów, np. 1/2 oraz 1/4.
    """

    class_name: str
    name: str
    group_type: str | None = None

    def __post_init__(self) -> None:
        if not self.class_name.strip():
            raise ValueError("Grupa musi należeć do klasy.")
        if not self.name.strip():
            raise ValueError("Grupa musi mieć nazwę.")
        # Walidujemy standardowy kod, ale dopuszczamy też nazwy niestandardowe.
        parse_group_code(self.name)

    @property
    def key(self) -> tuple[str, str]:
        return self.class_name, self.name

    @property
    def group_number(self) -> int | None:
        code = parse_group_code(self.name)
        return code.number if code else None

    @property
    def division_count(self) -> int | None:
        code = parse_group_code(self.name)
        return code.division_count if code else None

    def overlaps(self, other: "ClassGroup") -> bool:
        """Czy grupy mogą zawierać wspólnych uczniów.

        Grupy z różnych klas nigdy się nie pokrywają. W tym samym podziale
        (np. 1/4 i 2/4) są rozłączne. Grupy z różnych podziałów traktujemy
        zachowawczo jako potencjalnie nakładające się, dopóki nie znamy
        faktycznych składów uczniów.
        """

        if self.class_name != other.class_name:
            return False
        if self.key == other.key:
            return True
        own = parse_group_code(self.name)
        foreign = parse_group_code(other.name)
        if own and foreign and own.division_count == foreign.division_count:
            return own.number == foreign.number
        return True


@dataclass(slots=True)
class ScheduleOwner:
    """Wspólna logika dla nauczyciela, oddziału i sali."""

    name: str
    _lessons: list[Lesson] = field(default_factory=list, repr=False)

    def lessons(self) -> tuple[Lesson, ...]:
        return tuple(sorted(self._lessons, key=_lesson_sort_key))

    def lessons_on(self, day_index: int) -> tuple[Lesson, ...]:
        return tuple(lesson for lesson in self.lessons() if lesson.day_index == day_index)

    def monday(self) -> tuple[Lesson, ...]:
        return self.lessons_on(0)

    def daily_load(self) -> dict[int, int]:
        result: dict[int, int] = {}
        for lesson in self._lessons:
            result[lesson.day_index] = result.get(lesson.day_index, 0) + 1
        return dict(sorted(result.items()))

    def occupied_slots(self) -> frozenset[tuple[int, int]]:
        return frozenset(lesson.slot for lesson in self._lessons)

    def gaps(self, day_index: int | None = None) -> dict[int, tuple[int, ...]]:
        days = [day_index] if day_index is not None else sorted({lesson.day_index for lesson in self._lessons})
        result: dict[int, tuple[int, ...]] = {}
        for day in days:
            numbers = sorted({lesson.lesson_number for lesson in self._lessons if lesson.day_index == day})
            if len(numbers) < 2:
                result[day] = ()
                continue
            occupied = set(numbers)
            result[day] = tuple(number for number in range(numbers[0], numbers[-1] + 1) if number not in occupied)
        return result

    def free_hours(self, day_index: int | None = None) -> dict[int, tuple[int, ...]]:
        return self.gaps(day_index)

    def _replace_lessons(self, lessons: Iterable[Lesson]) -> None:
        self._lessons = list(lessons)


@dataclass(slots=True)
class Teacher(ScheduleOwner):
    second_school: bool = False
    home_room: str | None = None

    def building_changes(self, room_buildings: dict[str, str] | None = None) -> tuple[tuple[Lesson, Lesson], ...]:
        if not room_buildings:
            return ()
        changes: list[tuple[Lesson, Lesson]] = []
        for day in sorted({lesson.day_index for lesson in self._lessons}):
            lessons = list(self.lessons_on(day))
            for previous, current in zip(lessons, lessons[1:]):
                previous_building = room_buildings.get(previous.room_name or "")
                current_building = room_buildings.get(current.room_name or "")
                if previous_building and current_building and previous_building != current_building:
                    changes.append((previous, current))
        return tuple(changes)


@dataclass(slots=True)
class SchoolClass(ScheduleOwner):
    building: str | None = None


@dataclass(slots=True)
class Room(ScheduleOwner):
    building: str | None = None
    capacity: int | None = None
    room_type: str | None = None
    equipment: tuple[str, ...] = ()

    def occupancy(self) -> frozenset[tuple[int, int]]:
        return self.occupied_slots()


def _lesson_sort_key(lesson: Lesson) -> tuple[int, int, str, str]:
    return (lesson.day_index, lesson.lesson_number, lesson.class_name or "", lesson.subject)
