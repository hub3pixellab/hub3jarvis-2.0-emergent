import asyncio
import httpx
import os
import time
from datetime import datetime

class ConsensusEngine:
    def __init__(self):
        self.models = {
            "groq": {
                "url": "https://api.groq.com/openai/v1/chat/completions",
                "key": os.getenv("GROQ_API_KEY"),
                "model": "llama-3.1-70b-versatile",
                "weight": 1.0,
                "cost_per_1k": 0.0,
                "display_name": "Groq (Llama 3.1 70B)"
            },
            "mistral": {
                "url": "https://api.mistral.ai/v1/chat/completions",
                "key": os.getenv("MISTRAL_API_KEY"),
                "model": "mistral-large-latest",
                "weight": 1.0,
                "cost_per_1k": 0.002,
                "display_name": "Mistral Large"
            },
            "claude": {
                "url": "https://api.anthropic.com/v1/messages",
                "key": os.getenv("ANTHROPIC_API_KEY"),
                "model": "claude-3-5-sonnet-20241022",
                "weight": 1.5,
                "cost_per_1k": 0.015,
                "display_name": "Claude 3.5 Sonnet"
            },
            "gpt": {
                "url": "https://api.openai.com/v1/chat/completions",
                "key": os.getenv("OPENAI_API_KEY"),
                "model": "gpt-4o",
                "weight": 1.5,
                "cost_per_1k": 0.005,
                "display_name": "GPT-4o"
            },
            "gemini": {
                "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent",
                "key": os.getenv("GOOGLE_API_KEY"),
                "model": "gemini-1.5-pro",
                "weight": 1.3,
                "cost_per_1k": 0.0035,
                "display_name": "Gemini 1.5 Pro"
            }
        }
        self.system_prompt = (
            "Voce e o Hub3 JARVIS, um assistente pessoal brasileiro. "
            "Responda sempre em portugues brasileiro, de forma clara e direta. "
            "Use tom profissional mas amigavel, estilo Jarvis do Iron Man. "
            "Quando controlar dispositivos, confirme a acao antes de executar. "
            "Para contatos protegidos na whitelist, recuse qualquer interacao."
        )

    async def query_model(self, client, name, config, question, context=None):
        start = time.time()
        try:
            full_prompt = question
            if context:
                full_prompt = f"Contexto do Second Brain:\n{context}\n\nPergunta: {question}"

            if name == "claude":
                resp = await client.post(
                    config["url"],
                    headers={
                        "x-api-key": config["key"],
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": config["model"],
                        "max_tokens": 1000,
                        "system": self.system_prompt,
                        "messages": [{"role": "user", "content": full_prompt}]
                    },
                    timeout=30
                )
                data = resp.json()
                answer = data["content"][0]["text"]

            elif name == "gemini":
                resp = await client.post(
                    f"{config['url']}?key={config['key']}",
                    json={
                        "contents": [{"parts": [{"text": f"{self.system_prompt}\n\n{full_prompt}"}]}],
                        "generationConfig": {"maxOutputTokens": 1000}
                    },
                    timeout=30
                )
                data = resp.json()
                answer = data["candidates"][0]["content"]["parts"][0]["text"]

            else:
                resp = await client.post(
                    config["url"],
                    headers={
                        "Authorization": f"Bearer {config['key']}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": config["model"],
                        "messages": [
                            {"role": "system", "content": self.system_prompt},
                            {"role": "user", "content": full_prompt}
                        ],
                        "max_tokens": 1000
                    },
                    timeout=30
                )
                data = resp.json()
                answer = data["choices"][0]["message"]["content"]

            elapsed = time.time() - start
            tokens = len(answer.split())
            confidence = min(1.0, tokens / 80)

            return {
                "model": name,
                "display_name": config["display_name"],
                "answer": answer,
                "confidence": confidence,
                "weight": config["weight"],
                "cost": (tokens / 1000) * config["cost_per_1k"],
                "latency": round(elapsed, 2),
                "tokens": tokens,
                "error": None
            }

        except Exception as e:
            return {
                "model": name,
                "display_name": config["display_name"],
                "answer": None,
                "confidence": 0,
                "weight": config["weight"],
                "cost": 0,
                "latency": round(time.time() - start, 2),
                "tokens": 0,
                "error": str(e)
            }

    async def query_all(self, question, user_plan="free", context=None):
        if user_plan == "free":
            active = ["groq", "mistral"]
        else:
            active = ["groq", "mistral", "claude", "gpt", "gemini"]

        async with httpx.AsyncClient() as client:
            tasks = [
                self.query_model(client, name, self.models[name], question, context)
                for name in active
                if self.models[name]["key"]
            ]
            results = await asyncio.gather(*tasks)

        valid = [r for r in results if r["answer"] and not r["error"]]

        if not valid:
            return {
                "consensus": "Nenhuma IA respondeu. Tente novamente.",
                "best_model": None,
                "confidence": 0,
                "responses": results,
                "total_cost": 0,
                "total_latency": 0,
                "models_used": 0,
                "timestamp": datetime.now().isoformat()
            }

        best = max(valid, key=lambda r: r["confidence"] * r["weight"])
        total_cost = sum(r["cost"] for r in results)
        total_latency = max(r["latency"] for r in results)

        return {
            "consensus": best["answer"],
            "best_model": best["display_name"],
            "confidence": round(best["confidence"], 2),
            "responses": [
                {
                    "model": r["display_name"],
                    "answer": r["answer"],
                    "confidence": round(r["confidence"], 2),
                    "latency": r["latency"],
                    "cost": round(r["cost"], 6),
                    "error": r["error"]
                }
                for r in results
            ],
            "total_cost": round(total_cost, 6),
            "total_latency": total_latency,
            "models_used": len(valid),
            "timestamp": datetime.now().isoformat()
        }

consensus_engine = ConsensusEngine()
