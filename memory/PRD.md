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
