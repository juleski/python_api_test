# Python API Test

A layered FastAPI starter project for practicing API development. The project
uses Python 3.14.6 and [uv](https://docs.astral.sh/uv/) for Python, dependency,
and virtual-environment management.

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

Start the development server with automatic reload:

```shell
uv run uvicorn app.main:app --reload
```

The API is available at <http://127.0.0.1:8000>. Interactive documentation is
available at <http://127.0.0.1:8000/docs>.

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/` | Return a welcome message. |
| `GET` | `/health` | Return the API health status. |

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
