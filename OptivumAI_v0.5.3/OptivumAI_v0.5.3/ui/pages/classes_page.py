from PySide6.QtWidgets import QWidget
from sqlalchemy import select

from database.database import SessionLocal
from database.models import SchoolClass
from ui.pages.entity_page import EntityListPage


def load_classes() -> list[str]:
    with SessionLocal() as session:
        return list(session.scalars(select(SchoolClass.name).order_by(SchoolClass.name)))


class ClassesPage(EntityListPage):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            "Klasy",
            "Lista oddziałów szkolnych dostępnych w zaimportowanym planie.",
            "Klasa",
            load_classes,
            parent,
        )
