from __future__ import annotations
import re
from dataclasses import dataclass
from pathlib import Path
from bs4 import BeautifulSoup
from importer.models import ParsedLesson

DAYS = {
    "poniedziałek": ("Poniedziałek", 0), "poniedzialek": ("Poniedziałek", 0),
    "wtorek": ("Wtorek", 1), "środa": ("Środa", 2), "sroda": ("Środa", 2),
    "czwartek": ("Czwartek", 3), "piątek": ("Piątek", 4), "piatek": ("Piątek", 4),
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
                                           data["class_name"], data["group_name"], data["subject"], data["room"], data["participants"]))
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
        if not text or text in {"-", "–", "—"}:
            return None

        # Sala znajduje się na końcu wpisu. Oprócz sal rozpoczynających
        # się cyfrą, W, SALA lub CKZ obsługujemy specjalne oznaczenie "@".
        room = None
        rm = re.search(
            r"(?P<room>"
            r"@"
            r"|(?:SALA(?:[_ -]+\S+)*)"
            r"|(?:CKZ(?:[_ -]+\S+)*)"
            r"|(?:W\S*)"
            r"|(?:\d+\S*)"
            r")$",
            text,
            re.IGNORECASE,
        )
        if rm:
            candidate = rm.group("room").strip(" ,;|")
            looks_like_class = bool(re.fullmatch(
                r"\d{1,2}[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż][A-Za-z0-9_ĄĆĘŁŃÓŚŹŻąćęłńóśźż]*",
                candidate,
            ))
            # Gdy przed końcowym tokenem występuje oznaczenie grupy, token
            # podobny do 3TA jest klasą, a nie salą.
            if looks_like_class and re.search(r"-[^\s,]+\s+" + re.escape(candidate) + r"$", text):
                rm = None
            elif candidate == "@" or not candidate.casefold().startswith("w") or candidate.startswith("W"):
                room = candidate
            else:
                rm = None

        content = text[:rm.start()] if rm else text
        content = content.strip(" ,;|")

        # Zajęcia mogą obejmować kilka grup z różnych klas, np.:
        # "3TA -3/3, 3TB -2/2 j.hiszpański". Wyłapujemy wszystkie
        # pary klasa-grupa z początku wpisu. Nazwą grupy jest cały ciąg
        # po myślniku do najbliższej spacji lub przecinka.
        participant_pattern = re.compile(
            r"(?P<class>\d{1,2}[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż]"
            r"[A-Za-z0-9_ĄĆĘŁŃÓŚŹŻąćęłńóśźż]*)"
            r"(?:\s*-(?P<group>[^\s,]+))?"
        )
        matches = list(participant_pattern.finditer(content))
        participants: list[tuple[str, str | None]] = []
        prefix_end = 0
        for match in matches:
            # Uznajemy za uczestników tylko kolejne oznaczenia na początku
            # wpisu, rozdzielone spacją lub przecinkiem.
            between = content[prefix_end:match.start()]
            if participants and between.strip(" ,"):
                break
            if not participants and match.start() != 0:
                break
            participants.append((match.group("class"), match.group("group")))
            prefix_end = match.end()

        if participants:
            subject = content[prefix_end:].lstrip(" ,")
        else:
            # Starsze i nietypowe wpisy mogą mieć przedmiot przed oznaczeniem
            # grupy/klasy. Wtedy zachowujemy uniwersalną regułę: grupa to
            # wszystko po "-" do spacji, niezależnie od położenia.
            class_match = re.search(
                r"(?<![A-Za-z0-9_])\d{1,2}[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż]"
                r"[A-Za-z0-9_ĄĆĘŁŃÓŚŹŻąćęłńóśźż]*",
                content,
            )
            group_match = re.search(r"-([^\s,]+)", content)
            class_name = class_match.group(0) if class_match else None
            group_name = group_match.group(1) if group_match else None
            if class_name:
                participants = [(class_name, group_name)]
            subject = content
            if class_match:
                subject = subject[:class_match.start()] + " " + subject[class_match.end():]
            if group_match:
                subject = re.sub(r"-[^\s,]+", " ", subject, count=1)

        # Zgodność wsteczna: główna klasa i grupa to pierwszy uczestnik.
        class_name = participants[0][0] if participants else None
        group_name = participants[0][1] if participants else None
        subject = " ".join(subject.split()).strip(" -|,")
        return {
            "class_name": class_name,
            "group_name": group_name,
            "participants": tuple(participants),
            "subject": subject,
            "room": room,
        }

    @staticmethod
    def _soup(path):
        return BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "lxml")

    @staticmethod
    def _title(soup):
        node = soup.select_one(".tytulnapis") or soup.find(["h1", "h2", "title"])
        return " ".join(node.get_text(" ", strip=True).split()) if node else None
