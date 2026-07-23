from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations

from core.services.timetable_view import TimetableLesson


@dataclass(frozen=True, slots=True)
class TimetableConflict:
    kind: str
    resource: str
    day_index: int
    lesson_number: int
    lesson_ids: tuple[int, int]

    @property
    def key(self) -> tuple[str, str, int, int, tuple[int, int]]:
        return (self.kind, self.resource, self.day_index, self.lesson_number, self.lesson_ids)

    def describe(self, day_names: tuple[str, ...]) -> str:
        column = self.day_index - 1 if 1 <= self.day_index <= len(day_names) else self.day_index
        day = day_names[column] if 0 <= column < len(day_names) else str(self.day_index)
        labels = {
            "teacher": "Nauczyciel",
            "room": "Sala",
            "class": "Klasa lub grupa",
        }
        return f"{labels.get(self.kind, self.kind)} {self.resource}: {day}, lekcja {self.lesson_number}"


@dataclass(frozen=True, slots=True)
class TimetableMetrics:
    score: int
    conflicts: int
    teacher_gaps: int
    class_gaps: int
    overloaded_days: int


def analyze_timetable(lessons: list[TimetableLesson] | tuple[TimetableLesson, ...]) -> TimetableMetrics:
    conflicts = detect_conflicts(lessons)
    teacher_gaps = _count_gaps(lessons, lambda lesson: (lesson.teacher_name,))
    class_gaps = _count_gaps(lessons, lambda lesson: lesson.class_names)
    overloaded_days = _count_overloaded_days(lessons)
    penalty = len(conflicts) * 15 + teacher_gaps * 2 + class_gaps * 2 + overloaded_days
    return TimetableMetrics(
        score=max(0, 100 - penalty),
        conflicts=len(conflicts),
        teacher_gaps=teacher_gaps,
        class_gaps=class_gaps,
        overloaded_days=overloaded_days,
    )


def detect_conflicts(
    lessons: list[TimetableLesson] | tuple[TimetableLesson, ...],
) -> tuple[TimetableConflict, ...]:
    by_slot: dict[tuple[int, int], list[TimetableLesson]] = defaultdict(list)
    for lesson in lessons:
        by_slot[(lesson.day_index, lesson.lesson_number)].append(lesson)

    result: dict[tuple, TimetableConflict] = {}
    for (day_index, lesson_number), slot_lessons in by_slot.items():
        for first, second in combinations(slot_lessons, 2):
            ids = tuple(sorted((first.id, second.id)))
            if first.teacher_name and first.teacher_name == second.teacher_name:
                conflict = TimetableConflict("teacher", first.teacher_name, day_index, lesson_number, ids)
                result[conflict.key] = conflict
            if first.room_name and first.room_name == second.room_name:
                conflict = TimetableConflict("room", first.room_name, day_index, lesson_number, ids)
                result[conflict.key] = conflict
            for resource in _overlapping_participants(first, second):
                conflict = TimetableConflict("class", resource, day_index, lesson_number, ids)
                result[conflict.key] = conflict
    return tuple(sorted(result.values(), key=lambda item: item.key))


def preview_positions(
    lessons: list[TimetableLesson] | tuple[TimetableLesson, ...],
    positions: dict[int, tuple[int, str, int]],
) -> tuple[TimetableLesson, ...]:
    preview = []
    for lesson in lessons:
        position = positions.get(lesson.id)
        if position is None:
            preview.append(lesson)
            continue
        day_index, day_name, lesson_number = position
        preview.append(
            TimetableLesson(
                id=lesson.id,
                day_index=day_index,
                day_name=day_name,
                lesson_number=lesson_number,
                time_range=lesson.time_range,
                subject=lesson.subject,
                teacher_name=lesson.teacher_name,
                room_name=lesson.room_name,
                participants=lesson.participants,
            )
        )
    return tuple(preview)


def introduced_conflicts(
    before: list[TimetableLesson] | tuple[TimetableLesson, ...],
    after: list[TimetableLesson] | tuple[TimetableLesson, ...],
    changed_ids: set[int],
) -> tuple[TimetableConflict, ...]:
    before_keys = {item.key for item in detect_conflicts(before)}
    return tuple(
        item
        for item in detect_conflicts(after)
        if item.key not in before_keys and changed_ids.intersection(item.lesson_ids)
    )


def _overlapping_participants(first: TimetableLesson, second: TimetableLesson) -> tuple[str, ...]:
    overlaps = []
    for first_class, first_group in first.participants:
        for second_class, second_group in second.participants:
            if not first_class or first_class != second_class:
                continue
            if not first_group or not second_group or first_group == second_group:
                suffix = f" ({first_group})" if first_group and first_group == second_group else ""
                overlaps.append(first_class + suffix)
    return tuple(dict.fromkeys(overlaps))


def _count_gaps(lessons, owners_getter) -> int:
    schedules: dict[tuple[str, int], set[int]] = defaultdict(set)
    for lesson in lessons:
        for owner in owners_getter(lesson):
            if owner:
                schedules[(owner, lesson.day_index)].add(lesson.lesson_number)
    total = 0
    for periods in schedules.values():
        if len(periods) > 1:
            total += max(periods) - min(periods) + 1 - len(periods)
    return total


def _count_overloaded_days(lessons) -> int:
    schedules: dict[tuple[str, int], set[int]] = defaultdict(set)
    for lesson in lessons:
        for class_name in lesson.class_names:
            schedules[(class_name, lesson.day_index)].add(lesson.lesson_number)
    return sum(1 for periods in schedules.values() if len(periods) > 8)
