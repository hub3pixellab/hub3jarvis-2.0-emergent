"""Orquestrador Autonomo JARVIS v4.2 — Loop continuo em background"""
import asyncio, time, os, json
from datetime import datetime, timezone
from modules.policy_engine import SENSITIVE_ACTIONS

class AutonomousOrchestrator:
    def __init__(self):
        self.status = {
            "online": False, "started_at": None, "last_cycle": None,
            "next_cycle": None, "cycle_count": 0, "cycle_interval_s": 30,
            "services": {}, "errors_recent": [], "policies_active": 0,
            "summary": "Inicializando..."
        }
        self._services = {}
        self._running = False

    def configure(self, services: dict):
        self._services = services
        self.status["policies_active"] = len(SENSITIVE_ACTIONS)

    async def start(self, app_state):
        self._running = True
        self.status["online"] = True
        self.status["started_at"] = datetime.now(timezone.utc).isoformat()
        asyncio.create_task(self._loop(app_state))

    async def stop(self):
        self._running = False
        self.status["online"] = False

    async def _loop(self, app_state):
        import httpx
        while self._running:
            try:
                for nome, url in self._services.items():
                    try:
                        async with httpx.AsyncClient(timeout=3.0) as c:
                            resp = await c.get(url)
                            self.status["services"][nome] = {"online": resp.status_code < 500, "code": resp.status_code, "last_check": datetime.now(timezone.utc).isoformat()}
                    except:
                        was = self.status["services"].get(nome, {}).get("online", False)
                        self.status["services"][nome] = {"online": False, "code": None, "last_check": datetime.now(timezone.utc).isoformat()}
                        if was:
                            self.status["errors_recent"].append({"time": datetime.now(timezone.utc).isoformat(), "error": f"Servico {nome} ficou offline"})
                agora = time.time()
                self.status["errors_recent"] = [e for e in self.status["errors_recent"] if (agora - datetime.fromisoformat(e["time"]).timestamp()) < 3600]
                self.status["cycle_count"] += 1
                self.status["last_cycle"] = datetime.now(timezone.utc).isoformat()
                self.status["next_cycle"] = datetime.fromtimestamp(time.time() + self.status["cycle_interval_s"], tz=timezone.utc).isoformat()
                online = sum(1 for s in self.status["services"].values() if s.get("online"))
                self.status["summary"] = f"{self.status['cycle_count']} ciclos | {online}/{len(self._services)} servicos online"
                if hasattr(app_state, 'orchestrator_status'):
                    app_state.orchestrator_status = self.status
            except Exception as e:
                self.status["errors_recent"].append({"time": datetime.now(timezone.utc).isoformat(), "error": str(e)[:100]})
                self.status["errors_recent"] = self.status["errors_recent"][-10:]
            await asyncio.sleep(self.status["cycle_interval_s"])

orchestrator = AutonomousOrchestrator()
