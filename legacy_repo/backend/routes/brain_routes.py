from fastapi import APIRouter, Depends
from pydantic import BaseModel
from modules.second_brain import second_brain
from middleware.auth_middleware import get_current_user

router = APIRouter()

class KnowledgeRequest(BaseModel):
    source: str
    content: str
    k_type: str = "text"

class PreferenceRequest(BaseModel):
    key: str
    value: str

@router.post("/upload")
async def upload_knowledge(req: KnowledgeRequest, user: dict = Depends(get_current_user)):
    entry = await second_brain.add_knowledge(req.source, req.content, req.k_type, user["id"])
    return {"status": "added", "entry": entry}

@router.get("/search")
async def search_brain(query: str, user: dict = Depends(get_current_user)):
    results = second_brain.search_sync(query)
    return {"query": query, "results": results, "count": len(results)}

@router.get("/stats")
async def brain_stats(user: dict = Depends(get_current_user)):
    return second_brain.get_stats()

@router.post("/preference")
async def set_preference(req: PreferenceRequest, user: dict = Depends(get_current_user)):
    await second_brain.add_preference(req.key, req.value)
    return {"status": "saved", "key": req.key}

@router.get("/preferences")
async def get_preferences(user: dict = Depends(get_current_user)):
    return second_brain.get_preferences()

@router.get("/history")
async def get_history(user: dict = Depends(get_current_user)):
    return second_brain.get_history()
