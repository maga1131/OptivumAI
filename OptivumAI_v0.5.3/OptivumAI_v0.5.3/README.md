# OptivumAI v0.5.0

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
