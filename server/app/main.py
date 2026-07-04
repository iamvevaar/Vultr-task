"""
Application entrypoint.

This creates the FastAPI app object that uvicorn runs (see the Dockerfile CMD:
`uvicorn app.main:app`). For P0 it only exposes a health check so we can prove
the API is up AND can reach Postgres. Real routers get mounted here as we build
each phase.
"""

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db

# The task specifies every route lives under /api. Setting a root_path-style
# prefix on each router (later) keeps that consistent. For now, the health route
# is explicit.
app = FastAPI(title="Challenge & Rewards Engine")


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    """
    Liveness + DB connectivity check.

    - If the API process is running, this handler executes at all.
    - We run a trivial `SELECT 1` to confirm the database is actually reachable,
      not just that the web server booted. Returns the two facts separately.
    """
    db.execute(text("SELECT 1"))  # raises if the DB is unreachable
    return {"status": "ok", "database": "connected"}
