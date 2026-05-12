import logging
import os
import sqlite3
from json import dumps
from pathlib import Path

import pytest

from mirandole.config import Settings
from mirandole.search import (
    AdzunaConnector,
    AdzunaHttpResponse,
    DemoSourceConnector,
    DemoSourceUnavailable,
    FranceTravailConnector,
    FranceTravailHttpResponse,
    OfferResult,
    SourceConnectorUnavailable,
    build_result_identity,
    build_source_connectors,
    run_search_trace,
)
from mirandole.storage import (
    initialize_storage,
    list_favorite_offer_results,
    list_hidden_offer_results,
    list_offer_results_for_session,
    list_recent_searches,
    list_search_sessions,
    list_source_failures_for_session,
    mark_offer_result_consulted,
    toggle_offer_result_favorite,
    toggle_offer_result_hidden,
)


class MutableSourceConnector:
    source_name = "Source mutable"

    def __init__(self, source_identifiers: list[str]) -> None:
        self.source_identifiers = source_identifiers

    def search(
        self, *, intitule: str, localisation: str, rayon_demande_km: int
    ) -> list[OfferResult]:
        return [
            OfferResult(
                source_name=self.source_name,
                source_radius_km=rayon_demande_km,
                title=f"{intitule} {source_identifier}",
                company="Entreprise test",
                city=localisation,
                published_at=f"2026-05-0{index + 1}",
                contract_type="CDI",
                salary=None,
                description_source="Developpement Python.",
                source_url=f"https://example.test/{source_identifier}",
                source_identifier=source_identifier,
            )
            for index, source_identifier in enumerate(self.source_identifiers)
        ]


class AlwaysUnavailableConnector:
    source_name = "Source mutable"

    def search(
        self, *, intitule: str, localisation: str, rayon_demande_km: int
    ) -> list[OfferResult]:
        raise DemoSourceUnavailable("Source mutable indisponible.")


class FakeFranceTravailHttpClient:
    def __init__(
        self,
        *,
        token_status_code: int = 200,
        location_status_code: int = 200,
        search_status_code: int = 200,
        location_payload: list[dict[str, object]] | None = None,
        search_payload: dict[str, object] | None = None,
    ) -> None:
        self.token_status_code = token_status_code
        self.location_status_code = location_status_code
        self.search_status_code = search_status_code
        self.location_payload = location_payload or [
            {"code": "44109", "codePostal": "44000", "libelle": "NANTES"},
            {"code": "35238", "codePostal": "35000", "libelle": "RENNES"},
        ]
        self.search_payload = search_payload or {"resultats": []}
        self.token_data: dict[str, str] | None = None
        self.location_params: dict[str, str] | None = None
        self.search_params: dict[str, str] | None = None

    def post_form(
        self, url: str, data: dict[str, str], headers: dict[str, str]
    ) -> FranceTravailHttpResponse:
        self.token_data = data
        return FranceTravailHttpResponse(
            status_code=self.token_status_code,
            body=dumps({"access_token": "token-test"}).encode(),
        )

    def get_json(
        self, url: str, params: dict[str, str], headers: dict[str, str]
    ) -> FranceTravailHttpResponse:
        if "referentiel/communes" in url:
            self.location_params = params
            return FranceTravailHttpResponse(
                status_code=self.location_status_code,
                body=dumps(self.location_payload).encode(),
            )
        self.search_params = params
        return FranceTravailHttpResponse(
            status_code=self.search_status_code,
            body=dumps(self.search_payload).encode(),
        )


class FakeAdzunaHttpClient:
    def __init__(
        self,
        *,
        search_status_code: int = 200,
        search_payload: dict[str, object] | None = None,
        search_payloads: list[dict[str, object]] | None = None,
    ) -> None:
        self.search_status_code = search_status_code
        self.search_payloads = search_payloads or [search_payload or {"results": []}]
        self.search_urls: list[str] = []
        self.search_params_history: list[dict[str, str]] = []
        self.search_headers_history: list[dict[str, str]] = []
        self.search_params: dict[str, str] | None = None
        self.search_headers: dict[str, str] | None = None

    def get_json(
        self, url: str, params: dict[str, str], headers: dict[str, str]
    ) -> AdzunaHttpResponse:
        payload_index = min(len(self.search_urls), len(self.search_payloads) - 1)
        self.search_urls.append(url)
        self.search_params_history.append(params)
        self.search_headers_history.append(headers)
        self.search_params = params
        self.search_headers = headers
        return AdzunaHttpResponse(
            status_code=self.search_status_code,
            body=dumps(self.search_payloads[payload_index]).encode(),
        )


def _adzuna_search_payload(
    *, page: int, result_count: int, total_count: int
) -> dict[str, object]:
    return {
        "count": total_count,
        "results": [
            {
                "id": f"{page}-{index}",
                "title": f"Developpeur Python page {page} offre {index}",
                "redirect_url": f"https://www.adzuna.fr/details/{page}-{index}",
            }
            for index in range(result_count)
        ],
    }


def test_initialize_storage_is_idempotent(tmp_path: Path) -> None:
    database_path = tmp_path / "stockage" / "app.sqlite3"

    initialize_storage(database_path)
    initialize_storage(database_path)

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            "SELECT value FROM app_metadata WHERE key = 'schema_version'"
        ).fetchone()

    assert row == ("1",)


def test_search_trace_creates_session_and_persists_results(tmp_path: Path) -> None:
    database_path = tmp_path / "stockage" / "app.sqlite3"
    initialize_storage(database_path)

    trace = run_search_trace(
        database_path,
        intitule="Developpeur backend",
        localisation="Nantes",
        rayon_demande_km=30,
    )

    sessions = list_search_sessions(database_path)
    results = list_offer_results_for_session(database_path, trace.session.id)

    assert [session.id for session in sessions] == [trace.session.id]
    assert sessions[0].intitule == "Developpeur backend"
    assert sessions[0].localisation == "Nantes"
    assert sessions[0].rayon_demande_km == 30
    assert trace.result_count == 5
    assert len(results) == 5
    assert results[0].source_name == "Source demo"
    assert results[0].result_identity == "Source demo:demo-developpeur-backend-1"
    assert results[0].title == "Developpeur backend Python"
    assert results[0].company == "Atelier Hexagone"
    assert results[0].city == "Nantes"
    assert results[0].published_at == "2026-05-09"
    assert results[0].contract_type == "CDI"
    assert results[0].salary == "45 000 - 55 000 EUR"
    assert results[0].skill_tags == ("API", "FastAPI", "Python")
    assert results[0].experience_level == "Avance"
    assert results[0].diploma_level == "Bac+5"
    assert results[0].source_url == (
        "https://example.test/offres/developpeur-backend-python"
    )
    assert results[0].remote_text == "Teletravail partiel"
    assert results[0].is_new is False
    assert results[0].inactive is False


def test_demo_source_maps_rayon_demande_to_supported_rayon_source() -> None:
    connector = DemoSourceConnector()

    assert connector.map_rayon_source(10) == 20
    assert connector.map_rayon_source(20) == 20
    assert connector.map_rayon_source(30) == 50
    assert connector.map_rayon_source(50) == 50
    assert connector.map_rayon_source(100) == 100


def test_france_travail_connector_normalizes_resultats_offre() -> None:
    http_client = FakeFranceTravailHttpClient(
        search_payload={
            "resultats": [
                {
                    "id": "176ABC",
                    "intitule": "Developpeur Python",
                    "entreprise": {"nom": "Atelier Hexagone"},
                    "lieuTravail": {"libelle": "44 - Nantes"},
                    "dateCreation": "2026-05-10T09:30:00.000Z",
                    "typeContrat": "CDI",
                    "salaire": {"libelle": "45 000 EUR annuel"},
                    "description": "Developpement API Python. Bac+5 apprecie.",
                    "origineOffre": {
                        "urlOrigine": "https://candidat.francetravail.fr/offres/recherche/detail/176ABC"
                    },
                    "deplacementLibelle": "Teletravail partiel",
                }
            ]
        }
    )
    connector = FranceTravailConnector(
        client_id="client-id", client_secret="client-secret", http_client=http_client
    )

    results = connector.search(
        intitule="Developpeur", localisation="Nantes", rayon_demande_km=30
    )

    assert http_client.token_data == {
        "grant_type": "client_credentials",
        "client_id": "client-id",
        "client_secret": "client-secret",
        "scope": "api_offresdemploiv2 o2dsoffre",
    }
    assert http_client.location_params == {}
    assert http_client.search_params == {
        "motsCles": "Developpeur",
        "commune": "44109",
        "distance": "30",
    }
    assert len(results) == 1
    assert results[0].source_name == "France Travail"
    assert results[0].source_radius_km == 30
    assert results[0].title == "Developpeur Python"
    assert results[0].company == "Atelier Hexagone"
    assert results[0].city == "44 - Nantes"
    assert results[0].published_at == "2026-05-10"
    assert results[0].contract_type == "CDI"
    assert results[0].salary == "45 000 EUR annuel"
    assert results[0].description_source == "Developpement API Python. Bac+5 apprecie."
    assert results[0].source_url == (
        "https://candidat.francetravail.fr/offres/recherche/detail/176ABC"
    )
    assert results[0].source_identifier == "176ABC"
    assert results[0].result_identity == "France Travail:176ABC"
    assert results[0].remote_text == "Teletravail partiel"


def test_france_travail_connector_resolves_lyon_to_commune_code() -> None:
    http_client = FakeFranceTravailHttpClient(
        location_payload=[{"code": "69123", "codePostal": "69000", "libelle": "LYON"}]
    )
    connector = FranceTravailConnector(
        client_id="client-id", client_secret="client-secret", http_client=http_client
    )

    connector.search(intitule="Linux", localisation="Lyon", rayon_demande_km=50)

    assert http_client.location_params == {}
    assert http_client.search_params == {
        "motsCles": "Linux",
        "commune": "69123",
        "distance": "50",
    }


def test_france_travail_connector_resolves_postal_code_to_commune_code() -> None:
    http_client = FakeFranceTravailHttpClient(
        location_payload=[
            {"code": "75101", "codePostal": "75001", "libelle": "PARIS 01"}
        ]
    )
    connector = FranceTravailConnector(
        client_id="client-id", client_secret="client-secret", http_client=http_client
    )

    connector.search(intitule="Linux", localisation="75001", rayon_demande_km=10)

    assert http_client.location_params == {}
    assert http_client.search_params == {
        "motsCles": "Linux",
        "commune": "75101",
        "distance": "10",
    }


def test_france_travail_connector_handles_missing_optional_fields() -> None:
    connector = FranceTravailConnector(
        client_id="client-id",
        client_secret="client-secret",
        http_client=FakeFranceTravailHttpClient(
            search_payload={
                "resultats": [
                    {
                        "id": "176DEF",
                        "intitule": "Support applicatif",
                    }
                ]
            }
        ),
    )

    results = connector.search(
        intitule="Support", localisation="Rennes", rayon_demande_km=10
    )

    assert len(results) == 1
    assert results[0].company == "Entreprise non precisee"
    assert results[0].city == "Rennes"
    assert results[0].published_at is None
    assert results[0].contract_type == "Non precise"
    assert results[0].salary is None
    assert results[0].description_source is None
    assert results[0].source_url == (
        "https://candidat.francetravail.fr/offres/recherche/detail/176DEF"
    )


def test_france_travail_source_failure_does_not_fail_session(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "stockage" / "app.sqlite3"
    initialize_storage(database_path)
    france_travail = FranceTravailConnector(
        client_id="client-id",
        client_secret="client-secret",
        http_client=FakeFranceTravailHttpClient(search_status_code=429),
    )

    trace = run_search_trace(
        database_path,
        intitule="Developpeur backend",
        localisation="Nantes",
        rayon_demande_km=20,
        connectors=[DemoSourceConnector(), france_travail],
    )

    results = list_offer_results_for_session(database_path, trace.session.id)
    failures = list_source_failures_for_session(database_path, trace.session.id)

    assert trace.result_count == 5
    assert trace.failure_count == 1
    assert results
    assert failures[0].source_name == "France Travail"
    assert "HTTP 429" in failures[0].message


def test_france_travail_auth_failure_is_echec_de_source() -> None:
    connector = FranceTravailConnector(
        client_id="client-id",
        client_secret="client-secret",
        http_client=FakeFranceTravailHttpClient(token_status_code=401),
    )

    try:
        connector.search(
            intitule="Developpeur", localisation="Nantes", rayon_demande_km=20
        )
    except SourceConnectorUnavailable as exc:
        assert "auth" in str(exc)
        assert "HTTP 401" in str(exc)
    else:
        raise AssertionError("Expected SourceConnectorUnavailable")


def test_adzuna_connector_normalizes_resultats_offre(
    caplog: pytest.LogCaptureFixture,
) -> None:
    http_client = FakeAdzunaHttpClient(
        search_payload={
            "count": 42,
            "results": [
                {
                    "id": "499",
                    "title": "Developpeur Python",
                    "company": {"display_name": "Atelier Hexagone"},
                    "location": {
                        "display_name": "Nantes, Loire-Atlantique",
                        "area": ["France", "Pays de la Loire", "Nantes"],
                    },
                    "created": "2026-05-10T08:15:00Z",
                    "contract_type": "permanent",
                    "salary_min": 45000,
                    "salary_max": 55000,
                    "description": "Developpement API Python. Bac+5 apprecie.",
                    "redirect_url": "https://www.adzuna.fr/details/499?utm=test",
                }
            ],
        }
    )
    connector = AdzunaConnector(
        app_id="app-id", app_key="app-key", http_client=http_client
    )
    caplog.set_level(logging.INFO, logger="mirandole.search")

    results = connector.search(
        intitule="Developpeur", localisation="Nantes", rayon_demande_km=30
    )

    assert http_client.search_params == {
        "app_id": "app-id",
        "app_key": "app-key",
        "what": "Developpeur",
        "where": "Nantes",
        "distance": "30",
        "results_per_page": "50",
        "sort_by": "date",
        "sort_direction": "down",
        "content-type": "application/json",
    }
    assert http_client.search_headers == {"Accept": "application/json"}
    assert http_client.search_urls == ["https://api.adzuna.com/v1/api/jobs/fr/search/1"]
    assert len(results) == 1
    assert results[0].source_name == "Adzuna"
    assert results[0].source_radius_km == 30
    assert results[0].title == "Developpeur Python"
    assert results[0].company == "Atelier Hexagone"
    assert results[0].city == "Nantes, Loire-Atlantique"
    assert results[0].published_at == "2026-05-10"
    assert results[0].contract_type == "CDI"
    assert results[0].salary == "45000 - 55000 EUR"
    assert results[0].description_source == "Developpement API Python. Bac+5 apprecie."
    assert results[0].source_url == "https://www.adzuna.fr/details/499?utm=test"
    assert results[0].source_identifier == "499"
    assert results[0].result_identity == "Adzuna:499"
    assert (
        "Adzuna a recupere 1 offre(s) sur 42 disponible(s) en 1 page(s) "
        "pour intitule='Developpeur' localisation='Nantes' rayon=30 km."
    ) in caplog.messages


def test_adzuna_connector_fetches_four_pages_sorted_by_date_descending() -> None:
    http_client = FakeAdzunaHttpClient(
        search_payloads=[
            _adzuna_search_payload(page=page, result_count=50, total_count=250)
            for page in range(1, 5)
        ]
    )
    connector = AdzunaConnector(
        app_id="app-id", app_key="app-key", http_client=http_client
    )

    results = connector.search(
        intitule="Python", localisation="Paris", rayon_demande_km=25
    )

    assert len(results) == 200
    assert http_client.search_urls == [
        f"https://api.adzuna.com/v1/api/jobs/fr/search/{page}" for page in range(1, 5)
    ]
    assert http_client.search_params_history == [
        {
            "app_id": "app-id",
            "app_key": "app-key",
            "what": "Python",
            "where": "Paris",
            "distance": "25",
            "results_per_page": "50",
            "sort_by": "date",
            "sort_direction": "down",
            "content-type": "application/json",
        }
        for _ in range(4)
    ]
    assert results[0].result_identity == "Adzuna:1-0"
    assert results[-1].result_identity == "Adzuna:4-49"


def test_adzuna_connector_stops_when_page_returns_less_than_page_size() -> None:
    http_client = FakeAdzunaHttpClient(
        search_payloads=[
            _adzuna_search_payload(page=1, result_count=50, total_count=62),
            _adzuna_search_payload(page=2, result_count=12, total_count=62),
            _adzuna_search_payload(page=3, result_count=50, total_count=62),
        ]
    )
    connector = AdzunaConnector(
        app_id="app-id", app_key="app-key", http_client=http_client
    )

    results = connector.search(
        intitule="Python", localisation="Paris", rayon_demande_km=25
    )

    assert len(results) == 62
    assert http_client.search_urls == [
        "https://api.adzuna.com/v1/api/jobs/fr/search/1",
        "https://api.adzuna.com/v1/api/jobs/fr/search/2",
    ]


def test_adzuna_connector_uses_configured_pages_per_search() -> None:
    http_client = FakeAdzunaHttpClient(
        search_payloads=[
            _adzuna_search_payload(page=page, result_count=50, total_count=250)
            for page in range(1, 4)
        ]
    )
    connector = AdzunaConnector(
        app_id="app-id",
        app_key="app-key",
        pages_per_search=3,
        http_client=http_client,
    )

    results = connector.search(
        intitule="Python", localisation="Paris", rayon_demande_km=25
    )

    assert len(results) == 150
    assert http_client.search_urls == [
        f"https://api.adzuna.com/v1/api/jobs/fr/search/{page}" for page in range(1, 4)
    ]


def test_adzuna_connector_handles_missing_optional_fields() -> None:
    connector = AdzunaConnector(
        app_id="app-id",
        app_key="app-key",
        http_client=FakeAdzunaHttpClient(
            search_payload={
                "results": [
                    {
                        "id": "500",
                        "title": "Support applicatif",
                        "location": {"area": ["France", "Bretagne", "Rennes"]},
                    }
                ]
            }
        ),
    )

    results = connector.search(
        intitule="Support", localisation="Rennes", rayon_demande_km=10
    )

    assert len(results) == 1
    assert results[0].company == "Entreprise non precisee"
    assert results[0].city == "France"
    assert results[0].published_at is None
    assert results[0].contract_type == "Non precise"
    assert results[0].salary is None
    assert results[0].description_source is None
    assert results[0].source_url == "https://www.adzuna.fr/details/500"
    assert results[0].result_identity == "Adzuna:500"


def test_adzuna_source_failure_does_not_fail_session(tmp_path: Path) -> None:
    database_path = tmp_path / "stockage" / "app.sqlite3"
    initialize_storage(database_path)
    adzuna = AdzunaConnector(
        app_id="app-id",
        app_key="app-key",
        http_client=FakeAdzunaHttpClient(search_status_code=429),
    )

    trace = run_search_trace(
        database_path,
        intitule="Developpeur backend",
        localisation="Nantes",
        rayon_demande_km=20,
        connectors=[DemoSourceConnector(), adzuna],
    )

    results = list_offer_results_for_session(database_path, trace.session.id)
    failures = list_source_failures_for_session(database_path, trace.session.id)

    assert trace.result_count == 5
    assert trace.failure_count == 1
    assert results
    assert failures[0].source_name == "Adzuna"
    assert "HTTP 429" in failures[0].message


def test_adzuna_auth_failure_is_echec_de_source() -> None:
    connector = AdzunaConnector(
        app_id="app-id",
        app_key="app-key",
        http_client=FakeAdzunaHttpClient(search_status_code=401),
    )

    try:
        connector.search(
            intitule="Developpeur", localisation="Nantes", rayon_demande_km=20
        )
    except SourceConnectorUnavailable as exc:
        assert "HTTP 401" in str(exc)
    else:
        raise AssertionError("Expected SourceConnectorUnavailable")


def test_france_travail_connector_is_disabled_by_configuration(tmp_path: Path) -> None:
    settings = Settings(
        password="correct horse battery staple",
        session_secret="x" * 32,
        database_path=tmp_path / "app.sqlite3",
        cookie_secure=False,
        france_travail_enabled=False,
        france_travail_client_id=None,
        france_travail_client_secret=None,
    )

    connectors = build_source_connectors(settings)

    assert [connector.source_name for connector in connectors] == ["Source demo"]


def test_france_travail_connector_is_enabled_by_configuration(tmp_path: Path) -> None:
    settings = Settings(
        password="correct horse battery staple",
        session_secret="x" * 32,
        database_path=tmp_path / "app.sqlite3",
        cookie_secure=False,
        france_travail_enabled=True,
        france_travail_client_id="client-id",
        france_travail_client_secret="client-secret",
    )

    connectors = build_source_connectors(settings)

    assert [connector.source_name for connector in connectors] == [
        "Source demo",
        "France Travail",
    ]


def test_demo_connector_is_disabled_in_prod_configuration(tmp_path: Path) -> None:
    settings = Settings(
        password="correct horse battery staple",
        session_secret="x" * 32,
        database_path=tmp_path / "app.sqlite3",
        cookie_secure=False,
        prod=True,
        france_travail_enabled=True,
        france_travail_client_id="client-id",
        france_travail_client_secret="client-secret",
    )

    connectors = build_source_connectors(settings)

    assert [connector.source_name for connector in connectors] == ["France Travail"]


def test_adzuna_connector_is_disabled_by_configuration(tmp_path: Path) -> None:
    settings = Settings(
        password="correct horse battery staple",
        session_secret="x" * 32,
        database_path=tmp_path / "app.sqlite3",
        cookie_secure=False,
        adzuna_enabled=False,
        adzuna_app_id=None,
        adzuna_app_key=None,
    )

    connectors = build_source_connectors(settings)

    assert [connector.source_name for connector in connectors] == ["Source demo"]


def test_adzuna_connector_is_enabled_by_configuration(tmp_path: Path) -> None:
    settings = Settings(
        password="correct horse battery staple",
        session_secret="x" * 32,
        database_path=tmp_path / "app.sqlite3",
        cookie_secure=False,
        adzuna_enabled=True,
        adzuna_app_id="app-id",
        adzuna_app_key="app-key",
    )

    connectors = build_source_connectors(settings)

    assert [connector.source_name for connector in connectors] == [
        "Source demo",
        "Adzuna",
    ]
    assert isinstance(connectors[1], AdzunaConnector)
    assert connectors[1].pages_per_search == 4


def test_adzuna_pages_per_search_is_passed_from_configuration(
    tmp_path: Path,
) -> None:
    settings = Settings(
        password="correct horse battery staple",
        session_secret="x" * 32,
        database_path=tmp_path / "app.sqlite3",
        cookie_secure=False,
        adzuna_enabled=True,
        adzuna_app_id="app-id",
        adzuna_app_key="app-key",
        adzuna_pages_per_search=6,
    )

    connectors = build_source_connectors(settings)

    assert isinstance(connectors[1], AdzunaConnector)
    assert connectors[1].pages_per_search == 6


@pytest.mark.live_adzuna
def test_live_adzuna_smoke_returns_resultats_offre() -> None:
    app_id = os.getenv("MIRANDOLE_ADZUNA_APP_ID")
    app_key = os.getenv("MIRANDOLE_ADZUNA_APP_KEY")
    if not app_id or not app_key:
        pytest.skip("MIRANDOLE_ADZUNA_APP_ID and MIRANDOLE_ADZUNA_APP_KEY are required")
    connector = AdzunaConnector(app_id=app_id, app_key=app_key)

    results = connector.search(
        intitule="Python", localisation="Paris", rayon_demande_km=10
    )

    assert isinstance(results, list)
    if results:
        assert results[0].source_name == "Adzuna"
        assert results[0].source_url
        assert results[0].result_identity.startswith("Adzuna:")


def test_results_are_sorted_by_freshness_with_unknown_dates_last(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "stockage" / "app.sqlite3"
    initialize_storage(database_path)

    trace = run_search_trace(
        database_path,
        intitule="Ingenieur logiciel",
        localisation="Rennes",
        rayon_demande_km=10,
    )

    results = list_offer_results_for_session(database_path, trace.session.id)

    assert [result.published_at for result in results] == [
        "2026-05-09",
        "2026-05-08",
        "2026-05-07",
        "2026-05-06",
        None,
    ]


def test_recent_searches_are_limited_deduplicated_and_sorted_by_last_use(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "stockage" / "app.sqlite3"
    initialize_storage(database_path)

    for index in range(11):
        run_search_trace(
            database_path,
            intitule=f"Developpeur {index}",
            localisation="Nantes",
            rayon_demande_km=20,
        )
    run_search_trace(
        database_path,
        intitule="  developpeur   1  ",
        localisation="NANTES",
        rayon_demande_km=20,
    )

    recent_searches = list_recent_searches(database_path)

    assert len(recent_searches) == 10
    assert recent_searches[0].intitule == "developpeur   1"
    assert recent_searches[0].last_session_id == 12
    assert [recent_search.intitule for recent_search in recent_searches].count(
        "developpeur   1"
    ) == 1
    assert "Developpeur 0" not in [
        recent_search.intitule for recent_search in recent_searches
    ]


def test_offre_nouvelle_compares_with_previous_session_for_same_recherche(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "stockage" / "app.sqlite3"
    initialize_storage(database_path)
    run_search_trace(
        database_path,
        intitule="Developpeur backend",
        localisation="Nantes",
        rayon_demande_km=20,
        connector=MutableSourceConnector(["known-a", "known-b"]),
    )

    trace = run_search_trace(
        database_path,
        intitule="Developpeur backend",
        localisation="Nantes",
        rayon_demande_km=20,
        connector=MutableSourceConnector(["known-b", "new-c"]),
    )

    results = list_offer_results_for_session(database_path, trace.session.id)
    active_results = [result for result in results if not result.inactive]

    assert {result.result_identity: result.is_new for result in active_results} == {
        "Source mutable:known-b": False,
        "Source mutable:new-c": True,
    }


def test_identite_resultat_includes_source_and_url_or_source_identifier() -> None:
    assert (
        build_result_identity(
            source_name="Source A",
            source_url="https://example.test/offres/1/",
        )
        == "Source A:https://example.test/offres/1"
    )
    assert (
        build_result_identity(
            source_name="Source B",
            source_url="https://example.test/offres/1/",
        )
        == "Source B:https://example.test/offres/1"
    )
    assert (
        build_result_identity(
            source_name="Source A",
            source_url="https://example.test/offres/changed",
            source_identifier="stable-1",
        )
        == "Source A:stable-1"
    )


def test_missing_known_offer_becomes_inactive_and_keeps_user_states(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "stockage" / "app.sqlite3"
    initialize_storage(database_path)
    first_trace = run_search_trace(
        database_path,
        intitule="Developpeur backend",
        localisation="Nantes",
        rayon_demande_km=20,
        connector=MutableSourceConnector(["known-a", "known-b"]),
    )
    first_results = list_offer_results_for_session(
        database_path, first_trace.session.id
    )
    known_a = next(
        result for result in first_results if result.title.endswith("known-a")
    )
    mark_offer_result_consulted(database_path, known_a.id)
    toggle_offer_result_favorite(database_path, known_a.id)

    second_trace = run_search_trace(
        database_path,
        intitule="Developpeur backend",
        localisation="Nantes",
        rayon_demande_km=20,
        connector=MutableSourceConnector(["known-b"]),
    )

    second_results = list_offer_results_for_session(
        database_path, second_trace.session.id
    )
    inactive_result = next(result for result in second_results if result.inactive)
    favorites = list_favorite_offer_results(database_path)

    assert inactive_result.result_identity == "Source mutable:known-a"
    assert inactive_result.consulted_at is not None
    assert inactive_result.favorite_at is not None
    assert favorites[0].result_identity == "Source mutable:known-a"
    assert favorites[0].inactive is True


def test_echec_de_source_does_not_make_known_offers_inactive(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "stockage" / "app.sqlite3"
    initialize_storage(database_path)
    successful_trace = run_search_trace(
        database_path,
        intitule="Developpeur backend",
        localisation="Nantes",
        rayon_demande_km=20,
        connector=MutableSourceConnector(["known-a"]),
    )

    failed_trace = run_search_trace(
        database_path,
        intitule="Developpeur backend",
        localisation="Nantes",
        rayon_demande_km=20,
        connector=AlwaysUnavailableConnector(),
    )

    failed_results = list_offer_results_for_session(
        database_path, failed_trace.session.id
    )
    previous_results = list_offer_results_for_session(
        database_path, successful_trace.session.id
    )

    assert failed_trace.failure_count == 1
    assert failed_results == []
    assert all(not result.inactive for result in previous_results)


def test_source_failure_keeps_session_and_existing_results_active(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "stockage" / "app.sqlite3"
    initialize_storage(database_path)
    successful_trace = run_search_trace(
        database_path,
        intitule="Administrateur systeme",
        localisation="Lyon",
        rayon_demande_km=20,
    )

    failed_trace = run_search_trace(
        database_path,
        intitule="Echec source",
        localisation="Lyon",
        rayon_demande_km=20,
    )

    failures = list_source_failures_for_session(database_path, failed_trace.session.id)
    previous_results = list_offer_results_for_session(
        database_path, successful_trace.session.id
    )

    assert failed_trace.result_count == 0
    assert failed_trace.failure_count == 1
    assert failures[0].source_name == "Source demo"
    assert "indisponible" in failures[0].message
    assert previous_results
    assert all(not result.inactive for result in previous_results)


def test_offer_result_consulted_state_follows_identite_resultat(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "stockage" / "app.sqlite3"
    initialize_storage(database_path)
    trace = run_search_trace(
        database_path,
        intitule="Developpeur backend",
        localisation="Nantes",
        rayon_demande_km=30,
    )
    result = list_offer_results_for_session(database_path, trace.session.id)[0]

    source_url = mark_offer_result_consulted(database_path, result.id)

    updated_result = list_offer_results_for_session(database_path, trace.session.id)[0]
    assert source_url == "https://example.test/offres/developpeur-backend-python"
    assert updated_result.consulted_at is not None


def test_offer_favorite_toggle_persists_in_stockage_applicatif(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "stockage" / "app.sqlite3"
    initialize_storage(database_path)
    trace = run_search_trace(
        database_path,
        intitule="Developpeur backend",
        localisation="Nantes",
        rayon_demande_km=30,
    )
    result = list_offer_results_for_session(database_path, trace.session.id)[0]

    assert toggle_offer_result_favorite(database_path, result.id) is True

    initialize_storage(database_path)
    favorites = list_favorite_offer_results(database_path)
    updated_result = list_offer_results_for_session(database_path, trace.session.id)[0]
    assert [favorite.result_identity for favorite in favorites] == [
        "Source demo:demo-developpeur-backend-1"
    ]
    assert updated_result.favorite_at is not None

    assert toggle_offer_result_favorite(database_path, result.id) is False
    assert list_favorite_offer_results(database_path) == []


def test_offer_hidden_toggle_persists_in_stockage_applicatif(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "stockage" / "app.sqlite3"
    initialize_storage(database_path)
    trace = run_search_trace(
        database_path,
        intitule="Developpeur backend",
        localisation="Nantes",
        rayon_demande_km=30,
    )
    result = list_offer_results_for_session(database_path, trace.session.id)[0]

    assert toggle_offer_result_hidden(database_path, result.id) is True

    initialize_storage(database_path)
    hidden_results = list_hidden_offer_results(database_path)
    updated_result = list_offer_results_for_session(database_path, trace.session.id)[0]
    assert [hidden.result_identity for hidden in hidden_results] == [
        "Source demo:demo-developpeur-backend-1"
    ]
    assert updated_result.hidden_at is not None

    assert toggle_offer_result_hidden(database_path, result.id) is False
    assert list_hidden_offer_results(database_path) == []


def test_hidden_offer_results_are_sorted_by_hidden_date(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "stockage" / "app.sqlite3"
    initialize_storage(database_path)
    trace = run_search_trace(
        database_path,
        intitule="Developpeur backend",
        localisation="Nantes",
        rayon_demande_km=30,
    )
    results = list_offer_results_for_session(database_path, trace.session.id)
    python_result = results[0]
    data_result = results[2]
    toggle_offer_result_hidden(database_path, python_result.id)
    toggle_offer_result_hidden(database_path, data_result.id)

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE offer_user_states
            SET hidden_at = ?
            WHERE result_identity = ?
            """,
            ("2026-05-10T10:00:00+00:00", python_result.result_identity),
        )
        connection.execute(
            """
            UPDATE offer_user_states
            SET hidden_at = ?
            WHERE result_identity = ?
            """,
            ("2026-05-10T11:00:00+00:00", data_result.result_identity),
        )

    hidden_results = list_hidden_offer_results(database_path)

    assert [result.title for result in hidden_results] == [
        "Developpeur backend Data",
        "Developpeur backend Python",
    ]


def test_favorite_offer_results_support_both_tri_favoris_modes(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "stockage" / "app.sqlite3"
    initialize_storage(database_path)
    trace = run_search_trace(
        database_path,
        intitule="Developpeur backend",
        localisation="Nantes",
        rayon_demande_km=30,
    )
    results = list_offer_results_for_session(database_path, trace.session.id)
    python_result = results[0]
    data_result = results[2]
    toggle_offer_result_favorite(database_path, python_result.id)
    toggle_offer_result_favorite(database_path, data_result.id)

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE offer_user_states
            SET favorite_at = ?
            WHERE result_identity = ?
            """,
            ("2026-05-10T10:00:00+00:00", python_result.result_identity),
        )
        connection.execute(
            """
            UPDATE offer_user_states
            SET favorite_at = ?
            WHERE result_identity = ?
            """,
            ("2026-05-10T11:00:00+00:00", data_result.result_identity),
        )

    favorites_by_favorite_date = list_favorite_offer_results(
        database_path, sort="favorite_at"
    )
    favorites_by_publication_date = list_favorite_offer_results(
        database_path, sort="published_at"
    )

    assert [result.title for result in favorites_by_favorite_date] == [
        "Developpeur backend Data",
        "Developpeur backend Python",
    ]
    assert [result.title for result in favorites_by_publication_date] == [
        "Developpeur backend Python",
        "Developpeur backend Data",
    ]
