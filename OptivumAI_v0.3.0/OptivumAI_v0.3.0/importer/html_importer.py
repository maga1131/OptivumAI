from __future__ import annotations
import re
from dataclasses import dataclass
from pathlib import Path
from bs4 import BeautifulSoup
from importer.models import ParsedLesson

DAYS = {
    "poniedziałek": ("Poniedziałek", 1), "poniedzialek": ("Poniedziałek", 1),
    "wtorek": ("Wtorek", 2), "środa": ("Środa", 3), "sroda": ("Środa", 3),
    "czwartek": ("Czwartek", 4), "piątek": ("Piątek", 5), "piatek": ("Piątek", 5),
}

@dataclass(slots=True)
class ImportResult:
    teachers: set[str]
    classes: set[str]
    rooms: set[str]
    lessons: list[ParsedLesson]

class HtmlImporter:
    def __init__(self, folder: str | Path):
        self.folder = Path(folder)
        self.plans_folder = self.folder / "plany"

    def validate(self):
        return [x for x in ("index.html", "lista.html", "plany") if not (self.folder / x).exists()]

    def import_project(self):
        missing = self.validate()
        if missing:
            raise ValueError("Brakuje: " + ", ".join(missing))
        teachers = self._entity_names("n*.html")
        classes = self._entity_names("o*.html")
        rooms = self._entity_names("s*.html")
        lessons = []
        for path in sorted(self.plans_folder.glob("n*.html")):
            lessons.extend(self._parse_teacher(path))
        teachers.update(x.teacher for x in lessons)
        classes.update(x.class_name for x in lessons if x.class_name)
        rooms.update(x.room for x in lessons if x.room)
        return ImportResult(teachers, classes, rooms, lessons)

    def _entity_names(self, pattern):
        result = set()
        for path in self.plans_folder.glob(pattern):
            soup = self._soup(path)
            title = self._title(soup)
            if title: result.add(title)
        return result

    def _parse_teacher(self, path):
        soup = self._soup(path)
        teacher = self._title(soup) or path.stem
        tables = soup.find_all("table")
        if not tables: return []
        table = max(tables, key=lambda t: sum(day in t.get_text(" ", strip=True).casefold() for day in DAYS))
        rows = table.find_all("tr")
        day_columns = self._day_columns(rows)
        result = []
        for row in rows:
            cells = row.find_all(["td", "th"], recursive=False)
            if not cells: continue
            number, time_range = self._lesson_meta(cells[0].get_text(" ", strip=True))
            if number is None: continue
            for col, day_name, day_index in day_columns:
                if col >= len(cells): continue
                data = self._cell_data(cells[col].get_text(" ", strip=True))
                if not data or not data["subject"]: continue
                result.append(ParsedLesson(teacher, day_name, day_index, number, time_range,
                                           data["class_name"], data["group_name"], data["subject"], data["room"]))
        return result

    def _day_columns(self, rows):
        best = []
        for row in rows[:5]:
            current = []
            for i, cell in enumerate(row.find_all(["td", "th"], recursive=False)):
                text = cell.get_text(" ", strip=True).casefold()
                for alias, value in DAYS.items():
                    if alias in text:
                        current.append((i, value[0], value[1])); break
            if len(current) > len(best): best = current
        return best

    @staticmethod
    def _lesson_meta(text):
        m = re.search(r"(?<!\d)(\d{1,2})(?!\d)", text)
        if not m: return None, None
        tm = re.search(r"(\d{1,2}[:.]\d{2})\s*[-–—]\s*(\d{1,2}[:.]\d{2})", text)
        return int(m.group(1)), (f"{tm.group(1).replace('.', ':')}-{tm.group(2).replace('.', ':')}" if tm else None)

    @staticmethod
    def _cell_data(text):
        text = " ".join(text.replace("\xa0", " ").split())
        if not text or text in {"-", "–", "—"}: return None
        tokens = re.split(r"\s+", text)
        class_name = next((t for t in tokens if re.fullmatch(r"\d{1,2}[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż][A-Za-z0-9-]*", t)), None)
        group_name = next((t for t in tokens if re.fullmatch(r"\d+/\d+", t)), None)
        room = None
        rm = re.search(r"(?:sala|s\.?)\s*[:.]?\s*([A-Za-z0-9-]+)", text, re.I)
        if rm: room = rm.group(1)
        subject = text
        for value in (class_name, group_name):
            if value: subject = subject.replace(value, " ", 1)
        if rm: subject = subject.replace(rm.group(0), " ", 1)
        subject = " ".join(subject.split()).strip(" -|,")
        return {"class_name": class_name, "group_name": group_name, "subject": subject, "room": room}

    @staticmethod
    def _soup(path):
        return BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "lxml")

    @staticmethod
    def _title(soup):
        node = soup.select_one(".tytulnapis") or soup.find(["h1", "h2", "title"])
        return " ".join(node.get_text(" ", strip=True).split()) if node else None
