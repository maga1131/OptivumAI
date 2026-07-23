from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class BasePage(QWidget):
    def __init__(self, title: str, description: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(32, 28, 32, 28)
        self.root_layout.setSpacing(16)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("pageTitle")
        self.root_layout.addWidget(self.title_label)

        if description:
            self.description_label = QLabel(description)
            self.description_label.setObjectName("pageDescription")
            self.description_label.setWordWrap(True)
            self.root_layout.addWidget(self.description_label)
        else:
            self.description_label = None

    def add_stretch(self) -> None:
        self.root_layout.addStretch(1)
