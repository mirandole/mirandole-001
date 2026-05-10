from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mirandole.app import create_app
from mirandole.config import ConfigError, Settings


def make_settings(database_path: Path, *, cookie_secure: bool = False) -> Settings:
    return Settings(
        password="correct horse battery staple",
        session_secret="x" * 32,
        database_path=database_path,
        cookie_secure=cookie_secure,
    )


def test_protected_home_redirects_to_login(tmp_path: Path) -> None:
    app = create_app(make_settings(tmp_path / "app.sqlite3"))

    with TestClient(app) as client:
        response = client.get("/", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_utilisateur_principal_can_login_and_access_home(tmp_path: Path) -> None:
    app = create_app(make_settings(tmp_path / "app.sqlite3"))

    with TestClient(app) as client:
        login_response = client.post(
            "/login",
            data={"password": "correct horse battery staple"},
            follow_redirects=False,
        )
        home_response = client.get("/")

    assert login_response.status_code == 303
    assert login_response.headers["location"] == "/"
    assert home_response.status_code == 200
    assert "Recherche d'offres d'emploi" in home_response.text
    assert "Rayon demande" in home_response.text
    assert "100 km" in home_response.text


def test_invalid_password_keeps_access_protected(tmp_path: Path) -> None:
    app = create_app(make_settings(tmp_path / "app.sqlite3"))

    with TestClient(app) as client:
        login_response = client.post("/login", data={"password": "bad password"})
        home_response = client.get("/", follow_redirects=False)

    assert login_response.status_code == 401
    assert "Mot de passe incorrect" in login_response.text
    assert home_response.status_code == 303
    assert home_response.headers["location"] == "/login"


def test_logout_removes_access_to_protected_home(tmp_path: Path) -> None:
    app = create_app(make_settings(tmp_path / "app.sqlite3"))

    with TestClient(app) as client:
        client.post(
            "/login",
            data={"password": "correct horse battery staple"},
            follow_redirects=False,
        )
        logout_response = client.post("/logout", follow_redirects=False)
        home_response = client.get("/", follow_redirects=False)

    assert logout_response.status_code == 303
    assert logout_response.headers["location"] == "/login"
    assert home_response.status_code == 303
    assert home_response.headers["location"] == "/login"


def test_session_cookie_has_deployment_defaults(tmp_path: Path) -> None:
    app = create_app(make_settings(tmp_path / "app.sqlite3", cookie_secure=True))

    with TestClient(app, base_url="https://testserver") as client:
        response = client.post(
            "/login",
            data={"password": "correct horse battery staple"},
            follow_redirects=False,
        )

    set_cookie = response.headers["set-cookie"].lower()
    assert "mirandole_session=" in set_cookie
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie
    assert "secure" in set_cookie


def test_sqlite_stockage_applicatif_is_initialized(tmp_path: Path) -> None:
    database_path = tmp_path / "state" / "mirandole.sqlite3"
    app = create_app(make_settings(database_path))

    with TestClient(app):
        pass

    assert database_path.exists()


def test_utilisateur_principal_can_submit_recherche_offres(
    tmp_path: Path,
) -> None:
    app = create_app(make_settings(tmp_path / "app.sqlite3"))

    with TestClient(app) as client:
        client.post(
            "/login",
            data={"password": "correct horse battery staple"},
            follow_redirects=False,
        )
        response = client.post(
            "/",
            data={
                "intitule": "Developpeur backend",
                "localisation": "Nantes",
                "rayon_demande_km": "30",
            },
            follow_redirects=True,
        )

    assert response.status_code == 200
    assert "Session de recherche #1" in response.text
    assert "Developpeur backend Python" in response.text
    assert "Atelier Hexagone" in response.text
    assert "Identite de resultat Source demo:demo-developpeur-backend-1" in (
        response.text
    )
    assert "Rayon source 50 km" in response.text


def test_echec_de_source_is_visible_without_failing_session(
    tmp_path: Path,
) -> None:
    app = create_app(make_settings(tmp_path / "app.sqlite3"))

    with TestClient(app) as client:
        client.post(
            "/login",
            data={"password": "correct horse battery staple"},
            follow_redirects=False,
        )
        response = client.post(
            "/",
            data={
                "intitule": "Echec source",
                "localisation": "Nantes",
                "rayon_demande_km": "20",
            },
            follow_redirects=True,
        )

    assert response.status_code == 200
    assert "Session de recherche #1" in response.text
    assert "Echec de source - Source demo" in response.text
    assert "Aucun Resultat d'offre" in response.text


def test_missing_password_configuration_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MIRANDOLE_PASSWORD", raising=False)
    monkeypatch.setenv("MIRANDOLE_SESSION_SECRET", "x" * 32)
    monkeypatch.setenv("MIRANDOLE_DATABASE_PATH", "/tmp/mirandole.sqlite3")

    with pytest.raises(ConfigError, match="MIRANDOLE_PASSWORD is required"):
        Settings.from_env()


def test_invalid_password_configuration_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MIRANDOLE_PASSWORD", "too-short")
    monkeypatch.setenv("MIRANDOLE_SESSION_SECRET", "x" * 32)
    monkeypatch.setenv("MIRANDOLE_DATABASE_PATH", "/tmp/mirandole.sqlite3")

    with pytest.raises(ConfigError, match="at least 12 characters"):
        Settings.from_env()
