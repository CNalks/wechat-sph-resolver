"""Runtime settings."""
from functools import lru_cache
import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    yuanbao_cookie: str = os.getenv("YUANBAO_COOKIE", "")
    request_timeout_seconds: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
    allowed_hosts: set[str] = {
        host.strip().lower()
        for host in os.getenv(
            "ALLOWED_HOSTS",
            "weixin.qq.com,channels.weixin.qq.com",
        ).split(",")
        if host.strip()
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
