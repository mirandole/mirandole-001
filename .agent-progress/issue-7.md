# Issue 7: Recent Searches, New Offers, And Inactive Offers

## Summary

Implemented continuity features across Sessions de recherche:

- Recherches recentes are persisted in stockage applicatif, deduplicated by identical Recherche d'offres, sorted by last use, and capped at 10.
- Identite de resultat is derived from Source d'offres plus source identifier when present, otherwise canonical source URL.
- Offre nouvelle is computed against the previous Session de recherche for the same Recherche d'offres.
- Offre inactive rows are added for known Resultats d'offre missing from a later successful session for the same Recherche d'offres and Source d'offres.
- Offre favorite and Offre consultee states remain keyed by Identite de resultat and are preserved when a result becomes inactive.
- Echec de source records a failed session without marking offers from that Source d'offres inactive.

## Important Decisions

- The first Session de recherche for a Recherche d'offres marks no Resultats d'offre as Offre nouvelle because there is no previous session to compare.
- A Resultat d'offre becomes inactive after a later successful response from the same Source d'offres omits it; failed source responses are ignored for inactive transitions.
- Inactive results are represented as new offer_results rows in the current session so the existing list and Vue favoris can display persisted user states through the same Identite de resultat join.
- Recherches recentes use normalized title, location, and rayon demande for deduplication, while preserving the latest submitted display values.

## Files Changed

- `src/mirandole/app.py`
- `src/mirandole/search.py`
- `src/mirandole/storage.py`
- `src/mirandole/templates/favorites.html`
- `src/mirandole/templates/home.html`
- `tests/test_app.py`
- `tests/test_storage.py`
- `.agent-progress/issue-7.md`

## Commands Run

- `gh issue view 7 --repo mirandole/mirandole-001 --comments --json number,title,body,labels,comments`
- `gh issue view 4 --repo mirandole/mirandole-001 --json number,title,state,labels,url`
- `gh issue view 6 --repo mirandole/mirandole-001 --json number,title,state,labels,url`
- `uv run --extra dev pytest`
- `uv run --extra dev ruff check .`
- `uv run --extra dev ruff format .`
- `uv run --extra dev ruff format --check .`

## Remaining Blockers

None.
