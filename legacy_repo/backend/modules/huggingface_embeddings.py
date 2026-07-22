"""
Hugging Face Inference API — Embeddings Gratuitos
Usa o modelo BERT multi-lingue (sentence-transformers) para gerar embeddings
100% gratuito, sem necessidade de API key (rate limit: ~30 req/min)
Alimenta o Second Brain e o Knowledge Vault com busca semantica
"""

import os
import json
import httpx
import asyncio
import numpy as np
from datetime import datetime, timezone
from pathlib import Path

class HuggingFaceEmbeddings:
    """Gerador de embeddings semanticos via Hugging Face Inference API (gratis)"""

    def __init__(self):
        # Modelo multi-lingue otimizado para similaridade semantica
        self.model = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        self.api_url = f"https://api-inference.huggingface.co/models/{self.model}"
        self.api_key = os.getenv("HF_API_KEY", "")  # opcional, gratis mesmo sem
        self.headers = {}
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
        self._cache = {}  # cache em memoria de embeddings
        self.cache_path = "/Volumes/JARVIS HUB3/hub3-jarvis/data/embeddings_cache.json"
        self._load_cache()

    @property
    def configured(self):
        """Sempre disponivel — gratis, sem necessidade de chave"""
        return True

    def _load_cache(self):
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except:
                self._cache = {}

    def _save_cache(self):
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        # Limitar cache a 1000 entradas para nao ficar pesado
        if len(self._cache) > 1000:
            keys = list(self._cache.keys())
            for k in keys[:-800]:
                del self._cache[k]
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(self._cache, f, ensure_ascii=False)

    async def embed(self, text: str) -> list:
        """Gera embedding para um texto (com cache)"""
        cache_key = text.strip()[:200].lower()
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json={"inputs": text}
                )
                if resp.status_code == 200:
                    embedding = resp.json()
                    if isinstance(embedding, list) and len(embedding) > 0:
                        # Se veio como lista de listas, pega o primeiro
                        if isinstance(embedding[0], list):
                            embedding = embedding[0]
                        self._cache[cache_key] = embedding
                        self._save_cache()
                        return embedding
                elif resp.status_code == 503:
                    # Modelo carregando — esperar e tentar denovo
                    await asyncio.sleep(2)
                    return await self.embed(text)
                return [0.0] * 384  # fallback: vetor zero
        except Exception:
            return [0.0] * 384  # fallback silencioso

    async def embed_batch(self, texts: list) -> list:
        """Gera embeddings para multiplos textos em paralelo"""
        tasks = [self.embed(t) for t in texts]
        return await asyncio.gather(*tasks)

    def cosine_similarity(self, vec_a: list, vec_b: list) -> float:
        """Calcula similaridade por cosseno entre dois vetores"""
        try:
            a = np.array(vec_a, dtype=np.float32)
            b = np.array(vec_b, dtype=np.float32)
            norm = np.linalg.norm(a) * np.linalg.norm(b)
            if norm == 0:
                return 0.0
            return float(np.dot(a, b) / norm)
        except:
            return 0.0

    async def semantic_search(self, query: str, documents: list, top_k: int = 5,
                              text_key: str = "content", score_key: str = "relevance_score"):
        """
        Busca semantica: gera embedding da query e compara com todos os documentos.
        - documents: lista de dicts com pelo menos o text_key
        - Retorna os top_k documentos ordenados por similaridade
        """
        if not documents:
            return []

        query_emb = await self.embed(query)
        texts = [d.get(text_key, "") for d in documents]
        doc_embs = await self.embed_batch(texts)

        scored = []
        for doc, emb in zip(documents, doc_embs):
            score = self.cosine_similarity(query_emb, emb)
            if score > 0.15:  # threshold minimo de relevancia
                doc[score_key] = round(score, 4)
                scored.append(doc)

        scored.sort(key=lambda x: x.get(score_key, 0), reverse=True)
        return scored[:top_k]

    async def embed_and_store(self, doc_id: str, text: str, metadata: dict = None):
        """Gera embedding e armazena para uso futuro"""
        emb = await self.embed(text)
        entry = {
            "doc_id": doc_id,
            "text": text[:500],
            "embedding": emb,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        self._cache[f"stored_{doc_id}"] = {
            "text": text[:200],
            "embedding": emb,
            "metadata": metadata or {}
        }
        self._save_cache()
        return entry

    async def get_status(self) -> dict:
        """Status do servico de embeddings"""
        return {
            "provider": "huggingface",
            "model": self.model,
            "configured": True,
            "plan": "gratuito",
            "cache_size": len(self._cache),
            "embedding_dim": 384,
            "api_url": "https://api-inference.huggingface.co (gratis, sem key)"
        }

hf_embeddings = HuggingFaceEmbeddings()
