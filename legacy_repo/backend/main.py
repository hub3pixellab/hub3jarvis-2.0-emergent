from fastapi import FastAPI, Body, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pydantic import BaseModel
import httpx
import os
import subprocess
import json
from modules.orchestrator import orchestrator

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida: inicia orquestrador autônomo no startup"""
    app.state.orchestrator_status = orchestrator.status
    orchestrator.configure(SERVICES)
    await orchestrator.start(app.state)
    print(f"[JARVIS] Orquestrador autonomo iniciado - {len(SERVICES)} servicos monitorados")
    yield
    await orchestrator.stop()
    print("[JARVIS] Orquestrador autonomo parado")

app = FastAPI(title="JARVIS Backend v4.2", version="4.2", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

VAULT_DIR = "/Volumes/JARVIS HUB3/hub3-jarvis/knowledge-vault"
REPOS_DIR = "/Volumes/JARVIS HUB3/hub3-jarvis/repos"
GITHUB_USER = "hub3pixellab"

SERVICES = {
    "ollama": "http://localhost:11434",
    "whisper": "http://localhost:9000",
    "n8n": "http://localhost:5678",
    "bitwarden": "http://localhost:8080"
}

class RequisicaoJarvis(BaseModel):
    mensagem: str

class RequisicaoConsensus(BaseModel):
    prompt: str
    model: str = "llama3.2:1b"

class RequisicaoIssue(BaseModel):
    repo: str
    titulo: str
    corpo: str = ""
    labels: str = ""

class RequisicaoWhisper(BaseModel):
    audio_path: str

@app.get("/")
async def root():
    return {
        "sistema": "JARVIS",
        "versao": "4.2",
        "status": "online",
        "modelos": ["llama3.2:1b", "tinyllama:latest"],
        "vault": VAULT_DIR,
        "github_user": GITHUB_USER,
        "repos": ["hub3jarvis", "Site"],
        "servicos": SERVICES
    }

@app.get("/services/status")
async def status_servicos():
    resultados = {}
    for nome, url in SERVICES.items():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                resultados[nome] = {"status": "online", "code": resp.status_code}
        except:
            resultados[nome] = {"status": "offline"}
    return {"servicos": resultados}

@app.post("/api/jarvis/conversar")
async def conversar_com_jarvis(req: RequisicaoJarvis):
    url_ollama = "http://localhost:11434/api/generate"
    payload = {"model": "llama3.2:1b", "prompt": req.mensagem, "stream": False}
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resposta = await client.post(url_ollama, json=payload)
            resposta.raise_for_status()
            return {"resposta_jarvis": resposta.json().get("response")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro Ollama: {str(e)}")

@app.post("/consensus/ollama")
async def consensus_ollama(req: RequisicaoConsensus, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token ausente")
    url_ollama = "http://localhost:11434/api/generate"
    payload = {"model": req.model, "prompt": req.prompt, "stream": False}
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resposta = await client.post(url_ollama, json=payload)
            resposta.raise_for_status()
            data = resposta.json()
            return {
                "status": "consensus_reached",
                "model": req.model,
                "resposta": data.get("response"),
                "tokens_gerados": data.get("eval_count", 0),
                "tempo_ms": round(data.get("total_duration", 0) / 1_000_000, 1)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro Consensus: {str(e)}")

@app.get("/ollama/models")
async def listar_modelos_ollama():
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get("http://localhost:11434/api/tags")
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ollama inacessivel: {str(e)}")

@app.post("/whisper/transcribe")
async def whisper_transcribe(req: RequisicaoWhisper, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token ausente")
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            with open(req.audio_path, "rb") as f:
                resp = await client.post(
                    f"{SERVICES['whisper']}/asr",
                    files={"audio_file": f}
                )
            resp.raise_for_status()
            return {"transcricao": resp.json().get("text", "")}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Arquivo de audio nao encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro Whisper: {str(e)}")

@app.get("/github/repos")
async def listar_repos():
    try:
        result = subprocess.run(
            ["gh", "repo", "list", GITHUB_USER, "--json", "name,description,url,updatedAt,isPrivate"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Erro gh: {result.stderr}")
        repos = json.loads(result.stdout)
        return {"usuario": GITHUB_USER, "repositorios": repos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@app.get("/github/repos/{repo}/issues")
async def listar_issues(repo: str, estado: str = "all", limite: int = 20):
    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--repo", f"{GITHUB_USER}/{repo}",
             "--state", estado, "--limit", str(limite),
             "--json", "number,title,state,labels,createdAt,assignees"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Erro gh: {result.stderr}")
        issues = json.loads(result.stdout)
        return {"repo": repo, "total": len(issues), "issues": issues}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@app.post("/github/repos/{repo}/issues")
async def criar_issue(repo: str, req: RequisicaoIssue, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token ausente")
    try:
        cmd = ["gh", "issue", "create", "--repo", f"{GITHUB_USER}/{repo}",
               "--title", req.titulo, "--body", req.corpo]
        if req.labels:
            cmd.extend(["--label", req.labels])
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Erro gh: {result.stderr}")
        return {"status": "criada", "repo": repo, "url": result.stdout.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@app.get("/github/repos/{repo}/commits")
async def listar_commits(repo: str, limite: int = 10):
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{GITHUB_USER}/{repo}/commits",
             "--jq", f".[:{limite}] | map({{sha: .sha[0:7], msg: .commit.message, data: .commit.author.date, autor: .commit.author.name}})"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Erro gh: {result.stderr}")
        commits = json.loads(result.stdout) if result.stdout.strip() else []
        return {"repo": repo, "commits": commits}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@app.get("/github/repos/{repo}/pr")
async def listar_prs(repo: str, estado: str = "all", limite: int = 10):
    try:
        result = subprocess.run(
            ["gh", "pr", "list", "--repo", f"{GITHUB_USER}/{repo}",
             "--state", estado, "--limit", str(limite),
             "--json", "number,title,state,author,createdAt,headRefName"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Erro gh: {result.stderr}")
        prs = json.loads(result.stdout)
        return {"repo": repo, "pull_requests": prs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@app.get("/vault/stats")
async def stats_vault(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token ausente")
    categorias = {}
    total_arquivos = 0
    tamanho_total = 0
    if os.path.exists(VAULT_DIR):
        for categoria in os.listdir(VAULT_DIR):
            cat_path = os.path.join(VAULT_DIR, categoria)
            if os.path.isdir(cat_path) and not categoria.startswith("."):
                arquivos = [f for f in os.listdir(cat_path) if not f.startswith(".")]
                count = len(arquivos)
                size = sum(
                    os.path.getsize(os.path.join(cat_path, f))
                    for f in arquivos
                    if os.path.isfile(os.path.join(cat_path, f))
                )
                categorias[categoria] = {"arquivos": count, "tamanho_mb": round(size / (1024*1024), 1)}
                total_arquivos += count
                tamanho_total += size
    return {
        "status": "online",
        "vault_dir": VAULT_DIR,
        "total_arquivos": total_arquivos,
        "tamanho_total_gb": round(tamanho_total / (1024*1024*1024), 2),
        "categorias": categorias
    }

@app.get("/repos/local")
async def listar_repos_local():
    repos = []
    if os.path.exists(REPOS_DIR):
        for repo in os.listdir(REPOS_DIR):
            repo_path = os.path.join(REPOS_DIR, repo)
            if os.path.isdir(repo_path) and not repo.startswith("."):
                git_path = os.path.join(repo_path, ".git")
                is_git = os.path.exists(git_path)
                file_count = sum(len(files) for _, _, files in os.walk(repo_path) if ".git" not in _)
                repos.append({
                    "nome": repo,
                    "caminho": repo_path,
                    "is_git": is_git,
                    "arquivos": file_count
                })
    return {"repos_dir": REPOS_DIR, "repositorios": repos}

@app.get("/repos/local/{repo}/analyze")
async def analisar_repo_local(repo: str, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token ausente")
    repo_path = os.path.join(REPOS_DIR, repo)
    if not os.path.exists(repo_path):
        raise HTTPException(status_code=404, detail="Repositorio nao encontrado")
    
    extensoes = {}
    linguagens = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".html": "HTML", ".css": "CSS", ".json": "JSON",
        ".md": "Markdown", ".yml": "YAML", ".yaml": "YAML",
        ".sh": "Shell", ".sql": "SQL", ".java": "Java",
        ".c": "C", ".cpp": "C++", ".go": "Go", ".rs": "Rust"
    }
    
    total_arquivos = 0
    total_linhas = 0
    
    for raiz, dirs, files in os.walk(repo_path):
        if ".git" in raiz:
            continue
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in linguagens:
                extensoes[ext] = extensoes.get(ext, 0) + 1
                total_arquivos += 1
                try:
                    with open(os.path.join(raiz, f), 'r', errors='ignore') as fh:
                        total_linhas += sum(1 for _ in fh)
                except:
                    pass
    
    return {
        "repo": repo,
        "caminho": repo_path,
        "total_arquivos_codigo": total_arquivos,
        "total_linhas": total_linhas,
        "linguagens": {linguagens.get(k, k): v for k, v in extensoes.items()}
    }

@app.get("/n8n/workflows")
async def listar_workflows_n8n(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token ausente")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{SERVICES['n8n']}/api/v1/workflows")
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"n8n inacessivel: {str(e)}")

# ===== ROTAS DO AI STUDIO (Open Generative AI) =====

MUAPI_BASE = "https://api.muapi.ai/api/v1"

@app.post("/ai/generate")
async def ai_generate(data: dict = Body(...)):
    """Submete geracao de imagem ou video via Muapi.ai"""
    model_endpoint = data.get("model", "flux")
    prompt = data.get("prompt", "")
    api_key = data.get("api_key", "")
    aspect_ratio = data.get("aspect_ratio", "1:1")
    image_url = data.get("image_url", None)

    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt obrigatorio")
    if not api_key:
        raise HTTPException(status_code=400, detail="API key da Muapi.ai obrigatoria")

    payload = {"prompt": prompt, "aspect_ratio": aspect_ratio}
    if image_url:
        payload["image_url"] = image_url

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{MUAPI_BASE}/{model_endpoint}",
                json=payload,
                headers={"x-api-key": api_key, "Content-Type": "application/json"}
            )
            result = resp.json()
            if resp.status_code != 200:
                return {"erro": result.get("detail", "Erro na API"), "status_code": resp.status_code}
            return {"request_id": result.get("id") or result.get("request_id"), "status": "pending", "raw": result}
    except Exception as e:
        return {"erro": str(e)}

@app.get("/ai/prediction/{request_id}")
async def ai_prediction(request_id: str, api_key: str = ""):
    """Consulta status de uma geracao"""
    if not api_key:
        raise HTTPException(status_code=400, detail="API key obrigatoria")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{MUAPI_BASE}/predictions/{request_id}/result",
                headers={"x-api-key": api_key}
            )
            result = resp.json()
            status = result.get("status", "unknown")
            output = result.get("output")
            if isinstance(output, list) and len(output) > 0:
                output = output[0]
            return {"status": status, "output": output, "raw": result}
    except Exception as e:
        return {"erro": str(e)}

@app.post("/ai/upload")
async def ai_upload(data: dict = Body(...)):
    """Upload de imagem de referencia"""
    api_key = data.get("api_key", "")
    file_path = data.get("file_path", "")
    if not api_key or not file_path:
        raise HTTPException(status_code=400, detail="api_key e file_path obrigatorios")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Arquivo nao encontrado")
    try:
        import aiofiles
    except ImportError:
        import subprocess
        subprocess.run(["pip", "install", "aiofiles"], capture_output=True)
        import aiofiles

    async with aiofiles.open(file_path, "rb") as f:
        file_data = await f.read()

    filename = os.path.basename(file_path)
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{MUAPI_BASE}/upload_file",
            files={"file": (filename, file_data)},
            headers={"x-api-key": api_key}
        )
        result = resp.json()
        return {"url": result.get("url") or result.get("file_url"), "raw": result}

AI_MODELS = {
    "image": [
        {"id": "flux", "nome": "Flux", "desc": "Texto para imagem - rapido e versatil"},
        {"id": "flux-realism", "nome": "Flux Realism", "desc": "Foto-realista de alta qualidade"},
        {"id": "flux-anime", "nome": "Flux Anime", "desc": "Estilo anime e manga"},
        {"id": "midjourney", "nome": "Midjourney", "desc": "Estilo artistico Midjourney"},
        {"id": "nano-banana-2", "nome": "Nano Banana 2", "desc": "Google Gemini 3.1 Flash - ate 4K"},
        {"id": "seedream-5", "nome": "Seedream 5.0", "desc": "ByteDance - alta qualidade ate 4K"},
        {"id": "minimax-image-01", "nome": "MiniMax Image 01", "desc": "MiniMax - ate 4 imagens por request"},
        {"id": "sdxl", "nome": "SDXL", "desc": "Stable Diffusion XL"},
        {"id": "playground-v2.5", "nome": "Playground v2.5", "desc": "Estilo artistico"},
        {"id": "ideogram-v2", "nome": "Ideogram v2", "desc": "Texto em imagens"},
    ],
    "video": [
        {"id": "kling-v2", "nome": "Kling v2", "desc": "Texto para video - ate 10s"},
        {"id": "sora", "nome": "Sora", "desc": "OpenAI Sora - cinematico"},
        {"id": "veo-2", "nome": "Veo 2", "desc": "Google Veo 2 - alta qualidade"},
        {"id": "seedance-2-i2v", "nome": "Seedance 2.0 I2V", "desc": "ByteDance - imagem para video"},
        {"id": "grok-imagine-t2v", "nome": "Grok Imagine T2V", "desc": "xAI - ate 15s"},
        {"id": "minimax-hailuo-02", "nome": "MiniMax Hailuo 02", "desc": "Full HD - multiplos aspect ratios"},
        {"id": "ltx-video", "nome": "LTX Video", "desc": "Rapido e leve"},
    ],
    "lipsync": [
        {"id": "infinitetalk-image-to-video", "nome": "Infinite Talk", "desc": "Retrato + audio -> video falando"},
        {"id": "wan2.2-speech-to-video", "nome": "Wan 2.2 Speech", "desc": "Speech to video - 480p/720p"},
        {"id": "ltx-2-19b-lipsync", "nome": "LTX 2 19B Lipsync", "desc": "Alta qualidade - ate 1080p"},
    ]
}

@app.get("/ai/models")
async def ai_models():
    """Lista modelos disponiveis"""
    return {"modelos": AI_MODELS}




# ===== SKILLS AUTONOMAS =====
from enum import Enum

class SkillCategory(str, Enum):
    cybersecurity = "cybersecurity"
    seo = "seo"
    ui_ux = "ui_ux"
    marketing = "marketing"
    escrita = "escrita"
    design = "design"
    vendas = "vendas"
    desenvolvimento = "desenvolvimento"
    produtividade = "produtividade"
    conhecimento = "conhecimento"
    dados = "dados"

SKILLS_DATA = {
    "cybersecurity": {"title": "CyberSecurity Expert", "description": "817 skills de ciberseguranca em 29 dominios", "subskills": 817, "icon": "shield", "color": "red", "domains": ["Cloud Security", "Threat Hunting", "Malware Analysis", "DFIR", "Red Teaming", "SOC", "Web AppSec"], "commands": ["auditar seguranca", "detectar vulnerabilidades", "forense digital"]},
    "seo": {"title": "SEO Agent Expert", "description": "25 sub-skills com 18 agentes especialistas em auditoria SEO", "subskills": 25, "icon": "target", "color": "green", "domains": ["SEO Tecnico", "E-E-A-T", "Schema.org", "GEO"], "commands": ["auditar site", "analisar pagina", "schema markup"]},
    "ui_ux": {"title": "UI Recreation Agent", "description": "Recria interfaces HTML a partir de referencias visuais com fidelidade total", "subskills": 6, "icon": "camera", "color": "violet", "domains": ["Replicacao Layout", "Extracao Conteudo", "Animacoes"], "commands": ["recriar interface", "extrair design", "gerar variacoes"]},
    "marketing": {"title": "Marketing Skills", "description": "30+ agentes de marketing: auditorias SEO, copywriting, CRO", "subskills": 30, "icon": "trending", "color": "orange", "domains": ["Auditoria SEO", "Copywriting", "Email", "CRO"], "commands": ["auditoria seo", "copy landing page", "sequencia emails"]},
    "escrita": {"title": "Stop-Slop", "description": "Remove sinais de texto IA: aberturas genericas, cliches", "subskills": 1, "icon": "pen", "color": "yellow", "domains": ["Humanizacao", "Revisao Estilo"], "commands": ["humanizar texto", "revisar estilo"]},
    "design": {"title": "UI/UX + Design Tools", "description": "50+ estilos de UI, Picsart GenAI, Algorithmic Art", "subskills": 4, "icon": "palette", "color": "fuchsia", "domains": ["Design System", "Interface", "Arte Generativa"], "commands": ["criar design system", "gerar interface", "criar arte"]},
    "vendas": {"title": "AI Sales Team", "description": "14 skills e 5 agentes: prospeccao, qualificacao BANT/MEDDIC", "subskills": 14, "icon": "dollar", "color": "green", "domains": ["Prospeccao", "Qualificacao", "Pipeline"], "commands": ["pesquisar prospects", "qualificar lead", "criar sequencia"]},
    "desenvolvimento": {"title": "Superpowers + React Native", "description": "Ciclo completo: TDD, subagentes, revisao codigo, merge", "subskills": 2, "icon": "code", "color": "blue", "domains": ["Planejamento", "Execucao", "Testes"], "commands": ["planejar projeto", "executar tarefas", "revisar codigo"]},
    "produtividade": {"title": "Context Engineering + Caveman", "description": "Otimizacao de tokens e contexto + respostas ultracompactas", "subskills": 2, "icon": "zap", "color": "yellow", "domains": ["Otimizacao", "Economia Tokens"], "commands": ["otimizar contexto", "modo compacto"]},
    "conhecimento": {"title": "Obsidian Second Brain", "description": "31 comandos para gerenciar base Obsidian com IA", "subskills": 31, "icon": "brain", "color": "violet", "domains": ["Gestao Notas", "Pesquisa Web"], "commands": ["pesquisar base", "sintetizar notas"]},
    "dados": {"title": "D3.js Visualization", "description": "Visualizacoes interativas com D3.js", "subskills": 1, "icon": "chart", "color": "sky", "domains": ["Visualizacao", "Graficos"], "commands": ["criar grafico", "visualizar dados"]}
}

@app.get('/skills')
async def list_skills():
    return {'skills': SKILLS_DATA, 'total': len(SKILLS_DATA)}

@app.get('/skills/{category}')
async def get_skill(category: SkillCategory):
    skill = SKILLS_DATA.get(category.value)
    if not skill:
        raise HTTPException(404, 'Skill nao encontrada')
    return skill

@app.post('/skills/autonomous')
async def autonomous_analysis(data: dict):
    user_input = data.get('input', '').lower()
    keywords = [
        ('seguran', 'cybersecurity'), ('vulnerabilidad', 'cybersecurity'), ('hack', 'cybersecurity'),
        ('malware', 'cybersecurity'), ('pentest', 'cybersecurity'),
        ('seo', 'seo'), ('google', 'seo'), ('schema', 'seo'), ('backlink', 'seo'),
        ('ui', 'ui_ux'), ('ux', 'ui_ux'), ('interface', 'ui_ux'), ('layout', 'ui_ux'),
        ('marketing', 'marketing'), ('copy', 'marketing'), ('landing page', 'marketing'),
        ('humanizar', 'escrita'), ('revisar texto', 'escrita'),
        ('venda', 'vendas'), ('prospect', 'vendas'), ('lead', 'vendas'),
        ('codigo', 'desenvolvimento'), ('react', 'desenvolvimento'), ('api', 'desenvolvimento'),
        ('produtividade', 'produtividade'), ('token', 'produtividade'),
        ('obsidian', 'conhecimento'), ('segundo cerebro', 'conhecimento'),
        ('grafico', 'dados'), ('dashboard', 'dados'), ('visualizar', 'dados'),
    ]
    detected = []
    for kw, cat in keywords:
        if kw in user_input and cat not in detected:
            detected.append(cat)
    if not detected:
        return {'detected_skills': [], 'message': 'Nenhuma skill detectada'}
    results = []
    for cat in detected[:3]:
        skill = SKILLS_DATA.get(cat, {})
        results.append({'skill': cat, 'title': skill.get('title', cat), 'description': skill.get('description', ''), 'suggested_command': skill.get('commands', [''])[0]})
    return {'detected_skills': detected, 'analysis': results, 'message': f'JARVIS detectou {len(detected)} skill(s)'}

# ===== ROTAS DE AUTONOMIA =====
from routes.autonomy_routes import register_routes
app = register_routes(app, orchestrator)

# ===== ROTA DE INTEGRACOES =====
from routes.integrations_route import register_integrations_route
app = register_integrations_route(app)

@app.get("/groq/models")
async def groq_models():
	"""Lista modelos disponiveis no Groq"""
	from modules.groq_chat import groq_chat
	return await groq_chat.models_available()

@app.get("/chat/status")
async def chat_status():
	"""Status do motor de chat"""
	from modules.groq_chat import groq_chat
	return {
		"primary": "groq" if groq_chat.configured else "ollama (fallback)",
		"groq_configured": groq_chat.configured,
		"groq_model": groq_chat.model,
		"fallback": "ollama (llama3.2:1b)"
	}

@app.get("/embeddings/status")
async def embeddings_status():
	"""Status do servico de embeddings Hugging Face"""
	from modules.huggingface_embeddings import hf_embeddings
	from modules.second_brain import second_brain
	brain = second_brain.get_stats()
	emb = await hf_embeddings.get_status()
	return {
		"embeddings": emb,
		"second_brain": brain,
		"total_knowledge_indexed": brain.get("total_knowledge", 0),
		"model": "paraphrase-multilingual-MiniLM-L12-v2",
		"dimensao": 384,
		"plan": "gratuito (huggingface inference api)"
	}

app.mount("/frontend", StaticFiles(directory="/Volumes/JARVIS HUB3/hub3-jarvis/frontend"), name="frontend")
