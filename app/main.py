"""FastAPI entrypoint."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.config import get_settings
from app.resolver import ResolveError, resolve_share_url

app = FastAPI(title="WeChat SPH Resolver", version="0.1.0")


class ResolveRequest(BaseModel):
    url: str


@app.get("/healthz")
async def healthz():
    return {"ok": True}


@app.post("/api/fetch_video_profile")
async def fetch_video_profile(request: ResolveRequest):
    settings = get_settings()
    try:
        return await resolve_share_url(
            request.url,
            settings.yuanbao_cookie,
            settings.request_timeout_seconds,
            settings.allowed_hosts,
        )
    except ResolveError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
