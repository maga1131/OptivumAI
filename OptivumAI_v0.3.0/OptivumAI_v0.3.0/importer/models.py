from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class ParsedLesson:
    teacher: str
    day_name: str
    day_index: int
    lesson_number: int
    time_range: str | None
    class_name: str | None
    group_name: str | None
    subject: str
    room: str | None
