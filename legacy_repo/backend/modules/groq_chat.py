"""
Groq Chat Engine — Motor principal de conversa do JARVIS
Usa Groq (Llama 3.1 70B) como padrao com fallback para Ollama local
Velocidade ultrarrápida via LPUs, 100% gratuito
"""

import os
import httpx
import json

class GroqChatEngine:
    """Motor de chat usando Groq API como primario"""

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.1-70b-versatile"
        self.system_prompt = (
            "Voce e o JARVIS, assistente pessoal do Hub3 Pixel Lab. "
            "Responda SEMPRE em portugues brasileiro, de forma clara, direta e objetiva. "
            "Seja profissional mas com personalidade. "
            "Quando nao souber algo, admita. "
            "Use marcacoes como **negrito** para enfase quando apropriado."
        )

    @property
    def configured(self):
        return bool(self.api_key)

    async def chat(self, message, history=None, temperature=0.7, max_tokens=2048):
        """Envia mensagem para Groq e retorna resposta"""
        if not self.configured:
            return await self._fallback_ollama(message)

        messages = [{"role": "system", "content": self.system_prompt}]
        if history:
            for h in history[-20:]:  # ultimas 20 mensagens de contexto
                messages.append(h)
        messages.append({"role": "user", "content": message})

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "stream": False
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "resposta": data["choices"][0]["message"]["content"],
                        "model": self.model,
                        "provider": "groq",
                        "tokens": data.get("usage", {}).get("total_tokens", 0),
                        "latency_ms": None  # preenchido pelo caller
                    }
                return await self._fallback_ollama(message, f"Groq HTTP {resp.status_code}")
        except Exception as e:
            return await self._fallback_ollama(message, str(e))

    async def _fallback_ollama(self, message, error=None):
        """Fallback para Ollama local se Groq falhar"""
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    "http://localhost:11434/api/generate",
                    json={"model": "llama3.2:1b", "prompt": message, "stream": False}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "resposta": data.get("response", ""),
                        "model": "llama3.2:1b",
                        "provider": "ollama",
                        "tokens": data.get("eval_count", 0),
                        "fallback_reason": error
                    }
                return {"resposta": f"Erro: Ollama e Groq indisponiveis", "model": "none", "provider": "error", "tokens": 0}
        except Exception as e2:
            return {"resposta": f"Erro: {error or e2}", "model": "none", "provider": "error", "tokens": 0}

    async def stream_chat(self, message, history=None):
        """Versao streaming (se quiser implementar SSE depois)"""
        return await self.chat(message, history)

    async def models_available(self):
        """Lista modelos disponiveis no Groq"""
        if not self.configured:
            return {"provider": "groq", "configured": False, "models": []}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                if resp.status_code == 200:
                    models = [{
                        "id": m["id"],
                        "owned_by": m.get("owned_by", ""),
                        "context_window": m.get("context_window", 32768)
                    } for m in resp.json().get("data", []) if "llama" in m["id"] or "mixtral" in m["id"] or "gemma" in m["id"]]
                    return {"provider": "groq", "configured": True, "models": models, "total": len(models)}
                return {"provider": "groq", "configured": True, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"provider": "groq", "configured": True, "error": str(e)}

groq_chat = GroqChatEngine()
