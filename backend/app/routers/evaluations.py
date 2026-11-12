from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_optional_user
from ..ml.errors import EvaluationError
from ..ml.registry import list_algorithms
from ..schemas_evaluation import EvaluationRequest
from ..services import evaluation_service

router = APIRouter(prefix="/evaluations", tags=["evaluations"])
algorithms_router = APIRouter(prefix="/algorithms", tags=["algorithms"])


def _to_http_error(error: EvaluationError) -> HTTPException:
    headers = {"Retry-After": "5"} if error.status_code == 503 else None
    return HTTPException(error.status_code, error.message, headers=headers)


@algorithms_router.get("")
def algorithms():
    return {"items": [{"id": item.id, "name": item.name, "description": item.description}
                      for item in list_algorithms()]}


@router.post("")
def create_evaluation(body: EvaluationRequest, user=Depends(get_optional_user), db: Session = Depends(get_db)):
    user_id = user.user_id if user else None
    try:
        return evaluation_service.execute_evaluation(db, user_id, body)
    except EvaluationError as error:
        raise _to_http_error(error) from None


@router.get("/{run_id}")
def get_evaluation(run_id: str, user=Depends(get_optional_user), db: Session = Depends(get_db)):
    try:
        return evaluation_service.get_evaluation(db, run_id, user.user_id if user else None)
    except EvaluationError as error:
        raise _to_http_error(error) from None
