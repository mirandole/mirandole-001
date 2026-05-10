import sqlite3
from pathlib import Path

from mirandole.search import DemoSourceConnector, run_search_trace
from mirandole.storage import (
    initialize_storage,
    list_favorite_offer_results,
    list_offer_results_for_session,
    list_search_sessions,
    list_source_failures_for_session,
    mark_offer_result_consulted,
    toggle_offer_result_favorite,
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
        "2026-05-08",
        "2026-05-07",
        "2026-05-06",
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
