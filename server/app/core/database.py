"""
Database plumbing (SQLAlchemy 2.0).

Three things live here:
  1. engine   - the actual connection pool to Postgres.
  2. SessionLocal - a factory that hands out short-lived DB sessions.
  3. Base     - the parent class every ORM model inherits from.

Plus a get_db() dependency that FastAPI uses to open a session per request and
guarantee it's closed afterwards.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# The engine manages a pool of connections to Postgres. pool_pre_ping checks a
# connection is still alive before handing it out (avoids "server closed the
# connection" errors after the DB restarts).
engine = create_engine(settings.database_url, pool_pre_ping=True)

# A session is your "unit of work" — you add/query objects through it, then
# commit. autoflush/autocommit off = explicit, predictable behaviour.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Every model (User, Post, Challenge, ...) will subclass this."""
    pass


def get_db():
    """
    FastAPI dependency. Usage in a route:  db: Session = Depends(get_db)

    It opens a session, gives it to the request handler, and — crucially —
    closes it afterwards even if the handler raises. The `yield` makes this a
    generator-based dependency: code before yield runs on the way in, code in
    `finally` runs on the way out.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
