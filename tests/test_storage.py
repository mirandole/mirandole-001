import sqlite3
from pathlib import Path

from mirandole.search import DemoSourceConnector, run_search_trace
from mirandole.storage import (
    initialize_storage,
    list_offer_results_for_session,
    list_search_sessions,
    list_source_failures_for_session,
)


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
    assert trace.result_count == 3
    assert len(results) == 3
    assert results[0].source_name == "Source demo"
    assert results[0].result_identity == "Source demo:demo-developpeur-backend-1"
    assert results[0].title == "Developpeur backend Python"
    assert results[0].company == "Atelier Hexagone"
    assert results[0].city == "Nantes"
    assert results[0].published_at == "2026-05-09"
    assert results[0].contract_type == "CDI"
    assert results[0].salary == "45 000 - 55 000 EUR"
    assert results[0].source_url == (
        "https://example.test/offres/developpeur-backend-python"
    )
    assert results[0].remote_text == "Teletravail partiel"


def test_demo_source_maps_rayon_demande_to_supported_rayon_source() -> None:
    connector = DemoSourceConnector()

    assert connector.map_rayon_source(10) == 20
    assert connector.map_rayon_source(20) == 20
    assert connector.map_rayon_source(30) == 50
    assert connector.map_rayon_source(50) == 50
    assert connector.map_rayon_source(100) == 100


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
        "2026-05-07",
        None,
    ]


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
