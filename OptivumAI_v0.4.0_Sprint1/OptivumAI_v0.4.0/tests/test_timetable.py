import pytest

from core.entities import Lesson, Room, SchoolClass, Teacher
from core.timetable import Timetable


def lesson(
    number: int,
    *,
    day: int = 0,
    teacher: str = "A. Nowak",
    school_class: str = "1A",
    room: str = "12",
    subject: str = "Matematyka",
) -> Lesson:
    return Lesson(
        id=None,
        teacher_name=teacher,
        day_index=day,
        lesson_number=number,
        subject=subject,
        class_name=school_class,
        room_name=room,
    )


def test_builds_indexes_from_lessons():
    timetable = Timetable([lesson(1), lesson(2)])

    assert len(timetable.teacher("A. Nowak").lessons()) == 2
    assert len(timetable.class_("1A").lessons()) == 2
    assert len(timetable.room("12").lessons()) == 2
    assert timetable.counts() == {
        "teachers": 1,
        "classes": 1,
        "rooms": 1,
        "lessons": 2,
    }


def test_detects_gaps_between_first_and_last_lesson():
    timetable = Timetable([lesson(1), lesson(3), lesson(5)])

    assert timetable.teacher("A. Nowak").gaps(0) == {0: (2, 4)}
    assert timetable.class_("1A").free_hours(0) == {0: (2, 4)}


def test_monday_and_daily_load():
    timetable = Timetable([lesson(1), lesson(2), lesson(1, day=2)])

    teacher = timetable.teacher("A. Nowak")
    assert [item.lesson_number for item in teacher.monday()] == [1, 2]
    assert teacher.daily_load() == {0: 2, 2: 1}


def test_replace_lesson_rebuilds_all_indexes():
    old = lesson(1)
    new = lesson(4, teacher="B. Kowalska", school_class="2B", room="20")
    timetable = Timetable([old])

    timetable.replace_lesson(old, new)

    assert timetable.teacher("A. Nowak").lessons() == ()
    assert timetable.teacher("B. Kowalska").lessons() == (new,)
    assert timetable.class_("2B").lessons() == (new,)
    assert timetable.room("20").lessons() == (new,)


def test_preserves_metadata_of_explicit_entities():
    teacher = Teacher("A. Nowak", second_school=True, home_room="12")
    school_class = SchoolClass("1A", building="A")
    room = Room("12", building="A", capacity=30, room_type="ogólna")

    timetable = Timetable(
        [lesson(1)], teachers=[teacher], classes=[school_class], rooms=[room]
    )

    assert timetable.teacher("A. Nowak").second_school is True
    assert timetable.class_("1A").building == "A"
    assert timetable.room("12").capacity == 30


def test_reports_building_changes_for_teacher():
    first = lesson(1, room="A12")
    second = lesson(2, room="B04")
    timetable = Timetable([first, second])

    changes = timetable.teacher("A. Nowak").building_changes(
        {"A12": "A", "B04": "B"}
    )

    assert changes == ((first, second),)


def test_unknown_owner_raises_clear_error():
    timetable = Timetable()

    with pytest.raises(KeyError, match="Nie znaleziono nauczyciela"):
        timetable.teacher("Nie istnieje")


def test_invalid_lesson_is_rejected():
    with pytest.raises(ValueError, match="Numer lekcji"):
        lesson(0)
