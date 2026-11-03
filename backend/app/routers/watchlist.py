import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..market.service import get_provider
from ..market.universe import BY_SYMBOL
from ..models import WatchlistItem
from ..schemas import WatchlistAdd
from .market import meta

log = logging.getLogger("watchlist")
router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


@router.get("")
def get_watchlist(db: Session = Depends(get_db)):
    items = db.scalars(select(WatchlistItem).order_by(WatchlistItem.created_at)).all()
    quotes = get_provider().get_quotes([i.symbol for i in items]) if items else {}
    rows = []
    for i in items:
        q = quotes.get(i.symbol)
        rows.append({"symbol": i.symbol, "name": BY_SYMBOL.get(i.symbol, {}).get("name", i.symbol),
                     "added_at": i.created_at, "quote": q.dict() if q else None})
    return {**meta(), "items": rows}


@router.post("", status_code=201)
def add_to_watchlist(body: WatchlistAdd, db: Session = Depends(get_db)):
    if body.symbol not in BY_SYMBOL:
        raise HTTPException(404, f"Unknown NSE symbol '{body.symbol}'")
    if db.scalar(select(WatchlistItem).where(WatchlistItem.symbol == body.symbol)):
        raise HTTPException(409, f"{body.symbol} is already in your watchlist")
    db.add(WatchlistItem(symbol=body.symbol))
    db.commit()
    log.info("Watchlist add %s", body.symbol)
    return {"symbol": body.symbol}


@router.delete("/{symbol}", status_code=204)
def remove_from_watchlist(symbol: str, db: Session = Depends(get_db)):
    item = db.scalar(select(WatchlistItem).where(WatchlistItem.symbol == symbol.upper()))
    if not item:
        raise HTTPException(404, f"{symbol.upper()} is not in your watchlist")
    db.delete(item)
    db.commit()
    log.info("Watchlist remove %s", symbol.upper())
