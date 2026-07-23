"""Niezależny od GUI i bazy danych rdzeń OptivumAI."""

from core.entities import Lesson, Room, SchoolClass, Teacher
from core.timetable import Timetable

__all__ = ["Lesson", "Room", "SchoolClass", "Teacher", "Timetable"]
