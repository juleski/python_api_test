# Project Instructions

## Purpose

This repository is a learning project for building APIs with FastAPI. Keep
implementations clear and incremental, and briefly explain important FastAPI,
Pydantic, Python, or API-design decisions when introducing them.

## Environment and Dependencies

- Use Python 3.14.6 as pinned in `.python-version`.
- Use uv for Python, dependency, and virtual-environment management.
- Declare project metadata and dependencies in `pyproject.toml`.
- Keep `uv.lock` committed for deterministic builds; never edit it manually.
- Use `uv add` and `uv remove` to change dependencies so the project metadata
  and lockfile stay synchronized.
- Do not add a production dependency without explaining why it is needed.
- Never commit secrets, credentials, `.env` files, or the local `.venv`.

## Application Structure

- Keep the FastAPI application factory and exported application in
  `app/main.py`.
- Put route handlers in `app/routes/` and group related endpoints by module.
- Put Pydantic request and response models in `app/schemas/`.
- Keep route handlers small. Move reusable business logic into dedicated
  modules as the application grows.
- Use Python type annotations throughout application and test code.
- Use explicit Pydantic response models for public JSON endpoints.
- Keep API schemas separate from future database persistence models.
- Keep task business logic and its small repository protocol in
  `app/services/tasks.py`; routes should inject and call that service directly.
- Keep SQLAlchemy models, queries, and session handling under `app/adapters/`
  so database details do not leak into routes or schemas.
- Keep Alembic configuration and revisions in the top-level `migrations/`
  directory, separate from application code.

## API Conventions

- Prefer async route handlers unless a synchronous implementation is required.
- Return appropriate HTTP status codes and stable, documented response shapes.
- Validate client input with Pydantic models rather than manual dictionary
  parsing.
- Preserve the existing `GET /` and `GET /health` behavior unless a task
  explicitly changes their contracts.
- Preserve the documented task API and opaque cursor contract unless a task
  explicitly changes them.
- Let FastAPI generate OpenAPI documentation from route and schema definitions.

## Tests and Quality

- Add or update tests in `tests/` whenever endpoint behavior or validation
  changes.
- Test response status codes and JSON bodies for public endpoint contracts.
- Run these checks after making relevant changes:

```shell
uv lock --check
uv run pre-commit run --all-files
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

- Use `uv run ruff format .` when formatting changes are required.
- Report any check that could not be run and the reason it was unavailable.

## Scope and Collaboration

- Favor straightforward code over premature abstractions.
- Make focused changes that match the current request.
- Do not introduce databases, authentication, containers, deployment tooling,
  or CI configuration unless explicitly requested.
- Update `README.md` when setup steps, commands, dependencies, or public API
  behavior change.
