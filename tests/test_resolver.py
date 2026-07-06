import httpx
import pytest

from app.resolver import ResolveError, extract_feed_params, resolve_share_url, validate_share_url


def test_validate_share_url_accepts_sph():
    assert validate_share_url("https://weixin.qq.com/sph/AxPprQgcwh", {"weixin.qq.com"})


def test_validate_share_url_rejects_other_weixin_path():
    with pytest.raises(ResolveError):
        validate_share_url("https://weixin.qq.com/not-sph/AxPprQgcwh", {"weixin.qq.com"})


def test_extract_feed_params():
    token, eid = extract_feed_params("https://channels.weixin.qq.com/x?token=tok&eid=eid123")
    assert token == "tok"
    assert eid == "eid123"


@pytest.mark.anyio
async def test_resolve_share_url_flow(monkeypatch):
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        if "yuanbao.tencent.com" in str(request.url):
            return httpx.Response(200, json={
                "data": {
                    "wx_export_id": "export/abc",
                    "playable_url": "https://channels.weixin.qq.com/finder-preview/pages/feed?token=tok&eid=export%2Fabc",
                }
            })
        return httpx.Response(200, json={
            "errCode": 0,
            "errMsg": "",
            "data": {
                "authorInfo": {"nickname": "tester"},
                "feedInfo": {"description": "hello", "videoUrl": "https://finder.video.qq.com/video.mp4"},
            },
        })

    transport = httpx.MockTransport(handler)

    class FakeClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            super().__init__(transport=transport)

    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
    result = await resolve_share_url(
        "https://weixin.qq.com/sph/AxPprQgcwh",
        "cookie=yes",
        1,
        {"weixin.qq.com"},
    )
    assert result["data"]["feedInfo"]["videoUrl"].endswith("video.mp4")
    assert len(calls) == 2
