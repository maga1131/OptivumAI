from __future__ import annotations

from dataclasses import dataclass

from core.services.timetable_analysis import (
    TimetableMetrics,
    analyze_timetable,
    detect_conflicts,
    introduced_conflicts,
    preview_positions,
)
from core.services.timetable_view import TimetableLesson


@dataclass(frozen=True, slots=True)
class TimetableSuggestion:
    source_ids: tuple[int, ...]
    target_ids: tuple[int, ...]
    source_day_index: int
    source_day_name: str
    source_lesson_number: int
    target_day_index: int
    target_day_name: str
    target_lesson_number: int
    score_before: int
    score_after: int
    description: str
    reasons: tuple[str, ...]

    @property
    def improvement(self) -> int:
        return self.score_after - self.score_before

    @property
    def is_swap(self) -> bool:
        return bool(self.target_ids)


def lesson_diagnosis(
    lessons: list[TimetableLesson] | tuple[TimetableLesson, ...],
    selected_ids: set[int],
) -> tuple[str, ...]:
    selected = [lesson for lesson in lessons if lesson.id in selected_ids]
    if not selected:
        return ("Nie wybrano lekcji.",)

    messages: list[str] = []
    conflicts = [
        conflict
        for conflict in detect_conflicts(lessons)
        if selected_ids.intersection(conflict.lesson_ids)
    ]
    if conflicts:
        messages.append(f"⚠ Lekcja uczestniczy w {len(conflicts)} konflikcie/konfliktach.")
    else:
        messages.append("✓ Lekcja nie powoduje bezpośredniego konfliktu.")

    teacher_names = {lesson.teacher_name for lesson in selected if lesson.teacher_name}
    class_names = {name for lesson in selected for name in lesson.class_names}
    day_indexes = {lesson.day_index for lesson in selected}
    periods = {lesson.lesson_number for lesson in selected}

    teacher_gaps = _gaps_touching_slot(lessons, teacher_names, day_indexes, periods, owner="teacher")
    class_gaps = _gaps_touching_slot(lessons, class_names, day_indexes, periods, owner="class")
    if teacher_gaps:
        messages.append("⚠ Termin leży przy okienku nauczyciela.")
    else:
        messages.append("✓ Termin nie leży przy okienku nauczyciela.")
    if class_gaps:
        messages.append("⚠ Termin leży przy okienku klasy.")
    else:
        messages.append("✓ Termin nie leży przy okienku klasy.")

    if any(lesson.lesson_number > 8 for lesson in selected):
        messages.append("⚠ Lekcja odbywa się późno — po 8. godzinie.")
    else:
        messages.append("✓ Lekcja mieści się w pierwszych ośmiu godzinach.")

    return tuple(messages)


def find_best_suggestions(
    lessons: list[TimetableLesson] | tuple[TimetableLesson, ...],
    source_ids: tuple[int, ...],
    owner_lessons: list[TimetableLesson] | tuple[TimetableLesson, ...],
    day_names: tuple[str, ...],
    *,
    max_period: int = 10,
    limit: int = 5,
) -> tuple[TimetableSuggestion, ...]:
    source_set = set(source_ids)
    source = [lesson for lesson in lessons if lesson.id in source_set]
    if not source:
        return ()

    source_day_index = _normalized_day_index(source[0], day_names)
    source_period = source[0].lesson_number
    source_day_name = day_names[source_day_index - 1]
    before = analyze_timetable(lessons)

    owner_by_slot: dict[tuple[int, int], tuple[int, ...]] = {}
    for lesson in owner_lessons:
        day_index = _normalized_day_index(lesson, day_names)
        key = (day_index, lesson.lesson_number)
        owner_by_slot[key] = owner_by_slot.get(key, ()) + (lesson.id,)

    results: list[TimetableSuggestion] = []
    for target_day_index, target_day_name in enumerate(day_names, start=1):
        for target_period in range(1, max_period + 1):
            if target_day_index == source_day_index and target_period == source_period:
                continue

            target_ids = tuple(
                identifier
                for identifier in owner_by_slot.get((target_day_index, target_period), ())
                if identifier not in source_set
            )
            positions = {
                identifier: (target_day_index, target_day_name, target_period)
                for identifier in source_ids
            }
            if target_ids:
                positions.update({
                    identifier: (source_day_index, source_day_name, source_period)
                    for identifier in target_ids
                })

            preview = preview_positions(lessons, positions)
            if introduced_conflicts(lessons, preview, set(positions)):
                continue

            after = analyze_timetable(preview)
            if after.score <= before.score:
                continue

            reasons = _metric_reasons(before, after)
            action = "Zamień" if target_ids else "Przenieś"
            description = (
                f"{action}: {source_day_name}, lekcja {source_period} → "
                f"{target_day_name}, lekcja {target_period}  (+{after.score - before.score} pkt)"
            )
            results.append(TimetableSuggestion(
                source_ids=tuple(source_ids),
                target_ids=target_ids,
                source_day_index=source_day_index,
                source_day_name=source_day_name,
                source_lesson_number=source_period,
                target_day_index=target_day_index,
                target_day_name=target_day_name,
                target_lesson_number=target_period,
                score_before=before.score,
                score_after=after.score,
                description=description,
                reasons=reasons,
            ))

    results.sort(key=lambda item: (-item.improvement, item.target_day_index, item.target_lesson_number))
    return tuple(results[:limit])


def _metric_reasons(before: TimetableMetrics, after: TimetableMetrics) -> tuple[str, ...]:
    reasons: list[str] = []
    if after.conflicts < before.conflicts:
        reasons.append(f"mniej konfliktów: {before.conflicts} → {after.conflicts}")
    if after.teacher_gaps < before.teacher_gaps:
        reasons.append(f"mniej okienek nauczycieli: {before.teacher_gaps} → {after.teacher_gaps}")
    if after.class_gaps < before.class_gaps:
        reasons.append(f"mniej okienek klas: {before.class_gaps} → {after.class_gaps}")
    if after.overloaded_days < before.overloaded_days:
        reasons.append(f"mniej przepełnionych dni: {before.overloaded_days} → {after.overloaded_days}")
    return tuple(reasons or ("lepszy łączny rozkład planu",))


def _normalized_day_index(lesson: TimetableLesson, day_names: tuple[str, ...]) -> int:
    normalized = lesson.day_name.strip().casefold()
    for index, name in enumerate(day_names, start=1):
        if normalized == name.casefold():
            return index
    if 1 <= lesson.day_index <= len(day_names):
        return lesson.day_index
    if 0 <= lesson.day_index < len(day_names):
        return lesson.day_index + 1
    return 1


def _gaps_touching_slot(lessons, names, day_indexes, periods, *, owner: str) -> bool:
    for name in names:
        for day_index in day_indexes:
            scheduled = set()
            for lesson in lessons:
                matches = lesson.teacher_name == name if owner == "teacher" else name in lesson.class_names
                if matches and lesson.day_index == day_index:
                    scheduled.add(lesson.lesson_number)
            if len(scheduled) < 2:
                continue
            for period in periods:
                if min(scheduled) <= period <= max(scheduled):
                    if period - 1 not in scheduled or period + 1 not in scheduled:
                        return True
    return False
