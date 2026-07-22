from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


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

    @property
    def slot(self) -> tuple[int, int]:
        return self.day_index, self.lesson_number


@dataclass(slots=True)
class ScheduleOwner:
    """Wspólna logika dla nauczyciela, oddziału i sali."""

    name: str
    _lessons: list[Lesson] = field(default_factory=list, repr=False)

    def lessons(self) -> tuple[Lesson, ...]:
        return tuple(sorted(self._lessons, key=_lesson_sort_key))

    def lessons_on(self, day_index: int) -> tuple[Lesson, ...]:
        return tuple(
            lesson for lesson in self.lessons() if lesson.day_index == day_index
        )

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
        """Zwraca wolne numery lekcji pomiędzy pierwszą i ostatnią lekcją."""

        days = (
            [day_index]
            if day_index is not None
            else sorted({lesson.day_index for lesson in self._lessons})
        )
        result: dict[int, tuple[int, ...]] = {}
        for day in days:
            numbers = sorted(
                {lesson.lesson_number for lesson in self._lessons if lesson.day_index == day}
            )
            if len(numbers) < 2:
                result[day] = ()
                continue
            occupied = set(numbers)
            result[day] = tuple(
                number
                for number in range(numbers[0], numbers[-1] + 1)
                if number not in occupied
            )
        return result

    def free_hours(self, day_index: int | None = None) -> dict[int, tuple[int, ...]]:
        """Alias używany w interfejsie i analizatorze."""

        return self.gaps(day_index)

    def _replace_lessons(self, lessons: Iterable[Lesson]) -> None:
        self._lessons = list(lessons)


@dataclass(slots=True)
class Teacher(ScheduleOwner):
    second_school: bool = False
    home_room: str | None = None

    def building_changes(
        self, room_buildings: dict[str, str] | None = None
    ) -> tuple[tuple[Lesson, Lesson], ...]:
        """Wykrywa kolejne lekcje nauczyciela odbywające się w różnych budynkach.

        Brak mapy budynków oznacza brak możliwych do wykrycia przejść.
        """

        if not room_buildings:
            return ()
        changes: list[tuple[Lesson, Lesson]] = []
        for day in sorted({lesson.day_index for lesson in self._lessons}):
            lessons = list(self.lessons_on(day))
            for previous, current in zip(lessons, lessons[1:]):
                previous_building = room_buildings.get(previous.room_name or "")
                current_building = room_buildings.get(current.room_name or "")
                if (
                    previous_building
                    and current_building
                    and previous_building != current_building
                ):
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
    return (
        lesson.day_index,
        lesson.lesson_number,
        lesson.class_name or "",
        lesson.subject,
    )
