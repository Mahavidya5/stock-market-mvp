import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..market.base import ProviderError
from ..market.service import get_provider
from ..market.universe import BY_SYMBOL
from ..models import Alert
from ..schemas import AlertCreate, AlertOut, AlertUpdate

log = logging.getLogger("alerts")
router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def _out(alert: Alert, prices: dict[str, float]) -> AlertOut:
    o = AlertOut.model_validate(alert)
    o.name = BY_SYMBOL.get(alert.symbol, {}).get("name")
    o.current_price = prices.get(alert.symbol)
    return o


def _prices(symbols: list[str]) -> dict[str, float]:
    if not symbols:
        return {}
    try:
        return {s: q.price for s, q in get_provider().get_quotes(symbols).items()}
    except ProviderError:
        return {}  # alert management must keep working if the provider is down


def _get(db: Session, alert_id: int) -> Alert:
    a = db.get(Alert, alert_id)
    if not a:
        raise HTTPException(404, "Alert not found")
    return a


@router.get("", response_model=list[AlertOut])
def list_alerts(db: Session = Depends(get_db)):
    alerts = db.scalars(select(Alert).order_by(Alert.created_at.desc())).all()
    prices = _prices(sorted({a.symbol for a in alerts}))
    return [_out(a, prices) for a in alerts]


@router.post("", response_model=AlertOut, status_code=201)
def create_alert(body: AlertCreate, db: Session = Depends(get_db)):
    if body.symbol not in BY_SYMBOL:
        raise HTTPException(404, f"Unknown NSE symbol '{body.symbol}'")
    a = Alert(symbol=body.symbol, condition=body.condition, target_price=body.target_price)
    db.add(a)
    db.commit()
    log.info("Alert created #%s %s %s %s", a.id, a.symbol, a.condition, a.target_price)
    return _out(a, _prices([a.symbol]))


@router.put("/{alert_id}", response_model=AlertOut)
def update_alert(alert_id: int, body: AlertUpdate, db: Session = Depends(get_db)):
    a = _get(db, alert_id)
    was_triggered = a.triggered_at is not None
    changed_rule = False
    if body.condition is not None and body.condition != a.condition:
        a.condition, changed_rule = body.condition, True
    if body.target_price is not None and body.target_price != a.target_price:
        a.target_price, changed_rule = body.target_price, True
    if body.enabled is not None:
        a.enabled = body.enabled
    # Editing the rule or re-enabling re-arms a previously triggered alert.
    if changed_rule or body.enabled is True:
        a.triggered_at = a.triggered_price = None
        if changed_rule and body.enabled is None and was_triggered:
            a.enabled = True
    db.commit()
    log.info("Alert updated #%s", a.id)
    return _out(a, _prices([a.symbol]))


@router.delete("/{alert_id}", status_code=204)
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    db.delete(_get(db, alert_id))
    db.commit()
    log.info("Alert deleted #%s", alert_id)
