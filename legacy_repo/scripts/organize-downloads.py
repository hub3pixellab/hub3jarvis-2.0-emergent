#!/usr/bin/env python3
"""
JARVIS - Organizador de Arquivos
Monitora uma pasta de origem, move arquivos para o Knowledge Vault,
detecta duplicatas por hash SHA-256 e renomeia se for diferente.
"""

import os
import hashlib
import shutil
import json
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

SOURCE_DIR = os.environ.get("JARVIS_WATCH_DIR", "/Users/diogozachioliveira/Downloads")
VAULT_DIR = "/Volumes/JARVIS HUB3/hub3-jarvis/knowledge-vault"
HASH_DB = os.path.join(VAULT_DIR, ".hash_registry.json")

CATEGORIES = {
    "imagens": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".raw", ".heic"],
    "videos": [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm"],
    "audios": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"],
    "documentos": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".pages"],
    "planilhas": [".xls", ".xlsx", ".csv", ".ods", ".numbers"],
    "apresentacoes": [".ppt", ".pptx", ".key", ".odp"],
    "codigos": [".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".yaml", ".yml", ".sh", ".sql"],
    "compactados": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "textos": [".md", ".log"],
}

def get_category(filename):
    ext = Path(filename).suffix.lower()
    for category, exts in CATEGORIES.items():
        if ext in exts:
            return category
    return "outros"

def calculate_hash(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def load_hash_db():
    if os.path.exists(HASH_DB):
        with open(HASH_DB, "r") as f:
            return json.load(f)
    return {}

def save_hash_db(db):
    with open(HASH_DB, "w") as f:
        json.dump(db, f, indent=2)

def ensure_vault_dirs():
    for category in list(CATEGORIES.keys()) + ["outros"]:
        os.makedirs(os.path.join(VAULT_DIR, category), exist_ok=True)

def process_file(filepath):
    filename = os.path.basename(filepath)
    if filename.startswith("."):
        return
    if not os.path.exists(filepath):
        return

    category = get_category(filename)
    dest_dir = os.path.join(VAULT_DIR, category)
    dest_path = os.path.join(dest_dir, filename)

    try:
        file_hash = calculate_hash(filepath)
    except Exception as e:
        print(f"[ERRO] Nao foi possivel ler {filename}: {e}")
        return

    hash_db = load_hash_db()

    if file_hash in hash_db:
        existing = hash_db[file_hash]
        existing_path = existing.get("path", "")
        existing_name = os.path.basename(existing_path)

        if filename == existing_name:
            os.remove(filepath)
            print(f"[DUPLICATA] {filename} removido (identico a {existing_path})")
            return
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base, ext = os.path.splitext(filename)
            new_name = f"{base}_{timestamp}{ext}"
            dest_path = os.path.join(dest_dir, new_name)
            shutil.move(filepath, dest_path)
            hash_db[file_hash] = {
                "path": dest_path,
                "original_name": filename,
                "renamed_to": new_name,
                "timestamp": datetime.now().isoformat()
            }
            save_hash_db(hash_db)
            print(f"[RENOMEADO] {filename} -> {new_name} (hash igual a {existing_name})")
            return

    if os.path.exists(dest_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base, ext = os.path.splitext(filename)
        new_name = f"{base}_{timestamp}{ext}"
        dest_path = os.path.join(dest_dir, new_name)
        filename = new_name

    shutil.move(filepath, dest_path)
    hash_db[file_hash] = {
        "path": dest_path,
        "original_name": filename,
        "timestamp": datetime.now().isoformat()
    }
    save_hash_db(hash_db)
    print(f"[MOVIDO] {filename} -> {category}/")

class JarvisHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            process_file(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            process_file(event.dest_path)

def scan_existing():
    print(f"\n[JARVIS] Escaneando {SOURCE_DIR}...")
    count = 0
    for item in os.listdir(SOURCE_DIR):
        filepath = os.path.join(SOURCE_DIR, item)
        if os.path.isfile(filepath) and not item.startswith("."):
            process_file(filepath)
            count += 1
    print(f"[JARVIS] {count} arquivos processados.\n")

def start_monitor():
    ensure_vault_dirs()
    scan_existing()

    observer = Observer()
    observer.schedule(JarvisHandler(), SOURCE_DIR, recursive=False)
    observer.start()

    print(f"[JARVIS] Monitorando {SOURCE_DIR} em tempo real...")
    print(f"[JARVIS] Vault: {VAULT_DIR}")
    print(f"[JARVIS] Pressione Ctrl+C para parar.\n")

    try:
        while True:
            observer.join(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n[JARVIS] Monitoramento interrompido.")

if __name__ == "__main__":
    start_monitor()
