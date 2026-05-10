# Issue #4: Search Tracer With Demo Source

## Summary

Implemented the first protected Recherche d'offres vertical slice with a demo
Connecteur de source. The Utilisateur principal can submit an intitule,
localisation and Rayon demande, creating a persisted Session de recherche with
normalized Resultats d'offre in Stockage applicatif.

## Important decisions

- Kept the first slice server-rendered in FastAPI/Jinja and SQLite, matching the
  existing app shell and ADR-0003.
- Added a demo Connecteur de source with supported Rayon source values of 20,
  50 and 100 km, mapping each Rayon demande to the exact or next-higher value.
- Simulated an Echec de source when the submitted intitule contains "echec", so
  the Session de recherche is still persisted and the failure is visible without
  marking existing Resultats d'offre inactive.
- Sorted displayed Resultats d'offre by Date de publication newest first, with
  unknown dates after dated results.

## Files changed

- `src/mirandole/app.py`
- `src/mirandole/search.py`
- `src/mirandole/storage.py`
- `src/mirandole/templates/base.html`
- `src/mirandole/templates/home.html`
- `tests/test_app.py`
- `tests/test_storage.py`
- `.agent-progress/issue-4.md`

## Commands run

- `gh issue view 4 --repo mirandole/mirandole-001 --comments --json number,title,body,labels,comments`
- `gh issue view 2 --repo mirandole/mirandole-001 --json number,title,state,url,labels`
- `uv run pytest` (failed: dev tools not installed without extra)
- `uv run ruff check .` (failed: dev tools not installed without extra)
- `uv run ruff format --check .` (failed: dev tools not installed without extra)
- `uv run --extra dev pytest`
- `uv run --extra dev ruff check .`
- `uv run --extra dev ruff format --check .`
- `uv run --extra dev ruff check --fix src/mirandole/search.py`
- `uv run --extra dev ruff format .`

## Remaining blockers

None.
