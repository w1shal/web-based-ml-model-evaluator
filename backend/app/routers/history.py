
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import EvaluationRun, User
from ..services import history as svc

# MLE-SEC-003: every route below depends on get_current_user, so an unauthenticated
# request gets 401 before any handler code runs. The user identity always comes from
# the token, never from a client-supplied user id.
router = APIRouter(prefix="/history", tags=["history"])


def _owned_run(db: Session, user: User, run_id: str) -> EvaluationRun:
    run = svc.get_run(db, run_id)
    if run is None:
        raise HTTPException(404, "Run not found")
    if run.user_id != user.user_id:
        raise HTTPException(403, "You do not have access to this run")
    return run


@router.get("")
def list_history(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    runs, total = svc.list_runs(db, user.user_id, limit, offset)
    return {
        "items": [svc.run_summary(r) for r in runs],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{run_id}")
def get_history_entry(
    run_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return svc.run_detail(_owned_run(db, user, run_id))


@router.delete("/{run_id}")
def delete_history_entry(
    run_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc.delete_run(db, _owned_run(db, user, run_id))
    return {"message": "Run deleted"}
