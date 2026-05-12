## Parent

Parent PRD: #1

## What to build

Add the Careerjet / Optioncarriere Connecteur de source end to end. The connector should use the source access documented in the source checklist, query the source using Recherche d'offres criteria, normalize returned offers into Resultats d'offre, and integrate with existing partial failure behavior.

## API description

### Interroger l'API

#### Authentification

L'authentification de base est utilisee pour acceder a cette API. Cela signifie que vous devrez ajouter un header Authorization a chaque requete pour obtenir l'acces. Le nom d'utilisateur pour l'authentification de base est votre cle API, et le mot de passe pour l'authentification de base est une chaine vide.

Le format du header Authorization est:

```http
Authorization: Basic {credentials}
```

Ou `{credentials}` est la chaine encodee en Base64 de la cle API suivie de deux-points.

#### Endpoint et parametres

Le endpoint de l'API est `https://search.api.careerjet.net/v4/query` et expose les parametres HTTP GET ci-dessous.

| Nom du parametre | Valeurs | Commentaires |
| --- | --- | --- |
| `locale_code` | `[language_code]_[COUNTRY_CODE]` | La valeur doit correspondre a la liste des locales prises en charge. La valeur par defaut est `en_GB` si elle n'est pas specifiee. |
| `keywords` | `string` | Une liste d'un ou plusieurs mots-cles de recherche encodes au format URL. |
| `location` | `string` | La localite de recherche; lorsqu'elle n'est pas specifiee, indique une recherche a l'echelle du pays. |
| `contract_type` | `p`, `c`, `t`, `i`, `v` | Type de contrat: `p` CDI, `c` mission en contrat, `t` CDD, `i` stage, `v` poste de benevolat. |
| `work_hours` | `f`, `p` | Temps de travail: `f` poste a temps plein, `p` poste a temps partiel. |
| `fragment_size` | `integer` | Taille de l'extrait du resultat de recherche en caracteres, par defaut a `120`. |
| `sort` | `relevance`, `date`, `salary` | Ordre de tri: pertinence decroissante, date decroissante, ou salaire decroissant. Par defaut: `relevance`. |
| `offset` | `integer` | De `1` a `999`, par defaut a `0`. |
| `page` | `integer` | De `1` a `10`. |
| `page_size` | `integer` | De `1` a `100`, avec une valeur par defaut de `20`. |
| `radius` | `integer` | Defaut a 5 km/miles selon la localisation. |
| `user_ip` | `string` | Obligatoire: adresse IP de l'utilisateur dont l'action a declenche l'appel a l'API. |
| `user_agent` | `string` | Obligatoire: User Agent de l'utilisateur dont l'action a declenche l'appel a l'API. |

### Types de reponse

#### Succes

Une requete reussie donne lieu a une reponse JSON HTTP 200, dont la structure generale est la suivante:

```json
{
  "type": "JOBS",
  "hits": 62,
  "message": "62 matching jobs found",
  "pages": 4,
  "response_time": 0.322,
  "jobs": []
}
```

#### Reponses d'erreur

Les requetes incorrectes entrainent divers codes d'etat d'erreur HTTP et un corps de reponse minimal indiquant le type d'erreur et les details, si present.

| Code HTTP | Message | Commentaires |
| --- | --- | --- |
| `400` | `Unsupported locale code` | Le code de locale fourni n'est pas pris en charge. |
| `403` | `Missing param user_ip or user_agent` | La requete n'incluait pas les parametres `user_ip` ou `user_agent`. |

### Mode localisation

Pas strictement une erreur, mais une situation qui empechera toute recherche d'avoir lieu. Le mode localite est declenche comme decrit ci-dessous.

| Message | Commentaires |
| --- | --- |
| `no matching location found` | Aucune localite ne correspond au parametre `location` fourni. |
| `multiple locations found` | Plusieurs localites correspondent au parametre `location` fourni. Vous pouvez alors choisir l'une d'elles dans la liste fournie `locations`. |

Exemple sans localite correspondante:

```json
{
  "type": "LOCATIONS",
  "locations": [],
  "message": "no matching location found",
  "response_time": 0.11
}
```

Exemple avec plusieurs localites:

```json
{
  "type": "LOCATIONS",
  "locations": ["choix 1", "choix 2", "choix 3"],
  "message": "multiple locations found",
  "response_time": 0.11
}
```

### Structure emploi

Chaque emploi est structure comme suit:

```json
{
  "title": "Consultant Java/J2EE/Websphere",
  "company": "Danone",
  "date": "Wed,15 Nov 2025 19:13:43 GMT",
  "description": "Job description excerpt",
  "locations": "Paris",
  "salary": "30k-40k EUR",
  "salary_currency_code": "EUR",
  "salary_max": 0,
  "salary_min": 0,
  "salary_type": "Y",
  "site": "domain.com",
  "url": "https://jobviewtrack.com/v2/lien-unique"
}
```

`salary_type` peut etre:

- `Y`: par an
- `M`: par mois
- `W`: par semaine
- `D`: par jour
- `H`: par heure

## Acceptance criteria

- [ ] Careerjet / Optioncarriere access configuration is read from environment configuration and never committed.
- [ ] The connector supports intitule, localisation, and Rayon source according to the documented source capabilities.
- [ ] Returned offers are normalized into the common Resultat d'offre contract.
- [ ] Careerjet / Optioncarriere source identifiers or canonical URLs are used for Identite de resultat.
- [ ] Source errors, auth failures, and rate-limit responses are reported as Echec de source without failing the whole Session de recherche.
- [ ] The connector can be enabled or disabled by configuration.
- [ ] Tests cover successful normalization, missing optional fields, source failure, and disabled-source behavior.

## Blocked by

- #3
- #4
