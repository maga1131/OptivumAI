from core.services.timetable_analysis import analyze_timetable, introduced_conflicts, preview_positions
from core.services.timetable_view import TimetableLesson


def lesson(identifier, *, teacher="T1", room="R1", participants=(("1A", ""),), day=1, period=1):
    return TimetableLesson(identifier, day, "Poniedziałek", period, "", "Matematyka", teacher, room, participants)


def test_detects_teacher_room_and_class_conflicts():
    metrics = analyze_timetable([lesson(1), lesson(2)])
    assert metrics.conflicts == 3
    assert metrics.score == 55


def test_parallel_different_groups_do_not_create_class_conflict():
    first = lesson(1, teacher="T1", room="R1", participants=(("1A", "g1"),))
    second = lesson(2, teacher="T2", room="R2", participants=(("1A", "g2"),))
    assert analyze_timetable([first, second]).conflicts == 0


def test_preview_reports_only_new_conflicts():
    lessons = [lesson(1), lesson(2, teacher="T2", room="R2", participants=(("2A", ""),), period=2)]
    preview = preview_positions(lessons, {2: (1, "Poniedziałek", 1)})
    conflicts = introduced_conflicts(lessons, preview, {2})
    assert len(conflicts) == 0


def test_preview_blocks_new_teacher_conflict():
    lessons = [lesson(1), lesson(2, teacher="T1", room="R2", participants=(("2A", ""),), period=2)]
    preview = preview_positions(lessons, {2: (1, "Poniedziałek", 1)})
    conflicts = introduced_conflicts(lessons, preview, {2})
    assert [item.kind for item in conflicts] == ["teacher"]


def test_counts_gaps():
    lessons = [lesson(1, period=1), lesson(2, teacher="T1", room="R2", participants=(("1A", ""),), period=3)]
    metrics = analyze_timetable(lessons)
    assert metrics.teacher_gaps == 1
    assert metrics.class_gaps == 1
