#!/usr/bin/env python3
"""
Ingest legacy second-brain.json into the Hub3 JARVIS v4.2 MongoDB Second Brain.

Usage:
    python scripts/ingest_second_brain.py --path /Volumes/JARVIS\\ HUB3/hub3-jarvis/data/second-brain.json --user admin@hub3.ai
    python scripts/ingest_second_brain.py --path ./legacy_repo/data/second-brain.json --user admin@hub3.ai

Reads the legacy JSON structure (either an array of items or {knowledge:[...], preferences:{}, conversations:[]})
and inserts each entry into MongoDB via the SecondBrain module, computing embeddings on the fly.

The legacy JSON expected format:
{
  "knowledge": [
    {"content": "...", "source": "chat", "type": "insight", "created_at": "ISO"}, ...
  ],
  "preferences": {"key": {"value": "..."}, ...},
  "conversations": [ ... ]
}
"""
import os
import sys
import json
import asyncio
import argparse
from pathlib import Path

# Make backend imports work
ROOT = Path(__file__).parent.parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv
load_dotenv(BACKEND / ".env")

from motor.motor_asyncio import AsyncIOMotorClient
from modules.second_brain import make_second_brain


DEFAULT_PATHS = [
    "/Volumes/JARVIS HUB3/hub3-jarvis/data/second-brain.json",  # legacy portable HD path
    str(ROOT / "legacy_repo/data/second-brain.json"),
    str(ROOT / "data/second-brain.json"),
]


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default=None, help="Path to second-brain.json (defaults: HD, legacy_repo, /app/data)")
    parser.add_argument("--user", required=True, help="Target user email (or user_id)")
    args = parser.parse_args()

    candidate_paths = [args.path] if args.path else DEFAULT_PATHS
    src = next((p for p in candidate_paths if p and os.path.exists(p)), None)
    if not src:
        print(f"[!] second-brain.json not found. Tried: {candidate_paths}")
        sys.exit(1)
    print(f"[*] Reading {src}")

    with open(src, "r", encoding="utf-8") as f:
        payload = json.load(f)

    if isinstance(payload, list):
        items = payload
        prefs = {}
    else:
        items = payload.get("knowledge", [])
        prefs = payload.get("preferences", {}) or {}

    print(f"[*] Found {len(items)} knowledge entries, {len(prefs)} preferences")

    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ["DB_NAME"]
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    # Resolve user
    q = {"email": args.user.lower()} if "@" in args.user else {"id": args.user}
    u = await db.users.find_one(q, {"_id": 0, "id": 1, "email": 1})
    if not u:
        print(f"[!] User not found: {args.user}")
        sys.exit(1)
    user_id = u["id"]
    print(f"[*] Target user: {u['email']} ({user_id})")

    sb = make_second_brain(db)
    # Batch insert (in chunks of 32 to avoid huge batches)
    CHUNK = 32
    total_inserted = 0
    for i in range(0, len(items), CHUNK):
        chunk = items[i:i+CHUNK]
        r = await sb.add_bulk(user_id, chunk)
        total_inserted += r.get("inserted", 0)
        print(f"    [{i+len(chunk)}/{len(items)}] +{r.get('inserted', 0)}")

    # Preferences
    for k, v in prefs.items():
        val = v.get("value") if isinstance(v, dict) else v
        if val is not None:
            await sb.add_preference(user_id, k, val)

    print(f"[✓] Done. Inserted {total_inserted} knowledge entries + {len(prefs)} preferences.")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
