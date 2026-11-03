from fastapi import APIRouter, HTTPException, Query

from ..market.base import RANGES
from ..market.service import get_provider
from ..market.universe import BY_SYMBOL, search
from .market import meta

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


def _require(symbol: str) -> str:
    symbol = symbol.strip().upper()
    if symbol not in BY_SYMBOL:
        raise HTTPException(404, f"Unknown NSE symbol '{symbol}'")
    return symbol


@router.get("/search")
def search_stocks(q: str = Query(min_length=1, max_length=50)):
    results = search(q)
    quotes = get_provider().get_quotes([r["symbol"] for r in results]) if results else {}
    for r in results:
        qt = quotes.get(r["symbol"])
        r["price"], r["change_pct"] = (qt.price, qt.change_pct) if qt else (None, None)
    return {**meta(), "results": results}


@router.get("/{symbol}")
def stock_detail(symbol: str):
    symbol = _require(symbol)
    p = get_provider()
    quote = p.get_quotes([symbol]).get(symbol)
    if not quote:
        raise HTTPException(502, "No quote available from market data provider")
    profile = p.get_profile(symbol) or {"name": BY_SYMBOL[symbol]["name"], "sector": BY_SYMBOL[symbol]["sector"],
                                        "exchange": "NSE", "description": None}
    return {**meta(), "quote": quote.dict(), "profile": profile}


@router.get("/{symbol}/history")
def stock_history(symbol: str, range: str = "1M"):
    symbol = _require(symbol)
    if range not in RANGES:
        raise HTTPException(422, f"range must be one of {list(RANGES)}")
    return {**meta(), "symbol": symbol, "range": range, "points": get_provider().get_history(symbol, range)}


@router.get("/{symbol}/fundamentals")
def stock_fundamentals(symbol: str):
    symbol = _require(symbol)
    f = get_provider().get_fundamentals(symbol)
    if f is None:
        return {**meta(), "symbol": symbol, "available": False,
                "message": "Fundamentals are not available from the current data provider/plan."}
    return {**meta(), "symbol": symbol, "available": True, **f}
