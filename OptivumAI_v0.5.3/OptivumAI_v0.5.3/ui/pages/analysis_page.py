from PySide6.QtWidgets import QWidget
from ui.pages.placeholder_page import PlaceholderPage


class AnalysisPage(PlaceholderPage):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            "Analiza",
            "W tym miejscu pojawi się automatyczna ocena jakości planu.",
            "Moduł analizy zostanie dodany w kolejnym sprincie. Będzie wykrywał między innymi okienka, konflikty, przenoszenie między budynkami i nieprawidłowe położenie religii.",
            parent,
        )
