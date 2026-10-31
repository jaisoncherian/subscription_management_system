# NexBill

Subscription management system for Brightloop Software: products, plans, subscriptions, recurring invoicing, payments and revenue reporting.

It covers the whole workflow: catalog, quotation templates, subscriptions, the billing run, invoices, payments, reports and a customer portal. See [docs/API.md](docs/API.md).

**Backend:** Python 3.11+, Flask, Flask-SQLAlchemy, Flask-Migrate, PostgreSQL, marshmallow,
Flask-JWT-Extended, argon2-cffi, Flask-Limiter, pytest.

**Frontend:** React, Vite, Tailwind CSS, TanStack Query, React Hook Form, zod.

## Run a demo

Once setup below is done, this fills the database with six months of demo data. Set `DEMO_PASSWORD` in `.env` first. It refuses to run in production, and running it again changes nothing.

```bash
cd backend
flask seed-demo
```

Then start both servers, each in its own terminal:

```bash
# backend/
flask run

# frontend/ (run npm install the first time)
npm run dev
```

Open <http://localhost:5173> and log in:

| Role | Email | Password |
| ---- | ----- | -------- |
| Admin | `ADMIN_EMAIL` in `.env` | `ADMIN_PASSWORD` in `.env` |
| Staff | `sales@brightloop.example` | `DEMO_PASSWORD` in `.env` |
| Customer | `ana@acme.example` | `DEMO_PASSWORD` in `.env` |

Logins are limited to 5 per minute from one address, so avoid switching accounts too quickly during a demo.

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

Without `TEST_DATABASE_URL`, the tests use an in-memory SQLite database, so they need neither PostgreSQL nor a `.env` file. With it, each parallel test worker makes its own database next to it, named like `nexbill_test_gw0`. Tests refuse to run against the dev database.

**Run them on PostgreSQL before trusting a billing change.** The billing and concurrency tests need real row locks and savepoints, so they are skipped on SQLite. Set `TEST_DATABASE_URL` to a separate, empty database. The tests create and drop every table in it, so never point it at a database you care about.

### 10. Run billing

Invoices are created by the billing run. Run it on a daily schedule in production. It is safe to run more than once.

```bash
flask run-billing
```

### 11. Check the whole workflow

With the server running, this exercises every step over HTTP and stops at the first failure. It creates data, so point the server at a database you do not mind filling.

```bash
python scripts/e2e_smoke.py
```

## Going live

The app serves the built frontend itself, so production needs one server behind HTTPS.

```bash
cd frontend
npm ci
npm run build

cd ../backend
pip install -r requirements.txt
flask db upgrade
flask create-admin
python serve.py
```

With `APP_ENV=production`, the app refuses to start on example or short secrets, on SQLite, or without `FRONTEND_URL`. Session cookies are then HTTPS-only.

Before opening it to real users:

1. **Generate new secrets.** Use new values for `SECRET_KEY`, `JWT_SECRET_KEY` and `ADMIN_PASSWORD`: `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
2. **Use a dedicated database role** with a strong password, not the `postgres` superuser.
3. **Put a reverse proxy with HTTPS in front**, such as Caddy or nginx, forwarding to `127.0.0.1:5000`. Set `FRONTEND_URL` to the public address and `TRUSTED_PROXY_COUNT=1`. Without that setting, every client shares one rate limit.
4. **Configure `SMTP_HOST`**, or password reset and invoice emails are dropped.
5. **Schedule `flask run-billing` daily**, with Windows Task Scheduler or cron.
6. **Back up the database**, for example with a daily `pg_dump`, and test a restore.
7. **Point an uptime check at `/api/health/ready`**, which also proves the database answers.

Run `serve.py` as a single process, because rate limits are kept in memory. To run several, set `RATELIMIT_STORAGE_URI` to a shared store such as Redis.

To rehearse production on your own machine over plain HTTP, also set `JWT_COOKIE_SECURE=false` and `FRONTEND_URL=http://localhost:5000`. Never do that on a real server.

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
| `DEMO_PASSWORD`                          | Password for the accounts made by `flask seed-demo`       |
| `TRUSTED_PROXY_COUNT`                    | Number of reverse proxies in front of the app. Defaults to 0 |
| `JWT_COOKIE_SECURE`                      | Production only. `false` allows plain HTTP, for a rehearsal |
| `HOST`, `PORT`, `THREADS`                | Optional settings for `serve.py`                          |
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
      jobs/          CLI commands and demo data
    migrations/      Alembic migrations
    scripts/         End-to-end workflow check
    serve.py         Production server
    tests/
  frontend/          React app. features/ holds one folder per area
  docs/API.md        Endpoints and error format
```
