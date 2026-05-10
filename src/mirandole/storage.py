from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from json import dumps, loads
from pathlib import Path


@dataclass(frozen=True)
class SearchSession:
    id: int
    intitule: str
    localisation: str
    rayon_demande_km: int
    created_at: str


@dataclass(frozen=True)
class StoredOfferResult:
    id: int
    session_id: int
    source_name: str
    source_radius_km: int
    result_identity: str
    title: str
    company: str
    city: str
    published_at: str | None
    contract_type: str
    salary: str | None
    description_source: str | None
    skill_tags: tuple[str, ...]
    experience_level: str
    diploma_level: str
    source_url: str
    remote_text: str | None
    inactive: bool
    consulted_at: str | None = None
    favorite_at: str | None = None


@dataclass(frozen=True)
class SourceFailure:
    id: int
    session_id: int
    source_name: str
    message: str


def initialize_storage(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS app_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO app_metadata (key, value)
            VALUES ('schema_version', '1')
            ON CONFLICT(key) DO NOTHING
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS search_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                intitule TEXT NOT NULL,
                localisation TEXT NOT NULL,
                rayon_demande_km INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS offer_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES search_sessions(id),
                source_name TEXT NOT NULL,
                source_radius_km INTEGER NOT NULL,
                result_identity TEXT NOT NULL,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                city TEXT NOT NULL,
                published_at TEXT,
                contract_type TEXT NOT NULL,
                salary TEXT,
                description_source TEXT,
                skill_tags TEXT NOT NULL DEFAULT '[]',
                experience_level TEXT NOT NULL DEFAULT 'Non precise',
                diploma_level TEXT NOT NULL DEFAULT 'Non precise',
                source_url TEXT NOT NULL,
                remote_text TEXT,
                inactive INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS source_failures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES search_sessions(id),
                source_name TEXT NOT NULL,
                message TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS offer_user_states (
                result_identity TEXT PRIMARY KEY,
                consulted_at TEXT,
                favorite_at TEXT
            )
            """
        )
        _ensure_column(connection, "offer_results", "description_source", "TEXT")
        _ensure_column(
            connection, "offer_results", "skill_tags", "TEXT NOT NULL DEFAULT '[]'"
        )
        _ensure_column(
            connection,
            "offer_results",
            "experience_level",
            "TEXT NOT NULL DEFAULT 'Non precise'",
        )
        _ensure_column(
            connection,
            "offer_results",
            "diploma_level",
            "TEXT NOT NULL DEFAULT 'Non precise'",
        )


def _connect(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def _ensure_column(
    connection: sqlite3.Connection, table_name: str, column_name: str, definition: str
) -> None:
    columns = {
        row[1]
        for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name not in columns:
        connection.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
        )


def create_search_session(
    database_path: Path,
    *,
    intitule: str,
    localisation: str,
    rayon_demande_km: int,
) -> SearchSession:
    created_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    with _connect(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO search_sessions (
                intitule, localisation, rayon_demande_km, created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (intitule, localisation, rayon_demande_km, created_at),
        )
        session_id = int(cursor.lastrowid)

    return SearchSession(
        id=session_id,
        intitule=intitule,
        localisation=localisation,
        rayon_demande_km=rayon_demande_km,
        created_at=created_at,
    )


def save_offer_results(
    database_path: Path,
    *,
    session_id: int,
    results: list[StoredOfferResult],
) -> None:
    with _connect(database_path) as connection:
        connection.executemany(
            """
            INSERT INTO offer_results (
                session_id,
                source_name,
                source_radius_km,
                result_identity,
                title,
                company,
                city,
                published_at,
                contract_type,
                salary,
                description_source,
                skill_tags,
                experience_level,
                diploma_level,
                source_url,
                remote_text,
                inactive
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    session_id,
                    result.source_name,
                    result.source_radius_km,
                    result.result_identity,
                    result.title,
                    result.company,
                    result.city,
                    result.published_at,
                    result.contract_type,
                    result.salary,
                    result.description_source,
                    dumps(list(result.skill_tags)),
                    result.experience_level,
                    result.diploma_level,
                    result.source_url,
                    result.remote_text,
                    int(result.inactive),
                )
                for result in results
            ],
        )


def save_source_failure(
    database_path: Path,
    *,
    session_id: int,
    source_name: str,
    message: str,
) -> None:
    with _connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO source_failures (session_id, source_name, message)
            VALUES (?, ?, ?)
            """,
            (session_id, source_name, message),
        )


def list_search_sessions(database_path: Path) -> list[SearchSession]:
    with _connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT id, intitule, localisation, rayon_demande_km, created_at
            FROM search_sessions
            ORDER BY id DESC
            """
        ).fetchall()

    return [
        SearchSession(
            id=row["id"],
            intitule=row["intitule"],
            localisation=row["localisation"],
            rayon_demande_km=row["rayon_demande_km"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


def list_offer_results_for_session(
    database_path: Path, session_id: int
) -> list[StoredOfferResult]:
    with _connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT
                offer_results.id,
                offer_results.session_id,
                offer_results.source_name,
                offer_results.source_radius_km,
                offer_results.result_identity,
                offer_results.title,
                offer_results.company,
                offer_results.city,
                offer_results.published_at,
                offer_results.contract_type,
                offer_results.salary,
                offer_results.description_source,
                offer_results.skill_tags,
                offer_results.experience_level,
                offer_results.diploma_level,
                offer_results.source_url,
                offer_results.remote_text,
                offer_results.inactive,
                offer_user_states.consulted_at,
                offer_user_states.favorite_at
            FROM offer_results
            LEFT JOIN offer_user_states
                ON offer_user_states.result_identity = offer_results.result_identity
            WHERE offer_results.session_id = ?
            ORDER BY
                offer_results.published_at IS NULL ASC,
                offer_results.published_at DESC,
                offer_results.id ASC
            """,
            (session_id,),
        ).fetchall()

    return [_stored_offer_result_from_row(row) for row in rows]


def mark_offer_result_consulted(
    database_path: Path, offer_result_id: int
) -> str | None:
    consulted_at = _now_isoformat()
    with _connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT result_identity, source_url
            FROM offer_results
            WHERE id = ?
            """,
            (offer_result_id,),
        ).fetchone()
        if row is None:
            return None

        connection.execute(
            """
            INSERT INTO offer_user_states (result_identity, consulted_at)
            VALUES (?, ?)
            ON CONFLICT(result_identity) DO UPDATE SET
                consulted_at = excluded.consulted_at
            """,
            (row["result_identity"], consulted_at),
        )

    return str(row["source_url"])


def toggle_offer_result_favorite(
    database_path: Path, offer_result_id: int
) -> bool | None:
    with _connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT
                offer_results.result_identity,
                offer_user_states.favorite_at
            FROM offer_results
            LEFT JOIN offer_user_states
                ON offer_user_states.result_identity = offer_results.result_identity
            WHERE offer_results.id = ?
            """,
            (offer_result_id,),
        ).fetchone()
        if row is None:
            return None

        is_favorite = row["favorite_at"] is not None
        next_favorite_at = None if is_favorite else _now_isoformat()
        connection.execute(
            """
            INSERT INTO offer_user_states (result_identity, favorite_at)
            VALUES (?, ?)
            ON CONFLICT(result_identity) DO UPDATE SET
                favorite_at = excluded.favorite_at
            """,
            (row["result_identity"], next_favorite_at),
        )

    return not is_favorite


def list_favorite_offer_results(
    database_path: Path, *, sort: str = "favorite_at"
) -> list[StoredOfferResult]:
    order_by = """
        offer_user_states.favorite_at DESC,
        latest_offer_results.id DESC
    """
    if sort == "published_at":
        order_by = """
            latest_offer_results.published_at IS NULL ASC,
            latest_offer_results.published_at DESC,
            offer_user_states.favorite_at DESC,
            latest_offer_results.id DESC
        """

    with _connect(database_path) as connection:
        rows = connection.execute(
            f"""
            SELECT
                latest_offer_results.id,
                latest_offer_results.session_id,
                latest_offer_results.source_name,
                latest_offer_results.source_radius_km,
                latest_offer_results.result_identity,
                latest_offer_results.title,
                latest_offer_results.company,
                latest_offer_results.city,
                latest_offer_results.published_at,
                latest_offer_results.contract_type,
                latest_offer_results.salary,
                latest_offer_results.description_source,
                latest_offer_results.skill_tags,
                latest_offer_results.experience_level,
                latest_offer_results.diploma_level,
                latest_offer_results.source_url,
                latest_offer_results.remote_text,
                latest_offer_results.inactive,
                offer_user_states.consulted_at,
                offer_user_states.favorite_at
            FROM offer_results AS latest_offer_results
            INNER JOIN (
                SELECT result_identity, MAX(id) AS id
                FROM offer_results
                GROUP BY result_identity
            ) AS latest_ids
                ON latest_ids.id = latest_offer_results.id
            INNER JOIN offer_user_states
                ON offer_user_states.result_identity =
                    latest_offer_results.result_identity
            WHERE offer_user_states.favorite_at IS NOT NULL
            ORDER BY {order_by}
            """
        ).fetchall()

    return [_stored_offer_result_from_row(row) for row in rows]


def list_source_failures_for_session(
    database_path: Path, session_id: int
) -> list[SourceFailure]:
    with _connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT id, session_id, source_name, message
            FROM source_failures
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        ).fetchall()

    return [
        SourceFailure(
            id=row["id"],
            session_id=row["session_id"],
            source_name=row["source_name"],
            message=row["message"],
        )
        for row in rows
    ]


def _stored_offer_result_from_row(row: sqlite3.Row) -> StoredOfferResult:
    return StoredOfferResult(
        id=row["id"],
        session_id=row["session_id"],
        source_name=row["source_name"],
        source_radius_km=row["source_radius_km"],
        result_identity=row["result_identity"],
        title=row["title"],
        company=row["company"],
        city=row["city"],
        published_at=row["published_at"],
        contract_type=row["contract_type"],
        salary=row["salary"],
        description_source=row["description_source"],
        skill_tags=tuple(loads(row["skill_tags"])),
        experience_level=row["experience_level"],
        diploma_level=row["diploma_level"],
        source_url=row["source_url"],
        remote_text=row["remote_text"],
        inactive=bool(row["inactive"]),
        consulted_at=row["consulted_at"],
        favorite_at=row["favorite_at"],
    )


def _now_isoformat() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
