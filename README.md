# Module 11 - SQLAlchemy Calculations, Pydantic Validation, and CI/CD

[![CI/CD](https://github.com/MatthewFeroz/calculator-sql/actions/workflows/test.yml/badge.svg)](https://github.com/MatthewFeroz/calculator-sql/actions/workflows/test.yml)

This project builds on the secure Module 10 user foundation by adding a
tested calculation data layer. SQLAlchemy persists user-owned calculations,
Pydantic validates operands and operation types, and a factory selects the
correct Add, Subtract, Multiply, or Divide strategy. Calculation HTTP routes
are intentionally deferred until Module 12.

- GitHub repository: [MatthewFeroz/calculator-sql](https://github.com/MatthewFeroz/calculator-sql)
- Docker Hub repository: [matthewferoz/calculator-sql](https://hub.docker.com/r/matthewferoz/calculator-sql)

## Calculation Design

The `calculations` table is defined entirely with SQLAlchemy:

| Column | Purpose |
| --- | --- |
| `id` | Database-generated integer primary key |
| `user_id` | Required foreign key to `users.id`, indexed with cascade delete |
| `a` | First finite numeric operand |
| `b` | Second finite numeric operand |
| `type` | Enum restricted to Add, Subtract, Multiply, or Divide |
| `result` | Result computed by the factory and stored for history |
| `created_at` | Database-generated, timezone-aware timestamp |

The implementation separates responsibilities:

1. `CalculationCreate` uses strict input validation, normalizes operation
   names, rejects unknown types, and prevents division by zero.
2. `CalculationFactory` instantiates an operation strategy behind a shared
   interface and reuses the existing arithmetic functions.
3. `create_calculation` verifies that the owner exists, computes the result,
   and stages the SQLAlchemy record without depending on an API route.
4. PostgreSQL enforces the user foreign key and deletes calculation history
   when its owning user is deleted.
5. `CalculationRead` serializes stored data without exposing the related user
   object or any credential fields.

The existing `User` model continues to store only a salted bcrypt password
hash. Username and email uniqueness remain protected by PostgreSQL constraints.

## Project Structure

```text
app/
|-- calculations/
|   |-- factory.py          # Factory and arithmetic strategy classes
|   `-- types.py            # Shared CalculationType enum and parser
|-- database.py             # SQLAlchemy engine, sessions, and shared Base
|-- database_init.py        # Create-if-missing table initialization
|-- models/
|   |-- calculation.py      # Calculation table and User relationship
|   `-- user.py             # Secure User table and calculation collection
|-- schemas/
|   |-- calculation.py      # CalculationCreate and CalculationRead
|   `-- user.py             # UserCreate and UserRead
|-- services/
|   |-- calculations.py     # Route-independent calculation persistence
|   `-- users.py            # Secure user creation
|-- operations/             # Existing arithmetic functions
`-- security.py             # bcrypt hash and verify functions
tests/
|-- unit/                   # Factory, schema, security, and service tests
|-- integration/            # API and real PostgreSQL persistence tests
`-- e2e/                    # Playwright tests against a live application
.github/workflows/test.yml  # Test -> smoke/scan -> Docker Hub deployment
```

## Run the Application with Docker Compose

Prerequisite: Docker Desktop with Docker Compose.

```bash
docker compose up --build
```

After the services become healthy:

- Application: <http://localhost:8000>
- Interactive API docs: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>
- pgAdmin: <http://localhost:5050> (`admin@example.com` / `admin`)
- PostgreSQL: `localhost:5432`, database `fastapi_db`, user/password
  `postgres` / `postgres`

The application creates missing mapped tables at startup. If an older course
volume contains an incompatible raw-SQL `calculations` table, recreate the
local coursework volumes before the first Module 11 run:

```bash
# Warning: this deletes local PostgreSQL and pgAdmin volume data.
docker compose down --volumes
docker compose up --build
```

## Run Tests Locally

### 1. Create the Python environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
```

### 2. Run tests that do not require PostgreSQL

```bash
pytest -m "not postgres"
```

PostgreSQL tests skip unless `TEST_DATABASE_URL` is explicitly defined. This
safety rule prevents test cleanup from targeting the normal development
database.

### 3. Run the complete suite with real PostgreSQL

Start a disposable PostgreSQL 17 test container:

```bash
docker run --rm --detach --name calculator-sql-test-db \
  --publish 5433:5432 \
  --env POSTGRES_USER=postgres \
  --env POSTGRES_PASSWORD=postgres \
  --env POSTGRES_DB=calculator_test \
  postgres:17
```

Windows PowerShell:

```powershell
$env:TEST_DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5433/calculator_test"
pytest
docker stop calculator-sql-test-db
```

macOS/Linux:

```bash
export TEST_DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5433/calculator_test"
pytest
docker stop calculator-sql-test-db
```

The complete Module 11 suite contains 118 unit, API integration, PostgreSQL,
and Playwright tests. Coverage is measured across `app/` and `main.py`.

Useful targeted commands:

```bash
pytest tests/unit/test_calculation_factory.py -v
pytest tests/unit/test_calculation_schemas.py -v
pytest tests/integration/test_calculations_database.py -v
pytest -m postgres -v
```

## Build and Run the Production Image

```bash
docker build --tag calculator-sql:local .
docker run --rm --publish 8000:8000 \
  --env DATABASE_URL="sqlite+pysqlite:///:memory:" \
  calculator-sql:local
```

The image runs as an unprivileged Linux user and includes an HTTP health check.
After CI deploys successfully, run the published image with:

```bash
docker pull matthewferoz/calculator-sql:latest
docker run --rm --publish 8000:8000 \
  --env DATABASE_URL="sqlite+pysqlite:///:memory:" \
  matthewferoz/calculator-sql:latest
```

## CI/CD Pipeline

`.github/workflows/test.yml` runs for pushes and pull requests to `main`:

1. **test** starts PostgreSQL 17, installs Chromium, runs all 118 tests, and
   uploads JUnit and XML coverage reports.
2. **security** builds the image, performs a live `/health` smoke test, and
   fails on fixable high or critical Trivy findings.
3. **deploy** runs only for successful pushes to `main`, then publishes Linux
   AMD64 and ARM64 images as both `latest` and the immutable Git commit SHA.

The deploy job uses the `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` repository
secrets and targets the `production` GitHub environment. Third-party actions
are pinned to full commit identifiers.

## Deployment Evidence

![Successful GitHub Actions test, security, and deploy jobs](PIC1.png)

![Published Docker Hub latest and commit-SHA tags](PIC2.png)

## Legacy Module 9 SQL Exercises

The scripts in `sql/` remain as earlier raw-SQL exercises. The Module 11
application model and its tests use SQLAlchemy rather than those scripts.
