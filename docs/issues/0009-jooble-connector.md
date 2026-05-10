## Parent

Parent PRD: #1

## What to build

Add the Jooble Connecteur de source end to end. The connector should use the source access documented in the source checklist, respect Jooble-supported rayons, normalize offers into Resultats d'offre, and integrate with partial source failure handling.

## Acceptance criteria

- [ ] Jooble credentials are read from environment configuration and never committed.
- [ ] The connector supports intitule, localisation, and Rayon source according to the documented Jooble capabilities.
- [ ] Rayon demande values are mapped to Jooble-supported Rayon source values using exact or next-higher fallback.
- [ ] Returned offers are normalized into the common Resultat d'offre contract.
- [ ] Jooble source identifiers or canonical URLs are used for Identite de resultat.
- [ ] Source errors, auth failures, and rate-limit responses are reported as Echec de source without failing the whole Session de recherche.
- [ ] The connector can be enabled or disabled by configuration.
- [ ] Tests cover rayon mapping, successful normalization, missing optional fields, source failure, and disabled-source behavior.

## Blocked by

- #3
- #4
