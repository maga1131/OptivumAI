from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QStackedWidget, QWidget

from ui.navigation import NavigationPanel
from ui.pages import (
    AnalysisPage,
    ClassesPage,
    LessonsPage,
    OptimizerPage,
    ProjectPage,
    ReportsPage,
    RoomsPage,
    TeachersPage,
)


APP_STYLE = """
QMainWindow, QWidget {
    background: #f4f6f8;
    color: #1f2933;
    font-family: "Segoe UI";
    font-size: 10pt;
}
#navigationPanel {
    background: #172033;
}
#appTitle {
    color: white;
    font-size: 20pt;
    font-weight: 700;
}
#appSubtitle, #versionLabel {
    color: #9fb0c6;
}
#navigationButton {
    background: transparent;
    color: #dce5f0;
    border: none;
    border-radius: 7px;
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
}
#navigationButton:hover {
    background: #23314a;
}
#navigationButton:checked {
    background: #2e6fdb;
    color: white;
}
#pageTitle {
    font-size: 22pt;
    font-weight: 700;
    color: #172033;
}
#pageDescription, #mutedText {
    color: #66788a;
}
#contentCard, #statCard {
    background: white;
    border: 1px solid #dce3ea;
    border-radius: 10px;
}
#sectionTitle {
    font-size: 12pt;
    font-weight: 700;
}
#statValue {
    font-size: 24pt;
    font-weight: 700;
    color: #2e6fdb;
}
#statCaption {
    color: #66788a;
}
QPushButton {
    background: white;
    border: 1px solid #cbd5df;
    border-radius: 6px;
    padding: 8px 14px;
}
QPushButton:hover {
    background: #edf2f7;
}
#primaryButton {
    background: #2e6fdb;
    color: white;
    border: 1px solid #2e6fdb;
    font-weight: 600;
}
#primaryButton:hover {
    background: #255fbe;
}
QLineEdit {
    background: white;
    border: 1px solid #cbd5df;
    border-radius: 6px;
    padding: 8px 10px;
}
QTableWidget {
    background: white;
    alternate-background-color: #f7f9fb;
    border: 1px solid #dce3ea;
    border-radius: 6px;
    gridline-color: #e7ecf1;
}
QHeaderView::section {
    background: #edf2f7;
    border: none;
    border-bottom: 1px solid #dce3ea;
    padding: 8px;
    font-weight: 600;
}
QStatusBar {
    background: white;
    border-top: 1px solid #dce3ea;
}
"""


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("OptivumAI v0.4.5")
        self.resize(1280, 780)
        self.setMinimumSize(980, 640)
        self.setStyleSheet(APP_STYLE)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.navigation = NavigationPanel()
        self.stack = QStackedWidget()
        layout.addWidget(self.navigation)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        self.pages = {
            "project": ProjectPage(),
            "teachers": TeachersPage(),
            "classes": ClassesPage(),
            "rooms": RoomsPage(),
            "lessons": LessonsPage(),
            "analysis": AnalysisPage(),
            "optimizer": OptimizerPage(),
            "reports": ReportsPage(),
        }
        for page in self.pages.values():
            self.stack.addWidget(page)

        self.navigation.page_selected.connect(self.show_page)
        self.pages["project"].data_changed.connect(self.refresh_data_pages)
        self.pages["project"].status_message.connect(self.statusBar().showMessage)

        self.show_page("project")
        self.statusBar().showMessage("Gotowy")

    def show_page(self, page_key: str) -> None:
        page = self.pages.get(page_key)
        if page is None:
            return
        refresh = getattr(page, "refresh_data", None)
        if callable(refresh) and page_key != "project":
            refresh()
        self.stack.setCurrentWidget(page)
        self.navigation.select(page_key)

    def refresh_data_pages(self) -> None:
        for key in ("teachers", "classes", "rooms", "lessons"):
            refresh = getattr(self.pages[key], "refresh_data", None)
            if callable(refresh):
                refresh()
        self.statusBar().showMessage("Zaimportowano i odświeżono dane")
