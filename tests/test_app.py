from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mirandole.app import create_app
from mirandole.config import ConfigError, Settings


def make_settings(
    database_path: Path, *, cookie_secure: bool = False, prod: bool = False
) -> Settings:
    return Settings(
        password="correct horse battery staple",
        session_secret="x" * 32,
        database_path=database_path,
        prod=prod,
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
    assert "Tags de competence: API, FastAPI, Python" in response.text
    assert "Niveau d'experience demande: Avance" in response.text
    assert "Niveau de diplome demande: Bac+5" in response.text
    assert "Remuneration indiquee: 45 000 - 55 000 EUR" in response.text
    assert "Teletravail partiel" in response.text
    assert "Identite de resultat Source demo:demo-developpeur-backend-1" in (
        response.text
    )
    assert 'href="/offer-results/1/open"' in response.text
    assert 'target="_blank"' in response.text
    assert 'rel="external noopener noreferrer"' in response.text
    assert "Rayon source 50 km" in response.text
    assert "Developpeur backend Stage web" not in response.text
    assert "Developpeur backend Alternance cloud" not in response.text


def test_prod_hides_existing_mock_offers_from_search_session(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "app.sqlite3"
    app = create_app(make_settings(database_path))

    with TestClient(app) as client:
        client.post(
            "/login",
            data={"password": "correct horse battery staple"},
            follow_redirects=False,
        )
        client.post(
            "/",
            data={
                "intitule": "Administrateur linux",
                "localisation": "Nantes",
                "rayon_demande_km": "30",
            },
            follow_redirects=False,
        )

    prod_app = create_app(make_settings(database_path, prod=True))
    with TestClient(prod_app) as client:
        client.post(
            "/login",
            data={"password": "correct horse battery staple"},
            follow_redirects=False,
        )
        response = client.get("/", params={"session_id": "1"})

    assert response.status_code == 200
    assert "https://example.test/offres/administrateur-linux-data" not in response.text
    assert "Administrateur linux Data" not in response.text
    assert "Aucun Resultat d'offre" in response.text


def test_prod_hides_existing_mock_offers_from_favorites(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "app.sqlite3"
    app = create_app(make_settings(database_path))

    with TestClient(app) as client:
        client.post(
            "/login",
            data={"password": "correct horse battery staple"},
            follow_redirects=False,
        )
        client.post(
            "/",
            data={
                "intitule": "Administrateur linux",
                "localisation": "Nantes",
                "rayon_demande_km": "30",
            },
            follow_redirects=False,
        )
        client.post(
            "/offer-results/2/favorite",
            data={"return_to": "/?session_id=1"},
            follow_redirects=False,
        )

    prod_app = create_app(make_settings(database_path, prod=True))
    with TestClient(prod_app) as client:
        client.post(
            "/login",
            data={"password": "correct horse battery staple"},
            follow_redirects=False,
        )
        response = client.get("/favorites")

    assert response.status_code == 200
    assert "https://example.test/offres/administrateur-linux-data" not in response.text
    assert "Administrateur linux Data" not in response.text


def test_home_displays_recent_searches_without_duplicates(tmp_path: Path) -> None:
    app = create_app(make_settings(tmp_path / "app.sqlite3"))

    with TestClient(app) as client:
        client.post(
            "/login",
            data={"password": "correct horse battery staple"},
            follow_redirects=False,
        )
        for index in range(11):
            client.post(
                "/",
                data={
                    "intitule": f"Developpeur {index}",
                    "localisation": "Nantes",
                    "rayon_demande_km": "20",
                },
                follow_redirects=False,
            )
        response = client.post(
            "/",
            data={
                "intitule": "Developpeur 1",
                "localisation": "Nantes",
                "rayon_demande_km": "20",
            },
            follow_redirects=True,
        )

    assert response.status_code == 200
    assert "Recherches recentes" in response.text
    assert "Derniere Session de recherche #12" in response.text
    assert response.text.count('value="Developpeur 1"') == 1
    assert 'value="Developpeur 0"' not in response.text


def test_filtres_de_resultats_are_applied_after_aggregation(
    tmp_path: Path,
) -> None:
    app = create_app(make_settings(tmp_path / "app.sqlite3"))

    with TestClient(app) as client:
        client.post(
            "/login",
            data={"password": "correct horse battery staple"},
            follow_redirects=False,
        )
        client.post(
            "/",
            data={
                "intitule": "Developpeur backend",
                "localisation": "Nantes",
                "rayon_demande_km": "30",
            },
            follow_redirects=False,
        )
        response = client.get(
            "/",
            params={
                "session_id": "1",
                "contract_type": "Stage",
                "experience_level": "Non precise",
                "diploma_level": "Bac+2",
            },
        )

    assert response.status_code == 200
    assert "Developpeur backend Stage web" in response.text
    assert "Developpeur backend Python" not in response.text
    assert "Remuneration indiquee" not in response.text


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


def test_opening_resultat_offre_marks_offre_consultee(tmp_path: Path) -> None:
    app = create_app(make_settings(tmp_path / "app.sqlite3"))

    with TestClient(app) as client:
        client.post(
            "/login",
            data={"password": "correct horse battery staple"},
            follow_redirects=False,
        )
        client.post(
            "/",
            data={
                "intitule": "Developpeur backend",
                "localisation": "Nantes",
                "rayon_demande_km": "30",
            },
            follow_redirects=False,
        )
        open_response = client.get("/offer-results/1/open", follow_redirects=False)
        home_response = client.get("/", params={"session_id": "1"})

    assert open_response.status_code == 303
    assert open_response.headers["location"] == (
        "https://example.test/offres/developpeur-backend-python"
    )
    assert "Offre consultee" in home_response.text


def test_favorite_toggle_persists_and_vue_favoris_lists_offres_favorites(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "app.sqlite3"
    app = create_app(make_settings(database_path))

    with TestClient(app) as client:
        client.post(
            "/login",
            data={"password": "correct horse battery staple"},
            follow_redirects=False,
        )
        client.post(
            "/",
            data={
                "intitule": "Developpeur backend",
                "localisation": "Nantes",
                "rayon_demande_km": "30",
            },
            follow_redirects=False,
        )
        toggle_response = client.post(
            "/offer-results/1/favorite",
            data={"return_to": "/?session_id=1"},
            follow_redirects=False,
        )
        home_response = client.get("/", params={"session_id": "1"})

    assert toggle_response.status_code == 303
    assert toggle_response.headers["location"] == "/?session_id=1"
    assert "Retirer des Offres favorites" in home_response.text

    restarted_app = create_app(make_settings(database_path))
    with TestClient(restarted_app) as client:
        client.post(
            "/login",
            data={"password": "correct horse battery staple"},
            follow_redirects=False,
        )
        favorites_response = client.get("/favorites")

    assert favorites_response.status_code == 200
    assert "Vue favoris" in favorites_response.text
    assert "Developpeur backend Python" in favorites_response.text
    assert 'href="/offer-results/1/open"' in favorites_response.text
    assert 'target="_blank"' in favorites_response.text
    assert 'rel="external noopener noreferrer"' in favorites_response.text
    assert "Ajoutee aux Offres favorites" in favorites_response.text
    assert "Developpeur backend Data" not in favorites_response.text


def test_vue_favoris_uses_default_tri_favoris(tmp_path: Path) -> None:
    app = create_app(make_settings(tmp_path / "app.sqlite3"))

    with TestClient(app) as client:
        client.post(
            "/login",
            data={"password": "correct horse battery staple"},
            follow_redirects=False,
        )
        client.post(
            "/",
            data={
                "intitule": "Developpeur backend",
                "localisation": "Nantes",
                "rayon_demande_km": "30",
            },
            follow_redirects=False,
        )
        client.post(
            "/offer-results/1/favorite",
            data={"return_to": "/?session_id=1"},
            follow_redirects=False,
        )
        response = client.get("/favorites")

    assert response.status_code == 200
    assert '<option value="favorite_at" selected>' in response.text


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


def test_france_travail_credentials_are_read_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MIRANDOLE_PASSWORD", "correct horse battery staple")
    monkeypatch.setenv("MIRANDOLE_SESSION_SECRET", "x" * 32)
    monkeypatch.setenv("MIRANDOLE_DATABASE_PATH", "/tmp/mirandole.sqlite3")
    monkeypatch.setenv("MIRANDOLE_FRANCE_TRAVAIL_ENABLED", "true")
    monkeypatch.setenv("MIRANDOLE_FRANCE_TRAVAIL_CLIENT_ID", "client-id")
    monkeypatch.setenv("MIRANDOLE_FRANCE_TRAVAIL_CLIENT_SECRET", "client-secret")

    settings = Settings.from_env()

    assert settings.france_travail_enabled is True
    assert settings.france_travail_client_id == "client-id"
    assert settings.france_travail_client_secret == "client-secret"


def test_prod_configuration_is_read_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MIRANDOLE_PASSWORD", "correct horse battery staple")
    monkeypatch.setenv("MIRANDOLE_SESSION_SECRET", "x" * 32)
    monkeypatch.setenv("MIRANDOLE_DATABASE_PATH", "/tmp/mirandole.sqlite3")
    monkeypatch.setenv("PROD", "true")

    settings = Settings.from_env()

    assert settings.prod is True


def test_prod_configuration_must_be_boolean(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MIRANDOLE_PASSWORD", "correct horse battery staple")
    monkeypatch.setenv("MIRANDOLE_SESSION_SECRET", "x" * 32)
    monkeypatch.setenv("MIRANDOLE_DATABASE_PATH", "/tmp/mirandole.sqlite3")
    monkeypatch.setenv("PROD", "yes")

    with pytest.raises(ConfigError, match="PROD must be true or false"):
        Settings.from_env()


def test_enabled_france_travail_requires_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MIRANDOLE_PASSWORD", "correct horse battery staple")
    monkeypatch.setenv("MIRANDOLE_SESSION_SECRET", "x" * 32)
    monkeypatch.setenv("MIRANDOLE_DATABASE_PATH", "/tmp/mirandole.sqlite3")
    monkeypatch.setenv("MIRANDOLE_FRANCE_TRAVAIL_ENABLED", "true")
    monkeypatch.delenv("MIRANDOLE_FRANCE_TRAVAIL_CLIENT_ID", raising=False)
    monkeypatch.delenv("MIRANDOLE_FRANCE_TRAVAIL_CLIENT_SECRET", raising=False)

    with pytest.raises(ConfigError, match="CLIENT_ID is required"):
        Settings.from_env()


def test_adzuna_credentials_are_read_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MIRANDOLE_PASSWORD", "correct horse battery staple")
    monkeypatch.setenv("MIRANDOLE_SESSION_SECRET", "x" * 32)
    monkeypatch.setenv("MIRANDOLE_DATABASE_PATH", "/tmp/mirandole.sqlite3")
    monkeypatch.setenv("MIRANDOLE_ADZUNA_ENABLED", "true")
    monkeypatch.setenv("MIRANDOLE_ADZUNA_APP_ID", "app-id")
    monkeypatch.setenv("MIRANDOLE_ADZUNA_APP_KEY", "app-key")

    settings = Settings.from_env()

    assert settings.adzuna_enabled is True
    assert settings.adzuna_app_id == "app-id"
    assert settings.adzuna_app_key == "app-key"
    assert settings.adzuna_pages_per_search == 4


def test_adzuna_pages_per_search_is_read_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MIRANDOLE_PASSWORD", "correct horse battery staple")
    monkeypatch.setenv("MIRANDOLE_SESSION_SECRET", "x" * 32)
    monkeypatch.setenv("MIRANDOLE_DATABASE_PATH", "/tmp/mirandole.sqlite3")
    monkeypatch.setenv("MIRANDOLE_ADZUNA_PAGES_PER_SEARCH", "7")

    settings = Settings.from_env()

    assert settings.adzuna_pages_per_search == 7


@pytest.mark.parametrize("value", ["0", "-1", "many"])
def test_adzuna_pages_per_search_must_be_positive_integer(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv("MIRANDOLE_PASSWORD", "correct horse battery staple")
    monkeypatch.setenv("MIRANDOLE_SESSION_SECRET", "x" * 32)
    monkeypatch.setenv("MIRANDOLE_DATABASE_PATH", "/tmp/mirandole.sqlite3")
    monkeypatch.setenv("MIRANDOLE_ADZUNA_PAGES_PER_SEARCH", value)

    with pytest.raises(ConfigError, match="MIRANDOLE_ADZUNA_PAGES_PER_SEARCH"):
        Settings.from_env()


def test_enabled_adzuna_requires_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MIRANDOLE_PASSWORD", "correct horse battery staple")
    monkeypatch.setenv("MIRANDOLE_SESSION_SECRET", "x" * 32)
    monkeypatch.setenv("MIRANDOLE_DATABASE_PATH", "/tmp/mirandole.sqlite3")
    monkeypatch.setenv("MIRANDOLE_ADZUNA_ENABLED", "true")
    monkeypatch.delenv("MIRANDOLE_ADZUNA_APP_ID", raising=False)
    monkeypatch.delenv("MIRANDOLE_ADZUNA_APP_KEY", raising=False)

    with pytest.raises(ConfigError, match="APP_ID is required"):
        Settings.from_env()
