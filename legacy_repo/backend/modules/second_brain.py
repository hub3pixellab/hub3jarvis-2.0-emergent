"""
Second Brain — JARVIS v4.2
Memoria de longo prazo com busca semantica via Hugging Face embeddings
"""

import os
import json
import asyncio
from datetime import datetime, timezone

SECOND_BRAIN_PATH = os.getenv(
    "SECOND_BRAIN_PATH",
    "/Volumes/JARVIS HUB3/hub3-jarvis/data/second-brain.json"
)

class SecondBrain:
    """Segundo cerebro: memoria persistente com busca semantica"""

    def __init__(self):
        self.path = SECOND_BRAIN_PATH
        self.data = {"knowledge": [], "preferences": {}, "conversations": []}
        self._load()

    def _load(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.data["knowledge"] = loaded.get("knowledge", [])
                    self.data["preferences"] = loaded.get("preferences", {})
                    self.data["conversations"] = loaded.get("conversations", [])
            except:
                pass

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add(self, content, source="chat", k_type="insight", user_id="admin"):
        """Adiciona conhecimento ao Second Brain"""
        entry = {
            "id": f"kb_{datetime.now(timezone.utc).timestamp()}_{len(self.data['knowledge'])}",
            "content": content,
            "source": source,
            "type": k_type,
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        self.data["knowledge"].append(entry)
        self._save()
        # Gerar embedding de forma assincrona (fire-and-forget)
        try:
            import asyncio
            from modules.huggingface_embeddings import hf_embeddings
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(hf_embeddings.embed_and_store(entry["id"], content, {
                    "source": source, "type": k_type
                }))
        except:
            pass
        return entry

    def search_sync(self, query, limit=5):
        """Busca por keywords (fallback sincrono)"""
        query_lower = query.lower()
        keywords = query_lower.split()
        scored = []
        for entry in self.data["knowledge"]:
            content_lower = entry["content"].lower()
            score = sum(1 for kw in keywords if kw in content_lower)
            if score > 0:
                scored.append({**entry, "relevance_score": score})
        scored.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored[:limit]

    async def search_semantic(self, query, limit=5):
        """Busca semantica via embeddings Hugging Face"""
        from modules.huggingface_embeddings import hf_embeddings
        docs = self.data["knowledge"]
        if not docs:
            return []
        return await hf_embeddings.semantic_search(
            query, docs, top_k=limit,
            text_key="content", score_key="relevance_score"
        )

    async def search(self, query, limit=5, use_semantic=True):
        """Busca inteligente: semantica primeiro, fallback keyword"""
        if use_semantic:
            try:
                results = await self.search_semantic(query, limit)
                if results:
                    return results
            except:
                pass
        return self.search_sync(query, limit)

    def get_context(self, query, limit=3):
        """Obtem contexto formatado para injetar no prompt do JARVIS"""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Tenta semantica assincrona
                future = asyncio.run_coroutine_threadsafe(
                    self.search(query, limit), loop
                )
                results = future.result(timeout=5)
            else:
                results = self.search_sync(query, limit)
        except:
            results = self.search_sync(query, limit)

        if not results:
            return None
        parts = [f"[{r.get('source', 'brain')}] {r['content'][:300]}" for r in results]
        return "\n\n".join(parts)

    def add_preference(self, key, value):
        """Armazena preferencia do usuario"""
        self.data["preferences"][key] = {
            "value": value,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        self._save()

    def get_preference(self, key):
        """Recupera preferencia do usuario"""
        pref = self.data["preferences"].get(key)
        return pref.get("value") if pref else None

    def get_stats(self):
        """Estatisticas do Second Brain"""
        return {
            "total_knowledge": len(self.data["knowledge"]),
            "total_preferences": len(self.data["preferences"]),
            "total_conversations": len(self.data["conversations"]),
            "path": self.path
        }

second_brain = SecondBrain()
