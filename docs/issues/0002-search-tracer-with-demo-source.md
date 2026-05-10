## Parent

Parent PRD: #1

## What to build

Implement the first complete Recherche d'offres path using a demo Connecteur de source. The Utilisateur principal should be able to submit an intitule de poste, localisation, and Rayon demande, then receive persisted Resultats d'offre from a simulated Source d'offres.

This slice should prove the vertical flow before real source integrations are added: form, Rayon source mapping, Session de recherche, normalized results, Echec de source handling, Stockage applicatif, and the main results UI sorted by Tri par fraicheur.

## Acceptance criteria

- [ ] The protected home page contains a Recherche d'offres form with intitule, localisation, and fixed Rayon demande choices: 10 km, 20 km, 30 km, 50 km, 100 km.
- [ ] Submitting the form creates a Session de recherche in Stockage applicatif.
- [ ] A demo Connecteur de source returns normalized Resultats d'offre with source, Identite de resultat, title, Entreprise, ville, Date de publication, Type de contrat recherche, Remuneration indiquee, URL source, and optional teletravail text.
- [ ] Rayon demande is mapped to the exact or next-higher Rayon source supported by the demo source.
- [ ] Results are displayed in the main list sorted by Date de publication newest first, with unknown dates after dated results.
- [ ] An Echec de source from the demo source is visible to the user without failing the whole Session de recherche.
- [ ] Existing results from a failed source are not marked inactive.
- [ ] Unit or integration tests cover session creation, result persistence, rayon mapping, date sorting, and partial source failure behavior.

## Blocked by

- #2
