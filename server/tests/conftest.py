"""
Shared test setup (pytest automatically loads any file named conftest.py).

The big idea: DB tests must NOT touch your real `challenge_engine` database (the
one you inspect in pgAdmin). So we use a SEPARATE database, `challenge_engine_test`,
and wipe it clean before every test. That gives each test an isolated blank slate.

Two fixtures:
  engine  (once per test run) : ensures the test DB exists and has all our tables.
  db      (once per test)      : truncates every table, then hands the test a
                                 fresh SQLAlchemy Session.
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

import app.models  # noqa: F401  -- import so every table is registered on Base.metadata
from app.core.config import settings
from app.models import Base

TEST_DB_NAME = "challenge_engine_test"


def _server_url() -> str:
    # Strip the database name off DATABASE_URL, leaving the server address.
    server, _dbname = settings.database_url.rsplit("/", 1)
    return server


@pytest.fixture(scope="session")
def engine():
    # 1. Create the test database if it doesn't exist yet. CREATE DATABASE can't
    #    run inside a transaction, so we connect in AUTOCOMMIT mode to the
    #    always-present "postgres" maintenance database.
    admin = create_engine(f"{_server_url()}/postgres", isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": TEST_DB_NAME}
        ).scalar()
        if not exists:
            conn.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))
    admin.dispose()

    # 2. Build the schema fresh (drop everything, recreate from our models).
    eng = create_engine(f"{_server_url()}/{TEST_DB_NAME}")
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def db(engine):
    # Clean slate before each test: empty every table (children first via CASCADE),
    # reset id counters. This is why tests can't pollute each other.
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE'))

    session = Session(bind=engine)
    try:
        yield session          # the test runs here, using this session
    finally:
        session.close()
