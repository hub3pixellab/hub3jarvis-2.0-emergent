from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from modules.auth import decode_token
from modules.database import db_manager
from bson import ObjectId
import os

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    user = await db_manager.users.find_one({"_id": ObjectId(payload["sub"])})
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return {
        "id": str(user["_id"]), "email": user["email"],
        "name": user["name"], "plan": user.get("plan", "free"),
        "areas": user.get("areas", ["you", "goals", "career"]),
    }

async def get_admin_user(user: dict = Depends(get_current_user)):
    admin_email = os.getenv("ADMIN_EMAIL", "")
    if user.get("plan") != "admin" and user.get("email") != admin_email:
        raise HTTPException(status_code=403, detail="Acesso restrito ao administrador")
    return user
