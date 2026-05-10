# Issue 9: Adzuna Connector

## Summary

Implemented the Adzuna Connecteur de source as an environment-gated source in
the existing Recherche d'offres flow. It reads credentials from configuration,
sends intitule, localisation, and Rayon source to Adzuna, normalizes returned
offers into Resultats d'offre, and reports Adzuna HTTP/source failures as Echec
de source without failing the Session de recherche.

## Important decisions

- Used `MIRANDOLE_ADZUNA_APP_ID`, `MIRANDOLE_ADZUNA_APP_KEY`, and
  `MIRANDOLE_ADZUNA_ENABLED` from the documented source checklist.
- Mapped Rayon demande directly to Adzuna's `distance` parameter because the
  issue notes confirmed validated distance behavior.
- Used Adzuna `id` as the primary Identite de resultat, with the redirect URL or
  an Adzuna details URL as the source URL.
- Kept the live Adzuna smoke test out of the default test suite with the
  `live_adzuna` pytest mark.

## Files changed

- `README.md`
- `pyproject.toml`
- `src/mirandole/config.py`
- `src/mirandole/search.py`
- `tests/test_app.py`
- `tests/test_storage.py`

## Commands run

- `gh issue view 9 --repo mirandole/mirandole-001 --comments --json number,title,body,labels,comments`
- `gh issue view 3 --repo mirandole/mirandole-001 --json number,title,state,labels,url`
- `gh issue view 4 --repo mirandole/mirandole-001 --json number,title,state,labels,url`
- `uv run ruff format --check .` (failed because dev dependencies were not installed)
- `uv run ruff check .` (failed because dev dependencies were not installed)
- `uv run pytest` (failed because dev dependencies were not installed)
- `uv run --extra dev ruff format src/mirandole/search.py tests/test_storage.py`
- `uv run --extra dev ruff check --fix tests/test_storage.py`
- `uv run --extra dev ruff format --check .`
- `uv run --extra dev ruff check .`
- `uv run --extra dev pytest`
- `uv run --extra dev pytest -m live_adzuna`

## Remaining blockers

None. The explicit live Adzuna smoke test skipped in this environment because
real Adzuna credentials are not configured.
