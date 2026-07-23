# OptivumAI v0.8.0

Wersja zapisująca dane z eksportu WWW programu Plan Lekcji Optivum do bazy SQLite.

## Instalacja

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Plik bazy powstaje automatycznie w `database/optivumai.sqlite3`.
Każdy nowy import zastępuje poprzednie dane.


## v0.5.3
- wymuszenie widoczności wszystkich dni tygodnia,
- reset przewinięcia tabeli do poniedziałku po każdym odświeżeniu,
- poprawiona czytelność nagłówków przy węższym oknie.


## v0.8.0
- przeciąganie lekcji między dniami i godzinami,
- zapis nowego terminu bezpośrednio w bazie SQLite,
- automatyczne odświeżenie planu po przeniesieniu,
- potwierdzenie przeniesienia na zajętą komórkę.


## Nowości w v0.8.0

- ocena jakości planu 0–100 aktualizowana na żywo,
- wykrywanie konfliktów nauczyciela, sali oraz klasy/grupy,
- blokowanie nowych konfliktów podczas przenoszenia i zamiany,
- zestawienie okienek nauczycieli i klas,
- wykrywanie przepełnionych dni klas.
