"""Seed a demo user with a few evaluation runs, for the Sprint 2 demo video.

Run from the backend folder:   python scripts/seed_history.py
Then log in as  demo / Demo12345  and open frontend/history.html
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.db import SessionLocal, engine  # noqa: E402
from app.models import Base, User  # noqa: E402
from app.security import hash_password  # noqa: E402
from app.services.history import save_run  # noqa: E402

Base.metadata.create_all(engine)

RUNS = [
    ("iris.csv", "species", ["sepal_length", "sepal_width", "petal_length", "petal_width"], [
        ("logistic_regression", 0.97, 0.97, 0.97, 0.97, None, [[10, 0, 0], [0, 9, 1], [0, 0, 10]]),
        ("random_forest", 1.0, 1.0, 1.0, 1.0, None, [[10, 0, 0], [0, 10, 0], [0, 0, 10]]),
    ]),
    ("breast_cancer.csv", "diagnosis", ["radius_mean", "texture_mean", "area_mean"], [
        ("svm", 0.95, 0.95, 0.94, 0.945, 0.98, [[70, 2], [4, 38]]),
        ("knn", 0.93, 0.92, 0.92, 0.92, 0.96, [[68, 4], [4, 38]]),
        ("decision_tree", 0.91, 0.9, 0.9, 0.9, 0.9, [[66, 6], [4, 38]]),
    ]),
]

with SessionLocal() as db:
    user = db.scalar(select(User).where(User.username == "demo"))
    if user is None:
        user = User(username="demo", email="demo@example.com", password_hash=hash_password("Demo12345"))
        db.add(user)
        db.commit()
        db.refresh(user)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for n, (name, target, feats, results) in enumerate(RUNS):
        save_run(
            db, user.user_id, dataset_name=name, target_column=target, feature_columns=feats,
            split_ratio=0.2, timestamp=now - timedelta(hours=len(RUNS) - n),
            results=[dict(zip(["algorithm", "accuracy", "precision", "recall", "f1_score", "roc_auc",
                               "confusion_matrix"], r)) for r in results],
        )
    print(f"Seeded {len(RUNS)} runs for user 'demo' (password: Demo12345)")
