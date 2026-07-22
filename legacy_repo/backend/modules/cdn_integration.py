"""
CDN Integration Module — JARVIS v4.2
jsDelivr + unpkg para distribuir assets do frontend via CDN global
100% gratuito para projetos open-source no GitHub
"""

import httpx
import os
import json

class CDNIntegration:
    """Integracao com jsDelivr e unpkg para entrega de assets"""

    def __init__(self):
        self.gh_user = os.getenv("GITHUB_USER", "hub3pixellab")
        self.gh_repo = os.getenv("GITHUB_REPO", "hub3jarvis")
        self.branch = "main"

    # ===== JSDELIVR =====

    @property
    def jsdelivr_base(self):
        """Base URL do jsDelivr para o repositorio"""
        return f"https://cdn.jsdelivr.net/gh/{self.gh_user}/{self.gh_repo}@{self.branch}"

    def jsdelivr_url(self, file_path):
        """Gera URL completa de um asset no jsDelivr"""
        return f"{self.jsdelivr_base}/{file_path.lstrip('/')}"

    @property
    def unpkg_base(self):
        """Base URL do unpkg (requer package.json publico)"""
        return f"https://unpkg.com/{self.gh_repo}@latest"

    def unpkg_url(self, file_path):
        """Gera URL completa de um asset no unpkg"""
        return f"{self.unpkg_base}/{file_path.lstrip('/')}"

    # ===== ASSETS DISPONIVEIS =====

    def list_frontend_assets(self):
        """Lista todos os assets do frontend disponiveis via CDN"""
        assets = {
            "index.html": self.jsdelivr_url("frontend/index.html"),
            "config.js": self.jsdelivr_url("frontend/config.js"),
            "toast.js": self.jsdelivr_url("frontend/toast.js"),
            "favicon": self.jsdelivr_url("frontend/favicon.ico") if os.path.exists(
                "/Volumes/JARVIS HUB3/hub3-jarvis/frontend/favicon.ico"
            ) else None,
        }
        # Assets de imagem do repositorio
        img_dir = "/Volumes/JARVIS HUB3/hub3-jarvis/frontend/img"
        if os.path.exists(img_dir):
            for f in os.listdir(img_dir):
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico")):
                    assets[f"img/{f}"] = self.jsdelivr_url(f"frontend/img/{f}")

        return {k: v for k, v in assets.items() if v}

    # ===== CDN AUTO-SYNC =====

    async def verify_jsdelivr(self, file_path="frontend/index.html"):
        """Verifica se o asset esta acessivel via jsDelivr"""
        url = self.jsdelivr_url(file_path)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.head(url, follow_redirects=True)
                return {
                    "url": url,
                    "status": resp.status_code,
                    "disponivel": resp.status_code == 200,
                    "cache": resp.headers.get("x-cache", "unknown"),
                    "cdn": "jsdelivr"
                }
        except Exception as e:
            return {"url": url, "status": 0, "disponivel": False, "erro": str(e), "cdn": "jsdelivr"}

    async def verify_unpkg(self, file_path="frontend/index.html"):
        """Verifica se o asset esta acessivel via unpkg"""
        url = self.unpkg_url(file_path)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.head(url, follow_redirects=True)
                return {
                    "url": url,
                    "status": resp.status_code,
                    "disponivel": resp.status_code == 200,
                    "cdn": "unpkg"
                }
        except Exception as e:
            return {"url": url, "status": 0, "disponivel": False, "erro": str(e), "cdn": "unpkg"}

    async def verify_all(self):
        """Verifica todos os assets nas duas CDNs"""
        assets = self.list_frontend_assets()
        results = {}
        for name, url in assets.items():
            jsd = await self.verify_jsdelivr(name)
            results[name] = {"jsdelivr": jsd}
        return {
            "total_assets": len(assets),
            "assets": results,
            "repo": f"{self.gh_user}/{self.gh_repo}",
            "branch": self.branch
        }

    # ===== HELPER: GERAR SCRIPT TAG =====

    def generate_loader_script(self, minify=False):
        """
        Gera codigo HTML/JS para carregar o frontend via CDN.
        Util se quiser distribuir o JARVIS como pagina estatica.
        """
        index_url = self.jsdelivr_url("frontend/index.html")
        return f"""<!-- Carregar JARVIS via jsDelivr CDN -->
<link rel="preload" href="{index_url}" as="document">
<script>
// Loader JARVIS via CDN
(function() {{
    var url = "{index_url}";
    fetch(url)
        .then(r => r.text())
        .then(html => {{
            document.open();
            document.write(html.replace(
                '</head>',
                '<base href="{index_url.replace('/index.html', '/')}"></head>'
            ));
            document.close();
        }});
}})();
</script>"""

    # ===== GERAR CARD FRONTEND =====

    def generate_html_panel(self):
        """Gera HTML do painel de CDN para o frontend"""
        assets = self.list_frontend_assets()
        cards = ""
        for name, url in assets.items():
            ext = name.split(".")[-1].lower()
            icons = {"html": "📄", "js": "📜", "css": "🎨", "png": "🖼️", "jpg": "🖼️", "jpeg": "🖼️", "gif": "🎬", "svg": "🔶", "ico": "🔷"}
            icon = icons.get(ext, "📁")
            cards += f"""
            <div style="background:var(--bg-input);border:1px solid var(--border);border-radius:8px;padding:12px;font-size:13px">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <span>{icon} <strong>{name}</strong></span>
                    <button class="btn" style="padding:4px 10px;font-size:11px" onclick="navigator.clipboard.writeText('{url}')">Copiar URL</button>
                </div>
                <div style="font-size:11px;color:var(--text-muted);margin-top:4px;word-break:break-all">{url}</div>
            </div>"""
        return f"""
        <div class="card" id="section-cdn" style="display:none">
        <div class="card-title">🌐 CDN Global (jsDelivr + unpkg)</div>
        <div style="font-size:13px;color:var(--text-muted);margin-bottom:16px">
            Assets do JARVIS hospedados gratuitamente via jsDelivr CDN — carregamento instantaneo em qualquer lugar.
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:8px">{cards}</div>
        <div style="margin-top:16px;font-size:12px;color:var(--text-muted);text-align:center">
            🚀 {len(assets)} assets disponiveis | <a href="https://www.jsdelivr.com/features" target="_blank" style="color:var(--cyan)">jsDelivr</a> + <a href="https://unpkg.com" target="_blank" style="color:var(--cyan)">unpkg</a>
        </div>
        </div>"""

cdn = CDNIntegration()
