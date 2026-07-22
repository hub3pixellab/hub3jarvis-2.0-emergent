"""
GitHub Integration Module — JARVIS v4.2
Unifica TODO o acesso ao GitHub: API REST + gh CLI fallback
Centraliza todas as operacoes para evitar duplicacao com main.py
"""

import httpx
import os
import base64
import subprocess
import json

class GitHubIntegration:
    """Integracao completa com GitHub via API REST com fallback para gh CLI"""

    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.username = os.getenv("GITHUB_USER", "hub3pixellab")
        self.repo = os.getenv("GITHUB_REPO", "hub3pixellab/hub3jarvis")
        self.api = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Hub3-JARVIS-v4.2"
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    # ===== METODOS AUXILIARES =====

    @property
    def configured(self):
        """Verifica se o token esta configurado"""
        return bool(self.token)

    async def _request(self, method, endpoint, **kwargs):
        """Faz requisicao a API do GitHub"""
        url = f"{self.api}{endpoint}" if endpoint.startswith("/") else f"{self.api}/repos/{self.repo}{endpoint}"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.request(method, url, headers=self.headers, **kwargs)
            return resp

    def _gh_cli(self, args):
        """Executa gh CLI como fallback"""
        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=15)
            if result.returncode == 0 and result.stdout.strip():
                return json.loads(result.stdout)
            return {"error": result.stderr, "fallback": True}
        except Exception as e:
            return {"error": str(e), "fallback": True}

    # ===== REPOSITORIOS =====

    async def list_repos(self):
        """Lista todos os repositorios do usuario"""
        if self.configured:
            resp = await self._request("GET", f"/users/{self.username}/repos?per_page=50&sort=updated")
            if resp.status_code == 200:
                data = resp.json()
                return [{
                    "name": r["name"],
                    "description": r.get("description", ""),
                    "url": r["html_url"],
                    "updatedAt": r.get("updated_at", ""),
                    "isPrivate": r.get("private", False),
                    "language": r.get("language", ""),
                    "stars": r.get("stargazers_count", 0),
                    "forks": r.get("forks_count", 0)
                } for r in data]
        # Fallback gh CLI
        return self._gh_cli(["gh", "repo", "list", self.username, "--json", "name,description,url,updatedAt,isPrivate"])

    async def get_repo_info(self, repo=None):
        """Obtem informacoes de um repositorio especifico"""
        r = repo or self.repo
        if self.configured:
            resp = await self._request("GET", f"/repos/{r}")
            if resp.status_code == 200:
                d = resp.json()
                return {
                    "name": d["name"],
                    "full_name": d["full_name"],
                    "description": d.get("description", ""),
                    "url": d["html_url"],
                    "stars": d.get("stargazers_count", 0),
                    "forks": d.get("forks_count", 0),
                    "open_issues": d.get("open_issues_count", 0),
                    "language": d.get("language", ""),
                    "default_branch": d.get("default_branch", "main"),
                    "license": d.get("license", {}).get("spdx_id", "") if d.get("license") else "",
                    "updated_at": d.get("updated_at", ""),
                    "created_at": d.get("created_at", ""),
                    "size_kb": d.get("size", 0)
                }
        return {"error": "GitHub token nao configurado", "repo": r}

    # ===== COMMITS =====

    async def list_commits(self, repo=None, per_page=10, branch="main"):
        """Lista commits de um repositorio"""
        r = repo or self.repo
        if self.configured:
            resp = await self._request("GET", f"/repos/{r}/commits",
                                       params={"per_page": per_page, "sha": branch})
            if resp.status_code == 200:
                return [{
                    "sha": c["sha"][:7],
                    "message": c["commit"]["message"].split("\n")[0],
                    "author": c["commit"]["author"]["name"],
                    "date": c["commit"]["author"]["date"],
                    "url": c["html_url"]
                } for c in resp.json()]
        # Fallback gh CLI
        result = self._gh_cli(["gh", "api", f"repos/{r}/commits",
                               "--jq", f".[:{per_page}] | map({{sha: .sha[0:7], msg: .commit.message, data: .commit.author.date, autor: .commit.author.name}})"])
        if isinstance(result, list):
            return [{"sha": c.get("sha", ""), "message": c.get("msg", ""),
                     "author": c.get("autor", ""), "date": c.get("data", "")} for c in result]
        return result

    # ===== ISSUES =====

    async def list_issues(self, repo=None, state="open", per_page=20, labels=None):
        """Lista issues de um repositorio"""
        r = repo or self.repo
        params = {"state": state, "per_page": per_page, "sort": "updated", "direction": "desc"}
        if labels:
            params["labels"] = labels
        if self.configured:
            resp = await self._request("GET", f"/repos/{r}/issues", params=params)
            if resp.status_code == 200:
                return [{
                    "number": i["number"],
                    "title": i["title"],
                    "state": i["state"],
                    "labels": [l["name"] for l in i.get("labels", [])],
                    "created_at": i.get("created_at", ""),
                    "updated_at": i.get("updated_at", ""),
                    "assignees": [a["login"] for a in i.get("assignees", [])],
                    "url": i["html_url"],
                    "body_preview": (i.get("body", "") or "")[:200]
                } for i in resp.json() if "pull_request" not in i]
        # Fallback gh CLI
        result = self._gh_cli(["gh", "issue", "list", "--repo", r,
                               "--state", state, "--limit", str(per_page),
                               "--json", "number,title,state,labels,createdAt,assignees"])
        if isinstance(result, list):
            return result
        return result

    async def create_issue(self, title, body, labels=None, repo=None):
        """Cria uma issue"""
        r = repo or self.repo
        if self.configured:
            resp = await self._request("POST", f"/repos/{r}/issues",
                                       json={"title": title, "body": body, "labels": labels or []})
            if resp.status_code in (200, 201):
                d = resp.json()
                return {"status": "criada", "number": d["number"], "url": d["html_url"], "title": d["title"]}
        # Fallback gh CLI
        cmd = ["gh", "issue", "create", "--repo", r, "--title", title, "--body", body]
        if labels:
            cmd.extend(["--label", ",".join(labels)])
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return {"status": "criada", "url": result.stdout.strip(), "title": title}
        return {"error": result.stderr}

    async def get_issue(self, issue_number, repo=None):
        """Obtem detalhes de uma issue especifica"""
        r = repo or self.repo
        if self.configured:
            resp = await self._request("GET", f"/repos/{r}/issues/{issue_number}")
            if resp.status_code == 200:
                d = resp.json()
                return {
                    "number": d["number"],
                    "title": d["title"],
                    "state": d["state"],
                    "body": d.get("body", ""),
                    "labels": [l["name"] for l in d.get("labels", [])],
                    "assignees": [a["login"] for a in d.get("assignees", [])],
                    "comments": d.get("comments", 0),
                    "created_at": d.get("created_at", ""),
                    "updated_at": d.get("updated_at", ""),
                    "url": d["html_url"]
                }
        return {"error": f"GitHub token nao configurado ou issue #{issue_number} nao encontrada"}

    async def close_issue(self, issue_number, repo=None):
        """Fecha uma issue"""
        r = repo or self.repo
        if self.configured:
            resp = await self._request("PATCH", f"/repos/{r}/issues/{issue_number}",
                                       json={"state": "closed"})
            if resp.status_code == 200:
                return {"status": "fechada", "number": issue_number, "url": resp.json()["html_url"]}
        return {"error": "GitHub token nao configurado"}

    # ===== PULL REQUESTS =====

    async def list_prs(self, repo=None, state="open", per_page=10):
        """Lista pull requests de um repositorio"""
        r = repo or self.repo
        if self.configured:
            resp = await self._request("GET", f"/repos/{r}/pulls",
                                       params={"state": state, "per_page": per_page, "sort": "updated", "direction": "desc"})
            if resp.status_code == 200:
                return [{
                    "number": pr["number"],
                    "title": pr["title"],
                    "state": pr["state"],
                    "author": pr["user"]["login"] if pr.get("user") else "unknown",
                    "created_at": pr.get("created_at", ""),
                    "head": pr["head"]["ref"] if pr.get("head") else "",
                    "base": pr["base"]["ref"] if pr.get("base") else "",
                    "url": pr["html_url"],
                    "draft": pr.get("draft", False)
                } for pr in resp.json()]
        # Fallback gh CLI
        result = self._gh_cli(["gh", "pr", "list", "--repo", r,
                               "--state", state, "--limit", str(per_page),
                               "--json", "number,title,state,author,createdAt,headRefName"])
        if isinstance(result, list):
            return result
        return result

    async def create_pull_request(self, title, head, base="main", body=""):
        """Cria um pull request"""
        if self.configured:
            resp = await self._request("POST", f"/repos/{self.repo}/pulls",
                                       json={"title": title, "head": head, "base": base, "body": body})
            if resp.status_code in (200, 201):
                d = resp.json()
                return {"status": "criado", "number": d["number"], "url": d["html_url"], "title": d["title"]}
        return {"error": "GitHub token nao configurado"}

    # ===== BRANCHES =====

    async def list_branches(self, repo=None):
        """Lista branches de um repositorio"""
        r = repo or self.repo
        if self.configured:
            resp = await self._request("GET", f"/repos/{r}/branches?per_page=50")
            if resp.status_code == 200:
                return [{"name": b["name"], "sha": b["commit"]["sha"][:7] if b.get("commit") else ""} for b in resp.json()]
        return {"error": "GitHub token nao configurado"}

    async def create_branch(self, branch_name, from_branch="main"):
        """Cria uma branch a partir de outra"""
        if self.configured:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.api}/repos/{self.repo}/git/refs/heads/{from_branch}",
                                        headers=self.headers)
                if resp.status_code != 200:
                    return {"error": f"Branch {from_branch} nao encontrada"}
                sha = resp.json()["object"]["sha"]
                resp = await client.post(f"{self.api}/repos/{self.repo}/git/refs",
                                         headers=self.headers,
                                         json={"ref": f"refs/heads/{branch_name}", "sha": sha})
                if resp.status_code == 201:
                    return {"status": "criada", "branch": branch_name, "from": from_branch, "sha": sha[:7]}
                return {"error": resp.json()}
        return {"error": "GitHub token nao configurado"}

    # ===== ARQUIVOS =====

    async def get_file(self, path, branch="main"):
        """Obtem conteudo de um arquivo do repositorio"""
        if self.configured:
            resp = await self._request("GET", f"/repos/{self.repo}/contents/{path}",
                                       params={"ref": branch})
            if resp.status_code == 200:
                d = resp.json()
                content = base64.b64decode(d["content"]).decode("utf-8") if d.get("content") else ""
                return {
                    "path": d["path"],
                    "name": d["name"],
                    "sha": d.get("sha", ""),
                    "size": d.get("size", 0),
                    "content": content,
                    "url": d["html_url"]
                }
        return {"error": "GitHub token nao configurado ou arquivo nao encontrado"}

    async def create_or_update_file(self, path, content, message, branch="main"):
        """Cria ou atualiza um arquivo no repositorio"""
        if self.configured:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.api}/repos/{self.repo}/contents/{path}",
                                        headers=self.headers, params={"ref": branch})
                sha = resp.json().get("sha") if resp.status_code == 200 else None
                encoded = base64.b64encode(content.encode()).decode()
                body = {"message": message, "content": encoded, "branch": branch}
                if sha:
                    body["sha"] = sha
                resp = await client.put(f"{self.api}/repos/{self.repo}/contents/{path}",
                                        headers=self.headers, json=body)
                if resp.status_code in (200, 201):
                    d = resp.json()
                    return {"status": "atualizado" if sha else "criado", "path": path, "url": d["content"]["html_url"] if d.get("content") else ""}
                return {"error": resp.json()}
        return {"error": "GitHub token nao configurado"}

    async def delete_file(self, path, message, branch="main"):
        """Deleta um arquivo do repositorio"""
        if self.configured:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.api}/repos/{self.repo}/contents/{path}",
                                        headers=self.headers, params={"ref": branch})
                if resp.status_code != 200:
                    return {"error": "Arquivo nao encontrado"}
                sha = resp.json()["sha"]
                resp = await client.delete(f"{self.api}/repos/{self.repo}/contents/{path}",
                                           headers=self.headers,
                                           json={"message": message, "sha": sha, "branch": branch})
                if resp.status_code in (200, 204):
                    return {"status": "deletado", "path": path}
                return {"error": resp.json()}
        return {"error": "GitHub token nao configurado"}

    # ===== RELEASES =====

    async def list_releases(self, repo=None, per_page=10):
        """Lista releases de um repositorio"""
        r = repo or self.repo
        if self.configured:
            resp = await self._request("GET", f"/repos/{r}/releases?per_page={per_page}")
            if resp.status_code == 200:
                return [{
                    "tag": rel["tag_name"],
                    "name": rel["name"],
                    "draft": rel.get("draft", False),
                    "prerelease": rel.get("prerelease", False),
                    "created_at": rel.get("created_at", ""),
                    "published_at": rel.get("published_at", ""),
                    "url": rel["html_url"],
                    "body": (rel.get("body", "") or "")[:300]
                } for rel in resp.json()]
        # Fallback gh CLI
        return self._gh_cli(["gh", "release", "list", "--repo", r, "--limit", str(per_page),
                             "--json", "tagName,name,isDraft,isPrerelease,createdAt,publishedAt,url"])

    async def create_release(self, tag, name, body, draft=False, prerelease=False):
        """Cria uma release"""
        if self.configured:
            resp = await self._request("POST", f"/repos/{self.repo}/releases",
                                       json={"tag_name": tag, "name": name, "body": body,
                                             "draft": draft, "prerelease": prerelease})
            if resp.status_code == 201:
                d = resp.json()
                return {"status": "criada", "tag": tag, "url": d["html_url"], "name": name}
            return {"error": resp.json()}
        return {"error": "GitHub token nao configurado"}

    # ===== WORKFLOWS / ACTIONS =====

    async def list_workflows(self, repo=None):
        """Lista workflows do GitHub Actions"""
        r = repo or self.repo
        if self.configured:
            resp = await self._request("GET", f"/repos/{r}/actions/workflows?per_page=50")
            if resp.status_code == 200:
                return [{
                    "name": w["name"],
                    "state": w.get("state", ""),
                    "path": w.get("path", ""),
                    "url": w["html_url"]
                } for w in resp.json().get("workflows", [])]
        return {"error": "GitHub token nao configurado"}

    async def dispatch_workflow(self, workflow_id, ref="main", inputs=None):
        """Dispara um workflow do GitHub Actions"""
        if self.configured:
            body = {"ref": ref}
            if inputs:
                body["inputs"] = inputs
            resp = await self._request("POST", f"/repos/{self.repo}/actions/workflows/{workflow_id}/dispatches",
                                       json=body)
            if resp.status_code == 204:
                return {"status": "disparado", "workflow": workflow_id, "ref": ref}
            return {"error": resp.json()}
        return {"error": "GitHub token nao configurado"}

    # ===== STATUS / SAUDE =====

    async def get_status(self):
        """Status completo da integracao GitHub"""
        if not self.configured:
            return {"configured": False, "token": False, "message": "GITHUB_TOKEN nao configurado"}

        # Testa a conexao
        try:
            resp = await self._request("GET", "/user")
            if resp.status_code == 200:
                user = resp.json()
                return {
                    "configured": True,
                    "token": True,
                    "user": user.get("login", ""),
                    "avatar": user.get("avatar_url", ""),
                    "plan": user.get("plan", {}).get("name", "free") if user.get("plan") else "free",
                    "repos_publicos": user.get("public_repos", 0),
                    "repos_privados": user.get("total_private_repos", 0),
                    "message": "Conectado"
                }
            return {"configured": True, "token": True, "error": f"HTTP {resp.status_code}", "message": "Falha na autenticacao"}
        except Exception as e:
            return {"configured": True, "token": True, "error": str(e), "message": "Erro de conexao"}

# Instancia global
github_integration = GitHubIntegration()
