# Source Access And Credentials Checklist

Last checked: 2026-05-10

This checklist evaluates the Sources prioritaires MVP against the Source maintenable rule. It records what can be integrated through an authorized and technically stable access path, what environment variables a Connecteur de source should read, and what human action is still required before production use.

## Summary

| Source d'offres | Classification | Source maintenable? | MVP connector recommendation |
| --- | --- | --- | --- |
| France Travail | Blocked on credentials | Yes, official API | Implement first once habilitation credentials are available. |
| Adzuna | Blocked on credentials and terms confirmation | Yes, official API with attribution and rate limits | Implement after API key registration and terms confirmation. |
| Jooble | Blocked on credentials | Yes, official REST API | Implement if 80 km Rayon source is acceptable for 100 km Rayon demande. |
| Careerjet / Optioncarriere | Blocked on credentials | Yes, official partner API | Implement after publisher API key is available. |
| Jobijoba | Blocked on partner approval and terms | Possible, but not confirmed until partner access docs are received | Do not implement until Jobijoba confirms API/feed contract and allowed usage. |

## Required Environment Variables

These names should be used by future Connecteurs de source. Credentials must be configured outside source code and must not be committed.

| Source d'offres | Environment variables |
| --- | --- |
| France Travail | `MIRANDOLE_FRANCE_TRAVAIL_CLIENT_ID`, `MIRANDOLE_FRANCE_TRAVAIL_CLIENT_SECRET`, `MIRANDOLE_FRANCE_TRAVAIL_ENABLED` |
| Adzuna | `MIRANDOLE_ADZUNA_APP_ID`, `MIRANDOLE_ADZUNA_APP_KEY`, `MIRANDOLE_ADZUNA_ENABLED` |
| Jooble | `MIRANDOLE_JOOBLE_API_KEY`, `MIRANDOLE_JOOBLE_ENABLED` |
| Careerjet / Optioncarriere | `MIRANDOLE_CAREERJET_API_KEY`, `MIRANDOLE_CAREERJET_ENABLED` |
| Jobijoba | `MIRANDOLE_JOBIJOBA_API_KEY` or feed-specific variables once partner access is documented, `MIRANDOLE_JOBIJOBA_ENABLED` |

## France Travail

Classification: blocked on credentials.

Access path:
- Official API Offres d'emploi, produced by France Travail and listed on data.gouv.fr.
- Access is listed as open, but requires a France Travail habilitation request before credentials are available.
- Authentication should use the France Travail developer credentials, expected as OAuth/client-credentials style `client_id` and `client_secret`.

Supported Recherche d'offres inputs:
- Intitule: use the API keyword criterion, documented as search by selection criteria and by metiers/keywords.
- Localisation: supported by commune, departement, and other location referentials.
- Rayon source: France Travail public help documents a radius from 0 to 100 km around a commune. The MVP Rayon demande values 10, 20, 30, 50, and 100 km can be sent directly as Rayon source.

Returned fields useful for Resultat d'offre:
- Search result and detail resources are documented for offer title, location, Entreprise, contract, and offer detail.
- France Travail user-facing search help also states result cards show title, workplace, contract nature and working time, Entreprise when specified, the first 200 characters of the job description, and Date de publication.
- Use the source offer id or canonical France Travail URL for Identite de resultat.

Limits and source errors:
- data.gouv.fr lists 10 calls per second and 99.8% availability.
- Treat authentication errors, rate-limit responses, unavailable responses, and malformed payloads as Echec de source.

Human action needed:
- Create or use a France Travail developer account.
- Request habilitation for API Offres d'emploi.
- Store credentials in deployment environment variables.
- Confirm the exact production OAuth scope and endpoint names from the France Travail portal after habilitation, because the public data.gouv.fr page links to portal documentation that requires interactive access.

References:
- https://dev.data.gouv.fr/dataservices/api-offres-demploi
- https://www.francetravail.fr/faq/candidat/ma-recherche-demploi/les-offres-demploi/rechercher-des-offres/lieu-de-travail.html
- https://www.francetravail.fr/faq/candidat/ma-recherche-demploi/les-offres-demploi/rechercher-des-offres/trouver-le-travail-qui-me-corres.html

## Adzuna

Classification: blocked on credentials and terms confirmation.

Access path:
- Official Adzuna REST API.
- Register to receive `app_id` and `app_key`.
- Endpoint shape is `https://api.adzuna.com/v1/api/jobs/{country}/search/{page}`. Use country code `fr` for France after validating it with the registered account.

Supported Recherche d'offres inputs:
- Intitule: `what`.
- Localisation: `where`.
- Rayon source: the static public documentation points to the interactive endpoint documentation for the full parameter list. Do not assume radius support until confirmed there. If a distance/radius parameter is available in the registered documentation, map MVP rayons directly when accepted; otherwise classify the connector as location-only and document that strict Rayon demande support is unavailable.

Returned fields useful for Resultat d'offre:
- `id`, `title`, `company.display_name`, `location.display_name` / `location.area`, `created`, `description` snippet, `redirect_url`, `contract_type`, `contract_time`, `salary_min`, `salary_max`, and category fields.
- Use `id` as primary Identite de resultat, with `redirect_url` as canonical URL fallback.

Limits and source errors:
- Default Adzuna API limits are 25 hits/minute, 250 hits/day, 1000 hits/week, and 2500 hits/month.
- Terms require attribution for published ad listings and may require written consent/licence for ongoing commercial, government, or academic use beyond trial/validation.
- Treat 4xx auth/terms/rate-limit responses and 5xx/unavailable responses as Echec de source.

Human action needed:
- Register for Adzuna API credentials.
- Confirm permitted use for a private MVP aggregator and any required attribution in the UI.
- Confirm France country code and radius/distance parameter in the interactive endpoint documentation before implementing Rayon source behavior.

References:
- https://developer.adzuna.com/overview
- https://developer.adzuna.com/docs/search
- https://developer.adzuna.com/docs/terms_of_service

## Jooble

Classification: blocked on credentials.

Access path:
- Official Jooble REST API.
- Register at the Jooble API page to receive an API key.
- Endpoint shape is `POST https://jooble.org/api/{api_key}`.

Supported Recherche d'offres inputs:
- Intitule: `keywords`.
- Localisation: `location`.
- Rayon source: `radius`, accepted values only `0`, `4`, `8`, `16`, `26`, `40`, `80`.
- MVP mapping should use the smallest supported higher value: 10 -> 16, 20 -> 26, 30 -> 40, 50 -> 80. The 100 km Rayon demande has no higher supported value; use 80 km only if the product accepts under-covering that request, otherwise disable Jooble for 100 km and report an Echec de source/capability message.

Returned fields useful for Resultat d'offre:
- `id`, `title`, `company`, `location`, `snippet`, `salary`, `source`, `type`, `link`, `updated`.
- Use `id` as primary Identite de resultat, with `link` as canonical URL fallback.

Limits and source errors:
- Public docs list 403 for invalid API key and 404 for unavailable endpoint/resource. No public rate limit was found in the REST API article; verify after registration.
- Treat auth failures, rate limits if returned, and endpoint errors as Echec de source.

Human action needed:
- Register for a Jooble API key.
- Confirm rate limits and whether France-specific endpoint behavior differs.
- Decide product behavior for 100 km Rayon demande, since Jooble tops out at 80 km.

References:
- https://help.jooble.org/en/support/solutions/articles/60001448238-rest-api-documentation

## Careerjet / Optioncarriere

Classification: blocked on credentials.

Access path:
- Official Careerjet / Optioncarriere partner API.
- Each publisher site requires a unique API key from a publisher account.
- Endpoint is `https://search.api.careerjet.net/v4/query`.
- Authentication is HTTP Basic auth with the API key as username and an empty password.

Supported Recherche d'offres inputs:
- Intitule: `keywords`.
- Localisation: `location`.
- Rayon source: `radius` integer; docs say it defaults to 5 km/miles depending on location. For France, validate km behavior with the publisher account, then map MVP rayons directly if accepted.
- Use `locale_code=fr_FR` for France if supported by the account.

Returned fields useful for Resultat d'offre:
- `title`, `company`, `date`, `description`, `locations`, `salary`, `salary_currency_code`, `salary_min`, `salary_max`, `salary_type`, `site`, `url`.
- Use `url` as canonical URL for Identite de resultat unless a stable source id is added by the API response.

Limits and source errors:
- The public API page documents 400 for unsupported locale and 403 for missing `user_ip` or `user_agent`; it does not publish numeric rate limits.
- Requests must include `user_ip` and `user_agent`; code examples also show a `Referer` header in some localized docs.
- Treat auth failures, missing required request context, unsupported locale/location mode, rate-limit responses if returned, and 5xx responses as Echec de source.

Human action needed:
- Create publisher account and obtain the API key for the deployed app/site.
- Confirm `fr_FR`, radius units/accepted range, rate limits, and whether `Referer` is required for the production use case.
- Ensure the app can provide the real Utilisateur principal request IP/user agent or an approved server-side equivalent.

References:
- https://www.optioncarriere.com/partners/api
- https://www.careerjet.com/partners/api

## Jobijoba

Classification: blocked on partner approval and terms.

Access path:
- Jobijoba publishes an affiliation page for integrating offers through Flux, API, or Widget, but does not publish public API parameters on that page.
- The affiliation page asks prospective partners to submit a contact form and be recontacted.

Supported Recherche d'offres inputs:
- Not confirmed from public docs. The public website supports searches by contract categories such as CDI/CDD, interim, alternance, independent, stage, and by location, but this is not enough to define a Source maintenable connector.
- Rayon source behavior is not documented publicly.

Returned fields useful for Resultat d'offre:
- Not documented publicly for partner API/feed. Must be confirmed in the partner contract/docs before implementation.

Limits and source errors:
- Not documented publicly. Must be confirmed by Jobijoba/HelloWork during partner onboarding.

Human action needed:
- Submit the Jobijoba affiliation contact form.
- Request API/feed documentation, rate limits, allowed storage/display terms, attribution requirements, supported search parameters, rayon behavior, and response fields.
- Do not implement a Jobijoba Connecteur de source until those terms confirm maintainable authorized access.

References:
- https://www.jobijoba.com/fr/affiliation-offres-emploi

## Connector Order Recommendation

1. France Travail: best first connector for #8 because it is official, France-focused, and supports the MVP radius range.
2. Careerjet / Optioncarriere: likely straightforward after publisher credentials because parameters and fields are documented.
3. Jooble: straightforward but needs a product decision for 100 km because max documented radius is 80 km.
4. Adzuna: useful source, but confirm radius support and attribution/licence constraints before implementation.
5. Jobijoba: wait for partner docs.

## API Documentation Links

- [Adzuna API](https://developer.adzuna.com/activedocs#/default/search)
- [Optioncarriere API](https://www.optioncarriere.com/partners/api)
- [France Travail API](https://francetravail.io/produits-partages/catalogue/offres-emploi/documentation#/api-reference/operations/recupererListeOffre)