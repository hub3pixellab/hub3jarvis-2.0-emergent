from fastapi import APIRouter, Depends
from pydantic import BaseModel
from modules.self_learning import learning_engine
from middleware.auth_middleware import get_current_user

router = APIRouter()

class FeedbackRequest(BaseModel):
    log_id: str
    feedback: str
    comment: str = ""

@router.post("/feedback")
async def add_feedback(req: FeedbackRequest, user: dict = Depends(get_current_user)):
    result = await learning_engine.add_feedback(req.log_id, req.feedback, req.comment)
    return result

@router.get("/patterns")
async def get_patterns(user: dict = Depends(get_current_user)):
    return await learning_engine.get_user_patterns(user["id"])
