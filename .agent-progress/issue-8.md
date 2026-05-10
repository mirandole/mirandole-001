# Issue #8: France Travail Connector

## Summary

Implemented an opt-in France Travail Connecteur de source that reads credentials
from environment-backed settings, maps Recherche d'offres inputs to the France
Travail API request, normalizes returned offers into the shared Resultat d'offre
contract, and reports France Travail failures as Echec de source while preserving
successful results from other Sources d'offres.

## Important decisions

- France Travail is disabled by default with
  `MIRANDOLE_FRANCE_TRAVAIL_ENABLED=false`.
- When enabled, `MIRANDOLE_FRANCE_TRAVAIL_CLIENT_ID` and
  `MIRANDOLE_FRANCE_TRAVAIL_CLIENT_SECRET` are required; no real credentials are
  stored in source code.
- France Travail Rayon source maps directly from the MVP Rayon demande values.
- Identite de resultat prefers the France Travail source offer id and falls back
  to the canonical France Travail offer URL.
- The existing demo source remains available so current local MVP behavior and
  tests stay intact.

## Files changed

- `README.md`
- `src/mirandole/app.py`
- `src/mirandole/config.py`
- `src/mirandole/search.py`
- `tests/test_app.py`
- `tests/test_storage.py`
- `.agent-progress/issue-8.md`

## Commands run

- `gh issue view 8 --repo mirandole/mirandole-001 --comments --json number,title,body,labels,comments`
- `gh issue view 3 --repo mirandole/mirandole-001 --json number,title,state,url,labels`
- `gh issue view 4 --repo mirandole/mirandole-001 --json number,title,state,url,labels`
- `gh issue view 3 --repo mirandole/mirandole-001 --comments --json number,title,body,comments`
- `uv run ruff format --check .` (failed before dev tools were installed, then passed)
- `uv run ruff check .` (failed before dev tools were installed, then passed)
- `uv run pytest` (failed before dev tools were installed, then passed)
- `uv sync --extra dev`
- `uv run ruff format .`
- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run pytest`

## Remaining blockers

None.
