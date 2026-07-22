"""Rota consolidada de status de todas as integracoes / APIs do JARVIS"""
import os

def register_integrations_route(app):
    @app.get("/api/integrations")
    async def list_integrations():
        """Lista todas as APIs disponiveis e seus status de configuracao"""
        # Chat APIs (Consensus)
        chat_apis = {
            "groq":       {"key": bool(os.getenv("GROQ_API_KEY")),       "type": "chat",  "plan": "gratis",  "model": "Llama 3.1 70B"},
            "mistral":    {"key": bool(os.getenv("MISTRAL_API_KEY")),     "type": "chat",  "plan": "pago",    "model": "Mistral Large"},
            "claude":     {"key": bool(os.getenv("ANTHROPIC_API_KEY")),   "type": "chat",  "plan": "pago",    "model": "Claude 3.5 Sonnet"},
            "gpt":        {"key": bool(os.getenv("OPENAI_API_KEY")),      "type": "chat",  "plan": "pago",    "model": "GPT-4o"},
            "gemini":     {"key": bool(os.getenv("GOOGLE_API_KEY")),      "type": "chat",  "plan": "pago",    "model": "Gemini 1.5 Pro"},
            "ollama":     {"key": True,                                   "type": "chat",  "plan": "local",   "model": "Llama 3.2 / TinyLlama"},
        }
        creative_tools = {
            "leonardo":   {"key": bool(os.getenv("LEONARDO_API_KEY")),    "type": "imagem",   "desc": "Geracao de imagens IA"},
            "suno":       {"key": bool(os.getenv("SUNO_API_KEY")),        "type": "musica",   "desc": "Musica com IA"},
            "kling":      {"key": bool(os.getenv("KLING_API_KEY")),       "type": "video",    "desc": "Video IA (Kuaishou)"},
            "luma":       {"key": bool(os.getenv("LUMA_API_KEY")),        "type": "video",    "desc": "Video IA (Dream Machine)"},
            "pika":       {"key": bool(os.getenv("PIKA_API_KEY")),        "type": "video",    "desc": "Video IA (Pika)"},
            "meshy":      {"key": bool(os.getenv("MESHY_API_KEY")),       "type": "3d",       "desc": "Modelos 3D IA"},
            "moises":     {"key": bool(os.getenv("MOISES_API_KEY")),      "type": "audio",    "desc": "Separacao de stems"},
            "splice":     {"key": bool(os.getenv("SPLICE_API_KEY")),      "type": "audio",    "desc": "Biblioteca de samples"},
            "bestcontent":{"key": bool(os.getenv("BESTCONTENT_API_KEY")), "type": "conteudo", "desc": "Geracao de conteudo"},
            "hedra":      {"key": bool(os.getenv("HEDRA_API_KEY")),       "type": "avatar",   "desc": "Avatar / lip sync"},
            "vizard":     {"key": bool(os.getenv("VIZARD_API_KEY")),      "type": "video",    "desc": "Edicao de video IA"},
            "cobalt":     {"key": bool(os.getenv("COBALT_API_KEY")),      "type": "midia",    "desc": "Download de midia"},
        }
        social_apis = {
            "postiz":     {"key": bool(os.getenv("POSTIZ_API_KEY")),      "type": "social",   "desc": "Agendamento redes sociais"},
            "adapta":     {"key": bool(os.getenv("ADAPTA_API_KEY")),      "type": "plataforma", "desc": "Adapta ONE AI"},
            "inner":      {"key": bool(os.getenv("INNER_API_KEY")),       "type": "plataforma", "desc": "Inner Platform"},
        }
        ai_studio = {
            "muapi": {"key": True, "type": "gateway", "desc": "Gateway Muapi.ai para 19+ modelos"},
            "modelos_imagem": ["flux", "flux-realism", "flux-anime", "midjourney", "nano-banana-2",
                             "seedream-5", "minimax-image-01", "sdxl", "playground-v2.5", "ideogram-v2"],
            "modelos_video": ["kling-v2", "sora", "veo-2", "seedance-2-i2v", "grok-imagine-t2v",
                            "minimax-hailuo-02", "ltx-video"],
            "modelos_lipsync": ["infinitetalk-image-to-video", "wan2.2-speech-to-video", "ltx-2-19b-lipsync"],
        }
        self_hosted = {
            "ollama":   {"porta": 11434, "desc": "LLMs locais"},
            "whisper":  {"porta": 9000,  "desc": "Transcricao de audio"},
            "n8n":      {"porta": 5678,  "desc": "Automacao low-code"},
            "bitwarden":{"porta": 8080,  "desc": "Gerenciador de senhas"},
        }
        total_chat = sum(1 for a in chat_apis.values() if a.get("key"))
        total_tools = sum(1 for a in creative_tools.values() if a.get("key"))
        total_social = sum(1 for a in social_apis.values() if a.get("key"))
        return {
            "total_apis": len(chat_apis) + len(creative_tools) + len(social_apis) + 2,
            "configuradas": total_chat + total_tools + total_social + 1,
            "chat": chat_apis,
            "creative_tools": creative_tools,
            "social": social_apis,
            "ai_studio": ai_studio,
            "self_hosted": self_hosted,
            "embeddings": {
                "huggingface": {"key": True, "type": "embeddings", "plan": "gratuito",
                               "modelo": "paraphrase-multilingual-MiniLM-L12-v2",
                               "dimensao": 384,
                               "desc": "Busca semantica para Second Brain + Knowledge Vault"}
            }
        }
        return app
