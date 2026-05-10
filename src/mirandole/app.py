from __future__ import annotations

import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from mirandole.config import Settings
from mirandole.storage import initialize_storage

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
        request: Request, _authenticated: None = Depends(require_user)
    ) -> HTMLResponse:
        return templates.TemplateResponse(
            request,
            "home.html",
            {"title": "Recherche d'offres d'emploi"},
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
