from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import (
    QFrame,
    QHeaderView,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.pages.base_page import BasePage


class EntityListPage(BasePage):
    def __init__(
        self,
        title: str,
        description: str,
        column_title: str,
        data_loader: Callable[[], list[str]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(title, description, parent)
        self.data_loader = data_loader
        self.all_names: list[str] = []

        card = QFrame()
        card.setObjectName("contentCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.summary_label = QLabel("Liczba pozycji: 0")
        self.summary_label.setObjectName("sectionTitle")
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Szukaj…")
        self.search_box.setClearButtonEnabled(True)
        self.search_box.textChanged.connect(self.apply_filter)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Lp.", column_title])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        layout.addWidget(self.summary_label)
        layout.addWidget(self.search_box)
        layout.addWidget(self.table)
        self.root_layout.addWidget(card, 1)
        self.refresh_data()

    def refresh_data(self) -> None:
        self.all_names = self.data_loader()
        self.apply_filter(self.search_box.text())

    def apply_filter(self, text: str) -> None:
        query = text.strip().casefold()
        visible = [name for name in self.all_names if query in name.casefold()]
        self.summary_label.setText(
            f"Liczba pozycji: {len(visible)}" if query else f"Liczba pozycji: {len(self.all_names)}"
        )
        self.table.setRowCount(len(visible))
        for row, name in enumerate(visible):
            self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.table.setItem(row, 1, QTableWidgetItem(name))
