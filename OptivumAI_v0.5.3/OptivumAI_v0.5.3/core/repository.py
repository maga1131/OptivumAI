from __future__ import annotations

from typing import Protocol

from core.entities import Lesson, Room, SchoolClass, Teacher
from core.timetable import Timetable


class TimetableRepository(Protocol):
    """Kontrakt źródła danych dla rdzenia programu."""

    def load_timetable(self) -> Timetable:
        ...


class InMemoryTimetableRepository:
    """Proste repozytorium wykorzystywane w testach i prototypach."""

    def __init__(self, timetable: Timetable | None = None) -> None:
        self._timetable = timetable or Timetable()

    def load_timetable(self) -> Timetable:
        return self._timetable

    def save_timetable(self, timetable: Timetable) -> None:
        self._timetable = timetable


def timetable_from_records(
    lessons: list[Lesson],
    *,
    teachers: list[Teacher] | None = None,
    classes: list[SchoolClass] | None = None,
    rooms: list[Room] | None = None,
) -> Timetable:
    """Fabryka ułatwiająca adapterom danych utworzenie planu."""

    return Timetable(
        lessons,
        teachers=teachers or (),
        classes=classes or (),
        rooms=rooms or (),
    )
