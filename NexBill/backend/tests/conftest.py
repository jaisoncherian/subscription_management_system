import itertools
import os

import psycopg
import pytest
from sqlalchemy.engine import make_url

from app import create_app
from app.config import Config, TestingConfig
from app.extensions import db, limiter
from app.repositories import sequences


def _use_a_separate_database():
    """Keep tests off the dev database, and pytest-xdist workers off each other."""
    uri = TestingConfig.SQLALCHEMY_DATABASE_URI
    if uri.startswith("sqlite"):
        return
    url = make_url(uri)
    if Config.SQLALCHEMY_DATABASE_URI and url.database == make_url(Config.SQLALCHEMY_DATABASE_URI).database:
        pytest.exit("TEST_DATABASE_URL must not point at the dev database.", returncode=1)

    worker = os.environ.get("PYTEST_XDIST_WORKER")
    if not worker:
        return
    # Every test creates and drops all tables, so each worker needs its own database.
    name = f"{url.database}_{worker}"
    with psycopg.connect(
        host=url.host,
        port=url.port,
        user=url.username,
        password=url.password,
        dbname=url.database,
        autocommit=True,
    ) as connection:
        exists = connection.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (name,)
        ).fetchone()
        if not exists:
            connection.execute(f'CREATE DATABASE "{name}"')
    TestingConfig.SQLALCHEMY_DATABASE_URI = url.set(database=name).render_as_string(
        hide_password=False
    )


_use_a_separate_database()


def pytest_collection_modifyitems(items):
    if not TestingConfig.SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
        return
    skip = pytest.mark.skip(reason="needs PostgreSQL: set TEST_DATABASE_URL")
    for item in items:
        if "postgres" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(autouse=True)
def sqlite_sequences(monkeypatch):
    """SQLite has no sequences, so emulate them. PostgreSQL uses the real ones."""
    if not TestingConfig.SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
        return
    counters = {}

    def next_value(sequence):
        return next(counters.setdefault(sequence.name, itertools.count(1)))

    monkeypatch.setattr(sequences, "next_value", next_value)


def _build_app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
    return app


def _destroy_app(app):
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture
def app():
    """No app context stays open, so each request gets its own, as in production.

    Open one with app_context, or `with app.app_context():`, to use the database.
    """
    app = _build_app()
    yield app
    _destroy_app(app)


@pytest.fixture
def app_context(app):
    with app.app_context():
        yield


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def rate_limited_app(monkeypatch):
    monkeypatch.setattr(TestingConfig, "RATELIMIT_ENABLED", True)
    app = _build_app()
    limiter.reset()
    yield app
    limiter.reset()
    _destroy_app(app)
