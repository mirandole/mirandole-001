## Parent

Parent PRD: #1

## What to build

Build the first deployable Application deployee shell for the agregateur d'offres d'emploi. The slice should provide a protected FastAPI application with server-rendered pages, password login, session cookie handling, logout, environment-based configuration, and an initialized SQLite Stockage applicatif.

The completed slice should be runnable locally and shaped for VPS deployment, even if it only shows a minimal protected home page.

## Acceptance criteria

- [ ] The application starts through a documented command and serves a protected page.
- [ ] Unauthenticated requests to protected pages are redirected to login.
- [ ] The Utilisateur principal can log in with a password configured outside source code.
- [ ] The Utilisateur principal can log out and lose access to protected pages.
- [ ] Session cookies are configured with sensible security defaults for deployment behind WireGuard.
- [ ] SQLite Stockage applicatif is initialized at a configurable path.
- [ ] Basic route tests cover login, logout, protected access, and missing/invalid password configuration.
- [ ] The README or deployment notes describe required environment variables for local run and VPS use.

## Blocked by

None - can start immediately.
