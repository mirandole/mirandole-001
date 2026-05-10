## Parent

Parent PRD: #1

## What to build

Add the Adzuna Connecteur de source end to end. The connector should use the source access documented in the source checklist, query Adzuna with Recherche d'offres criteria, normalize offers into Resultats d'offre, and integrate with the existing aggregation and Echec de source handling.

## Acceptance criteria

- [ ] Adzuna credentials are read from environment configuration and never committed.
- [ ] The connector supports intitule, localisation, and Rayon source according to the documented source capabilities.
- [ ] Returned offers are normalized into the common Resultat d'offre contract.
- [ ] Adzuna source identifiers or canonical URLs are used for Identite de resultat.
- [ ] Source errors, auth failures, and rate-limit responses are reported as Echec de source without failing the whole Session de recherche.
- [ ] The connector can be enabled or disabled by configuration.
- [ ] Tests cover successful normalization, missing optional fields, source failure, and disabled-source behavior.

## Implementation notes

- Use `scripts/check-adzuna-api.sh` as a working reference for the Adzuna search
  call shape, required environment variables, JSON response fields, and
  `distance` parameter handling.
- The script has been validated with `MIRANDOLE_ADZUNA_APP_ID` and
  `MIRANDOLE_ADZUNA_APP_KEY`; `distance=10` and `distance=50` change the result
  count for `what=Python&where=Paris`, so the connector can map
  `rayon_demande_km` to Adzuna's `distance` parameter.

## Blocked by

- #3
- #4
