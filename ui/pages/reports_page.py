from PySide6.QtWidgets import QWidget
from ui.pages.placeholder_page import PlaceholderPage


class ReportsPage(PlaceholderPage):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            "Raporty",
            "Eksport wyników analiz i zestawień.",
            "W przyszłości będzie można tworzyć raporty dla dyrekcji, nauczycieli, klas i sal.",
            parent,
        )
