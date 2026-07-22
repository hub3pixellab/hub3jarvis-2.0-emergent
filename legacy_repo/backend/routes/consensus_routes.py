from fastapi import APIRouter, Depends
from pydantic import BaseModel
from modules.consensus import consensus_engine
from modules.second_brain import second_brain
from modules.self_learning import learning_engine
from middleware.auth_middleware import get_current_user

router = APIRouter()

class AskRequest(BaseModel):
    question: str

@router.post("/ask")
async def ask_jarvis(req: AskRequest, user: dict = Depends(get_current_user)):
    context = second_brain.get_context(req.question)
    result = await consensus_engine.query_all(
        req.question, user_plan=user["plan"], context=context
    )
    log_id = await learning_engine.log_interaction(
        user["id"], req.question, result["consensus"],
        result.get("best_model", "unknown"),
        result.get("confidence", 0),
        result.get("total_cost", 0)
    )
    return {**result, "log_id": log_id, "context_used": bool(context)}
