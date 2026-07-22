#!/bin/bash
VAULT="/Volumes/JARVIS HUB3/hub3-jarvis/knowledge-vault"
SOURCE="$1"

if [ -z "$SOURCE" ]; then
    echo "Uso: ./ingest-folder.sh /caminho/da/pasta"
    exit 1
fi

echo "========================================"
echo "  Knowledge Vault - Ingestao em Massa"
echo "========================================"
echo "  Origem: $SOURCE"
echo ""

COUNT=0

for FILE in "$SOURCE"/*; do
    if [ -f "$FILE" ]; then
        EXT=$(echo "${FILE##*.}" | tr '[:upper:]' '[:lower:]')
        DEST="outros"

        case "$EXT" in
            txt|md|json|csv) DEST="textos" ;;
            jpg|jpeg|png|gif|webp|bmp|svg) DEST="imagens" ;;
            mp3|wav|flac|aac|m4a|ogg) DEST="musicas" ;;
            aiff|aif) DEST="samples" ;;
            mp4|avi|mov|mkv|webm|m4v) DEST="videos" ;;
            pdf) DEST="pdfs" ;;
            epub|mobi|azw3) DEST="livros" ;;
            zip)
                echo ">> Descompactando: $(basename "$FILE")"
                EXTRACT_DIR="$VAULT/zips/$(basename "${FILE%.*}")"
                mkdir -p "$EXTRACT_DIR"
                unzip -o "$FILE" -d "$EXTRACT_DIR" > /dev/null 2>&1
                for EXTRACTED in "$EXTRACT_DIR"/*; do
                    if [ -f "$EXTRACTED" ]; then
                        EEXT=$(echo "${EXTRACTED##*.}" | tr '[:upper:]' '[:lower:]')
                        EDEST="outros"
                        case "$EEXT" in
                            txt|md|json|csv) EDEST="textos" ;;
                            jpg|jpeg|png|gif|webp|bmp|svg) EDEST="imagens" ;;
                            mp3|wav|flac|aac|m4a|ogg) EDEST="musicas" ;;
                            aiff|aif) EDEST="samples" ;;
                            mp4|avi|mov|mkv|webm|m4v) EDEST="videos" ;;
                            pdf) EDEST="pdfs" ;;
                            epub|mobi|azw3) EDEST="livros" ;;
                        esac
                        cp "$EXTRACTED" "$VAULT/$EDEST/" 2>/dev/null
                        echo "  -> $(basename "$EXTRACTED") -> $EDEST"
                        COUNT=$((COUNT + 1))
                    fi
                done
                continue
                ;;
        esac

        cp "$FILE" "$VAULT/$DEST/" 2>/dev/null
        echo ">> $(basename "$FILE") -> $DEST"
        COUNT=$((COUNT + 1))
    fi
done

echo ""
echo "========================================"
echo "  $COUNT arquivos ingeridos!"
echo "  Vault: $VAULT"
echo "========================================"
