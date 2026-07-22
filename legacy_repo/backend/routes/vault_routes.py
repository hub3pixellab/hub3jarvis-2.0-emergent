from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel
from modules.knowledge_vault import knowledge_vault
from middleware.auth_middleware import get_current_user
import os
import tempfile

router = APIRouter()

@router.post("/upload")
async def upload_to_vault(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    tmp_path = os.path.join(tempfile.gettempdir(), file.filename)
    with open(tmp_path, "wb") as f:
        content = await file.read()
        f.write(content)
    result = await knowledge_vault.ingest_file(tmp_path, file.filename, user["id"])
    os.remove(tmp_path)
    return result

@router.get("/list")
async def list_vault(category: str = None, user: dict = Depends(get_current_user)):
    return await knowledge_vault.list_vault(category)

@router.get("/search")
async def search_vault(query: str, user: dict = Depends(get_current_user)):
    return await knowledge_vault.search_vault(query)

@router.get("/stats")
async def vault_stats(user: dict = Depends(get_current_user)):
    return await knowledge_vault.get_stats()

@router.get("/normativas")
async def get_normativas(user: dict = Depends(get_current_user)):
    return await knowledge_vault.load_normativas()
