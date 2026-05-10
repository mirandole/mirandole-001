from __future__ import annotations

import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Form, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
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
from mirandole.search import RAYONS_DEMANDE_KM, run_search_trace
from mirandole.storage import (
    SearchSession,
    initialize_storage,
    list_favorite_offer_results,
    list_offer_results_for_session,
    list_recent_searches,
    list_search_sessions,
    list_source_failures_for_session,
    mark_offer_result_consulted,
    toggle_offer_result_favorite,
)

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


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
        failures = []
        if selected_session is not None:
            results = list_offer_results_for_session(
                current_settings.database_path, selected_session.id
            )
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

        return RedirectResponse(url=source_url, status_code=status.HTTP_303_SEE_OTHER)

    @app.post("/offer-results/{offer_result_id}/favorite")
    async def toggle_offer_favorite(
        offer_result_id: int,
        return_to: str = Form(default="/"),
        _authenticated: None = Depends(require_user),
        current_settings: Settings = SETTINGS_DEPENDENCY,
    ) -> RedirectResponse:
        toggle_offer_result_favorite(current_settings.database_path, offer_result_id)
        return RedirectResponse(
            url=_safe_return_path(return_to),
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
