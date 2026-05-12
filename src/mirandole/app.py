from __future__ import annotations

import logging
import os
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import Depends, FastAPI, Form, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from mirandole.config import Settings
from mirandole.enrichment import (
    DEFAULT_INCLUDED_CONTRACT_TYPES,
    DIPLOMA_LEVELS,
    EXCLUDED_CONTRACT_TYPES,
    EXPERIENCE_LEVELS,
    ResultFilters,
    apply_result_filters,
    build_result_filters,
)
from mirandole.search import (
    RAYONS_DEMANDE_KM,
    build_source_connectors,
    run_search_trace,
)
from mirandole.storage import (
    SearchSession,
    StoredOfferResult,
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

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
DEMO_SOURCE_NAME = "Source demo"
MOCK_SOURCE_URL_PREFIX = "https://example.test/offres/"


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


SETTINGS_DEPENDENCY = Depends(get_settings)


def require_user(request: Request) -> None:
    if not request.session.get("authenticated"):
        raise_redirect = RedirectResponse(
            url="/login", status_code=status.HTTP_303_SEE_OTHER
        )
        raise_redirect.headers["Cache-Control"] = "no-store"
        raise _RedirectException(raise_redirect)


class _RedirectException(Exception):
    def __init__(self, response: RedirectResponse) -> None:
        self.response = response


def create_app(settings: Settings | None = None) -> FastAPI:
    _configure_logging_from_env()
    resolved_settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        initialize_storage(resolved_settings.database_path)
        yield

    app = FastAPI(title="Recherche d'offres d'emploi", lifespan=lifespan)
    app.state.settings = resolved_settings
    app.add_middleware(
        SessionMiddleware,
        secret_key=resolved_settings.session_secret,
        session_cookie="mirandole_session",
        https_only=resolved_settings.cookie_secure,
        same_site="lax",
        max_age=60 * 60 * 12,
    )

    @app.exception_handler(_RedirectException)
    async def redirect_exception_handler(
        _request: Request, exc: _RedirectException
    ) -> RedirectResponse:
        return exc.response

    @app.get("/", response_class=HTMLResponse)
    async def home(
        request: Request,
        session_id: int | None = Query(default=None),
        contract_type: Annotated[list[str] | None, Query()] = None,
        experience_level: Annotated[list[str] | None, Query()] = None,
        diploma_level: Annotated[list[str] | None, Query()] = None,
        source_name: Annotated[list[str] | None, Query()] = None,
        _authenticated: None = Depends(require_user),
        current_settings: Settings = SETTINGS_DEPENDENCY,
    ) -> HTMLResponse:
        result_filters = build_result_filters(
            contract_types=contract_type,
            experience_levels=experience_level,
            diploma_levels=diploma_level,
        )
        sessions = list_search_sessions(current_settings.database_path)
        recent_searches = list_recent_searches(current_settings.database_path)
        selected_session = _select_session(sessions, session_id)
        results = []
        source_filter_options = []
        failures = []
        if selected_session is not None:
            results = list_offer_results_for_session(
                current_settings.database_path, selected_session.id
            )
            results = _filter_prod_mock_results(results, current_settings)
            results = _filter_hidden_results(results)
            source_filter_options = _source_filter_options(results)
            results = _filter_by_source(results, source_name)
            results = apply_result_filters(results, result_filters)
            failures = list_source_failures_for_session(
                current_settings.database_path, selected_session.id
            )

        return templates.TemplateResponse(
            request,
            "home.html",
            {
                "title": "Recherche d'offres d'emploi",
                "rayons_demande_km": RAYONS_DEMANDE_KM,
                "selected_session": selected_session,
                "sessions": sessions,
                "recent_searches": recent_searches,
                "results": results,
                "filters": result_filters,
                "contract_filter_options": DEFAULT_INCLUDED_CONTRACT_TYPES
                + EXCLUDED_CONTRACT_TYPES,
                "experience_filter_options": EXPERIENCE_LEVELS,
                "diploma_filter_options": DIPLOMA_LEVELS,
                "source_filter_options": source_filter_options,
                "selected_source_names": tuple(source_name or ()),
                "failures": failures,
                "form_error": None,
            },
            headers={"Cache-Control": "no-store"},
        )

    @app.post("/", response_class=HTMLResponse, response_model=None)
    async def start_search(
        request: Request,
        intitule: str = Form(...),
        localisation: str = Form(...),
        rayon_demande_km: int = Form(...),
        _authenticated: None = Depends(require_user),
        current_settings: Settings = SETTINGS_DEPENDENCY,
    ) -> HTMLResponse | RedirectResponse:
        if rayon_demande_km not in RAYONS_DEMANDE_KM:
            sessions = list_search_sessions(current_settings.database_path)
            recent_searches = list_recent_searches(current_settings.database_path)
            return templates.TemplateResponse(
                request,
                "home.html",
                {
                    "title": "Recherche d'offres d'emploi",
                    "rayons_demande_km": RAYONS_DEMANDE_KM,
                    "selected_session": sessions[0] if sessions else None,
                    "sessions": sessions,
                    "recent_searches": recent_searches,
                    "results": [],
                    "filters": ResultFilters(),
                    "contract_filter_options": DEFAULT_INCLUDED_CONTRACT_TYPES
                    + EXCLUDED_CONTRACT_TYPES,
                    "experience_filter_options": EXPERIENCE_LEVELS,
                    "diploma_filter_options": DIPLOMA_LEVELS,
                    "source_filter_options": [],
                    "selected_source_names": (),
                    "failures": [],
                    "form_error": "Rayon demande non pris en charge.",
                },
                status_code=status.HTTP_400_BAD_REQUEST,
                headers={"Cache-Control": "no-store"},
            )

        trace = run_search_trace(
            current_settings.database_path,
            intitule=intitule,
            localisation=localisation,
            rayon_demande_km=rayon_demande_km,
            connectors=build_source_connectors(current_settings),
        )
        return RedirectResponse(
            url=f"/?session_id={trace.session.id}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    @app.get("/offer-results/{offer_result_id}/open")
    async def open_offer_result(
        offer_result_id: int,
        _authenticated: None = Depends(require_user),
        current_settings: Settings = SETTINGS_DEPENDENCY,
    ) -> RedirectResponse:
        source_url = mark_offer_result_consulted(
            current_settings.database_path, offer_result_id
        )
        if source_url is None:
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        if current_settings.prod and _is_mock_source_url(source_url):
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

        return RedirectResponse(url=source_url, status_code=status.HTTP_303_SEE_OTHER)

    @app.post("/offer-results/{offer_result_id}/favorite", response_model=None)
    async def toggle_offer_favorite(
        request: Request,
        offer_result_id: int,
        return_to: str = Form(default="/"),
        scroll_y: int | None = Form(default=None),
        _authenticated: None = Depends(require_user),
        current_settings: Settings = SETTINGS_DEPENDENCY,
    ) -> RedirectResponse | Response:
        toggle_offer_result_favorite(current_settings.database_path, offer_result_id)
        if _is_async_offer_action(request):
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        return RedirectResponse(
            url=_return_path_with_scroll(return_to, scroll_y),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    @app.post("/offer-results/{offer_result_id}/hidden", response_model=None)
    async def toggle_offer_hidden(
        request: Request,
        offer_result_id: int,
        return_to: str = Form(default="/"),
        scroll_y: int | None = Form(default=None),
        _authenticated: None = Depends(require_user),
        current_settings: Settings = SETTINGS_DEPENDENCY,
    ) -> RedirectResponse | Response:
        toggle_offer_result_hidden(current_settings.database_path, offer_result_id)
        if _is_async_offer_action(request):
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        return RedirectResponse(
            url=_return_path_with_scroll(return_to, scroll_y),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    @app.get("/favorites", response_class=HTMLResponse)
    async def favorites(
        request: Request,
        sort: str = Query(default="favorite_at"),
        _authenticated: None = Depends(require_user),
        current_settings: Settings = SETTINGS_DEPENDENCY,
    ) -> HTMLResponse:
        selected_sort = (
            sort if sort in {"favorite_at", "published_at"} else "favorite_at"
        )
        results = list_favorite_offer_results(
            current_settings.database_path, sort=selected_sort
        )
        results = _filter_prod_mock_results(results, current_settings)
        return templates.TemplateResponse(
            request,
            "favorites.html",
            {
                "title": "Vue favoris",
                "results": results,
                "sort": selected_sort,
            },
            headers={"Cache-Control": "no-store"},
        )

    @app.get("/hidden", response_class=HTMLResponse)
    async def hidden(
        request: Request,
        _authenticated: None = Depends(require_user),
        current_settings: Settings = SETTINGS_DEPENDENCY,
    ) -> HTMLResponse:
        results = list_hidden_offer_results(current_settings.database_path)
        results = _filter_prod_mock_results(results, current_settings)
        return templates.TemplateResponse(
            request,
            "hidden.html",
            {
                "title": "Offres masquees",
                "results": results,
            },
            headers={"Cache-Control": "no-store"},
        )

    @app.get("/login", response_class=HTMLResponse)
    async def login_form(request: Request) -> HTMLResponse:
        if request.session.get("authenticated"):
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": None, "title": "Acces protege"},
            headers={"Cache-Control": "no-store"},
        )

    @app.post("/login", response_class=HTMLResponse, response_model=None)
    async def login(
        request: Request,
        password: str = Form(...),
        current_settings: Settings = SETTINGS_DEPENDENCY,
    ) -> HTMLResponse | RedirectResponse:
        if secrets.compare_digest(password, current_settings.password):
            request.session.clear()
            request.session["authenticated"] = True
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Mot de passe incorrect.", "title": "Acces protege"},
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"Cache-Control": "no-store"},
        )

    @app.post("/logout")
    async def logout(request: Request) -> RedirectResponse:
        request.session.clear()
        response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        response.headers["Cache-Control"] = "no-store"
        return response

    return app


def _configure_logging_from_env() -> None:
    level_name = os.getenv("MIRANDOLE_LOG_LEVEL")
    if not level_name:
        return

    level = getattr(logging, level_name.upper(), None)
    if not isinstance(level, int):
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format="%(levelname)s:%(name)s:%(message)s",
        force=False,
    )
    logging.getLogger("mirandole").setLevel(level)


def _select_session(
    sessions: list[SearchSession], requested_session_id: int | None
) -> SearchSession | None:
    if requested_session_id is None:
        return sessions[0] if sessions else None

    for session in sessions:
        if session.id == requested_session_id:
            return session

    return sessions[0] if sessions else None


def _safe_return_path(value: str) -> str:
    if not value.startswith("/") or value.startswith("//"):
        return "/"
    return value


def _is_async_offer_action(request: Request) -> bool:
    return request.headers.get("X-Mirandole-Async") == "1"


def _return_path_with_scroll(value: str, scroll_y: int | None) -> str:
    safe_path = _safe_return_path(value)
    if scroll_y is None or scroll_y < 0:
        return safe_path

    parts = urlsplit(safe_path)
    query_items = [
        (key, item_value)
        for key, item_value in parse_qsl(parts.query, keep_blank_values=True)
        if key != "scroll_y"
    ]
    query_items.append(("scroll_y", str(scroll_y)))
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query_items), parts.fragment)
    )


def _filter_prod_mock_results(
    results: list[StoredOfferResult], settings: Settings
) -> list[StoredOfferResult]:
    if not settings.prod:
        return results
    return [result for result in results if not _is_mock_offer_result(result)]


def _is_mock_offer_result(result: StoredOfferResult) -> bool:
    return result.source_name == DEMO_SOURCE_NAME or _is_mock_source_url(
        result.source_url
    )


def _is_mock_source_url(source_url: str) -> bool:
    return source_url.startswith(MOCK_SOURCE_URL_PREFIX)


def _filter_hidden_results(results: list[StoredOfferResult]) -> list[StoredOfferResult]:
    return [result for result in results if result.hidden_at is None]


def _source_filter_options(results: list[StoredOfferResult]) -> list[str]:
    return sorted({result.source_name for result in results})


def _filter_by_source(
    results: list[StoredOfferResult], source_names: list[str] | None
) -> list[StoredOfferResult]:
    if not source_names:
        return results

    selected_source_names = set(source_names)
    return [
        result for result in results if result.source_name in selected_source_names
    ]
