# CLAUDE.md - VOKO Utrecht

VOKO Utrecht is a food collective ordering platform. Members order products from local suppliers, which are then distributed at pickup points.

## Tech Stack

- Python 3.11, Django 4.2
- Package manager: `uv` (always use `uv run` instead of calling python directly)
- Database: PostgreSQL (Docker) / SQLite (local dev)
- Testing: pytest + pytest-django + factory-boy
- Payments: Mollie (iDEAL)
- Custom user model: `accounts.VokoUser`

## Local Development

### Docker (recommended)

```bash
make docker-setup   # first-time setup: build, migrate, create superuser
make docker-up      # start services (web on :8000, db on :5433)
make docker-test    # run tests in container
```

### Without Docker

```bash
uv sync --dev
uv run python webapp/manage.py migrate --settings=vokou.settings.development
uv run python webapp/manage.py runserver --settings=vokou.settings.development
```

Default dev credentials: `admin@voko.local` / `admin123`

## Common Commands

```bash
# Tests
make test
uv run pytest webapp/ --ds=vokou.settings.testing

# Migrations
uv run python webapp/manage.py makemigrations --settings=vokou.settings.development
uv run python webapp/manage.py migrate --settings=vokou.settings.development

# Linting
flake8
```

## Settings

| Module | Use case |
|--------|----------|
| `vokou.settings.development` | Local dev, SQLite |
| `vokou.settings.docker_development` | Docker dev, PostgreSQL |
| `vokou.settings.testing` | Test suite (SQLite, MD5 passwords for speed) |
| `vokou.settings.production` | Production, PostgreSQL, env-based secrets |
| `vokou.settings.acceptance` | Staging |

## Django Apps

| App | Purpose |
|-----|---------|
| `accounts` | Custom user model (VokoUser), profiles, addresses |
| `ordering` | Core: products, suppliers, order rounds, checkout |
| `finance` | Payments, balances, Mollie integration |
| `distribution` | Distribution shifts and logistics |
| `transport` | Ride/transport coordination |
| `mailing` | Email templates and notifications |
| `groups` | User group management (Admin, Transport, etc.) |
| `agenda` | Events and calendar |
| `news` | News articles and announcements |
| `api` | REST API endpoints |
| `log` | Event logging |

## Code Style

- Linter: flake8 (config in `.flake8`)
- Max line length: 120
- Migrations and settings are excluded from linting
- CI runs flake8 and pytest on every PR

## Testing Patterns

- Test files: `test_*.py`, `*_test.py`, or `tests.py`
- Test data: use factory-boy factories (e.g., `VokoUserFactory`, `OrderRoundFactory`)
- Fixtures at `webapp/conftest.py`
- Always use `--ds=vokou.settings.testing` when running pytest directly
