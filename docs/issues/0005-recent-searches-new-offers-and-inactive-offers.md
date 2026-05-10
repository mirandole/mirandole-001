## Parent

Parent PRD: #1

## What to build

Add continuity features across Sessions de recherche: Recherches recentes, Offre nouvelle, and Offre inactive. The Utilisateur principal should be able to relaunch recent searches, see which Resultats d'offre are new compared with the previous Session de recherche for the same Recherche d'offres, and keep favorite/consulted states when an offer stops appearing.

## Acceptance criteria

- [ ] The app displays at most 10 Recherches recentes sorted by last use.
- [ ] Relaunching an identical Recherche d'offres moves it to the top instead of creating a duplicate Recherche recente.
- [ ] Offre nouvelle is calculated by comparing the current Session de recherche with the previous Session de recherche for the same Recherche d'offres.
- [ ] Identite de resultat uses Source d'offres plus URL canonique or source identifier.
- [ ] A known Resultat d'offre absent from recent successful sessions can become Offre inactive.
- [ ] Offres favorites and Offres consultees remain persisted if the result becomes Offre inactive.
- [ ] Echec de source does not make offers from that source inactive.
- [ ] Tests cover recent search limit/deduplication, new-offer calculation, source-level identity, inactive transitions, and preservation of favorite/consulted states.

## Blocked by

- #4
- #6
