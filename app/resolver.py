"""Resolve WeChat Channels SPH share links through Tencent Yuanbao."""
from __future__ import annotations

import random
import time
from urllib.parse import parse_qs, urlparse

import httpx


PARSE_URL = "https://yuanbao.tencent.com/api/weixin/get_parse_result"
FEED_INFO_URL = "https://channels.weixin.qq.com/finder-preview/api/feed/get_feed_info"


class ResolveError(RuntimeError):
    pass


PARSE_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
    "content-type": "application/json",
    "origin": "https://yuanbao.tencent.com",
    "referer": "https://yuanbao.tencent.com/chat/naQivTmsDa/cf4d0079-ed1b-4c55-a3f3-2ca1379727d1",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "x-agentid": "naQivTmsDa/cf4d0079-ed1b-4c55-a3f3-2ca1379727d1",
    "x-language": "zh-CN",
    "x-platform": "mac",
    "x-requested-with": "XMLHttpRequest",
    "x-source": "web",
    "x-web-third-source": "main",
}

FEED_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
    "content-type": "application/json",
    "origin": "https://channels.weixin.qq.com",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}


def validate_share_url(url: str, allowed_hosts: set[str]) -> str:
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower()
    if parsed.scheme not in {"http", "https"}:
        raise ResolveError("invalid url scheme")
    if host not in allowed_hosts:
        raise ResolveError(f"host not allowed: {host}")
    if host == "weixin.qq.com" and not parsed.path.startswith("/sph/"):
        raise ResolveError("not a weixin sph url")
    return url.strip()


def generate_rid() -> str:
    return f"{int(time.time()):x}-" + "".join(random.choice("0123456789abcdef") for _ in range(8))


async def parse_share_url(client: httpx.AsyncClient, share_url: str, cookie: str) -> dict:
    response = await client.post(
        PARSE_URL,
        json={"type": "video_channel_url", "url": share_url, "scene": 1},
        headers={**PARSE_HEADERS, "cookie": cookie},
    )
    if response.status_code == 401:
        raise ResolveError("yuanbao cookie unauthorized")
    if response.status_code >= 400:
        raise ResolveError(f"yuanbao parse http {response.status_code}: {response.text[:200]}")
    payload = response.json()
    data = payload.get("data") or {}
    if not data.get("wx_export_id") or not data.get("playable_url"):
        raise ResolveError(f"yuanbao parse missing export/playable url: {payload}")
    return data


async def get_feed_info(client: httpx.AsyncClient, export_id: str, general_token: str) -> dict:
    rid = generate_rid()
    referer = (
        "https://channels.weixin.qq.com/finder-preview/pages/feed"
        "?entry_card_type=48&comment_scene=39&appid=0"
        f"&token={general_token}&entry_scene=0&eid={export_id}"
    )
    response = await client.post(
        f"{FEED_INFO_URL}?_rid={rid}&_pageUrl=https:%2F%2Fchannels.weixin.qq.com%2Ffinder-preview%2Fpages%2Ffeed",
        json={"baseReq": {"generalToken": general_token}, "exportId": export_id},
        headers={**FEED_HEADERS, "referer": referer},
    )
    if response.status_code >= 400:
        raise ResolveError(f"feed info http {response.status_code}: {response.text[:200]}")
    payload = response.json()
    if "data" not in payload:
        raise ResolveError(f"feed info missing data: {payload}")
    return payload


def extract_feed_params(playable_url: str) -> tuple[str, str]:
    parsed = urlparse(playable_url)
    query = parse_qs(parsed.query)
    token = (query.get("token") or [""])[0]
    export_id = (query.get("eid") or [""])[0]
    if not token or not export_id:
        raise ResolveError("playable_url missing token/eid")
    return token, export_id


async def resolve_share_url(share_url: str, cookie: str, timeout: float, allowed_hosts: set[str]) -> dict:
    if not cookie:
        raise ResolveError("YUANBAO_COOKIE is not configured")
    clean_url = validate_share_url(share_url, allowed_hosts)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        parse_data = await parse_share_url(client, clean_url, cookie)
        token, export_id = extract_feed_params(parse_data["playable_url"])
        return await get_feed_info(client, export_id, token)
