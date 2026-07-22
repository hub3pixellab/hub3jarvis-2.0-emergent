from dotenv import load_dotenv
from pathlib import Path
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

import os
import json
import uuid
import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import List, Optional

import jwt
import bcrypt
from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr

from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone

# Absorbed from hub3pixellab/hub3jarvis (legacy repo)
import sys
sys.path.insert(0, str(Path(__file__).parent))
from modules.policy_engine import policy_engine
from modules.second_brain import make_second_brain
from modules.self_learning import make_learning_engine

# ------ Setup ------
MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']
JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGO = "HS256"
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]
second_brain = make_second_brain(db)
learning_engine = make_learning_engine(db)

app = FastAPI(title="Hub3 JARVIS v4.2")
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hub3")

# ------ Password / JWT helpers ------
def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id, "email": email, "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# ------ Models ------
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1, max_length=80)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class GoogleAuthIn(BaseModel):
    session_id: str

class ConsensusQuery(BaseModel):
    question: str = Field(min_length=1, max_length=2000)

class ChatMessageIn(BaseModel):
    text: str
    conversation_id: Optional[str] = None

class DeviceToggleIn(BaseModel):
    device_id: str
    state: dict

class BrainAddIn(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    source: str = "chat"
    k_type: str = "insight"

class BrainSearchIn(BaseModel):
    query: str
    limit: int = 5

class BrainPrefIn(BaseModel):
    key: str
    value: str

class FeedbackIn(BaseModel):
    log_id: str
    feedback: str  # positive | negative | neutral
    comment: str = ""

class PolicyCheckIn(BaseModel):
    action: str
    context: dict = {}

class BrainImportIn(BaseModel):
    items: list  # [{content, source?, type?, created_at?}]

class BrainSearchModeIn(BaseModel):
    query: str
    limit: int = 5
    mode: str = "auto"  # auto | semantic | keyword

# ------ Auth Endpoints ------
@api_router.post("/auth/register")
async def register(body: RegisterIn, response: Response):
    email = body.email.lower().strip()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = str(uuid.uuid4())
    doc = {
        "id": user_id,
        "email": email,
        "name": body.name,
        "password_hash": hash_password(body.password),
        "role": "user",
        "avatar": None,
        "provider": "local",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one(doc)
    token = create_access_token(user_id, email)
    response.set_cookie("access_token", token, httponly=True, secure=True, samesite="none", max_age=60*60*24*7, path="/")
    return {"id": user_id, "email": email, "name": body.name, "role": "user", "provider": "local", "token": token}

@api_router.post("/auth/login")
async def login(body: LoginIn, response: Response):
    email = body.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(body.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user["id"], email)
    response.set_cookie("access_token", token, httponly=True, secure=True, samesite="none", max_age=60*60*24*7, path="/")
    return {"id": user["id"], "email": email, "name": user["name"], "role": user.get("role", "user"), "provider": user.get("provider", "local"), "token": token}

@api_router.post("/auth/google")
async def google_auth(body: GoogleAuthIn, response: Response):
    """Emergent Managed Google Auth: exchanges session_id for user data."""
    import httpx
    async with httpx.AsyncClient(timeout=15) as hc:
        r = await hc.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": body.session_id},
        )
    if r.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Google session")
    data = r.json()
    email = data["email"].lower()
    existing = await db.users.find_one({"email": email})
    if existing:
        user_id = existing["id"]
        await db.users.update_one({"id": user_id}, {"$set": {"avatar": data.get("picture"), "name": data.get("name") or existing.get("name")}})
        name = data.get("name") or existing.get("name")
    else:
        user_id = str(uuid.uuid4())
        await db.users.insert_one({
            "id": user_id, "email": email, "name": data.get("name", email),
            "avatar": data.get("picture"), "role": "user", "provider": "google",
            "password_hash": "", "created_at": datetime.now(timezone.utc).isoformat(),
        })
        name = data.get("name", email)
    token = create_access_token(user_id, email)
    response.set_cookie("access_token", token, httponly=True, secure=True, samesite="none", max_age=60*60*24*7, path="/")
    return {"id": user_id, "email": email, "name": name, "avatar": data.get("picture"), "role": "user", "provider": "google", "token": token}

@api_router.get("/auth/me")
async def me(user=Depends(get_current_user)):
    return user

@api_router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"ok": True}

# ------ Consensus Engine ------
CONSENSUS_MODELS = [
    {"key": "claude", "provider": "anthropic", "model": "claude-sonnet-4-6", "display": "Claude Sonnet 4.6", "cost_per_1k": 0.003, "icon": "A"},
    {"key": "openai", "provider": "openai", "model": "gpt-5.4", "display": "GPT-5.4 Turbo", "cost_per_1k": 0.005, "icon": "G"},
    {"key": "gemini", "provider": "gemini", "model": "gemini-3-flash-preview", "display": "Gemini 3 Flash", "cost_per_1k": 0.002, "icon": "S"},
]

def _score_response(text: str) -> dict:
    """Heuristic scoring: length, structure, clarity."""
    if not text:
        return {"relevance": 0, "accuracy": 0, "completeness": 0, "clarity": 0, "recency": 0, "total": 0}
    length = len(text)
    words = len(text.split())
    has_structure = 1 if any(m in text for m in ["\n-", "\n•", "\n1.", "\n2.", "**", "###"]) else 0
    completeness = min(100, int(words / 3))
    clarity = 90 if has_structure else 75
    relevance = min(100, 60 + words // 10)
    accuracy = 85 + (5 if length > 500 else 0)
    recency = 80
    total = int(0.30*relevance + 0.25*accuracy + 0.20*completeness + 0.15*clarity + 0.10*recency)
    return {"relevance": relevance, "accuracy": accuracy, "completeness": completeness, "clarity": clarity, "recency": recency, "total": min(99, max(70, total))}

async def _call_model(m: dict, question: str):
    t0 = time.time()
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"consensus-{uuid.uuid4()}",
            system_message="You are one of several AI models in a consensus engine. Provide a concise, well-structured answer (150-250 words) with clarity and factual accuracy.",
        ).with_model(m["provider"], m["model"])
        resp = await chat.send_message(UserMessage(text=question))
        text = resp if isinstance(resp, str) else str(resp)
        scores = _score_response(text)
        latency = round(time.time() - t0, 2)
        tokens_est = max(1, len(text) // 4)
        cost = round((tokens_est / 1000) * m["cost_per_1k"], 5)
        return {
            "key": m["key"], "display": m["display"], "provider": m["provider"], "model": m["model"],
            "icon": m["icon"], "response": text, "scores": scores, "confidence": scores["total"],
            "latency": latency, "cost": cost, "tokens": tokens_est, "error": None,
        }
    except Exception as e:
        logger.error(f"Model {m['key']} failed: {e}")
        return {
            "key": m["key"], "display": m["display"], "provider": m["provider"], "model": m["model"],
            "icon": m["icon"], "response": f"[Model temporarily unavailable]",
            "scores": {"relevance":0,"accuracy":0,"completeness":0,"clarity":0,"recency":0,"total":0},
            "confidence": 0, "latency": round(time.time() - t0, 2), "cost": 0, "tokens": 0, "error": str(e)[:200],
        }

@api_router.post("/consensus/query")
async def consensus_query(body: ConsensusQuery, user=Depends(get_current_user)):
    t0 = time.time()
    # Second Brain: inject relevant context
    brain_context = await second_brain.get_context(user["id"], body.question, 3)
    prompt = body.question if not brain_context else f"[Second Brain context]\n{brain_context}\n\n[User question]\n{body.question}"
    results = await asyncio.gather(*[_call_model(m, prompt) for m in CONSENSUS_MODELS])
    ranked = sorted(results, key=lambda r: r["confidence"], reverse=True)
    winner = ranked[0] if ranked else None
    total_cost = round(sum(r["cost"] for r in results), 5)
    total_time = round(time.time() - t0, 2)
    confidences = [r["confidence"] for r in results if r["confidence"] > 0]
    avg_conf = int(sum(confidences)/len(confidences)) if confidences else 0
    spread = (max(confidences) - min(confidences)) if len(confidences) > 1 else 0
    agreement = "High" if spread < 10 else ("Medium" if spread < 20 else "Low")

    # Self-Learning: log the interaction
    log_id = None
    if winner and winner.get("response"):
        log_id = await learning_engine.log_interaction(
            user["id"], body.question, winner["response"],
            winner["display"], winner["confidence"] / 100.0, total_cost,
        )

    record = {
        "id": str(uuid.uuid4()), "user_id": user["id"], "question": body.question,
        "winner_key": winner["key"] if winner else None, "confidence": winner["confidence"] if winner else 0,
        "total_cost": total_cost, "total_time": total_time, "avg_confidence": avg_conf,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.consensus_queries.insert_one({**record, "results": results})

    return {
        "id": record["id"],
        "question": body.question,
        "results": results,
        "ranked": [{"key": r["key"], "display": r["display"], "icon": r["icon"], "confidence": r["confidence"]} for r in ranked],
        "winner": winner,
        "log_id": log_id,
        "context_used": bool(brain_context),
        "metrics": {
            "total_cost": total_cost, "total_time": total_time,
            "models_responded": sum(1 for r in results if r["error"] is None),
            "models_total": len(results),
            "consensus_confidence": winner["confidence"] if winner else 0,
            "avg_confidence": avg_conf, "agreement_level": agreement,
        },
    }

@api_router.get("/consensus/history")
async def consensus_history(user=Depends(get_current_user)):
    rows = await db.consensus_queries.find(
        {"user_id": user["id"]}, {"_id": 0, "results": 0}
    ).sort("created_at", -1).limit(20).to_list(20)
    return rows

# ------ Dashboard data (Life OS) ------
LIFE_AREAS = [
    {"key": "you", "en": "You", "pt": "Você", "sub_en": "Self Awareness & Growth", "sub_pt": "Autoconhecimento & Crescimento", "color": "#00D4FF", "icon": "user"},
    {"key": "goals", "en": "Goals", "pt": "Metas", "sub_en": "Plan, Track & Achieve", "sub_pt": "Planejar, Acompanhar & Alcançar", "color": "#FF8C42", "icon": "target"},
    {"key": "career", "en": "Career", "pt": "Carreira", "sub_en": "Growth & Opportunities", "sub_pt": "Crescimento & Oportunidades", "color": "#00D4FF", "icon": "briefcase"},
    {"key": "projects", "en": "Projects", "pt": "Projetos", "sub_en": "Build & Manage", "sub_pt": "Construir & Gerenciar", "color": "#00D4FF", "icon": "layers"},
    {"key": "finance", "en": "Finance", "pt": "Finanças", "sub_en": "Wealth & Stability", "sub_pt": "Riqueza & Estabilidade", "color": "#FF8C42", "icon": "dollar-sign"},
    {"key": "learning", "en": "Learning", "pt": "Aprendizado", "sub_en": "Knowledge & Skills", "sub_pt": "Conhecimento & Habilidades", "color": "#00D4FF", "icon": "book-open"},
    {"key": "health", "en": "Health", "pt": "Saúde", "sub_en": "Wellness & Fitness", "sub_pt": "Bem-estar & Fitness", "color": "#FF4757", "icon": "heart-pulse"},
    {"key": "relations", "en": "Relations", "pt": "Relações", "sub_en": "Connect & Nurture", "sub_pt": "Conectar & Nutrir", "color": "#FF8C42", "icon": "users"},
]

@api_router.get("/dashboard/overview")
async def dashboard_overview(user=Depends(get_current_user)):
    return {
        "life_areas": LIFE_AREAS,
        "life_balance": {"score": 78, "label_en": "Balanced", "label_pt": "Equilibrado"},
        "metrics": [
            {"key": "insights", "label_en": "Insights Today", "label_pt": "Insights Hoje", "value": 28, "delta": 18, "icon": "lightbulb"},
            {"key": "decisions", "label_en": "Decisions Supported", "label_pt": "Decisões Apoiadas", "value": 7, "delta": 12, "icon": "share-2"},
            {"key": "time_saved", "label_en": "Time Saved", "label_pt": "Tempo Salvo", "value": "2.4h", "delta": 22, "icon": "clock"},
            {"key": "momentum", "label_en": "Life Momentum", "label_pt": "Momentum de Vida", "value": "85%", "delta": 15, "icon": "trending-up"},
        ],
        "top_recommendation": {
            "title_en": "Focus on Project Orion",
            "title_pt": "Foque no Projeto Orion",
            "desc_en": "High impact opportunity aligned with your goals and career growth.",
            "desc_pt": "Oportunidade de alto impacto alinhada com suas metas e crescimento de carreira.",
            "consensus": 92,
        },
        "next_best_action": {
            "title_en": "Review Q2 financial plan",
            "title_pt": "Revise o plano financeiro do 2º trimestre",
            "desc_en": "Optimize investments and reduce unnecessary expenses.",
            "desc_pt": "Otimize investimentos e reduza gastos desnecessários.",
            "impact": 88,
        },
        "ai_models_breakdown": [
            {"name": "GPT-4o", "score": 94, "icon": "G"},
            {"name": "Claude 3.5", "score": 91, "icon": "A"},
            {"name": "Gemini 1.5", "score": 89, "icon": "S"},
            {"name": "Llama 3.1", "score": 86, "icon": "L"},
            {"name": "Mistral Large", "score": 84, "icon": "M"},
            {"name": "Perplexity", "score": 82, "icon": "P"},
            {"name": "Cohere Command", "score": 80, "icon": "C"},
            {"name": "Phi-3", "score": 78, "icon": "P"},
        ],
        "quote": {
            "en": '"The best way to predict the future is to create it." — Peter Drucker',
            "pt": '"A melhor forma de prever o futuro é criá-lo." — Peter Drucker',
        },
    }

# ------ Smart Home (mocked but stateful) ------
DEFAULT_DEVICES = {
    "lights": {"online": True, "on": True, "brightness": 75, "color": "#00D4FF", "scene": "Relax"},
    "thermostat": {"online": True, "on": True, "temp": 24.5, "target": 22, "mode": "cooling"},
    "cameras": {"online": True, "count": 4, "recording": True},
    "tv": {"online": True, "on": True, "input": "HDMI 1", "app": "Playing"},
    "lock": {"online": True, "locked": True},
    "speaker": {"online": True, "on": True, "volume": 60, "bluetooth": True},
    "wearable": {"online": True, "hr": 72, "steps": 8432, "sleep": "7h 24m", "calories": 562, "spo2": 98},
    "plugs": {"online": True, "list": [
        {"name": "Kitchen Plug", "on": True, "w": 125, "kwh": 0.62, "online": True},
        {"name": "Office Plug", "on": True, "w": 78, "kwh": 0.38, "online": True},
        {"name": "Bedroom Plug", "on": False, "w": 0, "kwh": 0, "online": False},
    ]},
}

async def _get_devices(user_id):
    doc = await db.smart_home.find_one({"user_id": user_id}, {"_id": 0})
    if not doc:
        doc = {"user_id": user_id, "devices": DEFAULT_DEVICES}
        await db.smart_home.insert_one(doc)
    return doc["devices"]

@api_router.get("/smart-home/state")
async def smart_home_state(user=Depends(get_current_user)):
    devices = await _get_devices(user["id"])
    return {"devices": devices, "network": True, "security_active": True, "devices_online": 11, "devices_total": 12}

@api_router.post("/smart-home/toggle")
async def smart_home_toggle(body: DeviceToggleIn, user=Depends(get_current_user)):
    devices = await _get_devices(user["id"])
    if body.device_id not in devices:
        raise HTTPException(status_code=404, detail="Device not found")
    devices[body.device_id] = {**devices[body.device_id], **body.state}
    await db.smart_home.update_one({"user_id": user["id"]}, {"$set": {"devices": devices}}, upsert=True)
    return {"device_id": body.device_id, "state": devices[body.device_id]}

# ------ Chat ------
JARVIS_SYSTEM = """You are Hub3 Jarvis, a friendly, concise smart-home + life OS AI assistant.
Reply in the user's language (Portuguese or English). Keep answers short (1-3 sentences).
When the user asks to control devices (lights, thermostat, camera, TV, lock, speaker), respond confirming the action naturally and mention the device state.
Mix helpfulness with slight personality (like JARVIS from Iron Man)."""

@api_router.post("/chat/send")
async def chat_send(body: ChatMessageIn, user=Depends(get_current_user)):
    conv_id = body.conversation_id or str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    # Policy Engine: check device_control if command detected
    lowered = body.text.lower()
    is_device_cmd = any(k in lowered for k in ["luz", "light", "acend", "apag", "termostato", "thermostat", "câmera", "camera", "tv", "trancar", "destrancar", "lock", "unlock"])
    policy_warning = None
    if is_device_cmd:
        pol = await policy_engine.evaluate(user["id"], "device_control", {}, db)
        if pol["warnings"]:
            policy_warning = pol["warnings"][0]
        if not pol["allowed"]:
            await db.chat_messages.insert_one({
                "id": str(uuid.uuid4()), "conversation_id": conv_id, "user_id": user["id"],
                "role": "user", "text": body.text, "created_at": now,
            })
            blocked_msg = f"⛔ {pol['warnings'][0]}"
            await db.chat_messages.insert_one({
                "id": str(uuid.uuid4()), "conversation_id": conv_id, "user_id": user["id"],
                "role": "assistant", "text": blocked_msg, "created_at": now,
            })
            return {"conversation_id": conv_id, "reply": blocked_msg, "inline_card": None, "policy_blocked": True, "created_at": now}

    # Save user message
    await db.chat_messages.insert_one({
        "id": str(uuid.uuid4()), "conversation_id": conv_id, "user_id": user["id"],
        "role": "user", "text": body.text, "created_at": now,
    })

    # Second Brain: inject context
    brain_context = await second_brain.get_context(user["id"], body.text, 3)
    prompt = body.text if not brain_context else f"[Second Brain]\n{brain_context}\n\n[User]\n{body.text}"

    reply_text = "Ok, feito!"
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"jarvis-{conv_id}",
            system_message=JARVIS_SYSTEM,
        ).with_model("anthropic", "claude-sonnet-4-6")
        resp = await chat.send_message(UserMessage(text=prompt))
        reply_text = resp if isinstance(resp, str) else str(resp)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        reply_text = "Estou com problemas para responder agora. / I'm having trouble responding right now."

    inline_card = "devices_snapshot" if is_device_cmd else None
    now2 = datetime.now(timezone.utc).isoformat()
    ai_msg = {
        "id": str(uuid.uuid4()), "conversation_id": conv_id, "user_id": user["id"],
        "role": "assistant", "text": reply_text, "created_at": now2, "inline_card": inline_card,
        "policy_warning": policy_warning,
    }
    await db.chat_messages.insert_one(ai_msg)

    # Second Brain: memorize salient short user messages (>20 chars, not a device cmd)
    if len(body.text) > 20 and not is_device_cmd:
        try:
            await second_brain.add(user["id"], body.text, source="chat", k_type="conversation")
        except Exception:
            pass

    return {"conversation_id": conv_id, "reply": reply_text, "inline_card": inline_card,
             "policy_warning": policy_warning, "created_at": now2}

@api_router.get("/chat/history/{conv_id}")
async def chat_history(conv_id: str, user=Depends(get_current_user)):
    rows = await db.chat_messages.find(
        {"conversation_id": conv_id, "user_id": user["id"]}, {"_id": 0}
    ).sort("created_at", 1).to_list(500)
    return rows

# ------ Streaming chat via SSE ------
@api_router.get("/chat/stream")
async def chat_stream(text: str, conversation_id: str = "jarvis", token: str = "", request: Request = None):
    """SSE endpoint. Token is passed as ?token= because EventSource cannot set headers."""
    # Manual auth (EventSource doesn't send Authorization headers)
    real_token = token or (request.cookies.get("access_token") if request else "")
    if not real_token:
        auth = request.headers.get("Authorization", "") if request else ""
        if auth.startswith("Bearer "):
            real_token = auth[7:]
    if not real_token:
        raise HTTPException(401, "Not authenticated")
    try:
        payload = jwt.decode(real_token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")
    user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(401, "User not found")

    conv_id = conversation_id
    now = datetime.now(timezone.utc).isoformat()

    # Policy check (device commands)
    lowered = text.lower()
    is_device_cmd = any(k in lowered for k in ["luz", "light", "acend", "apag", "termostato", "thermostat", "câmera", "camera", " tv", "trancar", "destrancar", "lock", "unlock"])

    await db.chat_messages.insert_one({
        "id": str(uuid.uuid4()), "conversation_id": conv_id, "user_id": user["id"],
        "role": "user", "text": text, "created_at": now,
    })

    # Second Brain context
    brain_context = await second_brain.get_context(user["id"], text, 3)
    prompt = text if not brain_context else f"[Second Brain]\n{brain_context}\n\n[User]\n{text}"

    async def event_gen():
        # Send meta first
        meta = {"conversation_id": conv_id, "context_used": bool(brain_context), "inline_card": "devices_snapshot" if is_device_cmd else None}
        yield f"event: meta\ndata: {json.dumps(meta)}\n\n"
        collected = []
        try:
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"jarvis-stream-{conv_id}",
                system_message=JARVIS_SYSTEM,
            ).with_model("anthropic", "claude-sonnet-4-6")
            async for ev in chat.stream_message(UserMessage(text=prompt)):
                if isinstance(ev, TextDelta):
                    collected.append(ev.content)
                    yield f"data: {json.dumps({'delta': ev.content})}\n\n"
                elif isinstance(ev, StreamDone):
                    break
        except Exception as e:
            logger.error(f"stream error: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)[:200]})}\n\n"
        full = "".join(collected) or "Sem resposta."
        now2 = datetime.now(timezone.utc).isoformat()
        await db.chat_messages.insert_one({
            "id": str(uuid.uuid4()), "conversation_id": conv_id, "user_id": user["id"],
            "role": "assistant", "text": full, "created_at": now2,
            "inline_card": "devices_snapshot" if is_device_cmd else None,
        })
        if len(text) > 20 and not is_device_cmd:
            try: await second_brain.add(user["id"], text, source="chat", k_type="conversation")
            except Exception: pass
        yield f"event: done\ndata: {json.dumps({'text': full, 'created_at': now2})}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"})

@api_router.get("/chat/conversations")
async def chat_conversations(user=Depends(get_current_user)):
    # Static list of mocked conversations + current Jarvis
    return [
        {"id": "jarvis", "name": "Hub3 Jarvis", "avatar_type": "jarvis", "last": "online", "time": "10:24", "unread": 1, "pinned": True},
        {"id": "family", "name": "Family Group", "avatar_type": "group", "last": "Laura: Obrigado!", "time": "09:15", "unread": 2},
        {"id": "diego", "name": "Diego", "avatar_type": "user", "last": "Vamos nos encontrar?", "time": "Ontem", "unread": 0},
        {"id": "trabalho", "name": "Trabalho", "avatar_type": "work", "last": "Marcos: Reunião às 11h", "time": "Ontem", "unread": 0, "muted": True},
        {"id": "ana", "name": "Ana Paula", "avatar_type": "user", "last": "Perfeito, até lá!", "time": "Ontem", "unread": 0},
        {"id": "casa", "name": "Casa Inteligente", "avatar_type": "home", "last": "Alarme desativado", "time": "Sábado", "unread": 1},
        {"id": "suporte", "name": "Suporte Hub3", "avatar_type": "support", "last": "Como podemos ajudar?", "time": "Sexta-feira", "unread": 0},
    ]

# ------ Second Brain (absorbed from legacy repo) ------
@api_router.post("/brain/add")
async def brain_add(body: BrainAddIn, user=Depends(get_current_user)):
    entry = await second_brain.add(user["id"], body.content, body.source, body.k_type)
    return entry

@api_router.post("/brain/search")
async def brain_search(body: BrainSearchModeIn, user=Depends(get_current_user)):
    return await second_brain.search(user["id"], body.query, body.limit, body.mode)

@api_router.post("/brain/import")
async def brain_import_json(body: BrainImportIn, user=Depends(get_current_user)):
    """Bulk import from JSON body: {items: [{content, source?, type?, created_at?}]}"""
    return await second_brain.add_bulk(user["id"], body.items)

@api_router.post("/brain/import-file")
async def brain_import_file(file: UploadFile = File(...), user=Depends(get_current_user)):
    """Bulk import from uploaded JSON file. Accepts either a JSON array or a {knowledge:[...]} object (legacy second-brain.json format)."""
    import json as _json
    raw = await file.read()
    try:
        payload = _json.loads(raw.decode("utf-8"))
    except Exception as e:
        raise HTTPException(400, f"Invalid JSON: {e}")
    items = payload if isinstance(payload, list) else payload.get("knowledge", [])
    if not isinstance(items, list):
        raise HTTPException(400, "JSON must be an array or object with 'knowledge' array")
    return await second_brain.add_bulk(user["id"], items)

@api_router.post("/brain/reindex")
async def brain_reindex(user=Depends(get_current_user)):
    return await second_brain.reindex_missing(user["id"])

@api_router.get("/brain/recent")
async def brain_recent(user=Depends(get_current_user)):
    return await second_brain.list_recent(user["id"], 20)

@api_router.get("/brain/stats")
async def brain_stats(user=Depends(get_current_user)):
    return await second_brain.stats(user["id"])

@api_router.post("/brain/pref")
async def brain_set_pref(body: BrainPrefIn, user=Depends(get_current_user)):
    await second_brain.add_preference(user["id"], body.key, body.value)
    return {"ok": True}

@api_router.get("/brain/prefs")
async def brain_get_prefs(user=Depends(get_current_user)):
    return await second_brain.get_preferences(user["id"])

# ------ Self-Learning (absorbed from legacy repo) ------
@api_router.post("/learning/feedback")
async def learning_feedback(body: FeedbackIn, user=Depends(get_current_user)):
    return await learning_engine.add_feedback(body.log_id, body.feedback, body.comment)

@api_router.get("/learning/patterns")
async def learning_patterns(user=Depends(get_current_user)):
    return await learning_engine.get_user_patterns(user["id"])

@api_router.get("/learning/recent")
async def learning_recent(user=Depends(get_current_user)):
    return await learning_engine.recent(user["id"], 10)

# ------ Policy Engine (absorbed from legacy repo) ------
@api_router.post("/policy/check")
async def policy_check(body: PolicyCheckIn, user=Depends(get_current_user)):
    return await policy_engine.evaluate(user["id"], body.action, body.context, db)

@api_router.get("/policy/whitelist")
async def policy_whitelist_list(user=Depends(get_current_user)):
    rows = await db.whitelist.find({"user_id": user["id"]}, {"_id": 0}).to_list(200)
    return rows

@api_router.post("/policy/whitelist")
async def policy_whitelist_add(body: dict, user=Depends(get_current_user)):
    phone = body.get("phone"); name = body.get("name"); level = body.get("level", "absolute")
    if not phone or not name:
        raise HTTPException(400, "phone and name required")
    await db.whitelist.update_one(
        {"user_id": user["id"], "phone": phone},
        {"$set": {"user_id": user["id"], "phone": phone, "name": name, "level": level,
                   "created_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    return {"ok": True}

# ------ Startup ------
@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id", unique=True)
    await db.second_brain_knowledge.create_index([("user_id", 1), ("created_at", -1)])
    await db.second_brain_prefs.create_index([("user_id", 1), ("key", 1)], unique=True)
    await db.learning_logs.create_index([("user_id", 1), ("created_at", -1)])
    await db.whitelist.create_index([("user_id", 1), ("phone", 1)], unique=True)
    # Warm up embeddings model in the background so first user call is fast
    try:
        from modules.embeddings import ensure_loaded
        asyncio.create_task(ensure_loaded())
        logger.info("Embeddings warm-up task scheduled")
    except Exception as e:
        logger.warning(f"embeddings warm-up skipped: {e}")
    # Seed admin
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@hub3.ai").lower()
    admin_password = os.environ.get("ADMIN_PASSWORD", "Hub3Admin!2026")
    existing = await db.users.find_one({"email": admin_email})
    if not existing:
        await db.users.insert_one({
            "id": str(uuid.uuid4()), "email": admin_email, "name": "Admin",
            "password_hash": hash_password(admin_password), "role": "admin",
            "provider": "local", "avatar": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info(f"Admin seeded: {admin_email}")
    elif not verify_password(admin_password, existing.get("password_hash", "")):
        await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}})
        logger.info("Admin password updated")

@app.on_event("shutdown")
async def shutdown():
    client.close()

@api_router.get("/")
async def root():
    return {"service": "Hub3 JARVIS v4.2", "status": "online"}

app.include_router(api_router)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
