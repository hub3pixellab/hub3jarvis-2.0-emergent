from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from modules.auth import hash_password, verify_password, create_token, verify_google_token
from modules.database import db_manager
from datetime import datetime, timezone
import os

router = APIRouter()
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "diogo.zachioliveira@gmail.com")

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class GoogleAuthRequest(BaseModel):
    id_token: str

@router.post("/register")
async def register(req: RegisterRequest):
    existing = await db_manager.users.find_one({"email": req.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    plan = "admin" if req.email == ADMIN_EMAIL else "free"
    areas = ["you","goals","career","projects","finance","learning","health","relations"] if plan == "admin" else ["you","goals","career"]
    user_doc = {
        "name": req.name, "email": req.email,
        "password_hash": hash_password(req.password),
        "plan": plan, "provider": "email",
        "created_at": datetime.now(timezone.utc),
        "areas": areas, "whitelist": [],
        "preferences": {"language": "pt-BR", "tone": "formal-amigavel", "wake_word": "ei_hub"},
    }
    result = await db_manager.users.insert_one(user_doc)
    token = create_token(str(result.inserted_id), req.email, plan)
    return {"token": token, "user": {"id": str(result.inserted_id), "name": req.name, "email": req.email, "plan": plan, "areas": areas}}

@router.post("/login")
async def login(req: LoginRequest):
    user = await db_manager.users.find_one({"email": req.email})
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    token = create_token(str(user["_id"]), user["email"], user.get("plan", "free"))
    return {"token": token, "user": {"id": str(user["_id"]), "name": user["name"], "email": user["email"], "plan": user.get("plan","free")}}

@router.post("/google")
async def google_auth(req: GoogleAuthRequest):
    try:
        payload = await verify_google_token(req.id_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    email = payload["email"]
    name = payload.get("name", email.split("@")[0])
    picture = payload.get("picture", "")
    user = await db_manager.users.find_one({"email": email})
    if not user:
        plan = "admin" if email == ADMIN_EMAIL else "free"
        areas = ["you","goals","career","projects","finance","learning","health","relations"] if plan == "admin" else ["you","goals","career"]
        user_doc = {
            "name": name, "email": email, "avatar": picture,
            "plan": plan, "provider": "google",
            "created_at": datetime.now(timezone.utc),
            "areas": areas, "whitelist": [],
            "preferences": {"language": "pt-BR", "tone": "formal-amigavel", "wake_word": "ei_hub"},
        }
        result = await db_manager.users.insert_one(user_doc)
        user_id = str(result.inserted_id)
        plan_val = plan
    else:
        user_id = str(user["_id"])
        plan_val = user.get("plan", "free")
    token = create_token(user_id, email, plan_val)
    return {"token": token, "user": {"id": user_id, "name": name, "email": email, "plan": plan_val}}
