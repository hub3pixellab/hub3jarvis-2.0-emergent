import httpx
import os

class CreativeToolsManager:
    def __init__(self):
        self.tools = {
            "leonardo": {"key": os.getenv("LEONARDO_API_KEY"), "url": "https://cloud.leonardo.ai/api/rest/v1"},
            "suno": {"key": os.getenv("SUNO_API_KEY"), "url": "https://api.suno.ai/v1"},
            "kling": {"key": os.getenv("KLING_API_KEY"), "url": "https://api.kuaishou.com/kling/v1"},
            "luma": {"key": os.getenv("LUMA_API_KEY"), "url": "https://api.lumalabs.ai/dream-machine/v1"},
            "pika": {"key": os.getenv("PIKA_API_KEY"), "url": "https://api.pika.art/v1"},
            "meshy": {"key": os.getenv("MESHY_API_KEY"), "url": "https://api.meshy.ai/v1"},
            "moises": {"key": os.getenv("MOISES_API_KEY"), "url": "https://api.moises.ai/v1"},
            "splice": {"key": os.getenv("SPLICE_API_KEY"), "url": "https://api.splice.com/v2"},
            "bestcontent": {"key": os.getenv("BESTCONTENT_API_KEY"), "url": "https://api.bestcontent.ai/v1"},
            "hedra": {"key": os.getenv("HEDRA_API_KEY"), "url": "https://api.hedra.com/v1"},
            "vizard": {"key": os.getenv("VIZARD_API_KEY"), "url": "https://api.vizard.ai/v1"},
            "cobalt": {"key": os.getenv("COBALT_API_KEY"), "url": "https://api.cobalt.tools/v1"},
        }

    def list_tools(self):
        return {name: {"url": t["url"], "configured": bool(t["key"])} for name, t in self.tools.items()}

    async def get_tool_status(self):
        return {name: {"url": t["url"], "configured": bool(t["key"])} for name, t in self.tools.items()}

    async def leonardo_generate(self, prompt, model="leonardo-diffusion-xl", width=1024, height=1024):
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(f"{self.tools['leonardo']['url']}/generations", headers={"Authorization": f"Bearer {self.tools['leonardo']['key']}"}, json={"prompt": prompt, "modelId": model, "width": width, "height": height, "num_images": 1})
            return resp.json()

    async def suno_generate(self, prompt, style="electronic", duration=30):
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{self.tools['suno']['url']}/generate", headers={"Authorization": f"Bearer {self.tools['suno']['key']}"}, json={"prompt": prompt, "style": style, "duration": duration})
            return resp.json()

    async def kling_generate_video(self, prompt, image_url=None, duration=5):
        async with httpx.AsyncClient(timeout=180) as client:
            body = {"prompt": prompt, "duration": duration}
            if image_url: body["image_url"] = image_url
            resp = await client.post(f"{self.tools['kling']['url']}/video/generate", headers={"Authorization": f"Bearer {self.tools['kling']['key']}"}, json=body)
            return resp.json()

    async def luma_generate_video(self, prompt, image_url=None):
        async with httpx.AsyncClient(timeout=180) as client:
            body = {"prompt": prompt}
            if image_url: body["keyframes"] = {"frame0": {"type": "image", "url": image_url}}
            resp = await client.post(f"{self.tools['luma']['url']}/generations", headers={"Authorization": f"Bearer {self.tools['luma']['key']}"}, json=body)
            return resp.json()

    async def pika_generate_video(self, prompt, image_url=None):
        async with httpx.AsyncClient(timeout=180) as client:
            body = {"promptText": prompt}
            if image_url: body["imageUrl"] = image_url
            resp = await client.post(f"{self.tools['pika']['url']}/generate", headers={"Authorization": f"Bearer {self.tools['pika']['key']}"}, json=body)
            return resp.json()

    async def meshy_generate_3d(self, prompt, mode="text-to-3d"):
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{self.tools['meshy']['url']}/v2/text-to-3d", headers={"Authorization": f"Bearer {self.tools['meshy']['key']}"}, json={"mode": mode, "prompt": prompt})
            return resp.json()

    async def moises_separate_stems(self, audio_url):
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{self.tools['moises']['url']}/separate", headers={"Authorization": f"Bearer {self.tools['moises']['key']}"}, json={"audio_url": audio_url})
            return resp.json()

    async def splice_search_samples(self, query, genre=None, bpm=None, key=None):
        params = {"q": query}
        if genre: params["genre"] = genre
        if bpm: params["bpm"] = bpm
        if key: params["key"] = key
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{self.tools['splice']['url']}/sounds", headers={"Authorization": f"Bearer {self.tools['splice']['key']}"}, params=params)
            return resp.json()

    async def bestcontent_generate(self, content_type, prompt, platform="instagram"):
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(f"{self.tools['bestcontent']['url']}/generate", headers={"Authorization": f"Bearer {self.tools['bestcontent']['key']}"}, json={"type": content_type, "prompt": prompt, "platform": platform})
            return resp.json()

    async def hedra_generate(self, audio_url, image_url, expression="neutral"):
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{self.tools['hedra']['url']}/generate", headers={"Authorization": f"Bearer {self.tools['hedra']['key']}"}, json={"audio_url": audio_url, "image_url": image_url, "expression": expression})
            return resp.json()

    async def vizard_create_clip(self, video_url, clip_count=5):
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(f"{self.tools['vizard']['url']}/clips", headers={"Authorization": f"Bearer {self.tools['vizard']['key']}"}, json={"video_url": video_url, "clip_count": clip_count})
            return resp.json()

    async def cobalt_download(self, url):
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(f"{self.tools['cobalt']['url']}/json", json={"url": url})
            return resp.json()

creative_tools = CreativeToolsManager()
