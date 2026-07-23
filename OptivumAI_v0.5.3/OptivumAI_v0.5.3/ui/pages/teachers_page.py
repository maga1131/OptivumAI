from PySide6.QtWidgets import QWidget
from sqlalchemy import select

from database.database import SessionLocal
from database.models import Teacher
from ui.pages.entity_page import EntityListPage


def load_teachers() -> list[str]:
    with SessionLocal() as session:
        return list(session.scalars(select(Teacher.name).order_by(Teacher.name)))


class TeachersPage(EntityListPage):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            "Nauczyciele",
            "Lista nauczycieli zaimportowanych z planu Optivum.",
            "Nauczyciel",
            load_teachers,
            parent,
        )
