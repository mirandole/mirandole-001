## Parent

Parent PRD: #1

## What to build

Add user states for Offre consultee and Offre favorite. The main results list should let the Utilisateur principal open a Resultat d'offre on its source, mark it as consulted, toggle a favorite star, and later find favorites in a dedicated Vue favoris.

The MVP does not create an internal offer detail page.

## Acceptance criteria

- [ ] Clicking a Resultat d'offre opens the source URL rather than an internal detail page.
- [ ] Opening the source URL marks the Resultat d'offre as Offre consultee.
- [ ] The main results list visibly distinguishes Offres consultees.
- [ ] The main results list allows toggling Offre favorite with an etoile control.
- [ ] Offres favorites persist in Stockage applicatif across sessions.
- [ ] Vue favoris lists all Offres favorites for the Utilisateur principal.
- [ ] Vue favoris can sort by favorite date newest first and Date de publication newest first.
- [ ] The default Tri des favoris is favorite date newest first.
- [ ] Tests cover consulted marking, favorite toggling, favorite persistence, Vue favoris listing, and both favorite sort modes.

## Blocked by

- #4
