from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def health():
    return {"status": "online", "service": "Hub3 JARVIS", "version": "4.1.0"}

@router.get("/db")
async def db_health():
    from modules.database import db_manager
    try:
        await db_manager.client.admin.command("ping")
        return {"database": "connected"}
    except Exception as e:
        return {"database": "error", "detail": str(e)}
