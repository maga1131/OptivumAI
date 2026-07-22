from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from database.database import SessionLocal
from database.repository import Repository
from importer.html_importer import HtmlImporter
from ui.pages.base_page import BasePage


class StatCard(QFrame):
    def __init__(self, caption: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("statCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(4)

        self.value_label = QLabel("0")
        self.value_label.setObjectName("statValue")
        caption_label = QLabel(caption)
        caption_label.setObjectName("statCaption")
        layout.addWidget(self.value_label)
        layout.addWidget(caption_label)

    def set_value(self, value: int) -> None:
        self.value_label.setText(str(value))


class ProjectPage(BasePage):
    data_changed = Signal()
    status_message = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            "Projekt",
            "Importuj pełny eksport WWW z programu Plan Lekcji Optivum i sprawdzaj stan bazy danych.",
            parent,
        )

        project_card = QFrame()
        project_card.setObjectName("contentCard")
        project_layout = QVBoxLayout(project_card)
        project_layout.setContentsMargins(20, 18, 20, 18)
        project_layout.setSpacing(12)

        caption = QLabel("Bieżący projekt")
        caption.setObjectName("sectionTitle")
        self.project_path_label = QLabel("Nie wybrano katalogu eksportu")
        self.project_path_label.setObjectName("mutedText")
        self.project_path_label.setWordWrap(True)
        self.project_path_label.setTextInteractionFlags(self.project_path_label.textInteractionFlags())

        buttons = QHBoxLayout()
        self.import_button = QPushButton("Importuj eksport HTML")
        self.import_button.setObjectName("primaryButton")
        self.import_button.clicked.connect(self.import_html)
        self.refresh_button = QPushButton("Odśwież dane")
        self.refresh_button.clicked.connect(self.refresh_data)
        buttons.addWidget(self.import_button)
        buttons.addWidget(self.refresh_button)
        buttons.addStretch(1)

        project_layout.addWidget(caption)
        project_layout.addWidget(self.project_path_label)
        project_layout.addLayout(buttons)
        self.root_layout.addWidget(project_card)

        stats_grid = QGridLayout()
        stats_grid.setHorizontalSpacing(14)
        stats_grid.setVerticalSpacing(14)
        self.cards = {
            "teachers": StatCard("Nauczyciele"),
            "classes": StatCard("Klasy"),
            "rooms": StatCard("Sale"),
            "lessons": StatCard("Lekcje"),
        }
        stats_grid.addWidget(self.cards["teachers"], 0, 0)
        stats_grid.addWidget(self.cards["classes"], 0, 1)
        stats_grid.addWidget(self.cards["rooms"], 1, 0)
        stats_grid.addWidget(self.cards["lessons"], 1, 1)
        self.root_layout.addLayout(stats_grid)
        self.add_stretch()

        self.refresh_data()

    def import_html(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            "Wybierz katalog eksportu WWW z Plan Lekcji Optivum",
        )
        if not folder:
            return

        importer = HtmlImporter(folder)
        missing = importer.validate()
        if missing:
            message = "Brakuje wymaganych elementów:\n\n" + "\n".join(
                f"• {item}" for item in missing
            )
            QMessageBox.warning(self, "Niepoprawny eksport", message)
            return

        self.import_button.setEnabled(False)
        self.status_message.emit("Trwa importowanie danych…")
        try:
            result = importer.import_project()
            with SessionLocal() as session:
                repository = Repository(session)
                repository.clear_all()
                repository.save_import(
                    result.teachers,
                    result.classes,
                    result.rooms,
                    result.lessons,
                )

            self.project_path_label.setText(str(Path(folder)))
            self.refresh_data()
            self.data_changed.emit()
            QMessageBox.information(
                self,
                "Import zakończony",
                "\n".join(
                    (
                        f"Nauczyciele: {len(result.teachers)}",
                        f"Klasy: {len(result.classes)}",
                        f"Sale: {len(result.rooms)}",
                        f"Lekcje: {len(result.lessons)}",
                    )
                ),
            )
        except Exception as error:  # noqa: BLE001 - komunikat powinien trafić do użytkownika
            QMessageBox.critical(self, "Błąd importu", str(error))
        finally:
            self.import_button.setEnabled(True)
            self.status_message.emit("Gotowy")

    def refresh_data(self) -> None:
        with SessionLocal() as session:
            counts = Repository(session).counts()
        for key, card in self.cards.items():
            card.set_value(counts[key])
        self.status_message.emit("Dane odświeżone")
