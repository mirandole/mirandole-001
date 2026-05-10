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
class RecentSearch:
    id: int
    intitule: str
    localisation: str
    rayon_demande_km: int
    last_session_id: int
    last_used_at: str


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
    is_new: bool
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
            CREATE TABLE IF NOT EXISTS recent_searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                intitule TEXT NOT NULL,
                localisation TEXT NOT NULL,
                rayon_demande_km INTEGER NOT NULL,
                normalized_key TEXT NOT NULL UNIQUE,
                last_session_id INTEGER NOT NULL REFERENCES search_sessions(id),
                last_used_at TEXT NOT NULL
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
                is_new INTEGER NOT NULL DEFAULT 0,
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
        _ensure_column(
            connection, "offer_results", "is_new", "INTEGER NOT NULL DEFAULT 0"
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
        _upsert_recent_search(
            connection,
            intitule=intitule,
            localisation=localisation,
            rayon_demande_km=rayon_demande_km,
            last_session_id=session_id,
            last_used_at=created_at,
        )

    return SearchSession(
        id=session_id,
        intitule=intitule,
        localisation=localisation,
        rayon_demande_km=rayon_demande_km,
        created_at=created_at,
    )


def _upsert_recent_search(
    connection: sqlite3.Connection,
    *,
    intitule: str,
    localisation: str,
    rayon_demande_km: int,
    last_session_id: int,
    last_used_at: str,
) -> None:
    connection.execute(
        """
        INSERT INTO recent_searches (
            intitule,
            localisation,
            rayon_demande_km,
            normalized_key,
            last_session_id,
            last_used_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(normalized_key) DO UPDATE SET
            intitule = excluded.intitule,
            localisation = excluded.localisation,
            rayon_demande_km = excluded.rayon_demande_km,
            last_session_id = excluded.last_session_id,
            last_used_at = excluded.last_used_at
        """,
        (
            intitule,
            localisation,
            rayon_demande_km,
            _recent_search_key(
                intitule=intitule,
                localisation=localisation,
                rayon_demande_km=rayon_demande_km,
            ),
            last_session_id,
            last_used_at,
        ),
    )
    old_rows = connection.execute(
        """
        SELECT id
        FROM recent_searches
        ORDER BY last_session_id DESC
        LIMIT -1 OFFSET 10
        """
    ).fetchall()
    if old_rows:
        connection.executemany(
            "DELETE FROM recent_searches WHERE id = ?",
            [(row["id"],) for row in old_rows],
        )


def _recent_search_key(
    *, intitule: str, localisation: str, rayon_demande_km: int
) -> str:
    return "|".join(
        (
            " ".join(intitule.casefold().split()),
            " ".join(localisation.casefold().split()),
            str(rayon_demande_km),
        )
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
                is_new,
                inactive
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    int(result.is_new),
                    int(result.inactive),
                )
                for result in results
            ],
        )


def find_previous_session_for_same_recherche(
    database_path: Path,
    *,
    session_id: int,
    intitule: str,
    localisation: str,
    rayon_demande_km: int,
) -> SearchSession | None:
    with _connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT id, intitule, localisation, rayon_demande_km, created_at
            FROM search_sessions
            WHERE id < ?
              AND lower(intitule) = lower(?)
              AND lower(localisation) = lower(?)
              AND rayon_demande_km = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (session_id, intitule, localisation, rayon_demande_km),
        ).fetchone()

    if row is None:
        return None

    return SearchSession(
        id=row["id"],
        intitule=row["intitule"],
        localisation=row["localisation"],
        rayon_demande_km=row["rayon_demande_km"],
        created_at=row["created_at"],
    )


def list_result_identities_for_session(
    database_path: Path, session_id: int
) -> set[str]:
    with _connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT result_identity
            FROM offer_results
            WHERE session_id = ?
              AND inactive = 0
            """,
            (session_id,),
        ).fetchall()

    return {row["result_identity"] for row in rows}


def save_inactive_offer_results_for_missing_identities(
    database_path: Path,
    *,
    session_id: int,
    recherche: SearchSession,
    successful_source_names: set[str],
    active_result_identities: set[str],
) -> None:
    if not successful_source_names:
        return

    with _connect(database_path) as connection:
        placeholders = ", ".join("?" for _ in successful_source_names)
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
                latest_offer_results.is_new,
                latest_offer_results.inactive,
                NULL AS consulted_at,
                NULL AS favorite_at
            FROM offer_results AS latest_offer_results
            INNER JOIN (
                SELECT offer_results.result_identity, MAX(offer_results.id) AS id
                FROM offer_results
                INNER JOIN search_sessions
                    ON search_sessions.id = offer_results.session_id
                WHERE search_sessions.id < ?
                  AND lower(search_sessions.intitule) = lower(?)
                  AND lower(search_sessions.localisation) = lower(?)
                  AND search_sessions.rayon_demande_km = ?
                  AND offer_results.source_name IN ({placeholders})
                GROUP BY offer_results.result_identity
            ) AS latest_ids
                ON latest_ids.id = latest_offer_results.id
            WHERE latest_offer_results.inactive = 0
            """,
            (
                session_id,
                recherche.intitule,
                recherche.localisation,
                recherche.rayon_demande_km,
                *successful_source_names,
            ),
        ).fetchall()

        missing_results = [
            _stored_offer_result_from_row(row)
            for row in rows
            if row["result_identity"] not in active_result_identities
        ]
        if not missing_results:
            return

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
                is_new,
                inactive
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 1)
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
                )
                for result in missing_results
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


def list_recent_searches(database_path: Path, *, limit: int = 10) -> list[RecentSearch]:
    with _connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                intitule,
                localisation,
                rayon_demande_km,
                last_session_id,
                last_used_at
            FROM recent_searches
            ORDER BY last_session_id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [
        RecentSearch(
            id=row["id"],
            intitule=row["intitule"],
            localisation=row["localisation"],
            rayon_demande_km=row["rayon_demande_km"],
            last_session_id=row["last_session_id"],
            last_used_at=row["last_used_at"],
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
                offer_results.is_new,
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
                latest_offer_results.is_new,
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
        is_new=bool(row["is_new"]),
        inactive=bool(row["inactive"]),
        consulted_at=row["consulted_at"],
        favorite_at=row["favorite_at"],
    )


def _now_isoformat() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
