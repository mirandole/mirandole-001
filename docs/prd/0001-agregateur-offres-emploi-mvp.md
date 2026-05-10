# PRD: Agregateur d'offres d'emploi MVP

## Problem Statement

L'utilisateur principal cherche des offres d'emploi en informatique sur plusieurs sources francaises ou utilisables en France. Aujourd'hui, il doit refaire la meme recherche sur plusieurs sites, comparer des resultats heterogenes, reperer manuellement les nouvelles offres, se souvenir des offres deja consultees et conserver ses favoris ailleurs.

Le MVP doit fournir une application web deployee sur un VPS, mono-utilisateur et protegee, qui lance une Recherche d'offres a la demande, agrege les Resultats d'offre depuis des Sources maintenables, puis permet de filtrer, consulter et retrouver les offres utiles.

## Solution

Construire une Application deployee FastAPI + HTMX avec Stockage applicatif SQLite. L'utilisateur saisit un intitule de poste, une localisation et un Rayon demande parmi 10 km, 20 km, 30 km, 50 km et 100 km. L'application interroge les Sources prioritaires MVP via des Connecteurs de source normalises, cree une Session de recherche, enrichit les Resultats d'offre, puis affiche une liste triee par Tri par fraicheur.

Les Resultats d'offre affichent les donnees utiles quand elles sont disponibles: intitule, Entreprise, ville, Date de publication, Source d'offres, Type de contrat recherche, Remuneration indiquee, Tags de competence, Niveau d'experience demande, Niveau de diplome demande, badges Offre nouvelle, Offre consultee, Offre favorite et Offre inactive si applicable.

Selectionner un Resultat d'offre ouvre directement son lien source et marque le Resultat d'offre comme Offre consultee. Une etoile permet de le marquer comme Offre favorite. Une Vue favoris dediee permet de retrouver les Offres favorites avec un Tri des favoris choisi par l'utilisateur.

## User Stories

1. As an Utilisateur principal, I want to access the Application deployee through my VPS, so that I can use the tool remotely.
2. As an Utilisateur principal, I want the app exposed initially only through the WireGuard interface and protected by a password, so that my searches and API usage are not public.
3. As an Utilisateur principal, I want to enter an intitule de poste, so that the Recherche d'offres targets the role I am looking for.
4. As an Utilisateur principal, I want to enter a localisation, so that the Recherche d'offres focuses on a practical geographic area.
5. As an Utilisateur principal, I want to choose a Rayon demande from 10 km, 20 km, 30 km, 50 km, and 100 km, so that I can control the geographic scope.
6. As an Utilisateur principal, I want the app to use the closest higher Rayon source when a source does not support my exact Rayon demande, so that the source can still be queried.
7. As an Utilisateur principal, I want the MVP to focus on offers in France with localisation and rayon, so that remote international offers do not dilute the results.
8. As an Utilisateur principal, I want each Recherche d'offres to run only when I launch it, so that the app stays simple and predictable.
9. As an Utilisateur principal, I want the app to query multiple Sources d'offres, so that I can compare offers in one place.
10. As an Utilisateur principal, I want only Sources maintenables to be integrated, so that the app does not depend on fragile or unauthorized access.
11. As an Utilisateur principal, I want France Travail, Adzuna, Jooble, Careerjet / Optioncarriere and Jobijoba evaluated first, so that the MVP starts with sources likely to be usable.
12. As an Utilisateur principal, I want Hellowork, Meteojob, Apec, LesJeudis, Talent.com, Welcome to the Jungle, Glassdoor and Monster kept as Sources candidates phase 2, so that they can be assessed later without blocking the MVP.
13. As an Utilisateur principal, I want an Echec de source to be visible without failing the whole Session de recherche, so that I still get available results.
14. As an Utilisateur principal, I want a source failure not to mark known offers inactive, so that temporary outages do not corrupt my offer states.
15. As an Utilisateur principal, I want Resultats d'offre normalized across sources, so that the list can be read and filtered consistently.
16. As an Utilisateur principal, I want Resultats d'offre sorted by Date de publication newest first by default, so that I see the freshest offers first.
17. As an Utilisateur principal, I want unknown Date de publication values shown as not specified and sorted after dated results, so that no fake dates are invented.
18. As an Utilisateur principal, I want CDI, CDD, Freelance and Interim included by default, so that the list matches my target contracts.
19. As an Utilisateur principal, I want Stage and Alternance excluded by default, so that the list is not polluted by irrelevant offers.
20. As an Utilisateur principal, I want to filter Resultats d'offre after aggregation by Niveau d'experience demande, so that I can focus on offers matching my experience.
21. As an Utilisateur principal, I want the experience values Debutant, Confirme, Avance, Senior and Non precise, so that ambiguous offers are still handled.
22. As an Utilisateur principal, I want to filter Resultats d'offre after aggregation by Niveau de diplome demande, so that I can focus on offers matching my education profile.
23. As an Utilisateur principal, I want diploma values Non precise, Aucun diplome requis, Bac, Bac+2, Bac+3, Bac+5 and Doctorat, so that the filter remains simple.
24. As an Utilisateur principal, I want no teletravail filter in the MVP, so that the first version stays focused.
25. As an Utilisateur principal, I want teletravail information displayed only if a source provides it, so that useful data is not discarded.
26. As an Utilisateur principal, I want Tags de competence detected from a configurable IT skills dictionary, so that I can scan offers quickly.
27. As an Utilisateur principal, I want no generated summary, so that the app does not invent or reinterpret the source content.
28. As an Utilisateur principal, I want the list to show Entreprise when available, so that I can understand who is recruiting.
29. As an Utilisateur principal, I want Remuneration indiquee shown when available, so that salary information is visible without becoming a MVP filter.
30. As an Utilisateur principal, I want selecting an offer to open the source directly, so that I can see the official offer page.
31. As an Utilisateur principal, I want selecting an offer to mark it as Offre consultee, so that I can distinguish offers I already opened.
32. As an Utilisateur principal, I want to mark a Resultat d'offre as Offre favorite with an etoile, so that I can come back to it later.
33. As an Utilisateur principal, I want Offres favorites and Offres consultees to persist even if a source stops returning the offer, so that I do not lose my decisions.
34. As an Utilisateur principal, I want a known result absent from recent sessions to become an Offre inactive, so that I can distinguish unavailable offers.
35. As an Utilisateur principal, I want a Vue favoris, so that I can find starred offers independently from the current search.
36. As an Utilisateur principal, I want the Vue favoris to allow sorting by most recent favorite date, so that my latest selections stay easy to find.
37. As an Utilisateur principal, I want the Vue favoris to allow sorting by most recent Date de publication, so that I can prioritize fresh favorites.
38. As an Utilisateur principal, I want the default Tri des favoris to be most recent favorite date first, so that newly starred offers stay at the top.
39. As an Utilisateur principal, I want the app to show up to 10 Recherches recentes, so that I can relaunch common searches quickly.
40. As an Utilisateur principal, I want relaunching an identical Recherche d'offres to move it to the top of Recherches recentes, so that duplicates are avoided.
41. As an Utilisateur principal, I want Offre nouvelle calculated against the previous Session de recherche for the same Recherche d'offres, so that novelty is meaningful.
42. As an Utilisateur principal, I want Resultats d'offre identified by Source d'offres plus URL canonique or source identifier, so that favorite and consulted states are stable.
43. As an Utilisateur principal, I want likely cross-source duplicates handled later, so that the MVP avoids unsafe merging.
44. As an Utilisateur principal, I want the app to persist Sessions de recherche and Resultats d'offre server-side, so that browser cache loss does not erase history.
45. As an operator of the VPS, I want API keys and passwords configured outside source code, so that deployment secrets stay separate from the repo.

## Implementation Decisions

- Build the MVP as an Application deployee on a VPS, initially served on the WireGuard interface.
- Keep the product mono-utilisateur, but protect it with a password and session cookie.
- Use FastAPI with server-rendered HTML and HTMX for incremental interactions.
- Use SQLite for Stockage applicatif in the MVP.
- Implement each Source d'offres through a Connecteur de source with a shared interface.
- Each Connecteur de source receives search criteria and a Rayon source, then returns normalized candidate Resultats d'offre.
- Keep source-specific API parsing inside each Connecteur de source.
- Keep shared enrichment outside connectors: Tags de competence, Niveau d'experience demande and Niveau de diplome demande are computed by common services after normalization.
- Add a source capability model for supported radii and map Rayon demande to the smallest supported higher Rayon source.
- Store Search criteria separately from Sessions de recherche. A Recherche d'offres is the criteria; a Session de recherche is one execution.
- Store source execution status per Session de recherche, including Echec de source.
- Store Identite de resultat using Source d'offres plus URL canonique or source identifier.
- Store Date de publication as normalized date when possible, with an unknown state when not available.
- Store Entreprise, Remuneration indiquee, Type de contrat recherche, source label, URL source, location/city, and available excerpt fields.
- Do not store Description source by default unless it is already returned by the search response without an extra request.
- Include CDI, CDD, Freelance and Interim by default; exclude Stage and Alternance by default.
- Apply Niveau d'experience demande and Niveau de diplome demande as Filtres de resultats after aggregation.
- Do not include a teletravail filter in the MVP.
- Implement the main results view as the primary offer surface. There is no internal offer detail page in the MVP.
- Opening a Resultat d'offre redirects to the source URL and marks it as Offre consultee.
- Implement favorite toggling from both search results and Vue favoris.
- Preserve Offre favorite and Offre consultee states indefinitely, including when a result becomes Offre inactive.
- Implement Vue favoris with two Tri des favoris choices: favorite date newest first and Date de publication newest first.
- Default Tri des favoris is favorite date newest first.
- Implement Recherches recentes as the last 10 unique Recherches d'offres, sorted by last use.
- Compute Offre nouvelle by comparing a Session de recherche with the previous Session de recherche for the same Recherche d'offres.
- Do not mark old offers inactive for a source when that source failed in the latest session.
- Sources prioritaires MVP are France Travail, Adzuna, Jooble, Careerjet / Optioncarriere and Jobijoba.
- Sources candidates phase 2 are Hellowork, Meteojob, Apec, LesJeudis, Talent.com, Welcome to the Jungle, Glassdoor and Monster.

Major modules to build:

- Authentication and access protection: password login, session cookie, logout, protected routes.
- Source connector framework: shared connector contract, source capabilities, source status reporting.
- Source connectors: France Travail, Adzuna, Jooble, Careerjet / Optioncarriere, Jobijoba.
- Aggregation engine: run connectors, tolerate Echec de source, create Session de recherche, persist normalized results.
- Normalization and enrichment: dates, contracts, experience level, diploma level, Tags de competence.
- Persistence layer: SQLite schema and repository functions for searches, sessions, results, favorites, consulted states, source statuses and recent searches.
- Results UI: search form, source status warnings, filters, freshness sorting, badges, favorite toggle, source link opening.
- Vue favoris UI: favorite list, inactive badge, favorite sorting, source link opening.
- Recherches recentes UI: display and relaunch recent searches.
- Deployment configuration: environment variables, secret handling, database path, VPS service entrypoint.

## Testing Decisions

Good tests should verify external behavior and stable contracts, not private implementation details. The highest-value tests are around normalization, state transitions and connector boundaries, because those modules encode most of the product rules.

- Test connector contract compliance with fake connector payloads.
- Test Rayon demande to Rayon source mapping, including exact match and next-higher fallback.
- Test aggregation with one successful source and one Echec de source.
- Test that Echec de source does not mark existing results inactive.
- Test Identite de resultat stability across repeated Sessions de recherche.
- Test Offre nouvelle calculation against the previous Session de recherche for the same Recherche d'offres.
- Test Date de publication normalization for absolute dates, relative dates when supported, and unknown dates.
- Test Tri par fraicheur with unknown dates after dated results.
- Test Type de contrat recherche inclusion and exclusion defaults.
- Test Niveau d'experience demande extraction for the five values, including Non precise.
- Test Niveau de diplome demande extraction for the configured values, including Non precise.
- Test Tags de competence extraction from the configurable dictionary.
- Test favorite toggling and persistence after a result becomes inactive.
- Test consulted marking when a source link route is opened.
- Test Vue favoris sorting by favorite date and by Date de publication.
- Test Recherches recentes limit of 10 and deduplication by identical criteria.
- Test authentication guards on all application pages.

There is no prior application test suite in the repo yet. The MVP should introduce focused unit tests for deep modules first, then add integration tests around the FastAPI routes that handle search, favorites, consulted redirects and authentication.

## Out of Scope

- Multi-user accounts.
- Public internet exposure without WireGuard.
- Alerts, scheduled searches or notifications.
- Application tracking or candidature status.
- Internal offer detail page.
- Generated summaries with AI.
- Teletravail filtering.
- Salary filtering.
- Strict distance verification by geocoding.
- Cross-source deduplication beyond preserving source-level Identite de resultat.
- Integrating non-maintainable sources through scraping or access circumvention.
- LinkedIn and Indeed integration unless a maintainable authorized access is found.
- Remote Europe or international-only sources in the MVP.
- Browser-only persistence.

## Further Notes

Relevant domain and architecture docs:

- `CONTEXT.md` defines the domain vocabulary and rules.
- ADR-0001 records the decision to integrate only Sources maintenables.
- ADR-0002 records VPS deployment.
- ADR-0003 records FastAPI, HTMX and SQLite for the MVP.
- ADR-0004 records connector isolation and normalized outputs.

Before implementation, each Source prioritaire MVP should be evaluated for credentials, terms, rate limits, field availability, supported radii and whether it can be used within the Source maintenable rule.
