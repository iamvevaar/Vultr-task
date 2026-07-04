"""
Application entrypoint.

Creates the FastAPI app that uvicorn runs (see Dockerfile CMD:
`uvicorn app.main:app`). Here we:
  1. install the global error handlers (consistent error envelope), and
  2. mount each feature router under the /api base path.
"""

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.routes import auth, events
from app.core.database import get_db
from app.core.errors import install_error_handlers

app = FastAPI(title="Challenge & Rewards Engine")

# All errors now return the { "error": { code, message, details } } envelope.
install_error_handlers(app)

# The task mandates a /api base path. Every router is mounted under it, so
# auth.router's own "/auth" prefix yields final paths like /api/auth/register.
app.include_router(auth.router, prefix="/api")
app.include_router(events.router, prefix="/api")


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    """Liveness + DB connectivity check."""
    db.execute(text("SELECT 1"))  # raises if the DB is unreachable
    return {"status": "ok", "database": "connected"}
