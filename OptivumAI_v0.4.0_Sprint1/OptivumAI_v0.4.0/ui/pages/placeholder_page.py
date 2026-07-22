from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from ui.pages.base_page import BasePage


class PlaceholderPage(BasePage):
    def __init__(self, title: str, description: str, message: str, parent: QWidget | None = None) -> None:
        super().__init__(title, description, parent)
        card = QFrame()
        card.setObjectName("contentCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        label = QLabel(message)
        label.setObjectName("mutedText")
        label.setWordWrap(True)
        layout.addWidget(label)
        self.root_layout.addWidget(card)
        self.add_stretch()
