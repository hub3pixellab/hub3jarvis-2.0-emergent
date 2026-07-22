import httpx
import os

class PostizIntegration:
    def __init__(self):
        self.api_key = os.getenv("POSTIZ_API_KEY")
        self.base_url = os.getenv("POSTIZ_API_URL", "https://api.postiz.com/api/v1")
        self.headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    async def list_accounts(self):
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/accounts", headers=self.headers)
            return resp.json()

    async def create_post(self, content, platforms, media_urls=None, scheduled_at=None, title=None):
        body = {"content": content, "platforms": platforms, "media": media_urls or [], "scheduledAt": scheduled_at, "title": title}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{self.base_url}/posts", headers=self.headers, json=body)
            return resp.json()

    async def schedule_campaign(self, posts):
        results = []
        for post in posts:
            r = await self.create_post(post.get("content", ""), post.get("platforms", ["instagram"]), post.get("media_urls", []), post.get("scheduled_at"), post.get("title"))
            results.append(r)
        return {"campaign": "scheduled", "posts": results, "total": len(results)}

    async def list_scheduled_posts(self):
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/posts/scheduled", headers=self.headers)
            return resp.json()

    async def delete_post(self, post_id):
        async with httpx.AsyncClient() as client:
            resp = await client.delete(f"{self.base_url}/posts/{post_id}", headers=self.headers)
            return resp.json()

    async def get_analytics(self, post_id=None):
        url = f"{self.base_url}/analytics"
        if post_id: url += f"/{post_id}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self.headers)
            return resp.json()

postiz_integration = PostizIntegration()
