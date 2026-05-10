# Issue #5: Post-Aggregation Enrichment And Filters

## Summary

Implemented post-aggregation enrichment for normalized Resultats d'offre and
Filtres de resultats on the main search results path. Resultats d'offre now
store and display Tags de competence, Niveau d'experience demande, Niveau de
diplome demande, Remuneration indiquee and teletravail information, while the
Utilisateur principal can filter displayed results by Type de contrat recherche,
experience and diplome.

## Important decisions

- Kept enrichment outside Connecteurs de source: the demo Connecteur de source
  still returns normalized source data, and `mirandole.enrichment` applies
  shared rules before persistence.
- Used a configurable IT skills dictionary API with a default in-code dictionary
  for the current MVP slice.
- Applied Filtres de resultats after aggregation by loading the persisted
  Session de recherche results and filtering the displayed list in the FastAPI
  route.
- Kept teletravail and Remuneration indiquee display-only; no filter controls
  were added for those fields.
- Included CDI, CDD, Freelance and Interim by default, which excludes Stage and
  Alternance unless the Utilisateur principal explicitly selects them.

## Files changed

- `src/mirandole/app.py`
- `src/mirandole/enrichment.py`
- `src/mirandole/search.py`
- `src/mirandole/storage.py`
- `src/mirandole/templates/base.html`
- `src/mirandole/templates/home.html`
- `tests/test_app.py`
- `tests/test_enrichment.py`
- `tests/test_storage.py`
- `.agent-progress/issue-5.md`

## Commands run

- `gh issue view 5 --repo mirandole/mirandole-001 --comments --json number,title,body,labels,comments`
- `gh issue view 4 --repo mirandole/mirandole-001 --json number,title,state,labels,url`
- `git fetch origin main && git merge --ff-only origin/main`
- `uv run ruff format .` (failed: dev tools not installed without `--extra dev`)
- `uv run --extra dev ruff format .`
- `uv run --extra dev ruff check .` (failed before fixes)
- `uv run --extra dev pytest`
- `uv run --extra dev ruff check --fix .`
- `uv run --extra dev ruff format .`
- `uv run --extra dev ruff format --check .`
- `uv run --extra dev ruff check .`
- `uv run --extra dev pytest`

## Remaining blockers

None.
