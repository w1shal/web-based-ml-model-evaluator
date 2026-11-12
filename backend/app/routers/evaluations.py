from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_optional_user
from ..ml.errors import EvaluationError
from ..ml.registry import list_algorithms
from ..schemas_evaluation import EvaluationRequest
from ..services import evaluation_service

router = APIRouter(prefix="/evaluations", tags=["evaluations"])
algorithms_router = APIRouter(prefix="/algorithms", tags=["algorithms"])


@algorithms_router.get("")
def algorithms():
    """Return registered algorithms (MLE-F-013)."""
    return {"items": [{"id": a.id, "name": a.name, "description": a.description} for a in list_algorithms()]}


@router.post("")
def create_evaluation(body: EvaluationRequest, user=Depends(get_optional_user)):
    """Run selected algorithms synchronously for a guest or authenticated user."""
    try:
        return evaluation_service.execute_evaluation(user.user_id if user else None, body)
    except EvaluationError as exc:
        raise HTTPException(exc.status_code, exc.message) from None
