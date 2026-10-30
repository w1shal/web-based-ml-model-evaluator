
from sqlalchemy import inspect

from backend.app.database import Base, engine
from backend.app import models


def test_database_tables_created():
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    assert "users" in table_names
    assert "evaluation_runs" in table_names
    assert "algorithm_results" in table_names
