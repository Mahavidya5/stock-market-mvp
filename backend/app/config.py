import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
load_dotenv()  # also allow a .env in the working directory / project root


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./stocks.db")
    # auto | demo | indianapi
    provider: str = os.getenv("MARKET_DATA_PROVIDER", "auto").lower()
    indian_api_key: str = os.getenv("INDIAN_API_KEY", "").strip()
    indian_api_base_url: str = os.getenv("INDIAN_API_BASE_URL", "https://stock.indianapi.in").rstrip("/")
    # "delayed" (typical for NSE on most plans) or "realtime" if your plan entitles you
    data_latency: str = os.getenv("MARKET_DATA_LATENCY", "delayed").lower()
    # Name IndianAPI should look up for the index (IndianAPI documents no index endpoint - verify with your key)
    index_name: str = os.getenv("NIFTY_INDEX_NAME", "NIFTY 50")
    quote_cache_seconds: int = _int("QUOTE_CACHE_SECONDS", 60)
    refresh_seconds: int = max(5, _int("MARKET_REFRESH_SECONDS", 60))  # UI auto-refresh interval
    alert_interval_seconds: int = _int("ALERT_CHECK_INTERVAL_SECONDS", 30)
    cors_origins: list[str] = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
        if o.strip()
    ]


settings = Settings()
