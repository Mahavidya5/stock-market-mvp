from dataclasses import dataclass, asdict
from typing import Protocol

RANGES = {"1W": 5, "1M": 21, "3M": 63, "6M": 126, "1Y": 250}


class ProviderError(Exception):
    """Raised when the market data provider cannot return usable data.

    Subclasses carry a distinct HTTP status and machine-readable `code` so the API and UI
    can tell "bad key" from "rate limited" from "symbol not found" - never one generic error.
    """
    status_code = 502
    code = "provider_error"
    retry_after: int | None = None

    def __init__(self, message: str = "Market data provider error", *, retry_after: int | None = None):
        super().__init__(message)
        if retry_after is not None:
            self.retry_after = retry_after


class InvalidApiKey(ProviderError):
    status_code, code = 502, "invalid_api_key"


class PermissionDenied(ProviderError):
    """API key is valid but the subscription does not include this endpoint/data."""
    status_code, code = 502, "subscription_required"


class RateLimited(ProviderError):
    status_code, code = 429, "rate_limited"


class ProviderUnavailable(ProviderError):
    status_code, code = 503, "provider_unavailable"


class SymbolNotFound(ProviderError):
    status_code, code = 404, "symbol_not_found"


class DataUnavailable(ProviderError):
    """Provider answered, but has no (usable) data for this request, e.g. no history."""
    status_code, code = 404, "data_unavailable"


@dataclass
class Quote:
    symbol: str
    name: str
    price: float
    prev_close: float
    change: float
    change_pct: float
    open: float | None = None
    high: float | None = None
    low: float | None = None
    volume: int | None = None
    as_of: str | None = None

    def dict(self) -> dict:
        return asdict(self)


class MarketDataProvider(Protocol):
    name: str
    data_mode: str  # "demo" | "delayed" | "live"

    def get_quotes(self, symbols: list[str]) -> dict[str, Quote]: ...
    def get_index(self) -> Quote: ...
    def get_history(self, symbol: str, range_: str) -> list[dict]: ...
    def get_index_history(self, range_: str) -> list[dict]: ...
    def get_profile(self, symbol: str) -> dict | None: ...
    def get_fundamentals(self, symbol: str) -> dict | None: ...
