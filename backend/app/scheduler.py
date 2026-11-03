"""Background price-alert monitor (asyncio task started with the app)."""
import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from .config import settings
from .database import SessionLocal
from .market.base import ProviderError
from .market.service import get_provider, market_status
from .market.universe import BY_SYMBOL
from .models import Alert, Notification

log = logging.getLogger("scheduler")


def check_alerts() -> int:
    """Evaluate enabled, untriggered alerts. Returns number triggered.

    Duplicate prevention: a firing sets triggered_at and disables the alert in the same
    transaction as the notification insert, so it can never fire twice until re-armed.
    """
    provider = get_provider()
    if provider.data_mode != "demo" and not market_status()["is_open"]:
        return 0  # real quotes don't move while the market is closed; save API credits
    with SessionLocal() as db:
        alerts = db.scalars(select(Alert).where(Alert.enabled.is_(True), Alert.triggered_at.is_(None))).all()
        if not alerts:
            return 0
        try:
            quotes = provider.get_quotes(sorted({a.symbol for a in alerts}))
        except ProviderError as e:
            log.warning("Alert check skipped: %s", e)
            return 0
        fired = 0
        for a in alerts:
            q = quotes.get(a.symbol)
            if not q:
                continue
            hit = q.price >= a.target_price if a.condition == "ABOVE" else q.price <= a.target_price
            if not hit:
                continue
            word = "risen above" if a.condition == "ABOVE" else "fallen below"
            name = BY_SYMBOL.get(a.symbol, {}).get("name", a.symbol)
            a.enabled = False
            a.triggered_at = datetime.now(timezone.utc)
            a.triggered_price = q.price
            db.add(Notification(
                alert_id=a.id, symbol=a.symbol, price=q.price, data_mode=provider.data_mode,
                message=f"{name} ({a.symbol}) has {word} ₹{a.target_price:,.2f} - now ₹{q.price:,.2f}"
                        + (" [DEMO data]" if provider.data_mode == "demo" else ""),
            ))
            fired += 1
            log.info("Alert #%s triggered: %s %s %s (price %s)", a.id, a.symbol, a.condition, a.target_price, q.price)
        db.commit()
        return fired


async def run_forever() -> None:
    log.info("Alert monitor started (every %ss)", settings.alert_interval_seconds)
    while True:
        try:
            await asyncio.to_thread(check_alerts)
        except Exception:  # keep the monitor alive no matter what
            log.exception("Alert monitor iteration failed")
        await asyncio.sleep(settings.alert_interval_seconds)
