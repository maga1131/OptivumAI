from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from core.entities import Lesson as CoreLesson
from core.entities import Room as CoreRoom
from core.entities import SchoolClass as CoreSchoolClass
from core.entities import Teacher as CoreTeacher
from core.timetable import Timetable
from database.models import Lesson, Room, SchoolClass, Teacher


class SqlAlchemyTimetableRepository:
    """Adapter odczytujący istniejącą bazę SQLite do modelu domenowego."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def load_timetable(self) -> Timetable:
        teacher_rows = list(self.session.scalars(select(Teacher).order_by(Teacher.name)))
        class_rows = list(
            self.session.scalars(select(SchoolClass).order_by(SchoolClass.name))
        )
        room_rows = list(self.session.scalars(select(Room).order_by(Room.name)))
        lesson_rows = list(
            self.session.scalars(
                select(Lesson)
                .options(
                    joinedload(Lesson.teacher),
                    joinedload(Lesson.school_class),
                    joinedload(Lesson.room),
                )
                .order_by(Lesson.day_index, Lesson.lesson_number, Lesson.id)
            )
        )

        return Timetable(
            lessons=[
                CoreLesson(
                    id=row.id,
                    teacher_name=row.teacher.name,
                    day_index=row.day_index,
                    lesson_number=row.lesson_number,
                    subject=row.subject,
                    day_name=row.day_name,
                    time_range=row.time_range,
                    class_name=row.school_class.name if row.school_class else None,
                    group_name=row.group_name,
                    room_name=row.room.name if row.room else None,
                )
                for row in lesson_rows
            ],
            teachers=[CoreTeacher(row.name) for row in teacher_rows],
            classes=[CoreSchoolClass(row.name) for row in class_rows],
            rooms=[CoreRoom(row.name) for row in room_rows],
        )
