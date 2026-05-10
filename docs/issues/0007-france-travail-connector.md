## Parent

Parent PRD: #1

## What to build

Add the France Travail Connecteur de source end to end. The connector should use the source access documented in the source checklist, map Recherche d'offres criteria into France Travail API requests, normalize returned offers into Resultats d'offre, and participate in partial failure reporting.

## Acceptance criteria

- [ ] France Travail credentials are read from environment configuration and never committed.
- [ ] The connector supports intitule, localisation, and Rayon source according to the documented source capabilities.
- [ ] Returned offers are normalized into the common Resultat d'offre contract.
- [ ] France Travail source identifiers or canonical URLs are used for Identite de resultat.
- [ ] Source errors, auth failures, and rate-limit responses are reported as Echec de source without failing the whole Session de recherche.
- [ ] The connector can be enabled or disabled by configuration.
- [ ] Tests cover successful normalization, missing optional fields, source failure, and disabled-source behavior.

## Blocked by

- #3
- #4
