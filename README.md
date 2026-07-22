# Python API Test

A PostgreSQL-backed todo API built with FastAPI, a simple layered service and
adapter structure, SQLAlchemy, and Alembic. The project uses Python 3.14.6 and
[uv](https://docs.astral.sh/uv/) for Python, dependency, and virtual-environment
management.

## Requirements

- uv

uv automatically installs the Python version pinned in `.python-version` when
it is not already available.

## Install

Create the virtual environment and install the locked dependencies:

```shell
uv sync
```

Install the repository's code-quality and commit-message Git hooks once per
clone:

```shell
uv run pre-commit install --install-hooks
```

## Run the API

Start PostgreSQL first and apply the database migrations:

```shell
docker-compose up -d db
uv run alembic upgrade head
```

Start the development server with automatic reload:

```shell
uv run uvicorn app.main:app --reload
```

The API is available at <http://127.0.0.1:8000>. Interactive documentation is
available at <http://127.0.0.1:8000/docs>. Prometheus-format application
metrics are exposed at <http://127.0.0.1:8000/metrics>.

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/` | Return a welcome message. |
| `GET` | `/health` | Return the API health status. |
| `POST` | `/tasks` | Create a task. |
| `GET` | `/tasks` | Filter, sort, and paginate tasks. |
| `GET` | `/tasks/{task_id}` | Return a task by UUID. |
| `PUT` | `/tasks/{task_id}` | Update selected task fields. |
| `GET` | `/metrics` | Export Prometheus API latency metrics. |

The task list accepts `status`, `name`, `sort_by`, `sort_order`, `limit`, and
`cursor` query parameters. Its response contains `items` and the opaque
`next_cursor` to pass to the following request.

## Configuration

Copy `.env.example` to `.env` to override the safe local defaults. The API
reads `DATABASE_URL`; Docker Compose builds it from the `POSTGRES_*` variables.
Never commit `.env` or production credentials.

```shell
cp .env.example .env
```

The application layers are intentionally small: routes validate HTTP input and
call `app/services/tasks.py`; the service owns task behavior and talks through
a repository protocol; `app/adapters/postgresql/` contains SQLAlchemy-specific
storage code.

## Database migrations

Alembic configuration and revisions live under the top-level `migrations/`
directory, separate from the FastAPI package.

Apply all migrations:

```shell
uv run alembic upgrade head
```

Create a migration after changing SQLAlchemy metadata:

```shell
uv run alembic revision --autogenerate -m "describe the schema change"
```

Roll back one migration:

```shell
uv run alembic downgrade -1
```

## Docker Compose and observability

Build the API image and start PostgreSQL, migrations, the API, Prometheus, and
Grafana:

```shell
docker-compose up --build
```

The `migrate` service runs once after PostgreSQL is healthy. The API starts only
after that migration succeeds. The local services are available at:

- API and metrics: <http://127.0.0.1:8000> and
  <http://127.0.0.1:8000/metrics>
- Prometheus: <http://127.0.0.1:9090>
- Grafana: <http://127.0.0.1:3000>

Grafana uses the `GRAFANA_ADMIN_USER` and `GRAFANA_ADMIN_PASSWORD` values from
`.env` (both default to `admin` for local development). Its Prometheus
datasource and **FastAPI / API Latency** dashboard are provisioned
automatically.

Generate traffic against the API before expecting p95 values. The dashboard
uses `histogram_quantile()` over the rate of histogram buckets in Grafana's
selected time range, so p95 is an estimate determined by the configured bucket
boundaries. It displays both each HTTP method/route combination and an aggregate
across all measured endpoints.

The `/metrics` endpoint is intentionally unauthenticated for this local Compose
setup. Restrict it with network policy or a reverse proxy before exposing the
application in production.

Stop the stack with `docker-compose down`; add `--volumes` only when you
intentionally want to delete local database, Prometheus, and Grafana data.

The Dockerfile uses two Python stages. The builder creates a locked production
virtual environment with uv. The runtime receives only that environment plus
the application and migrations, excluding dependency caches and development
tools. It also runs as an unprivileged user.

## Development commands

Run every pre-commit file check manually:

```shell
uv run pre-commit run --all-files
```

Some hooks safely fix lint or formatting problems. If a hook changes a file,
review and stage the change, then run the checks again.

Run the test suite:

```shell
uv run pytest
```

Integration tests require an isolated PostgreSQL database. They apply and roll
back Alembic migrations automatically:

```shell
docker-compose --profile test run --rm test
```

Compose creates the disposable `todo_test` database when its PostgreSQL volume
is initialized. To run the same tests from the host, set `TEST_DATABASE_URL` to
an isolated PostgreSQL database that the suite may migrate up and down. Run only
the fast tests with:

```shell
uv run pytest -m "not integration"
```

Lint the project:

```shell
uv run ruff check .
```

Format the project:

```shell
uv run ruff format .
```

Check formatting without changing files:

```shell
uv run ruff format --check .
```

Confirm that `uv.lock` is current:

```shell
uv lock --check
```

When dependencies change, update and commit `pyproject.toml` and the generated
`uv.lock` together. The lockfile is managed by uv and should not be edited by
hand.

## Commit messages

Commit messages are checked against the Conventional Commits format:

```text
type(optional-scope): short description
```

Examples that pass:

```text
feat(api): add users endpoint
fix: return the correct health status
docs: explain local development
```

An unstructured message such as `added health endpoint` fails the commit-message
hook. Allowed types are `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`,
`refactor`, `revert`, `style`, and `test`.
