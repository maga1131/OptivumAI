import sys
from PySide6.QtWidgets import QApplication
from database.database import init_database
from ui.main_window import MainWindow

def main() -> int:
    init_database()
    app = QApplication(sys.argv)
    app.setApplicationName("OptivumAI")
    window = MainWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
