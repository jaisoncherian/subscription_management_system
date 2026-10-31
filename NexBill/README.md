# NexBill

Subscription management system for Brightloop Software: products, plans, subscriptions, recurring invoicing, payments and revenue reporting.

The backend core is complete: authentication and roles, quotation templates, the subscription state machine, pricing, the billing run, invoices and payments. See [docs/API.md](docs/API.md). Catalog CRUD, the customer list, reports and the frontend are built separately.

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

`backend/migrations/` is already in this repository, with the initial schema, so a new setup only needs:

```bash
flask db upgrade
```

After changing a model, generate and apply a new migration:

```bash
flask db migrate -m "describe the change"
flask db upgrade
```

Only run `flask db init` if `backend/migrations/` is missing. It fails if the folder already exists.

Autogenerate does not detect standalone sequences. Add any new `db.Sequence` to the migration by hand.

### 7. Create the admin

Set `ADMIN_EMAIL` and `ADMIN_PASSWORD` in `.env`, then run this once. Running it again changes nothing.

```bash
flask create-admin
```

### 8. Run the app

```bash
flask run
```

Check it at <http://127.0.0.1:5000/api/health>. It should return `{"status": "ok"}`.

Use `flask run --debug` to get auto-reload while developing.

### 9. Run the tests

```bash
pytest
```

By default the tests use an in-memory SQLite database, so they need neither PostgreSQL nor a `.env` file.

**Run them on PostgreSQL before trusting a billing change.** The billing and concurrency tests need real row locks and savepoints, so they are skipped on SQLite. Set `TEST_DATABASE_URL` to a separate, empty database. The tests create and drop every table in it, so never point it at a database you care about.

### 10. Run billing

Invoices are created by the billing run. Run it on a daily schedule in production. It is safe to run more than once.

```bash
flask run-billing
```

## Configuration

Settings come from environment variables, or from `NexBill/.env`. Real environment variables take priority.

`DATABASE_URL`, `SECRET_KEY` and `JWT_SECRET_KEY` are required: the app refuses to start without them.

| Variable                                 | Purpose                                                   |
| ---------------------------------------- | --------------------------------------------------------- |
| `APP_ENV`                                | `development` (default), `testing` or `production`        |
| `DATABASE_URL`                           | PostgreSQL connection URL                                 |
| `DB_PASSWORD`                            | Password for the `docker-compose.yml` database            |
| `TEST_DATABASE_URL`                      | Optional PostgreSQL database for `pytest`                 |
| `SECRET_KEY`                             | Flask secret key                                          |
| `JWT_SECRET_KEY`                         | JWT signing key                                           |
| `RATELIMIT_STORAGE_URI`                  | Optional rate limit store. Defaults to in-memory          |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD`          | Credentials for `flask create-admin`                      |
| `FRONTEND_URL`                           | Base of the link in password reset emails                 |
| `INVOICE_PAYMENT_TERMS_DAYS`             | Days until an invoice falls due. Defaults to 15           |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `MAIL_FROM` | Optional email server. See below |
| `OLLAMA_URL`, `OLLAMA_MODEL`             | Reserved for the Ollama integration. Not used yet         |

### Email in development

Without `SMTP_HOST`, development writes each email to a file in `backend/dev_outbox/`, which is git-ignored. Open the newest file to get a password reset link. In production without `SMTP_HOST`, emails are dropped and a warning is logged.

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
