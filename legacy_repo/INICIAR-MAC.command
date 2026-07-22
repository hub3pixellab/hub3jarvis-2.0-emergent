#!/bin/bash
HD_ROOT="/Volumes/JARVIS HUB3"
PROJECT="$HD_ROOT/hub3-jarvis/backend"
MONGO_DATA="$HD_ROOT/mongodb-data"
MONGO_LOGS="$HD_ROOT/mongodb-logs"
HTML_FILE="$HD_ROOT/hub3-jarvis/frontend/index.html"

echo "========================================"
echo "  HUB3 JARVIS v4.1 — Iniciando (macOS)"
echo "========================================"

if [ ! -d "$HD_ROOT" ]; then
    echo "ERRO: HD JARVIS HUB3 nao encontrado!"
    echo "Conecte o HD externo e tente novamente."
    read -p "Pressione ENTER para sair..."
    exit 1
fi

echo ">> Verificando MongoDB..."
if pgrep -x mongod > /dev/null; then
    echo ">> MongoDB ja esta rodando."
else
    echo ">> Iniciando MongoDB no HD externo..."
    mongod --dbpath "$MONGO_DATA" --logpath "$MONGO_LOGS/mongod.log" --fork 2>/dev/null
    sleep 3
fi

echo ">> Ativando ambiente Python..."
cd "$PROJECT"
source venv/bin/activate

echo ">> Subindo backend FastAPI..."
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
sleep 4

echo ">> Abrindo interface no navegador..."
open "http://localhost:8000"

if [ -f "$HTML_FILE" ]; then
    open "$HTML_FILE"
fi

echo ""
echo "========================================"
echo "  HUB3 JARVIS v4.1 — ONLINE!"
echo "  Backend: http://localhost:8000"
echo "  Para parar: feche este terminal"
echo "========================================"
echo ""
read -p "Pressione ENTER para manter rodando ou Ctrl+C para parar..."
kill $BACKEND_PID 2>/dev/null
mongod --dbpath "$MONGO_DATA" --shutdown 2>/dev/null
