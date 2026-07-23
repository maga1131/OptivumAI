from core.services.timetable_view import (
    TimetableLesson,
    TimetableViewType,
    cell_text,
    lessons_for_owner,
    owner_names,
)


def lesson(**changes):
    values = dict(
        id=1,
        day_index=1,
        day_name="Wtorek",
        lesson_number=3,
        time_range="09:50-10:35",
        subject="Matematyka",
        teacher_name="Jan Kowalski",
        room_name="W12",
        participants=(("3TA", "1/2"),),
    )
    values.update(changes)
    return TimetableLesson(**values)


def test_owner_names_include_all_combined_classes():
    lessons = [lesson(participants=(("3TA", "3/3"), ("3TB", "2/2")))]
    assert owner_names(lessons, TimetableViewType.CLASS) == ("3TA", "3TB")


def test_combined_lesson_is_visible_in_both_class_plans():
    combined = lesson(participants=(("3TA", "3/3"), ("3TB", "2/2")))
    assert lessons_for_owner([combined], TimetableViewType.CLASS, "3TA") == (combined,)
    assert lessons_for_owner([combined], TimetableViewType.CLASS, "3TB") == (combined,)


def test_teacher_and_room_filters_use_same_lesson():
    item = lesson()
    assert lessons_for_owner([item], TimetableViewType.TEACHER, "Jan Kowalski") == (item,)
    assert lessons_for_owner([item], TimetableViewType.ROOM, "W12") == (item,)


def test_teacher_cell_contains_classes_groups_and_room():
    text = cell_text(
        lesson(participants=(("3TA", "3/3"), ("3TB", "2/2"))),
        TimetableViewType.TEACHER,
    )
    assert "3TA 3/3" in text
    assert "3TB 2/2" in text
    assert "W12" in text

