# WeChat SPH Resolver

Small FastAPI service for resolving WeChat Channels share links such as
`https://weixin.qq.com/sph/...` into `feedInfo.videoUrl` metadata.

The service is designed as a private sidecar for `wechat-kb-inbox`.

## API

```http
POST /api/fetch_video_profile
Content-Type: application/json

{"url":"https://weixin.qq.com/sph/AxPprQgcwh"}
```

Successful responses mirror the shape used by `wx_channels_download`'s
Cloudflare Worker:

```json
{
  "data": {
    "authorInfo": {},
    "feedInfo": {
      "videoUrl": "https://finder.video.qq.com/..."
    }
  },
  "errCode": 0,
  "errMsg": ""
}
```

## Configuration

`YUANBAO_COOKIE` is required. It must be a valid logged-in Tencent Yuanbao web
cookie.

Optional:

- `REQUEST_TIMEOUT_SECONDS`, default `30`
- `ALLOWED_HOSTS`, comma-separated URL host allowlist, default allows WeChat SPH
  share hosts

## Run

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
YUANBAO_COOKIE='...' uvicorn app.main:app --host 127.0.0.1 --port 8020
```

Then configure the inbox service:

```bash
SPH_RESOLVER_URL=http://127.0.0.1:8020/api/fetch_video_profile
```

## Notes

This implementation follows the public SPH resolution flow documented by
`ltaoo/wx_channels_download`: parse the share URL through Tencent Yuanbao, then
use the returned token/eid to call WeChat Channels `get_feed_info`.

Use only for content you have the right to archive.
