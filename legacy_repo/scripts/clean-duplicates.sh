#!/bin/bash
VAULT="/Volumes/JARVIS HUB3/hub3-jarvis/knowledge-vault"

echo "========================================"
echo "  Knowledge Vault - Limpeza de Duplicatas"
echo "========================================"
echo ""

declare -A SEEN_NAMES
declare -A SEEN_SIZES
REMOVED=0
KEPT=0

scan_dir() {
    local dir="$1"
    if [ ! -d "$dir" ]; then
        return
    fi
    
    for FILE in "$dir"/*; do
        if [ -f "$FILE" ]; then
            BASENAME=$(basename "$FILE")
            SIZE=$(stat -f%z "$FILE" 2>/dev/null || stat -c%s "$FILE" 2>/dev/null)
            HASH_KEY="${BASENAME}_${SIZE}"
            
            if [ -n "${SEEN_NAMES[$HASH_KEY]}" ]; then
                rm "$FILE"
                echo "  [REMOVIDO] $BASENAME (duplicata em $dir)"
                REMOVED=$((REMOVED + 1))
            else
                SEEN_NAMES[$HASH_KEY]=1
                KEPT=$((KEPT + 1))
            fi
        fi
    done
}

for CATEGORY in textos imagens musicas samples videos livros pdfs normativas outros; do
    echo ">> Escaneando: $CATEGORY/"
    scan_dir "$VAULT/$CATEGORY"
done

echo ""
echo ">> Escaneando subpastas de zips/"
if [ -d "$VAULT/zips" ]; then
    for SUBDIR in "$VAULT/zips"/*/; do
        if [ -d "$SUBDIR" ]; then
            for FILE in "$SUBDIR"*; do
                if [ -f "$FILE" ]; then
                    BASENAME=$(basename "$FILE")
                    SIZE=$(stat -f%z "$FILE" 2>/dev/null || stat -c%s "$FILE" 2>/dev/null)
                    HASH_KEY="${BASENAME}_${SIZE}"
                    
                    if [ -n "${SEEN_NAMES[$HASH_KEY]}" ]; then
                        rm "$FILE"
                        echo "  [REMOVIDO] $BASENAME (duplicata em zips)"
                        REMOVED=$((REMOVED + 1))
                    else
                        SEEN_NAMES[$HASH_KEY]=1
                        KEPT=$((KEPT + 1))
                    fi
                fi
            done
        fi
    done
fi

echo ""
echo "========================================"
echo "  Limpeza concluida!"
echo "  Arquivos mantidos: $KEPT"
echo "  Duplicatas removidas: $REMOVED"
echo "========================================"
