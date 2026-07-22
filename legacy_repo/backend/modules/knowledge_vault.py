import os
import json
import zipfile
import shutil
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

VAULT_ROOT = os.getenv("VAULT_PATH", "/Volumes/JARVIS HUB3/hub3-jarvis/knowledge-vault")

CATEGORIES = {
    ".txt": "textos", ".md": "textos", ".json": "textos", ".csv": "textos",
    ".jpg": "imagens", ".jpeg": "imagens", ".png": "imagens", ".gif": "imagens",
    ".webp": "imagens", ".bmp": "imagens", ".svg": "imagens",
    ".mp3": "musicas", ".wav": "musicas", ".flac": "musicas", ".aac": "musicas",
    ".m4a": "musicas", ".ogg": "musicas",
    ".mp4": "videos", ".avi": "videos", ".mov": "videos", ".mkv": "videos",
    ".webm": "videos", ".m4v": "videos",
    ".pdf": "pdfs",
    ".epub": "livros", ".mobi": "livros", ".azw3": "livros",
    ".zip": "zips", ".rar": "zips", ".7z": "zips", ".tar": "zips", ".gz": "zips",
}

class KnowledgeVault:
    def __init__(self):
        self.root = VAULT_ROOT
        self._ensure_dirs()

    def _ensure_dirs(self):
        for cat in set(CATEGORIES.values()) | {"normativas", "outros"}:
            os.makedirs(os.path.join(self.root, cat), exist_ok=True)

    def _categorize(self, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        return CATEGORIES.get(ext, "outros")

    async def ingest_file(self, file_path: str, original_name: str = None, user_id: str = "admin") -> dict:
        name = original_name or os.path.basename(file_path)
        ext = Path(name).suffix.lower()

        if ext in [".zip", ".rar", ".7z", ".tar", ".gz"]:
            return await self._ingest_archive(file_path, name, user_id)

        category = self._categorize(name)
        dest_dir = os.path.join(self.root, category)
        dest_path = os.path.join(dest_dir, name)
        shutil.copy2(file_path, dest_path)

        entry = {
            "filename": name,
            "category": category,
            "path": dest_path,
            "size_bytes": os.path.getsize(dest_path),
            "mime_type": mimetypes.guess_type(name)[0],
            "user_id": user_id,
            "ingested_at": datetime.now(timezone.utc).isoformat()
        }
        await self._log_entry(entry)
        return {"status": "ingested", "entry": entry}

    async def _ingest_archive(self, archive_path: str, archive_name: str, user_id: str) -> dict:
        extract_dir = os.path.join(self.root, "zips", Path(archive_name).stem)
        os.makedirs(extract_dir, exist_ok=True)

        ext = Path(archive_name).suffix.lower()
        if ext == ".zip":
            with zipfile.ZipFile(archive_path, 'r') as zf:
                zf.extractall(extract_dir)
        else:
            shutil.copy2(archive_path, os.path.join(self.root, "zips", archive_name))
            return {"status": "archived_unextracted", "reason": f"Formato {ext} nao suportado para extracao automatica"}

        ingested = []
        for root, dirs, files in os.walk(extract_dir):
            for f in files:
                fp = os.path.join(root, f)
                cat = self._categorize(f)
                if cat != "zips":
                    dest = os.path.join(self.root, cat, f)
                    if not os.path.exists(dest):
                        shutil.copy2(fp, dest)
                        entry = {
                            "filename": f,
                            "category": cat,
                            "path": dest,
                            "size_bytes": os.path.getsize(dest),
                            "mime_type": mimetypes.guess_type(f)[0],
                            "user_id": user_id,
                            "extracted_from": archive_name,
                            "ingested_at": datetime.now(timezone.utc).isoformat()
                        }
                        await self._log_entry(entry)
                        ingested.append(entry)

        return {
            "status": "extracted_and_ingested",
            "archive": archive_name,
            "files_ingested": len(ingested),
            "files": ingested
        }

    async def _log_entry(self, entry: dict):
        log_path = os.path.join(self.root, "vault_index.json")
        index = []
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                try:
                    index = json.load(f)
                except:
                    index = []
        index.append(entry)
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    async def list_vault(self, category: str = None) -> dict:
        log_path = os.path.join(self.root, "vault_index.json")
        if not os.path.exists(log_path):
            return {"total": 0, "items": []}
        with open(log_path, "r", encoding="utf-8") as f:
            index = json.load(f)
        if category:
            index = [i for i in index if i.get("category") == category]
        return {"total": len(index), "items": index}

    async def search_vault(self, query: str, use_semantic=True) -> dict:
        log_path = os.path.join(self.root, "vault_index.json")
        if not os.path.exists(log_path):
            return {"results": [], "total": 0}
        with open(log_path, "r", encoding="utf-8") as f:
            index = json.load(f)
        # Busca semantica via Hugging Face
        if use_semantic:
            try:
                from modules.huggingface_embeddings import hf_embeddings
                docs = [{"content": f"{i.get('filename','')} - {i.get('category','')} - {i.get('mime_type','')}", "entry": i} for i in index]
                results = await hf_embeddings.semantic_search(query, docs, top_k=10, text_key="content", score_key="relevance_score")
                if results:
                    return {"query": query, "results": [r["entry"] for r in results], "total": len(results), "mode": "semantico"}
            except:
                pass
        # Fallback: busca por keyword
        q = query.lower()
        results = [i for i in index if q in i.get("filename", "").lower() or q in i.get("category", "").lower()]
        return {"query": query, "results": results, "total": len(results), "mode": "keyword"}

    async def get_stats(self) -> dict:
        log_path = os.path.join(self.root, "vault_index.json")
        if not os.path.exists(log_path):
            return {"total_files": 0, "categories": {}, "total_size_mb": 0}
        with open(log_path, "r", encoding="utf-8") as f:
            index = json.load(f)
        cats = {}
        total_size = 0
        for entry in index:
            cat = entry.get("category", "outros")
            cats[cat] = cats.get(cat, 0) + 1
            total_size += entry.get("size_bytes", 0)
        return {
            "total_files": len(index),
            "categories": cats,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "vault_root": self.root
        }

    async def load_normativas(self) -> dict:
        norm_dir = os.path.join(self.root, "normativas")
        normativas = {}
        if os.path.exists(norm_dir):
            for f in os.listdir(norm_dir):
                if f.endswith(".json"):
                    with open(os.path.join(norm_dir, f), "r", encoding="utf-8") as fh:
                        key = Path(f).stem
                        normativas[key] = json.load(fh)
        return normativas

knowledge_vault = KnowledgeVault()
