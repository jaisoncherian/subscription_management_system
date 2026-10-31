# NexBill

Subscription management system. This repository currently holds the project skeleton only.

**Backend:** Python 3.11+, Flask, Flask-SQLAlchemy, Flask-Migrate, PostgreSQL, marshmallow,
Flask-JWT-Extended, argon2-cffi, Flask-Limiter, pytest.

**Frontend:** to be set up in `frontend/`.

## Setup

### 1. Clone

```bash
git clone <repository-url>
cd NexBill
```

### 2. Create a virtual environment

```bash
cd backend
python -m venv venv
```

Activate it:

```bash
# Windows PowerShell
venv\Scripts\Activate.ps1

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create your `.env`

From the `backend/` folder:

```bash
# Windows PowerShell
copy ..\.env.example ..\.env

# macOS / Linux
cp ../.env.example ../.env
```

Then replace the dummy values in `NexBill/.env`. The password in `DATABASE_URL` must match `DB_PASSWORD`.

### 5. Start the database

With Docker, from the `NexBill/` folder:

```bash
docker compose up -d
```

Or use a local PostgreSQL server instead. Stop here if it already uses port 5432 and you meant to use Docker, because the two will clash. Create the role and database as a superuser, using your `DB_PASSWORD` value:

```sql
CREATE ROLE nexbill LOGIN PASSWORD 'your-db-password';
CREATE DATABASE nexbill OWNER nexbill;
```

### 6. Run migrations

From `backend/`:

```bash
flask db init      # Only if backend/migrations/ does not exist yet. It is already in this repository.
flask db migrate -m "describe the change"
flask db upgrade
```

Until models exist, `flask db migrate` reports `No changes in schema detected` and creates no migration file. That is expected.

### 7. Run the app

```bash
flask run
```

Check it at <http://127.0.0.1:5000/api/health>. It should return `{"status": "ok"}`.

Use `flask run --debug` to get auto-reload while developing.

### 8. Run the tests

```bash
pytest
```

The tests use an in-memory SQLite database, so they need neither PostgreSQL nor a `.env` file.

## Configuration

Settings come from environment variables, or from `NexBill/.env`. Real environment variables take priority.

`DATABASE_URL`, `SECRET_KEY` and `JWT_SECRET_KEY` are required: the app refuses to start without them.

| Variable                                 | Purpose                                                   |
| ---------------------------------------- | --------------------------------------------------------- |
| `APP_ENV`                                | `development` (default), `testing` or `production`        |
| `DATABASE_URL`                           | PostgreSQL connection URL                                 |
| `DB_PASSWORD`                            | Password for the `docker-compose.yml` database            |
| `SECRET_KEY`                             | Flask secret key                                          |
| `JWT_SECRET_KEY`                         | JWT signing key                                           |
| `RATELIMIT_STORAGE_URI`                  | Optional rate limit store. Defaults to in-memory          |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD`          | Reserved for the admin account. Not used yet              |
| `OLLAMA_URL`, `OLLAMA_MODEL`             | Reserved for the Ollama integration. Not used yet         |

## Project layout

```text
NexBill/
  backend/
    app/
      core/          Errors, logging, security, decorators
      models/        SQLAlchemy models
      schemas/       Marshmallow schemas
      repositories/  Data access
      services/      Business logic
      routes/        Blueprints
      jobs/          Background jobs
    migrations/      Alembic migrations
    tests/
  frontend/
  docs/API.md        Endpoints and error format
```
