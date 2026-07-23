from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True, slots=True)
class NavigationItem:
    key: str
    label: str


NAVIGATION_ITEMS = (
    NavigationItem("project", "Projekt"),
    NavigationItem("plan", "Plan"),
    NavigationItem("teachers", "Nauczyciele"),
    NavigationItem("classes", "Klasy"),
    NavigationItem("rooms", "Sale"),
    NavigationItem("lessons", "Lekcje"),
    NavigationItem("analysis", "Analiza"),
    NavigationItem("optimizer", "Optymalizacja"),
    NavigationItem("reports", "Raporty"),
)


class NavigationPanel(QWidget):
    page_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("navigationPanel")
        self.setFixedWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(8)

        title = QLabel("OptivumAI")
        title.setObjectName("appTitle")
        subtitle = QLabel("Plan lekcji")
        subtitle.setObjectName("appSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(18)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.buttons: dict[str, QPushButton] = {}

        for item in NAVIGATION_ITEMS:
            button = QPushButton(item.label)
            button.setObjectName("navigationButton")
            button.setCheckable(True)
            button.setMinimumHeight(42)
            button.clicked.connect(
                lambda checked=False, page_key=item.key: self.page_selected.emit(page_key)
            )
            self.button_group.addButton(button)
            self.buttons[item.key] = button
            layout.addWidget(button)

        layout.addStretch(1)

        version = QLabel("wersja 0.5.3")
        version.setObjectName("versionLabel")
        layout.addWidget(version)

        self.select("project")

    def select(self, page_key: str) -> None:
        button = self.buttons.get(page_key)
        if button is not None:
            button.setChecked(True)
