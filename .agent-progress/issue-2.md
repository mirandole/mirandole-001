# Issue #2: Protected FastAPI App Shell

## Summary

Implemented the first deployable FastAPI Application deployee shell with
server-rendered pages, password login, signed session cookie handling, logout,
environment-based configuration, and configurable SQLite Stockage applicatif
initialization.

## Important decisions

- Used FastAPI factory mode: `uvicorn --factory mirandole.app:create_app`.
- Kept Acces protege mono-utilisateur for the Utilisateur principal; no account
  model or multi-user authentication was added.
- Required `MIRANDOLE_PASSWORD`, `MIRANDOLE_SESSION_SECRET`, and
  `MIRANDOLE_DATABASE_PATH` outside source code.
- Defaulted `MIRANDOLE_COOKIE_SECURE` to `true`, with documented local override
  for HTTP development.
- Initialized SQLite with an `app_metadata` table and schema version marker as
  the smallest useful Stockage applicatif foundation.

## Files changed

- `.gitignore`
- `README.md`
- `pyproject.toml`
- `uv.lock`
- `src/mirandole/__init__.py`
- `src/mirandole/app.py`
- `src/mirandole/config.py`
- `src/mirandole/storage.py`
- `src/mirandole/templates/base.html`
- `src/mirandole/templates/home.html`
- `src/mirandole/templates/login.html`
- `tests/test_app.py`
- `tests/test_storage.py`

## Commands run

- `gh issue view 2 --repo mirandole/mirandole-001 --comments --json number,title,body,labels,comments`
- `uv sync --extra dev`
- `uv run ruff format .`
- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run pytest`
- `timeout 5 env MIRANDOLE_PASSWORD='correct horse battery staple' MIRANDOLE_SESSION_SECRET='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' MIRANDOLE_DATABASE_PATH='/tmp/mirandole-smoke.sqlite3' MIRANDOLE_COOKIE_SECURE='false' uv run uvicorn --factory mirandole.app:create_app --host 127.0.0.1 --port 8765`

## Remaining blockers

None.
