## Parent

Parent PRD: #1

## What to build

Evaluate the Sources prioritaires MVP before implementation work depends on them. For each source, document whether it qualifies as a Source maintenable, how credentials are obtained, what fields are available, what rate limits apply, what rayons are supported, and whether the source can support the MVP Recherche d'offres contract.

This is a HITL slice because source access may require account creation, API registration, approval, credentials, or human confirmation of terms.

## Acceptance criteria

- [x] France Travail access path, credentials, limits, supported search inputs, returned fields, and rayon behavior are documented.
- [x] Adzuna access path, credentials, limits, supported search inputs, returned fields, and rayon behavior are documented.
- [x] Jooble access path, credentials, limits, supported search inputs, returned fields, and rayon behavior are documented.
- [x] Careerjet / Optioncarriere access path, credentials, limits, supported search inputs, returned fields, and rayon behavior are documented.
- [x] Jobijoba access path, credentials, limits, supported search inputs, returned fields, and rayon behavior are documented.
- [x] Each source is explicitly classified as usable now, blocked on credentials, blocked on terms, or not a Source maintenable.
- [x] Required environment variable names for usable sources are listed.
- [x] Any human action needed to unlock a source is listed clearly.

## Implementation

See `docs/source-access-and-credentials-checklist.md`.

## Blocked by

None - can start immediately.
