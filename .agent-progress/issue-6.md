# Issue 6: Consulted Offers And Favorites

## Summary

Implemented Offre consultee and Offre favorite user states for Resultats d'offre.
Opening a Resultat d'offre marks it as consulted and redirects to its source URL.
The main results list visibly marks Offres consultees and exposes an etoile
control for toggling Offres favorites. Added a Vue favoris that lists all Offres
favorites for the Utilisateur principal with Tri des favoris by favorite date
newest first by default or Date de publication newest first.

## Important decisions

- Stored user states in `offer_user_states`, keyed by Identite de resultat, so
  consulted and favorite state follows the source plus canonical identity across
  Sessions de recherche.
- Kept the MVP without an internal offer detail page. The open route only marks
  the Offre consultee, then redirects to the source URL.
- The Vue favoris uses the latest persisted Resultat d'offre snapshot for each
  favorite Identite de resultat.

## Files changed

- `src/mirandole/storage.py`
- `src/mirandole/app.py`
- `src/mirandole/templates/base.html`
- `src/mirandole/templates/home.html`
- `src/mirandole/templates/favorites.html`
- `tests/test_storage.py`
- `tests/test_app.py`
- `.agent-progress/issue-6.md`

## Commands run

- `gh issue view 6 --repo mirandole/mirandole-001 --comments --json number,title,body,labels,comments`
- `gh issue view 4 --repo mirandole/mirandole-001 --json number,title,state,labels,url`
- `uv run ruff format --check .` (initially failed before dev dependencies were installed and before formatting)
- `uv run ruff check .` (initially failed before dev dependencies were installed and before wrapping two long lines)
- `uv run pytest` (initially failed before dev dependencies were installed, then exposed an ambiguous SQL column that was fixed)
- `uv sync --extra dev`
- `uv run ruff format .`
- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run pytest`

## Remaining blockers

None.
