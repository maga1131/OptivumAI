import os

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QMessageBox,
)

from importer.html_importer import HtmlImporter


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("OptivumAI v0.2")
        self.resize(900, 600)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout()

        # Informacja o projekcie
        self.projectLabel = QLabel("Projekt: brak")

        # Statystyki
        self.teacherLabel = QLabel("Nauczyciele: 0")
        self.classLabel = QLabel("Klasy: 0")
        self.roomLabel = QLabel("Sale: 0")
        self.lessonLabel = QLabel("Lekcje: 0")

        # Przycisk importu
        self.importButton = QPushButton("Import HTML")
        self.importButton.clicked.connect(self.import_html)

        layout.addWidget(self.projectLabel)
        layout.addWidget(self.importButton)
        layout.addWidget(self.teacherLabel)
        layout.addWidget(self.classLabel)
        layout.addWidget(self.roomLabel)
        layout.addWidget(self.lessonLabel)

        central.setLayout(layout)

    def import_html(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Wybierz katalog z eksportem HTML Optivuma"
        )

        if not folder:
            return

        self.projectLabel.setText(f"Projekt: {folder}")

        required = [
            "index.html",
            "lista.html",
            "plany"
        ]

        missing = []

        for item in required:
            if not os.path.exists(os.path.join(folder, item)):
                missing.append(item)

        if missing:
            QMessageBox.warning(
                self,
                "Błąd",
                "To nie jest poprawny eksport Optivuma.\n\nBrakuje:\n"
                + "\n".join(missing)
            )
            return

        importer = HtmlImporter(folder)

        data = importer.import_project()

        self.teacherLabel.setText(
            f"Nauczyciele: {data['teachers']}"
        )

        self.classLabel.setText(
            f"Klasy: {data['classes']}"
        )

        self.roomLabel.setText(
            f"Sale: {data['rooms']}"
        )

        self.lessonLabel.setText(
            f"Lekcje: {data['lessons']}"
        )

        QMessageBox.information(
            self,
            "Import zakończony",
            "Eksport został poprawnie wczytany."
        )