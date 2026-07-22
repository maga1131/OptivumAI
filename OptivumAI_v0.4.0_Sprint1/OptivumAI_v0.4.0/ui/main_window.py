from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFileDialog, QGridLayout, QGroupBox, QHeaderView, QLabel,
                               QMainWindow, QMessageBox, QPushButton, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)
from database.database import SessionLocal
from database.repository import Repository
from importer.html_importer import HtmlImporter

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OptivumAI v0.4.0")
        self.resize(1150, 720)
        self.project_label = QLabel("Projekt: brak")
        self.project_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.teacher_label = QLabel("Nauczyciele: 0")
        self.class_label = QLabel("Klasy: 0")
        self.room_label = QLabel("Sale: 0")
        self.lesson_label = QLabel("Lekcje: 0")
        self.import_button = QPushButton("Importuj eksport HTML Optivum")
        self.import_button.clicked.connect(self.import_html)
        self.refresh_button = QPushButton("Odśwież dane z bazy")
        self.refresh_button.clicked.connect(self.refresh_view)
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["Dzień", "Lekcja", "Godzina", "Nauczyciel", "Klasa", "Grupa", "Przedmiot", "Sala"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        root = QWidget(); layout = QVBoxLayout(root)
        project = QGroupBox("Projekt"); pl = QVBoxLayout(project)
        pl.addWidget(self.project_label); pl.addWidget(self.import_button); pl.addWidget(self.refresh_button)
        stats = QGroupBox("Statystyki bazy"); sl = QGridLayout(stats)
        sl.addWidget(self.teacher_label,0,0); sl.addWidget(self.class_label,0,1)
        sl.addWidget(self.room_label,1,0); sl.addWidget(self.lesson_label,1,1)
        layout.addWidget(project); layout.addWidget(stats); layout.addWidget(QLabel("Zaimportowane lekcje")); layout.addWidget(self.table,1)
        self.setCentralWidget(root); self.statusBar().showMessage("Gotowy")
        self.refresh_view()

    def import_html(self):
        folder = QFileDialog.getExistingDirectory(self, "Wybierz katalog eksportu WWW z Plan Lekcji Optivum")
        if not folder: return
        importer = HtmlImporter(folder)
        missing = importer.validate()
        if missing:
            message = "Brakuje:\n\n" + "\n".join(f"• {x}" for x in missing)
            QMessageBox.warning(self, "Niepoprawny eksport", message)
            return
        self.import_button.setEnabled(False); self.statusBar().showMessage("Trwa importowanie danych…")
        try:
            result = importer.import_project()
            with SessionLocal() as session:
                repo = Repository(session); repo.clear_all(); repo.save_import(result.teachers, result.classes, result.rooms, result.lessons)
            self.project_label.setText(f"Projekt: {Path(folder)}"); self.refresh_view()
            summary = (
                f"Nauczyciele: {len(result.teachers)}\n"
                f"Klasy: {len(result.classes)}\n"
                f"Sale: {len(result.rooms)}\n"
                f"Lekcje: {len(result.lessons)}"
            )
            QMessageBox.information(self, "Import zakończony", summary)
        except Exception as e:
            QMessageBox.critical(self, "Błąd importu", str(e))
        finally:
            self.import_button.setEnabled(True); self.statusBar().showMessage("Gotowy")

    def refresh_view(self):
        with SessionLocal() as session:
            repo = Repository(session); counts = repo.counts(); lessons = repo.list_lessons()
        self.teacher_label.setText(f"Nauczyciele: {counts['teachers']}")
        self.class_label.setText(f"Klasy: {counts['classes']}")
        self.room_label.setText(f"Sale: {counts['rooms']}")
        self.lesson_label.setText(f"Lekcje: {counts['lessons']}")
        self.table.setRowCount(len(lessons))
        for r, lesson in enumerate(lessons):
            values=[lesson.day_name,str(lesson.lesson_number),lesson.time_range or "",lesson.teacher.name,
                    lesson.school_class.name if lesson.school_class else "",lesson.group_name or "",lesson.subject,
                    lesson.room.name if lesson.room else ""]
            for c, value in enumerate(values): self.table.setItem(r,c,QTableWidgetItem(value))
