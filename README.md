# Module 9 — FastAPI Calculator with PostgreSQL

The FastAPI calculator from Module 8, now running in a containerized
environment with **PostgreSQL** and **pgAdmin** managed by Docker Compose.
This module focuses on raw SQL: creating tables, inserting, querying,
updating, and deleting records, and modeling a one-to-many relationship
with a foreign key.

## Services (docker-compose.yml)

| Service   | Image          | Port | Purpose                                  |
|-----------|----------------|------|------------------------------------------|
| `web`     | built from `.` | 8000 | FastAPI calculator application           |
| `db`      | postgres:17    | 5432 | PostgreSQL database (`fastapi_db`)       |
| `pgadmin` | dpage/pgadmin4 | 5050 | Web UI for running SQL against the db    |

## Getting Started

```bash
docker compose up --build
```

- App: http://localhost:8000
- pgAdmin: http://localhost:5050 — log in with `admin@example.com` / `admin`

### Connect pgAdmin to PostgreSQL

1. In pgAdmin: right-click **Servers → Register → Server…**
2. General tab → Name: anything (e.g. `local-db`)
3. Connection tab → Host: `db`, Port: `5432`, Username: `postgres`,
   Password: `postgres` (host is `db` because pgAdmin talks to Postgres
   over the compose network, not through localhost)
4. Open the `fastapi_db` database → Query Tool

## SQL Exercises (sql/)

Run each script in the pgAdmin Query Tool, in order:

| Script                  | What it does                                            |
|-------------------------|---------------------------------------------------------|
| `01_create_tables.sql`  | Creates `users` and `calculations` (FK, ON DELETE CASCADE) |
| `02_insert_records.sql` | Inserts two users and three calculations                |
| `03_query_data.sql`     | SELECTs from both tables + JOIN across the relationship |
| `04_update_record.sql`  | UPDATEs a calculation's result                          |
| `05_delete_record.sql`  | DELETEs a calculation                                   |

The `users` → `calculations` design is a **one-to-many relationship**:
each calculation row stores the `user_id` of its owner, and
`ON DELETE CASCADE` removes a user's calculations when the user is deleted.

## Running the Tests

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt && playwright install chromium
pytest
```

## CI/CD Pipeline

`.github/workflows/test.yml` runs on every push/PR to `main`:

1. **test** — full test suite with a PostgreSQL service container.
2. **security** — Docker image build + Trivy vulnerability scan.
3. **deploy** — pushes the image to Docker Hub (`calculator-sql`).
   Requires `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN` secrets and a
   `production` GitHub environment.
