from fastapi import APIRouter, HTTPException

from ..config import settings
from ..market.base import RANGES, DataUnavailable, ProviderError
from ..market.service import get_provider, market_status
from ..market.universe import UNIVERSE

router = APIRouter(prefix="/api/market", tags=["market"])


def meta() -> dict:
    p = get_provider()
    return {"data_mode": p.data_mode, "provider": p.name, "refresh_seconds": settings.refresh_seconds}


@router.get("/overview")
def overview():
    p = get_provider()
    quotes = p.get_quotes([s["symbol"] for s in UNIVERSE])
    ranked = sorted(quotes.values(), key=lambda q: q.change_pct, reverse=True)
    sectors: dict[str, list[float]] = {}
    sector_of = {s["symbol"]: s["sector"] for s in UNIVERSE}
    for q in ranked:
        sectors.setdefault(sector_of.get(q.symbol, "Other"), []).append(q.change_pct)
    index, index_error = None, None
    try:
        index = p.get_index().dict()
    except (DataUnavailable, ProviderError) as e:
        if e.code not in ("data_unavailable", "symbol_not_found"):
            raise  # key / plan / rate-limit / outage problems must surface, not be hidden
        index_error = f"{settings.index_name} is not available from the data provider"
    return {
        **meta(),
        "status": market_status(),
        "index": index,
        "index_error": index_error,
        "gainers": [q.dict() for q in ranked[:5]],
        "losers": [q.dict() for q in reversed(ranked[-5:])],
        "advancers": sum(1 for q in ranked if q.change_pct > 0),
        "decliners": sum(1 for q in ranked if q.change_pct < 0),
        "sectors": sorted(
            ({"sector": k, "change_pct": round(sum(v) / len(v), 2)} for k, v in sectors.items()),
            key=lambda x: x["change_pct"], reverse=True),
    }


@router.get("/index/history")
def index_history(range: str = "1M"):
    if range not in RANGES:
        raise HTTPException(422, f"range must be one of {list(RANGES)}")
    return {**meta(), "range": range, "points": get_provider().get_index_history(range)}
