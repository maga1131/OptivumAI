from dataclasses import dataclass, field


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
    # Wszystkie pary (klasa, grupa) biorące udział w jednej lekcji.
    # Pole obsługuje zajęcia łączone, np. 3TA -3/3, 3TB -2/2.
    participants: tuple[tuple[str, str | None], ...] = field(default_factory=tuple)
