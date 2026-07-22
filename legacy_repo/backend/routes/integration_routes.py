from fastapi import APIRouter, Depends
from pydantic import BaseModel
from modules.github_integration import github_integration
from modules.postiz_integration import postiz_integration
from modules.creative_tools import creative_tools
from middleware.auth_middleware import get_current_user

router = APIRouter()

class GitHubFileRequest(BaseModel):
    path: str
    content: str
    message: str
    branch: str = "main"

class GitHubReleaseRequest(BaseModel):
    tag: str
    name: str
    body: str

class GitHubIssueRequest(BaseModel):
    title: str
    body: str
    labels: list = []

class GitHubPRRequest(BaseModel):
    title: str
    head: str
    base: str = "main"
    body: str = ""

class PostizCreateRequest(BaseModel):
    content: str
    platforms: list = ["instagram"]
    media_urls: list = []
    scheduled_at: str = None
    title: str = None

class PostizCampaignRequest(BaseModel):
    posts: list

class CreativeRequest(BaseModel):
    prompt: str
    image_url: str = None
    style: str = None
    duration: int = None

class SpliceRequest(BaseModel):
    query: str
    genre: str = None
    bpm: int = None
    key: str = None

class BestContentRequest(BaseModel):
    content_type: str
    prompt: str
    platform: str = "instagram"

@router.get("/github/repo")
async def github_repo(user: dict = Depends(get_current_user)):
    return await github_integration.get_repo_info()

@router.get("/github/commits")
async def github_commits(user: dict = Depends(get_current_user)):
    return await github_integration.list_commits()

@router.post("/github/file")
async def github_save_file(req: GitHubFileRequest, user: dict = Depends(get_current_user)):
    return await github_integration.create_or_update_file(req.path, req.content, req.message, req.branch)

@router.post("/github/branch/{name}")
async def github_branch(name: str, user: dict = Depends(get_current_user)):
    return await github_integration.create_branch(name)

@router.post("/github/pr")
async def github_pr(req: GitHubPRRequest, user: dict = Depends(get_current_user)):
    return await github_integration.create_pull_request(req.title, req.head, req.base, req.body)

@router.post("/github/issue")
async def github_issue(req: GitHubIssueRequest, user: dict = Depends(get_current_user)):
    return await github_integration.create_issue(req.title, req.body, req.labels)

@router.post("/github/release")
async def github_release(req: GitHubReleaseRequest, user: dict = Depends(get_current_user)):
    return await github_integration.create_release(req.tag, req.name, req.body)

@router.get("/github/releases")
async def github_releases(user: dict = Depends(get_current_user)):
    return await github_integration.list_releases()

@router.get("/postiz/accounts")
async def postiz_accounts(user: dict = Depends(get_current_user)):
    return await postiz_integration.list_accounts()

@router.post("/postiz/post")
async def postiz_create(req: PostizCreateRequest, user: dict = Depends(get_current_user)):
    return await postiz_integration.create_post(req.content, req.platforms, req.media_urls, req.scheduled_at, req.title)

@router.post("/postiz/campaign")
async def postiz_campaign(req: PostizCampaignRequest, user: dict = Depends(get_current_user)):
    return await postiz_integration.schedule_campaign(req.posts)

@router.get("/postiz/scheduled")
async def postiz_scheduled(user: dict = Depends(get_current_user)):
    return await postiz_integration.list_scheduled_posts()

@router.delete("/postiz/{post_id}")
async def postiz_delete(post_id: str, user: dict = Depends(get_current_user)):
    return await postiz_integration.delete_post(post_id)

@router.get("/postiz/analytics")
async def postiz_analytics(post_id: str = None, user: dict = Depends(get_current_user)):
    return await postiz_integration.get_analytics(post_id)

@router.get("/tools/list")
async def list_tools(user: dict = Depends(get_current_user)):
    return creative_tools.list_tools()

@router.get("/tools/status")
async def tools_status(user: dict = Depends(get_current_user)):
    return await creative_tools.get_tool_status()

@router.post("/tools/leonardo")
async def tool_leonardo(req: CreativeRequest, user: dict = Depends(get_current_user)):
    return await creative_tools.leonardo_generate(req.prompt)

@router.post("/tools/suno")
async def tool_suno(req: CreativeRequest, user: dict = Depends(get_current_user)):
    return await creative_tools.suno_generate(req.prompt, req.style or "electronic", req.duration or 30)

@router.post("/tools/kling")
async def tool_kling(req: CreativeRequest, user: dict = Depends(get_current_user)):
    return await creative_tools.kling_generate_video(req.prompt, req.image_url, req.duration or 5)

@router.post("/tools/luma")
async def tool_luma(req: CreativeRequest, user: dict = Depends(get_current_user)):
    return await creative_tools.luma_generate_video(req.prompt, req.image_url)

@router.post("/tools/pika")
async def tool_pika(req: CreativeRequest, user: dict = Depends(get_current_user)):
    return await creative_tools.pika_generate_video(req.prompt, req.image_url)

@router.post("/tools/meshy")
async def tool_meshy(req: CreativeRequest, user: dict = Depends(get_current_user)):
    return await creative_tools.meshy_generate_3d(req.prompt)

@router.post("/tools/moises")
async def tool_moises(req: CreativeRequest, user: dict = Depends(get_current_user)):
    return await creative_tools.moises_separate_stems(req.image_url or req.prompt)

@router.post("/tools/splice")
async def tool_splice(req: SpliceRequest, user: dict = Depends(get_current_user)):
    return await creative_tools.splice_search_samples(req.query, req.genre, req.bpm, req.key)

@router.post("/tools/bestcontent")
async def tool_bestcontent(req: BestContentRequest, user: dict = Depends(get_current_user)):
    return await creative_tools.bestcontent_generate(req.content_type, req.prompt, req.platform)

@router.post("/tools/hedra")
async def tool_hedra(req: CreativeRequest, user: dict = Depends(get_current_user)):
    return await creative_tools.hedra_generate(req.prompt, req.image_url)

@router.post("/tools/vizard")
async def tool_vizard(req: CreativeRequest, user: dict = Depends(get_current_user)):
    return await creative_tools.vizard_create_clip(req.image_url or req.prompt)

@router.post("/tools/cobalt")
async def tool_cobalt(req: CreativeRequest, user: dict = Depends(get_current_user)):
    return await creative_tools.cobalt_download(req.prompt)
