from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, joinedload

from database.models import ClassGroup, Lesson, Room, SchoolClass, Teacher, lesson_class_groups
from importer.models import ParsedLesson


class Repository:
    def __init__(self, session: Session):
        self.session = session

    def clear_all(self) -> None:
        self.session.execute(delete(lesson_class_groups))
        self.session.execute(delete(Lesson))
        self.session.execute(delete(ClassGroup))
        self.session.execute(delete(Teacher))
        self.session.execute(delete(SchoolClass))
        self.session.execute(delete(Room))
        self.session.commit()

    def save_import(self, teacher_names, class_names, room_names, lessons: list[ParsedLesson]) -> None:
        teachers = self._create(Teacher, teacher_names)
        classes = self._create(SchoolClass, class_names)
        rooms = self._create(Room, room_names)
        groups: dict[tuple[str, str], ClassGroup] = {}

        for item in lessons:
            teacher = teachers.get(item.teacher) or self._add(Teacher, item.teacher, teachers)
            school_class = self._get_or_add(SchoolClass, item.class_name, classes)
            room = self._get_or_add(Room, item.room, rooms)
            lesson = Lesson(
                teacher_id=teacher.id,
                school_class_id=school_class.id if school_class else None,
                room_id=room.id if room else None,
                day_name=item.day_name,
                day_index=item.day_index,
                lesson_number=item.lesson_number,
                time_range=item.time_range,
                group_name=item.group_name,
                subject=item.subject,
            )
            participant_pairs = item.participants or ((item.class_name, item.group_name),)
            for participant_class_name, participant_group_name in participant_pairs:
                participant_class = self._get_or_add(SchoolClass, participant_class_name, classes)
                if not participant_class or not participant_group_name:
                    continue
                key = (participant_class.name, participant_group_name)
                group = groups.get(key)
                if group is None:
                    group = ClassGroup(school_class_id=participant_class.id, name=participant_group_name)
                    self.session.add(group)
                    self.session.flush()
                    groups[key] = group
                lesson.groups.append(group)
            self.session.add(lesson)
        self.session.commit()

    def _create(self, model, names):
        result = {}
        for name in sorted({x.strip() for x in names if x and x.strip()}):
            obj = model(name=name)
            self.session.add(obj)
            result[name] = obj
        self.session.flush()
        return result

    def _add(self, model, name, mapping):
        obj = model(name=name)
        self.session.add(obj)
        self.session.flush()
        mapping[name] = obj
        return obj

    def _get_or_add(self, model, name, mapping):
        if not name:
            return None
        return mapping.get(name) or self._add(model, name, mapping)

    def counts(self):
        return {
            "teachers": self.session.scalar(select(func.count()).select_from(Teacher)) or 0,
            "classes": self.session.scalar(select(func.count()).select_from(SchoolClass)) or 0,
            "groups": self.session.scalar(select(func.count()).select_from(ClassGroup)) or 0,
            "rooms": self.session.scalar(select(func.count()).select_from(Room)) or 0,
            "lessons": self.session.scalar(select(func.count()).select_from(Lesson)) or 0,
        }

    def list_groups(self):
        stmt = (
            select(ClassGroup)
            .options(joinedload(ClassGroup.school_class))
            .order_by(SchoolClass.name, ClassGroup.name)
        )
        return list(self.session.scalars(stmt))

    def list_lessons(self, limit=5000):
        stmt = (
            select(Lesson)
            .options(
                joinedload(Lesson.teacher),
                joinedload(Lesson.school_class),
                joinedload(Lesson.room),
                joinedload(Lesson.groups),
            )
            .order_by(Lesson.day_index, Lesson.lesson_number)
            .limit(limit)
        )
        return list(self.session.scalars(stmt).unique())
