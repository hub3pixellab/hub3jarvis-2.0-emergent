"""
Second Brain v2 — persistent memory with semantic vector search (fastembed).
Absorbed from hub3pixellab/hub3jarvis (legacy) and upgraded to real embeddings.

MongoDB collections:
- second_brain_knowledge : { id, user_id, content, source, type, embedding[float,384], created_at }
- second_brain_prefs     : { user_id, key, value, updated_at }
"""
import uuid
from datetime import datetime, timezone
from modules.embeddings import embed_texts, embed_query, cosine, rank_by_similarity


class SecondBrain:
    def __init__(self, db):
        self.db = db
        self.knowledge = db.second_brain_knowledge
        self.prefs = db.second_brain_prefs

    async def add(self, user_id: str, content: str, source: str = "chat", k_type: str = "insight"):
        try:
            vec = (await embed_texts([content]))[0]
        except Exception:
            vec = None
        entry = {
            "id": f"kb_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "content": content,
            "source": source,
            "type": k_type,
            "embedding": vec,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await self.knowledge.insert_one(entry)
        e = {**entry}
        e.pop("_id", None)
        # Strip embedding from response (large)
        e.pop("embedding", None)
        e["has_embedding"] = vec is not None
        return e

    async def add_bulk(self, user_id: str, items: list):
        """items = [{content, source?, type?}]. Batches embeddings for speed."""
        if not items:
            return {"inserted": 0}
        contents = [i.get("content", "") for i in items if i.get("content")]
        if not contents:
            return {"inserted": 0}
        try:
            vecs = await embed_texts(contents)
        except Exception:
            vecs = [None] * len(contents)
        now = datetime.now(timezone.utc).isoformat()
        docs = []
        for it, vec in zip(items, vecs):
            docs.append({
                "id": f"kb_{uuid.uuid4().hex[:12]}",
                "user_id": user_id,
                "content": it.get("content", ""),
                "source": it.get("source", "import"),
                "type": it.get("type", "insight"),
                "embedding": vec,
                "created_at": it.get("created_at", now),
            })
        if docs:
            await self.knowledge.insert_many(docs)
        return {"inserted": len(docs)}

    async def _keyword_search(self, user_id: str, query: str, limit: int):
        q_lower = (query or "").lower()
        keywords = [k for k in q_lower.split() if len(k) > 2]
        rows = await self.knowledge.find(
            {"user_id": user_id}, {"_id": 0, "embedding": 0}
        ).sort("created_at", -1).limit(200).to_list(200)
        scored = []
        for r in rows:
            content = (r.get("content") or "").lower()
            score = sum(1 for kw in keywords if kw in content)
            if score > 0:
                scored.append({**r, "relevance_score": score, "match": "keyword"})
        scored.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored[:limit]

    async def search(self, user_id: str, query: str, limit: int = 5, mode: str = "auto"):
        """mode = 'auto' | 'semantic' | 'keyword'."""
        if mode in ("auto", "semantic"):
            try:
                qvec = await embed_query(query)
                rows = await self.knowledge.find(
                    {"user_id": user_id, "embedding": {"$exists": True, "$ne": None}}, {"_id": 0}
                ).limit(500).to_list(500)
                if rows:
                    ranked = rank_by_similarity(qvec, rows, key="embedding")
                    # drop embeddings from output
                    out = []
                    for r in ranked[:limit]:
                        rr = {k: v for k, v in r.items() if k != "embedding"}
                        rr["match"] = "semantic"
                        out.append(rr)
                    if out and out[0]["similarity"] > 0.6:
                        return out
                    # low-score semantic → fallback to keyword blend
                    if mode == "semantic":
                        return out
            except Exception:
                pass
        return await self._keyword_search(user_id, query, limit)

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
        with_vec = await self.knowledge.count_documents({"user_id": user_id, "embedding": {"$exists": True, "$ne": None}})
        prefs_total = await self.prefs.count_documents({"user_id": user_id})
        return {"total_knowledge": total, "with_embeddings": with_vec, "total_preferences": prefs_total}

    async def list_recent(self, user_id: str, limit: int = 20):
        return await self.knowledge.find(
            {"user_id": user_id}, {"_id": 0, "embedding": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)

    async def reindex_missing(self, user_id: str):
        """Recompute embeddings for docs where embedding is missing/None."""
        rows = await self.knowledge.find(
            {"user_id": user_id, "$or": [{"embedding": None}, {"embedding": {"$exists": False}}]},
            {"_id": 0}
        ).to_list(1000)
        if not rows:
            return {"reindexed": 0}
        vecs = await embed_texts([r["content"] for r in rows])
        for r, v in zip(rows, vecs):
            await self.knowledge.update_one({"id": r["id"]}, {"$set": {"embedding": v}})
        return {"reindexed": len(rows)}


def make_second_brain(db):
    return SecondBrain(db)
