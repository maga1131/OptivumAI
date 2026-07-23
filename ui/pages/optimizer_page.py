from PySide6.QtWidgets import QWidget
from ui.pages.placeholder_page import PlaceholderPage


class OptimizerPage(PlaceholderPage):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            "Optymalizacja",
            "Przyszły moduł proponujący bezpieczne zmiany w planie.",
            "Optymalizator będzie korzystał z rdzenia Timetable i zestawu reguł szkoły. Każda propozycja będzie zawierała ocenę oraz wyjaśnienie.",
            parent,
        )
