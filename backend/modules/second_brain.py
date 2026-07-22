"""
Second Brain — persistent long-term memory for Hub3 JARVIS v4.2
Absorbed from hub3pixellab/hub3jarvis (legacy) but rewritten to use MongoDB
instead of a JSON file, so it works out-of-the-box in the cloud environment.

Collections used:
- second_brain_knowledge : { id, content, source, k_type, user_id, created_at }
- second_brain_prefs     : { user_id, key, value, updated_at }
"""
import uuid
from datetime import datetime, timezone


class SecondBrain:
    def __init__(self, db):
        self.db = db
        self.knowledge = db.second_brain_knowledge
        self.prefs = db.second_brain_prefs

    async def add(self, user_id: str, content: str, source: str = "chat", k_type: str = "insight"):
        entry = {
            "id": f"kb_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "content": content,
            "source": source,
            "type": k_type,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await self.knowledge.insert_one(entry)
        entry.pop("_id", None)
        return entry

    async def search(self, user_id: str, query: str, limit: int = 5):
        """Keyword search — MongoDB $text or manual scoring."""
        q_lower = (query or "").lower()
        if not q_lower:
            return []
        keywords = [k for k in q_lower.split() if len(k) > 2]
        rows = await self.knowledge.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).limit(200).to_list(200)
        scored = []
        for r in rows:
            content = (r.get("content") or "").lower()
            score = sum(1 for kw in keywords if kw in content)
            if score > 0:
                scored.append({**r, "relevance_score": score})
        scored.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored[:limit]

    async def get_context(self, user_id: str, query: str, limit: int = 3) -> str:
        results = await self.search(user_id, query, limit)
        if not results:
            return ""
        parts = [f"[{r.get('source','brain')}] {r['content'][:300]}" for r in results]
        return "\n\n".join(parts)

    async def add_preference(self, user_id: str, key: str, value):
        await self.prefs.update_one(
            {"user_id": user_id, "key": key},
            {"$set": {"value": value, "updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True,
        )

    async def get_preferences(self, user_id: str):
        rows = await self.prefs.find({"user_id": user_id}, {"_id": 0}).to_list(100)
        return {r["key"]: r["value"] for r in rows}

    async def stats(self, user_id: str):
        total = await self.knowledge.count_documents({"user_id": user_id})
        prefs_total = await self.prefs.count_documents({"user_id": user_id})
        return {"total_knowledge": total, "total_preferences": prefs_total}

    async def list_recent(self, user_id: str, limit: int = 20):
        return await self.knowledge.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)


def make_second_brain(db):
    return SecondBrain(db)
