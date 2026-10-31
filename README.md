# NexBill – Subscription Management System

<p align="center">
  <strong>A Modern Platform for Subscription, Billing and Revenue Management</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue?logo=python" />
  <img src="https://img.shields.io/badge/Flask-Backend-black?logo=flask" />
  <img src="https://img.shields.io/badge/PostgreSQL-Database-4169E1?logo=postgresql" />
  <img src="https://img.shields.io/badge/Pytest-Testing-0A9EDC?logo=pytest" />
  <img src="https://img.shields.io/badge/Status-Active_Development-success" />
</p>

---

## Overview

**NexBill** is a subscription management and billing platform designed to simplify subscription tracking, invoice management, customer administration and financial reporting.

The platform provides a centralized system for managing customer subscriptions, monitoring payment statuses, tracking outstanding invoices and analyzing business revenue.

NexBill aims to make subscription operations more organized, transparent and efficient through a structured backend architecture and role-based access control.

## Key Features

### 1. Customer Management
- Customer registration and account management.
- Customer information and record management.
- Secure authentication.
- Customer-specific data access.

### 2. Subscription Management
- Manage customer subscriptions.
- Track subscription information and statuses.
- Associate subscriptions with customer records.
- Provide customers access to their own subscriptions.

### 3. Invoice Management
- Manage customer invoices.
- Track invoice payment statuses.
- Identify overdue invoices.
- Provide customers access to their own invoices.

### 4. Reports and Analytics
- Business summary reports.
- Revenue analysis grouped by month.
- Overdue invoice reporting.
- Date-range-based report filtering.
- Pagination for report data.

### 5. Authentication and Security
- Password hashing using Argon2.
- JWT-based authentication.
- Role-based access control.
- Protected API endpoints.
- Customer and staff access separation.

### 6. Backend Performance and Testing
- Modular Flask application architecture.
- Database integration using SQLAlchemy.
- Automated testing with Pytest.
- Parallel test execution using pytest-xdist.
- Structured application logging and error handling.

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, Flask |
| Database | PostgreSQL |
| ORM | Flask-SQLAlchemy |
| Database Migrations | Flask-Migrate |
| Authentication | Flask-JWT-Extended |
| Password Security | Argon2 |
| Rate Limiting | Flask-Limiter |
| Testing | Pytest |
| Parallel Testing | pytest-xdist |
| Version Control | Git and GitHub |

## Project Structure

```text
NexBill/
│
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── security.py
│   │   │   ├── errors.py
│   │   │   └── logging.py
│   │   │
│   │   ├── routes/
│   │   ├── models/
│   │   ├── jobs/
│   │   ├── config.py
│   │   ├── extensions.py
│   │   └── __init__.py
│   │
│   ├── tests/
│   ├── migrations/
│   ├── requirements.txt
│   ├── pytest.ini
│   └── .env.example
│
└── README.md
```

*The structure above describes the backend organization; additional frontend and deployment directories can be included as the project evolves.*

## Installation and Setup

### Prerequisites

Install the following before running the project:

- Python 3.13
- PostgreSQL
- Git
- Visual Studio Code (recommended)

### 1. Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

```bash
cd NexBill
```

### 2. Navigate to Backend

```bash
cd backend
```

### 3. Create a Virtual Environment

Windows PowerShell:

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file using the provided example:

```powershell
Copy-Item .env.example .env
```

Configure your local database connection and the required application secrets according to `app/config.py`.

Example database configuration:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/nexbill
```

**Security:** Never commit `.env` files, database passwords or secret keys to GitHub.

### 6. Configure PostgreSQL

Create a PostgreSQL database named:

```sql
CREATE DATABASE nexbill;
```

Ensure PostgreSQL is running and the credentials in `.env` match your local configuration.

### 7. Initialize Database Migrations

If the project uses Flask-Migrate, apply the existing migrations:

```bash
flask db upgrade
```

Ensure the Flask application is configured correctly before executing migration commands.

### 8. Run the Backend

Use the project's configured Flask entry point. For example, if `app` is the application package:

```bash
flask --app app run --debug
```

The development server will normally be available at:

```text
http://127.0.0.1:5000
```

## Running Tests

NexBill uses Pytest for automated backend testing.

Run the complete test suite:

```bash
python -m pytest tests -v
```

Run tests with parallel workers:

```bash
python -m pytest tests -n 4 -v
```

View detailed test results and skipped-test reasons:

```bash
python -m pytest tests -v -ra
```

Run a specific test module:

```bash
python -m pytest tests/test_auth.py -v
```

**Testing note:** PostgreSQL-dependent tests require a correctly configured and accessible test database. Skipped tests should be reviewed before considering the backend fully verified.

## API Modules

The backend organizes its functionality into API modules.

| Module | Purpose |
|---|---|
| Authentication | Registration, login and identity verification |
| Customer Portal | Customer-specific subscriptions and invoices |
| Reports | Business summaries, revenue and overdue reports |
| Core Security | JWT callbacks and password verification |

Example API endpoints:

```text
/api/portal/subscriptions
/api/portal/invoices
/api/reports/summary
/api/reports/revenue
/api/reports/overdue
```

Protected endpoints require the appropriate authentication credentials and user permissions.

## Security Practices

NexBill follows security-focused development practices:

- Passwords are stored using Argon2 hashing.
- JWT authentication protects restricted endpoints.
- Role-based authorization separates customer and staff access.
- Environment variables are used for sensitive configuration.
- Database credentials are not intended to be committed to source control.
- Rate limiting helps control excessive API requests.

## Development Workflow

The project uses Git and GitHub for collaborative development.

Recommended workflow:

1. Create a feature branch.
2. Implement and test changes locally.
3. Review modified files.
4. Commit changes with meaningful messages.
5. Push the feature branch.
6. Open a Pull Request targeting `main`.
7. Review and merge after verification.

Example:

```bash
git checkout -b feature/new-feature
git add .
git commit -m "Add new feature"
git push -u origin feature/new-feature
```

## Future Enhancements

Potential improvements include:

- Automated recurring billing.
- Payment gateway integration.
- Subscription renewal notifications.
- Advanced financial dashboards.
- Exportable invoice and revenue reports.
- Email notifications and reminders.
- Deployment with production-grade infrastructure.

## Contribution

Contributions, suggestions and improvements are welcome.

For significant changes, create a feature branch and submit a Pull Request for review.

## License

Specify the appropriate license for this repository before distributing or reusing the project.

---

<p align="center">
  <strong>NexBill</strong>
  <br/>
  Simplifying Subscription Management. Streamlining Billing. Empowering Business Insights.
</p>
