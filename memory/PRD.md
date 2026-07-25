# Hub3 JARVIS v4.2 — Product Requirements Document

## Original Problem Statement
Analise o repositório `hub3pixellab/hub3jarvis` e construa o Hub3 JARVIS v4.2:
absorver os conceitos (Consensus Engine, Second Brain, arquitetura modular) e reescrever
do zero em FastAPI + React seguindo 4 mockups fornecidos.

## User Choices (Sprint 1)
- Escopo: **Todos os 4 layouts navegáveis** (Dashboard totalmente funcional; Consensus com 3 LLMs reais; Smart Home com toggles persistidos; Chat com IA real)
- Consensus: **3 LLMs reais em paralelo** — Claude Sonnet 4.6, GPT-5.4 Turbo, Gemini 3 Flash (via Emergent Universal Key + asyncio.gather)
- Auth: **JWT (email/senha) + Emergent Managed Google Auth** — coexistem
- Codebase: **Reescrita do zero** em FastAPI + React (não clonar o repo antigo)
- Idioma: **Bilíngue PT/EN** com toggle persistido em localStorage

## Architecture
- **Backend**: FastAPI + Motor (MongoDB async) + PyJWT + bcrypt + emergentintegrations (LlmChat)
- **Frontend**: React 19 + react-router-dom v7 + Tailwind + Framer Motion + react-force-graph-2d + lucide-react + axios
- **DB**: MongoDB (`hub3_jarvis`) — collections: users, consensus_queries, smart_home, chat_messages
- **Auth**: JWT HS256 in httpOnly cookie AND Bearer token in localStorage (both work)

## Personas
- **Alex / Admin (Premium Member)** — the AI Life OS user (dashboard mockup)
- **Smart Home Admin** — controls IoT devices from web dashboard
- **Chat User** — converses with Hub3 Jarvis in natural language PT/EN

## Sprint 1 — Delivered ✅ (Jan 2026)
- [x] Backend FastAPI + MongoDB + JWT auth + Emergent Google Auth
- [x] Admin seeded on startup (admin@hub3.ai / Hub3Admin!2026)
- [x] Consensus Engine: real parallel calls to 3 LLMs, weighted scoring, cost tracking, agreement level
- [x] Dashboard Layout 1 — sidebar 8 life areas + Life Balance donut + AI Brain Network (react-force-graph-2d) + Ei Hub waveform + AI Consensus panel + 4 metric cards + footer quote
- [x] Consensus Layout 2 — 3 model cards + Consensus Engine gear (animated) + voting mechanism + AI response scores (live) + cost optimization + smart routing + system metrics + confidence guide + user question input (real /api/consensus/query)
- [x] Smart Home Layout 3 — 8 device cards (Lights color wheel, Thermostat dial, Cameras 2x2, TV, Lock, Speaker waveform, Wearable Health, Smart Plugs) + persisted toggles + status bar
- [x] Chat Layout 4 — WhatsApp-like sidebar (7 conversations) + real chat with Claude Sonnet 4.6 + inline devices_snapshot card (triggered by "luz/light" keyword)
- [x] i18n PT/EN toggle across all 4 layouts
- [x] Design system: navy #0A0E27, cyan #00D4FF, orange #FF8C42, HUD corner brackets, pill buttons, waveforms, gradient progress bars
- [x] Backend regression tests 14/14 passing
- [x] Frontend E2E: login → all 4 layouts → toggle → chat → logout all validated

## Backlog (P0 — next sprint)
- Streaming responses on chat (SSE) with token-by-token typing
- Consensus history page (queries table with filters)
- Full 7-model roster (add Groq, Mistral, ElevenLabs, AssemblyAI cards + real integrations for those with paid keys)
- Rate limiting on /api/auth/login (brute-force lockout — playbook spec)

## Backlog (P1)
- Second Brain: MongoDB Atlas Vector Search + RAG on user knowledge base
- Real voice input/output on Ei Hub (AssemblyAI STT + ElevenLabs TTS)
- Creative Suite (30+ tools)
- SoundCloud radio via Sanity CMS

## Backlog (P2)
- Home Assistant plug-in for real IoT
- Portable HD deploy scripts
- Vercel/Railway deploy pipeline

## Key Files
- `/app/backend/server.py` — all endpoints (auth, consensus, dashboard, smart-home, chat)
- `/app/frontend/src/App.js` — router
- `/app/frontend/src/contexts/AppContext.jsx` — auth + language
- `/app/frontend/src/pages/{Login,Dashboard,Consensus,SmartHome,Chat}Page.jsx`
- `/app/frontend/src/components/AppShell.jsx` — sidebar/rail nav
- `/app/frontend/src/locales/translations.js` — EN/PT strings
- `/app/design_guidelines.json` — HUD design system

## Sprint 2 — Absorption from hub3pixellab/hub3jarvis (Jan 2026)

**Repo original clonado em `/app/legacy_repo/` para referência.**

### Módulos absorvidos e refatorados para MongoDB (v4.2):
- **`modules/policy_engine.py`** — 3 Leis: whitelist protection, sensitive action confirmation, blocked search sources (onion/darknet)
- **`modules/second_brain.py`** — memória de longo prazo persistida em MongoDB (`second_brain_knowledge` + `second_brain_prefs`) com busca por palavra-chave e get_context() para injeção automática em prompts
- **`modules/self_learning.py`** — log de todas as interações do Consensus, sistema de feedback (positive/negative/neutral) e cálculo de padrões de uso por modelo + taxa de satisfação

### Novos endpoints:
- `POST /api/brain/add` · `POST /api/brain/search` · `GET /api/brain/recent` · `GET /api/brain/stats`
- `POST /api/brain/pref` · `GET /api/brain/prefs`
- `POST /api/learning/feedback` · `GET /api/learning/patterns` · `GET /api/learning/recent`
- `POST /api/policy/check` · `GET /api/policy/whitelist` · `POST /api/policy/whitelist`

### Integração automática:
- `/api/consensus/query` agora **injeta contexto do Second Brain** antes de chamar as 3 LLMs e **loga cada resposta vencedora** no Self-Learning
- `/api/chat/send` agora **checa Policy Engine antes de comandos de dispositivo** (whitelist bloqueia se necessário) e **injeta contexto do Second Brain** no prompt do Jarvis + **memoriza conversas relevantes** (>20 chars)

### Nova página frontend `/brain`:
- 3 abas: Segundo Cérebro (add/search/recent), Motor de Políticas (3 leis + whitelist CRUD), Auto-Aprendizado (métricas)
- 4 stat boxes no topo: Knowledge count, Preferences, Whitelist, AI Interactions
- Toda em i18n PT/EN

### Verificação:
- Adicionei manualmente "Meu projeto principal é o Project Orion focado em análise financeira Q2 com IA"
- No chat perguntei "O que você sabe sobre meu Project Orion?" → Jarvis respondeu usando o contexto correto ✅
- Adicionei "Mãe" como whitelist absolute → policy/check com phone dela bloqueou WhatsApp ✅
- Consensus query gerou log_id e apareceu no /learning/patterns ✅

## Sprint 3 — 4 Melhorias avançadas (Jan 2026)

### 1. Vector Search real ✅
- `modules/embeddings.py` — **fastembed** com `paraphrase-multilingual-MiniLM-L12-v2` (384-dim, PT+EN, ONNX ~90MB, 100% offline)
- Modelo pré-carregado em background no startup
- `SecondBrain.search(query, mode='auto|semantic|keyword')` — busca semântica com fallback automático
- Verificado: query "quem são meus companheiros de trabalho" achou "Minha equipe: Diego (eng), Ana Paula (design), Laura (produto)" via similaridade coseno
- `POST /api/brain/reindex` — recomputa embeddings faltantes

### 2. 👍/👎 feedback no Consensus ✅
- Após cada `POST /api/consensus/query`, resposta inclui `log_id`
- UI mostra 3 botões (positive / neutral / negative) no card AI Response Scores
- Chama `POST /api/learning/feedback` — `learning_patterns` já mostra satisfaction_rate 50% após 1 feedback

### 3. Chat streaming SSE token-a-token ✅
- Novo endpoint `GET /api/chat/stream` (SSE — token via query param pois EventSource não envia headers)
- Emite eventos `meta`, `data` (deltas), `done`, `error`
- ChatPage.jsx agora usa `EventSource` — mensagens aparecem letra-por-letra com cursor piscando (`animate-pulse`)
- Continua salvando no Mongo + memorizando conversas relevantes no Second Brain

### 4. Ingestão em batch do second-brain.json ✅
- **d1)** `POST /api/brain/import` (JSON body) e `POST /api/brain/import-file` (upload multipart)
- UI: botão "Import JSON" na página `/brain` (label + input file hidden) + botão "Re-index" para vetorizar entradas antigas
- **d2)** `scripts/ingest_second_brain.py` CLI:
  ```
  python scripts/ingest_second_brain.py --path /Volumes/JARVIS\ HUB3/hub3-jarvis/data/second-brain.json --user admin@hub3.ai
  ```
  Aceita array ou `{knowledge:[], preferences:{}}`, faz batch de 32 embeddings, resolve user por email ou id
- Testado com JSON fixture `/app/legacy_repo/data/second-brain.json` → 5 conhecimentos + 3 preferências ingeridos com sucesso

### Estado atual (verificado via curl + screenshots)
- 9/9 conhecimentos com embeddings, 3 preferências (language=pt-BR, timezone=America/Sao_Paulo, morning_briefing=true)
- 2 interações de consenso logadas, 1 feedback positivo, custo total $0.00158
- Streaming ativo, inline device card aparecendo nas respostas do Jarvis com comando "acenda as luzes"

### Novos endpoints
- `POST /api/brain/import` · `POST /api/brain/import-file` · `POST /api/brain/reindex`
- `GET  /api/chat/stream?text=&conversation_id=&token=` (SSE)

### Novos arquivos
- `/app/backend/modules/embeddings.py`
- `/app/scripts/ingest_second_brain.py`
- `/app/legacy_repo/data/second-brain.json` (fixture)

