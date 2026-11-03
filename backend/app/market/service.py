import logging
from datetime import datetime, time, timedelta, timezone

from ..config import settings
from .base import MarketDataProvider
from .demo import DemoProvider
from .indianapi import IndianApiProvider

log = logging.getLogger("market")
IST = timezone(timedelta(hours=5, minutes=30))
_provider: MarketDataProvider | None = None


def build_provider() -> MarketDataProvider:
    choice = settings.provider
    has_key = bool(settings.indian_api_key)
    if choice == "indianapi" and not has_key:
        log.warning("MARKET_DATA_PROVIDER=indianapi but INDIAN_API_KEY is empty; using DEMO data")
    if choice in ("indianapi", "auto") and has_key:
        p = IndianApiProvider(settings.indian_api_key)
        log.info("Market data provider: %s (%s)", p.name, p.data_mode)
        return p
    log.info("Market data provider: DEMO (simulated)")
    return DemoProvider()


def get_provider() -> MarketDataProvider:
    global _provider
    if _provider is None:
        _provider = build_provider()
    return _provider


def set_provider(p: MarketDataProvider | None) -> None:  # used by tests
    global _provider
    _provider = p


def market_status(now: datetime | None = None) -> dict:
    """NSE regular session: Mon-Fri 09:15-15:30 IST. Exchange holidays are NOT modelled."""
    now = (now or datetime.now(IST)).astimezone(IST)
    t = now.time()
    weekday = now.weekday() < 5
    if weekday and time(9, 15) <= t < time(15, 30):
        state, label = "open", "Market Open"
    elif weekday and time(9, 0) <= t < time(9, 15):
        state, label = "pre_open", "Pre-open Session"
    else:
        state, label = "closed", "Market Closed"
    return {"state": state, "is_open": state == "open", "label": label,
            "time_ist": now.strftime("%Y-%m-%d %H:%M:%S"), "note": "Exchange holidays are not modelled."}
