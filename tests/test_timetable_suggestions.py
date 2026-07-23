from core.services.timetable_suggestions import find_best_suggestions, lesson_diagnosis
from core.services.timetable_view import TimetableLesson

DAYS = ("Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek")


def lesson(identifier, day, period, teacher="T1", room="R1", class_name="1A"):
    return TimetableLesson(identifier, day, DAYS[day - 1], period, "", "Matematyka", teacher, room, ((class_name, ""),))


def test_finds_gap_reducing_move():
    lessons = [lesson(1, 1, 1), lesson(2, 1, 3)]
    suggestions = find_best_suggestions(lessons, (2,), lessons, DAYS)
    assert suggestions
    assert suggestions[0].improvement > 0


def test_rejects_new_conflicts():
    lessons = [lesson(1, 1, 1), lesson(2, 1, 3), lesson(3, 1, 2, teacher="T1", room="R9", class_name="2A")]
    suggestions = find_best_suggestions(lessons, (2,), [lessons[0], lessons[1]], DAYS)
    assert all(not (item.target_day_index == 1 and item.target_lesson_number == 2) for item in suggestions)


def test_diagnosis_returns_messages():
    messages = lesson_diagnosis([lesson(1, 1, 1)], {1})
    assert messages
    assert any("konflikt" in message.lower() for message in messages)
