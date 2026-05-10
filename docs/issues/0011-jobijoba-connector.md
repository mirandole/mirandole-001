## Parent

Parent PRD: #1

## What to build

Add the Jobijoba Connecteur de source if the source checklist confirms it is a Source maintenable. The connector should use the documented API, flux, or partner access path, normalize returned offers into Resultats d'offre, and integrate with the aggregation engine's Echec de source behavior.

## Acceptance criteria

- [ ] Jobijoba is confirmed as a Source maintenable before implementation proceeds.
- [ ] Jobijoba credentials or feed configuration are read from environment configuration and never committed.
- [ ] The connector supports intitule, localisation, and Rayon source according to the documented source capabilities.
- [ ] Returned offers are normalized into the common Resultat d'offre contract.
- [ ] Jobijoba source identifiers or canonical URLs are used for Identite de resultat.
- [ ] Source errors, auth failures, and rate-limit responses are reported as Echec de source without failing the whole Session de recherche.
- [ ] The connector can be enabled or disabled by configuration.
- [ ] Tests cover successful normalization, missing optional fields, source failure, and disabled-source behavior.

## Blocked by

- #3
- #4
