# OptivumAI v0.4.5

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
