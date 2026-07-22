"""
Embeddings module — fastembed (ONNX, local, ~90MB model) for Second Brain
Uses multilingual E5-small (384-dim) — works for PT + EN.

Model is lazily loaded on first use and cached process-wide.
"""
from typing import List
import asyncio
import numpy as np

_model = None
_lock = asyncio.Lock()
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"  # 384-dim, PT+EN


def _load_sync():
    global _model
    if _model is None:
        from fastembed import TextEmbedding
        _model = TextEmbedding(model_name=MODEL_NAME)
    return _model


async def ensure_loaded():
    async with _lock:
        if _model is None:
            # heavy — run in threadpool
            await asyncio.to_thread(_load_sync)


def _embed_sync(texts: List[str]) -> List[List[float]]:
    m = _load_sync()
    vecs = list(m.embed(texts))
    return [v.tolist() for v in vecs]


def _embed_query_sync(text: str) -> List[float]:
    m = _load_sync()
    v = list(m.embed([text]))[0]
    return v.tolist()


async def embed_texts(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    return await asyncio.to_thread(_embed_sync, texts)


async def embed_query(text: str) -> List[float]:
    return await asyncio.to_thread(_embed_query_sync, text)


def cosine(a: List[float], b: List[float]) -> float:
    av, bv = np.array(a, dtype=np.float32), np.array(b, dtype=np.float32)
    denom = (np.linalg.norm(av) * np.linalg.norm(bv)) or 1e-9
    return float(np.dot(av, bv) / denom)


def rank_by_similarity(query_vec: List[float], docs_with_vec: list, key: str = "embedding") -> list:
    """Returns docs sorted by cosine similarity to query_vec (desc). Each doc must have `key`."""
    scored = []
    for d in docs_with_vec:
        v = d.get(key)
        if not v:
            continue
        s = cosine(query_vec, v)
        scored.append({**d, "similarity": s})
    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored
