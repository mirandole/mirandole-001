# mirandole-001

Application d'agregation d'offres d'emploi. Le MVP est une Application deployee
FastAPI avec rendu serveur, Acces protege et Stockage applicatif SQLite.

## Development setup

```bash
uv sync --extra dev
```

## Local run

The application requires configuration from environment variables. Do not store
real passwords or secrets in source code.

```bash
export MIRANDOLE_PASSWORD="change-this-local-password"
export MIRANDOLE_SESSION_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export MIRANDOLE_DATABASE_PATH="./var/mirandole.sqlite3"
export MIRANDOLE_COOKIE_SECURE="false"
uv run uvicorn --factory mirandole.app:create_app --reload
```

Then open `http://127.0.0.1:8000/`.

## VPS configuration

Required environment variables:

- `MIRANDOLE_PASSWORD`: password for the Utilisateur principal. Minimum 12
  characters.
- `MIRANDOLE_SESSION_SECRET`: signing secret for the session cookie. Minimum 32
  characters; generate a unique value for the Application deployee.
- `MIRANDOLE_DATABASE_PATH`: filesystem path for the SQLite Stockage applicatif.
- `MIRANDOLE_COOKIE_SECURE`: optional, defaults to `true`. Keep `true` when the
  Application deployee is served over HTTPS. Set `false` only for local HTTP
  development or an explicitly controlled WireGuard-only HTTP deployment.
- `MIRANDOLE_FRANCE_TRAVAIL_ENABLED`: optional, defaults to `false`. Set `true`
  to enable the France Travail Connecteur de source.
- `MIRANDOLE_FRANCE_TRAVAIL_CLIENT_ID`: required only when France Travail is
  enabled.
- `MIRANDOLE_FRANCE_TRAVAIL_CLIENT_SECRET`: required only when France Travail is
  enabled. Store the real value in the deployment environment only.

Recommended production command:

```bash
uv run uvicorn --factory mirandole.app:create_app --host 127.0.0.1 --port 8000
```

The initial deployment should expose the service only through the WireGuard
interface or a local reverse proxy, while still keeping the password-based Acces
protege enabled.

## Checks

```bash
uv run ruff format --check .
uv run ruff check .
uv run pytest
```
