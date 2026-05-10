from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass
from json import JSONDecodeError, loads
from pathlib import Path
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from mirandole.config import Settings
from mirandole.enrichment import enrich_result
from mirandole.storage import (
    SearchSession,
    StoredOfferResult,
    create_search_session,
    find_previous_session_for_same_recherche,
    list_result_identities_for_session,
    save_inactive_offer_results_for_missing_identities,
    save_offer_results,
    save_source_failure,
)

RAYONS_DEMANDE_KM = [10, 20, 30, 50, 100]
LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class FranceTravailLocationCriteria:
    parameter_name: str
    value: str


class SourceConnectorUnavailable(RuntimeError):
    pass


class DemoSourceUnavailable(SourceConnectorUnavailable):
    pass


class SourceConnector(Protocol):
    source_name: str

    def search(
        self, *, intitule: str, localisation: str, rayon_demande_km: int
    ) -> list[OfferResult]: ...


@dataclass(frozen=True)
class OfferResult:
    source_name: str
    source_radius_km: int
    title: str
    company: str
    city: str
    published_at: str | None
    contract_type: str
    salary: str | None
    description_source: str | None
    source_url: str
    source_identifier: str | None = None
    remote_text: str | None = None

    @property
    def result_identity(self) -> str:
        return build_result_identity(
            source_name=self.source_name,
            source_url=self.source_url,
            source_identifier=self.source_identifier,
        )


@dataclass(frozen=True)
class SearchTrace:
    session: SearchSession
    result_count: int
    failure_count: int


class DemoSourceConnector:
    source_name = "Source demo"
    supported_radii_km = [20, 50, 100]

    def map_rayon_source(self, rayon_demande_km: int) -> int:
        for supported_radius in self.supported_radii_km:
            if supported_radius >= rayon_demande_km:
                return supported_radius
        return self.supported_radii_km[-1]

    def search(
        self, *, intitule: str, localisation: str, rayon_demande_km: int
    ) -> list[OfferResult]:
        if "echec" in intitule.casefold():
            raise DemoSourceUnavailable(
                "La Source d'offres demo est indisponible pour cette recherche."
            )

        rayon_source_km = self.map_rayon_source(rayon_demande_km)
        title = intitule.strip()
        city = localisation.strip()
        source_slug = _slugify(title)

        return [
            OfferResult(
                source_name=self.source_name,
                source_radius_km=rayon_source_km,
                title=f"{title} Python",
                company="Atelier Hexagone",
                city=city,
                published_at="2026-05-09",
                contract_type="CDI",
                salary="45 000 - 55 000 EUR",
                description_source=(
                    "Developpement Python et FastAPI. Experience 3 ans souhaitee. "
                    "Bac+5 apprecie."
                ),
                source_url=f"https://example.test/offres/{source_slug}-python",
                source_identifier=f"demo-{source_slug}-1",
                remote_text="Teletravail partiel",
            ),
            OfferResult(
                source_name=self.source_name,
                source_radius_km=rayon_source_km,
                title=f"{title} Data",
                company="Cooperative Loire",
                city=city,
                published_at="2026-05-07",
                contract_type="CDD",
                salary=None,
                description_source=(
                    "Analyse SQL et tableaux de bord PostgreSQL. Profil confirme "
                    "avec Bac+3."
                ),
                source_url=f"https://example.test/offres/{source_slug}-data",
                source_identifier=f"demo-{source_slug}-2",
            ),
            OfferResult(
                source_name=self.source_name,
                source_radius_km=rayon_source_km,
                title=f"{title} Support applicatif",
                company="Service Numerique Ouest",
                city=city,
                published_at=None,
                contract_type="Interim",
                salary="380 EUR / jour",
                description_source=(
                    "Support Linux, Docker et Git. Aucun diplome requis, premiere "
                    "experience acceptee."
                ),
                source_url=f"https://example.test/offres/{source_slug}-support",
                source_identifier=f"demo-{source_slug}-3",
            ),
            OfferResult(
                source_name=self.source_name,
                source_radius_km=rayon_source_km,
                title=f"{title} Stage web",
                company="Atelier Hexagone",
                city=city,
                published_at="2026-05-08",
                contract_type="Stage",
                salary=None,
                description_source="Stage JavaScript React pour etudiant Bac+2.",
                source_url=f"https://example.test/offres/{source_slug}-stage-web",
                source_identifier=f"demo-{source_slug}-4",
            ),
            OfferResult(
                source_name=self.source_name,
                source_radius_km=rayon_source_km,
                title=f"{title} Alternance cloud",
                company="Cooperative Loire",
                city=city,
                published_at="2026-05-06",
                contract_type="Alternance",
                salary=None,
                description_source="Alternance AWS Kubernetes niveau Bac.",
                source_url=f"https://example.test/offres/{source_slug}-alternance-cloud",
                source_identifier=f"demo-{source_slug}-5",
            ),
        ]


@dataclass(frozen=True)
class FranceTravailHttpResponse:
    status_code: int
    body: bytes


@dataclass(frozen=True)
class AdzunaHttpResponse:
    status_code: int
    body: bytes


class FranceTravailHttpClient:
    def post_form(
        self, url: str, data: dict[str, str], headers: dict[str, str]
    ) -> FranceTravailHttpResponse:
        encoded_data = urlencode(data).encode()
        request = Request(url, data=encoded_data, headers=headers, method="POST")
        return self._send(request)

    def get_json(
        self, url: str, params: dict[str, str], headers: dict[str, str]
    ) -> FranceTravailHttpResponse:
        separator = "&" if "?" in url else "?"
        request = Request(
            f"{url}{separator}{urlencode(params)}", headers=headers, method="GET"
        )
        return self._send(request)

    def _send(self, request: Request) -> FranceTravailHttpResponse:
        try:
            with urlopen(request, timeout=15) as response:
                return FranceTravailHttpResponse(
                    status_code=response.status, body=response.read()
                )
        except HTTPError as exc:
            raise SourceConnectorUnavailable(
                f"France Travail a retourne HTTP {exc.code}."
            ) from exc
        except URLError as exc:
            raise SourceConnectorUnavailable(
                "France Travail est indisponible."
            ) from exc


class AdzunaHttpClient:
    def get_json(
        self, url: str, params: dict[str, str], headers: dict[str, str]
    ) -> AdzunaHttpResponse:
        separator = "&" if "?" in url else "?"
        request = Request(
            f"{url}{separator}{urlencode(params)}", headers=headers, method="GET"
        )
        try:
            with urlopen(request, timeout=15) as response:
                return AdzunaHttpResponse(
                    status_code=response.status, body=response.read()
                )
        except HTTPError as exc:
            raise SourceConnectorUnavailable(
                f"Adzuna a retourne HTTP {exc.code}."
            ) from exc
        except URLError as exc:
            raise SourceConnectorUnavailable("Adzuna est indisponible.") from exc


class FranceTravailConnector:
    source_name = "France Travail"
    token_url = (
        "https://entreprise.francetravail.fr/connexion/oauth2/access_token"
        "?realm=/partenaire"
    )
    search_url = (
        "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
    )
    communes_reference_url = (
        "https://api.francetravail.io/partenaire/offresdemploi/v2/referentiel/communes"
    )
    scope = "api_offresdemploiv2 o2dsoffre"

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        http_client: FranceTravailHttpClient | None = None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.http_client = http_client or FranceTravailHttpClient()

    def map_rayon_source(self, rayon_demande_km: int) -> int:
        return rayon_demande_km

    def search(
        self, *, intitule: str, localisation: str, rayon_demande_km: int
    ) -> list[OfferResult]:
        rayon_source_km = self.map_rayon_source(rayon_demande_km)
        access_token = self._fetch_access_token()
        location_criteria = self._resolve_location_criteria(
            localisation, access_token=access_token
        )
        response = self.http_client.get_json(
            self.search_url,
            params={
                "motsCles": intitule,
                location_criteria.parameter_name: location_criteria.value,
                "distance": str(rayon_source_km),
            },
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        if response.status_code >= 400:
            raise SourceConnectorUnavailable(
                f"France Travail a retourne HTTP {response.status_code}."
            )

        payload = _decode_json_payload(response.body, source_name=self.source_name)
        raw_results = payload.get("resultats", [])
        if not isinstance(raw_results, list):
            raise SourceConnectorUnavailable(
                "France Travail a retourne un format inattendu."
            )

        return [
            self._normalize_offer(
                raw_offer,
                localisation=localisation,
                rayon_source_km=rayon_source_km,
            )
            for raw_offer in raw_results
            if isinstance(raw_offer, dict)
        ]

    def _resolve_location_criteria(
        self, localisation: str, *, access_token: str
    ) -> FranceTravailLocationCriteria:
        response = self.http_client.get_json(
            self.communes_reference_url,
            params={},
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        if response.status_code >= 400:
            raise SourceConnectorUnavailable(
                f"France Travail n'a pas pu charger le referentiel des communes "
                f"pour resoudre la localisation "
                f"{localisation.strip()}."
            )

        payload = _decode_json_value(response.body, source_name=self.source_name)
        if not isinstance(payload, list) or not payload:
            raise SourceConnectorUnavailable(
                f"France Travail n'a pas reconnu la localisation "
                f"{localisation.strip()}."
            )

        commune_code = _find_commune_code(payload, searched_localisation=localisation)
        if commune_code is None:
            raise SourceConnectorUnavailable(
                f"France Travail n'a pas reconnu la localisation "
                f"{localisation.strip()}."
            )
        return FranceTravailLocationCriteria(
            parameter_name="commune", value=commune_code
        )

    def _fetch_access_token(self) -> str:
        response = self.http_client.post_form(
            self.token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": self.scope,
            },
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        if response.status_code >= 400:
            raise SourceConnectorUnavailable(
                f"France Travail auth a retourne HTTP {response.status_code}."
            )

        payload = _decode_json_payload(response.body, source_name=self.source_name)
        access_token = payload.get("access_token")
        if not isinstance(access_token, str) or not access_token.strip():
            raise SourceConnectorUnavailable(
                "France Travail auth n'a pas retourne de jeton d'acces."
            )
        return access_token

    def _normalize_offer(
        self,
        raw_offer: dict[str, object],
        *,
        localisation: str,
        rayon_source_km: int,
    ) -> OfferResult:
        source_identifier = _string_value(raw_offer.get("id"))
        source_url = (
            _nested_string(raw_offer, "origineOffre", "urlOrigine")
            or _nested_string(raw_offer, "origineOffre", "url")
            or _france_travail_offer_url(source_identifier)
        )
        return OfferResult(
            source_name=self.source_name,
            source_radius_km=rayon_source_km,
            title=(
                _string_value(raw_offer.get("intitule"))
                or _string_value(raw_offer.get("appellationlibelle"))
                or "Intitule non precise"
            ),
            company=(
                _nested_string(raw_offer, "entreprise", "nom")
                or "Entreprise non precisee"
            ),
            city=(
                _nested_string(raw_offer, "lieuTravail", "libelle")
                or _nested_string(raw_offer, "lieuTravail", "commune")
                or localisation
            ),
            published_at=_date_value(raw_offer.get("dateCreation")),
            contract_type=_normalize_contract_type(
                _string_value(raw_offer.get("typeContrat"))
                or _string_value(raw_offer.get("typeContratLibelle"))
            ),
            salary=_nested_string(raw_offer, "salaire", "libelle"),
            description_source=_string_value(raw_offer.get("description")),
            source_url=source_url,
            source_identifier=source_identifier,
            remote_text=_string_value(raw_offer.get("deplacementLibelle")),
        )


class AdzunaConnector:
    source_name = "Adzuna"
    search_url_template = "https://api.adzuna.com/v1/api/jobs/fr/search/{page}"
    results_per_page = 50
    pages_per_search = 4

    def __init__(
        self,
        *,
        app_id: str,
        app_key: str,
        pages_per_search: int = 4,
        http_client: AdzunaHttpClient | None = None,
    ) -> None:
        self.app_id = app_id
        self.app_key = app_key
        self.pages_per_search = pages_per_search
        self.http_client = http_client or AdzunaHttpClient()

    def map_rayon_source(self, rayon_demande_km: int) -> int:
        return rayon_demande_km

    def search(
        self, *, intitule: str, localisation: str, rayon_demande_km: int
    ) -> list[OfferResult]:
        rayon_source_km = self.map_rayon_source(rayon_demande_km)
        raw_results: list[dict[str, object]] = []
        total_count: int | None = None
        pages_fetched = 0

        for page in range(1, self.pages_per_search + 1):
            response = self.http_client.get_json(
                self.search_url_template.format(page=page),
                params={
                    "app_id": self.app_id,
                    "app_key": self.app_key,
                    "what": intitule,
                    "where": localisation,
                    "distance": str(rayon_source_km),
                    "results_per_page": str(self.results_per_page),
                    "sort_by": "date",
                    "sort_direction": "down",
                    "content-type": "application/json",
                },
                headers={"Accept": "application/json"},
            )
            if response.status_code >= 400:
                raise SourceConnectorUnavailable(
                    f"Adzuna a retourne HTTP {response.status_code}."
                )

            payload = _decode_json_payload(response.body, source_name=self.source_name)
            page_raw_results = payload.get("results", [])
            if not isinstance(page_raw_results, list):
                raise SourceConnectorUnavailable(
                    "Adzuna a retourne un format inattendu."
                )
            page_total_count = payload.get("count")
            if total_count is None and isinstance(page_total_count, int):
                total_count = page_total_count
            raw_results.extend(
                raw_offer
                for raw_offer in page_raw_results
                if isinstance(raw_offer, dict)
            )
            pages_fetched += 1

            if len(page_raw_results) < self.results_per_page:
                break

        LOGGER.info(
            "Adzuna a recupere %d offre(s) sur %s disponible(s) en %d page(s) "
            "pour intitule=%r localisation=%r rayon=%d km.",
            len(raw_results),
            total_count if total_count is not None else "un nombre inconnu",
            pages_fetched,
            intitule,
            localisation,
            rayon_source_km,
        )

        return [
            self._normalize_offer(
                raw_offer,
                localisation=localisation,
                rayon_source_km=rayon_source_km,
            )
            for raw_offer in raw_results
        ]

    def _normalize_offer(
        self,
        raw_offer: dict[str, object],
        *,
        localisation: str,
        rayon_source_km: int,
    ) -> OfferResult:
        source_identifier = _string_value(raw_offer.get("id"))
        source_url = _string_value(raw_offer.get("redirect_url")) or _adzuna_offer_url(
            source_identifier
        )
        return OfferResult(
            source_name=self.source_name,
            source_radius_km=rayon_source_km,
            title=_string_value(raw_offer.get("title")) or "Intitule non precise",
            company=(
                _nested_string(raw_offer, "company", "display_name")
                or "Entreprise non precisee"
            ),
            city=(
                _nested_string(raw_offer, "location", "display_name")
                or _nested_first_string(raw_offer, "location", "area")
                or localisation
            ),
            published_at=_date_value(raw_offer.get("created")),
            contract_type=_normalize_adzuna_contract_type(
                _string_value(raw_offer.get("contract_type"))
                or _string_value(raw_offer.get("contract_time"))
            ),
            salary=_adzuna_salary(raw_offer),
            description_source=_string_value(raw_offer.get("description")),
            source_url=source_url,
            source_identifier=source_identifier,
        )


def build_source_connectors(settings: Settings) -> list[SourceConnector]:
    connectors: list[SourceConnector] = []
    if not settings.prod:
        connectors.append(DemoSourceConnector())
    if settings.france_travail_enabled:
        assert settings.france_travail_client_id is not None
        assert settings.france_travail_client_secret is not None
        connectors.append(
            FranceTravailConnector(
                client_id=settings.france_travail_client_id,
                client_secret=settings.france_travail_client_secret,
            )
        )
    if settings.adzuna_enabled:
        assert settings.adzuna_app_id is not None
        assert settings.adzuna_app_key is not None
        connectors.append(
            AdzunaConnector(
                app_id=settings.adzuna_app_id,
                app_key=settings.adzuna_app_key,
                pages_per_search=settings.adzuna_pages_per_search,
            )
        )
    return connectors


def run_search_trace(
    database_path: Path,
    *,
    intitule: str,
    localisation: str,
    rayon_demande_km: int,
    connector: SourceConnector | None = None,
    connectors: list[SourceConnector] | None = None,
) -> SearchTrace:
    session = create_search_session(
        database_path,
        intitule=intitule.strip(),
        localisation=localisation.strip(),
        rayon_demande_km=rayon_demande_km,
    )
    source_connectors = connectors or [connector or DemoSourceConnector()]

    results: list[OfferResult] = []
    failure_count = 0
    successful_source_names: set[str] = set()
    for source_connector in source_connectors:
        try:
            source_results = source_connector.search(
                intitule=session.intitule,
                localisation=session.localisation,
                rayon_demande_km=session.rayon_demande_km,
            )
        except SourceConnectorUnavailable as exc:
            failure_count += 1
            save_source_failure(
                database_path,
                session_id=session.id,
                source_name=source_connector.source_name,
                message=str(exc),
            )
            continue

        results.extend(source_results)
        successful_source_names.add(source_connector.source_name)

    previous_session = find_previous_session_for_same_recherche(
        database_path,
        session_id=session.id,
        intitule=session.intitule,
        localisation=session.localisation,
        rayon_demande_km=session.rayon_demande_km,
    )
    previous_result_identities = (
        list_result_identities_for_session(database_path, previous_session.id)
        if previous_session is not None
        else set()
    )
    active_result_identities = {result.result_identity for result in results}
    enriched_results = [
        _stored_result_from_offer_result(
            result,
            session_id=session.id,
            is_new=previous_session is not None
            and result.result_identity not in previous_result_identities,
        )
        for result in results
    ]
    save_offer_results(
        database_path,
        session_id=session.id,
        results=enriched_results,
    )
    save_inactive_offer_results_for_missing_identities(
        database_path,
        session_id=session.id,
        recherche=session,
        successful_source_names=successful_source_names,
        active_result_identities=active_result_identities,
    )
    return SearchTrace(
        session=session, result_count=len(results), failure_count=failure_count
    )


def _stored_result_from_offer_result(
    result: OfferResult, *, session_id: int, is_new: bool
) -> StoredOfferResult:
    enrichment = enrich_result(result)
    return StoredOfferResult(
        id=0,
        session_id=session_id,
        source_name=result.source_name,
        source_radius_km=result.source_radius_km,
        result_identity=result.result_identity,
        title=result.title,
        company=result.company,
        city=result.city,
        published_at=result.published_at,
        contract_type=result.contract_type,
        salary=result.salary,
        description_source=result.description_source,
        skill_tags=enrichment.skill_tags,
        experience_level=enrichment.experience_level,
        diploma_level=enrichment.diploma_level,
        source_url=result.source_url,
        remote_text=result.remote_text,
        is_new=is_new,
        inactive=False,
    )


def build_result_identity(
    *, source_name: str, source_url: str, source_identifier: str | None = None
) -> str:
    identity_value = source_identifier or _canonicalize_source_url(source_url)
    return f"{source_name}:{identity_value}"


def _canonicalize_source_url(source_url: str) -> str:
    return source_url.strip().split("#", maxsplit=1)[0].rstrip("/")


def _slugify(value: str) -> str:
    slug = "-".join(value.casefold().split())
    return slug or "recherche"


def _decode_json_value(body: bytes, *, source_name: str) -> object:
    try:
        return loads(body.decode())
    except (UnicodeDecodeError, JSONDecodeError) as exc:
        raise SourceConnectorUnavailable(
            f"{source_name} a retourne une reponse illisible."
        ) from exc


def _decode_json_payload(body: bytes, *, source_name: str) -> dict[str, object]:
    payload = _decode_json_value(body, source_name=source_name)
    if not isinstance(payload, dict):
        raise SourceConnectorUnavailable(
            f"{source_name} a retourne un format inattendu."
        )
    return payload


def _string_value(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def _first_string_value(value: object) -> str | None:
    if not isinstance(value, list):
        return None
    for item in value:
        string_item = _string_value(item)
        if string_item is not None:
            return string_item
    return None


def _find_commune_code(
    communes: list[object], *, searched_localisation: str
) -> str | None:
    searched_postal_code = _extract_postal_code(searched_localisation)
    if searched_postal_code is not None:
        for commune in communes:
            if not isinstance(commune, dict):
                continue
            if _string_value(commune.get("codePostal")) != searched_postal_code:
                continue
            commune_code = _string_value(commune.get("code"))
            if commune_code is not None:
                return commune_code

    searched_name = _normalize_search_text(
        re.sub(r"\b\d{5}\b", "", searched_localisation)
    )
    exact_name_match: str | None = None
    prefix_name_match: str | None = None
    for commune in communes:
        if not isinstance(commune, dict):
            continue
        commune_code = _string_value(commune.get("code"))
        commune_name = _string_value(commune.get("libelle"))
        if commune_code is None or commune_name is None:
            continue

        normalized_commune_name = _normalize_search_text(commune_name)
        if normalized_commune_name == searched_name:
            exact_name_match = commune_code
            break
        if (
            prefix_name_match is None
            and searched_name
            and normalized_commune_name.startswith(f"{searched_name} ")
        ):
            prefix_name_match = commune_code

    return exact_name_match or prefix_name_match


def _normalize_search_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return " ".join(ascii_value.casefold().split())


def _extract_postal_code(value: str) -> str | None:
    match = re.search(r"\b\d{5}\b", value.strip())
    if match is None:
        return None
    return match.group(0)


def _nested_string(
    payload: dict[str, object], parent_key: str, child_key: str
) -> str | None:
    parent = payload.get(parent_key)
    if not isinstance(parent, dict):
        return None
    return _string_value(parent.get(child_key))


def _nested_first_string(
    payload: dict[str, object], parent_key: str, child_key: str
) -> str | None:
    parent = payload.get(parent_key)
    if not isinstance(parent, dict):
        return None
    return _first_string_value(parent.get(child_key))


def _numeric_value(value: object) -> int | float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return value
    return None


def _date_value(value: object) -> str | None:
    raw_value = _string_value(value)
    if raw_value is None:
        return None
    return raw_value[:10]


def _france_travail_offer_url(source_identifier: str | None) -> str:
    if source_identifier is None:
        return "https://candidat.francetravail.fr/offres/recherche"
    return (
        f"https://candidat.francetravail.fr/offres/recherche/detail/{source_identifier}"
    )


def _adzuna_offer_url(source_identifier: str | None) -> str:
    if source_identifier is None:
        return "https://www.adzuna.fr/search"
    return f"https://www.adzuna.fr/details/{source_identifier}"


def _normalize_contract_type(value: str | None) -> str:
    if value is None:
        return "Non precise"

    normalized_value = value.casefold()
    if "cdi" in normalized_value or "indeterminee" in normalized_value:
        return "CDI"
    if "cdd" in normalized_value or "determinee" in normalized_value:
        return "CDD"
    if "interim" in normalized_value or "intérim" in normalized_value:
        return "Interim"
    if "freelance" in normalized_value or "independant" in normalized_value:
        return "Freelance"
    if "stage" in normalized_value:
        return "Stage"
    if "alternance" in normalized_value or "apprentissage" in normalized_value:
        return "Alternance"
    return value


def _normalize_adzuna_contract_type(value: str | None) -> str:
    if value is None:
        return "Non precise"

    normalized_value = value.casefold().replace("_", " ")
    if "permanent" in normalized_value:
        return "CDI"
    if "contract" in normalized_value:
        return "CDD"
    if "part time" in normalized_value:
        return "Temps partiel"
    if "full time" in normalized_value:
        return "Temps plein"
    return _normalize_contract_type(normalized_value)


def _adzuna_salary(raw_offer: dict[str, object]) -> str | None:
    salary_min = _numeric_value(raw_offer.get("salary_min"))
    salary_max = _numeric_value(raw_offer.get("salary_max"))
    if salary_min is None and salary_max is None:
        return None
    if salary_min is not None and salary_max is not None:
        return f"{salary_min:g} - {salary_max:g} EUR"
    if salary_min is not None:
        return f"{salary_min:g} EUR minimum"
    assert salary_max is not None
    return f"{salary_max:g} EUR maximum"
