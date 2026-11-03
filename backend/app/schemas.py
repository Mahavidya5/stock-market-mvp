from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Condition = Literal["ABOVE", "BELOW"]


class WatchlistAdd(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)

    @field_validator("symbol")
    @classmethod
    def up(cls, v: str) -> str:
        return v.strip().upper()


class AlertCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    condition: Condition
    target_price: float = Field(gt=0, lt=10_000_000)

    @field_validator("symbol")
    @classmethod
    def up(cls, v: str) -> str:
        return v.strip().upper()


class AlertUpdate(BaseModel):
    condition: Condition | None = None
    target_price: float | None = Field(default=None, gt=0, lt=10_000_000)
    enabled: bool | None = None


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    symbol: str
    name: str | None = None
    condition: Condition
    target_price: float
    enabled: bool
    triggered_at: datetime | None
    triggered_price: float | None
    current_price: float | None = None
    created_at: datetime


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    alert_id: int | None
    symbol: str
    message: str
    price: float
    data_mode: str
    is_read: bool
    created_at: datetime
