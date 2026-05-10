## Parent

Parent PRD: #1

## What to build

Add post-aggregation enrichment and Filtres de resultats to the main results path. The app should enrich normalized Resultats d'offre after connector output, then allow the Utilisateur principal to filter the displayed list by Type de contrat recherche, Niveau d'experience demande, and Niveau de diplome demande.

This slice should keep all enrichment outside Connecteurs de source.

## Acceptance criteria

- [ ] Resultats d'offre are enriched with Tags de competence from a configurable IT skills dictionary.
- [ ] Resultats d'offre receive a Niveau d'experience demande value: Debutant, Confirme, Avance, Senior, or Non precise.
- [ ] Resultats d'offre receive a Niveau de diplome demande value: Non precise, Aucun diplome requis, Bac, Bac+2, Bac+3, Bac+5, or Doctorat.
- [ ] CDI, CDD, Freelance, and Interim are included by default; Stage and Alternance are excluded by default.
- [ ] Filters are applied after aggregation, not sent to the source connector.
- [ ] Teletravail information is displayed when present but is not available as a filter.
- [ ] Remuneration indiquee is displayed when present but is not available as a filter.
- [ ] Tests cover contract inclusion/exclusion, experience extraction, diploma extraction, tags extraction, and post-aggregation filtering.

## Blocked by

- #4
