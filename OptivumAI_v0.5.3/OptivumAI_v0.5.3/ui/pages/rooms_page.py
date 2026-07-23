from PySide6.QtWidgets import QWidget
from sqlalchemy import select

from database.database import SessionLocal
from database.models import Room
from ui.pages.entity_page import EntityListPage


def load_rooms() -> list[str]:
    with SessionLocal() as session:
        return list(session.scalars(select(Room.name).order_by(Room.name)))


class RoomsPage(EntityListPage):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            "Sale",
            "Lista sal lekcyjnych wykrytych podczas importu.",
            "Sala",
            load_rooms,
            parent,
        )
