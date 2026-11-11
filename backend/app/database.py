"""Compatibility exports for older imports.

The application now uses app.db as its single engine, session, and model
metadata source. Keeping these names avoids creating a second SQLite database
for any remaining legacy imports.
"""

from .db import Base, DATABASE_URL, SessionLocal, engine, get_db

__all__ = ["Base", "DATABASE_URL", "SessionLocal", "engine", "get_db"]
