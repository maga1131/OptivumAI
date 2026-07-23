# Architektura OptivumAI

## Zasada nadrzędna

Rdzeń programu (`core`) nie zależy od PySide6, SQLAlchemy ani formatu eksportu Optivum.
Dzięki temu analizator i optymalizator można testować bez uruchamiania interfejsu i bez bazy danych.

## Przepływ danych

```text
Eksport HTML
    ↓
Importer
    ↓
SQLite / SQLAlchemy
    ↓
SqlAlchemyTimetableRepository
    ↓
Timetable (pamięć)
    ↓
Analizator / Optymalizator
    ↓
GUI
```

## Moduły Sprintu 1

- `core/entities.py` — encje domenowe: `Lesson`, `Teacher`, `SchoolClass`, `Room`.
- `core/timetable.py` — indeksowanie i modyfikowanie planu w pamięci.
- `core/repository.py` — niezależny kontrakt repozytorium.
- `database/timetable_repository.py` — adapter obecnej bazy SQLAlchemy.
- `tests/test_timetable.py` — testy zachowania modelu.

## Najważniejsze wywołania

```python
teacher = timetable.teacher("M.BAR")
teacher.lessons()
teacher.monday()
teacher.gaps()
teacher.building_changes(room_buildings)

school_class = timetable.class_("3TC")
school_class.daily_load()

room = timetable.room("12")
room.occupancy()
```

## Następny etap

Sprint 2 powinien dodać silnik reguł (`ConstraintEngine`) i pierwsze kontrole:
konflikt nauczyciela, konflikt klasy, konflikt sali, okienka klasy oraz limit 9 lekcji.
