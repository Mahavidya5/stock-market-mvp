"""IndianAPI provider (https://indianapi.in, base URL https://stock.indianapi.in).

Auth: the `x-api-key` request header (key from INDIAN_API_KEY; never logged, never sent to the browser).

Endpoints used (paths/params taken from the public IndianAPI documentation):
  GET /stock?name=<company name>                       price (currentPrice.NSE), percentChange, profile
  GET /historical_data?stock_name=&period=&filter=price  daily price series
  GET /historical_stats?stock_name=&stats=yoy_results|quarter_results   revenue / net profit

Behaviour:
  * TTL cache + single-flight: concurrent identical requests share one upstream call.
  * Retries (2) with backoff on timeouts / network errors / 5xx. 429 honours a short Retry-After,
    otherwise opens a cool-down so we stop hammering the provider.
  * Typed errors (see base.py) - invalid key, subscription, rate limit, unavailable, not found.
  * Nothing is fabricated: fields the provider does not return are None.
"""
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import httpx

from ..config import settings
from .base import (RANGES, DataUnavailable, InvalidApiKey, PermissionDenied, ProviderError,
                   ProviderUnavailable, Quote, RateLimited, SymbolNotFound)
from .universe import BY_SYMBOL

log = logging.getLogger("market.indianapi")
BASE_URL = "https://stock.indianapi.in"
MAX_RETRIES = 2
MAX_INLINE_RETRY_AFTER = 2      # seconds we are willing to sleep on a 429
COOLDOWN_SECONDS = 30           # stop calling the provider this long after 429 / bad key
HISTORY_TTL = 300
FUNDAMENTALS_TTL = 86400
# app range -> (provider `period`, number of trading-day points to keep)
HISTORY_MAP = {"1W": ("1m", 5), "1M": ("1m", 21), "3M": ("6m", 63), "6M": ("6m", 126), "1Y": ("1yr", 250)}
assert set(HISTORY_MAP) == set(RANGES)


def _f(v) -> float | None:
    """Parse provider numbers, which are often strings ('1,234.5', '-0.4%')."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        s = str(v).replace(",", "").replace("%", "").replace("₹", "").strip()
        return float(s) if s not in ("", "-", "--", "NA", "N/A", "null") else None
    except ValueError:
        return None


class IndianApiProvider:
    name = "IndianAPI (NSE)"

    def __init__(self, api_key: str, client: httpx.Client | None = None, sleep=time.sleep):
        self.api_key = api_key
        self.client = client or httpx.Client(base_url=settings.indian_api_base_url, timeout=15.0)
        self.data_mode = "live" if settings.data_latency == "realtime" else "delayed"
        self._sleep = sleep
        self._cache: dict[str, tuple[float, object]] = {}
        self._locks: dict[str, threading.Lock] = {}
        self._guard = threading.Lock()
        self._blocked_until = 0.0
        self._blocked_error: ProviderError | None = None

    # ---- plumbing -------------------------------------------------------
    def _lock_for(self, key: str) -> threading.Lock:
        with self._guard:
            return self._locks.setdefault(key, threading.Lock())

    def _cached(self, key: str, ttl: float, fn):
        hit = self._cache.get(key)
        if hit and time.time() < hit[0]:
            return hit[1]
        with self._lock_for(key):          # single-flight: others wait, then hit the cache
            hit = self._cache.get(key)
            if hit and time.time() < hit[0]:
                return hit[1]
            val = fn()                      # errors are NOT cached
            self._cache[key] = (time.time() + ttl, val)
            return val

    def _block(self, err: ProviderError, seconds: float) -> None:
        self._blocked_until = time.time() + seconds
        self._blocked_error = err

    def _get(self, path: str, **params):
        if time.time() < self._blocked_until and self._blocked_error is not None:
            e = self._blocked_error
            raise type(e)(str(e), retry_after=max(1, int(self._blocked_until - time.time())))
        last: ProviderError | None = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                r = self.client.get(path, params=params, headers={"x-api-key": self.api_key})
            except httpx.HTTPError as e:    # timeouts, connection errors
                log.warning("IndianAPI %s network error: %s (attempt %d)", path, type(e).__name__, attempt + 1)
                last = ProviderUnavailable("Market data provider is unreachable (network error or timeout)")
                if attempt < MAX_RETRIES:
                    self._sleep(0.5 * 2 ** attempt)
                    continue
                raise last from e
            sc = r.status_code
            if sc == 200:
                try:
                    data = r.json()
                except ValueError as e:
                    raise ProviderUnavailable("Provider returned a malformed response") from e
                if isinstance(data, dict) and set(data) <= {"error", "message", "detail"} and (data.get("error") or data.get("detail")):
                    msg = str(data.get("error") or data.get("detail"))
                    if "not found" in msg.lower():
                        raise SymbolNotFound(msg)
                    raise ProviderError(f"Provider error: {msg}")
                return data
            log.warning("IndianAPI %s -> HTTP %s (attempt %d)", path, sc, attempt + 1)
            if sc == 401:
                err = InvalidApiKey("IndianAPI rejected the API key (401). Check INDIAN_API_KEY in backend/.env")
                self._block(err, COOLDOWN_SECONDS)
                raise err
            if sc == 403:
                err = PermissionDenied("Your IndianAPI plan does not allow this request (403). Check your subscription")
                raise err
            if sc == 429:
                ra = int(_f(r.headers.get("retry-after")) or COOLDOWN_SECONDS)
                if ra <= MAX_INLINE_RETRY_AFTER and attempt < MAX_RETRIES:
                    self._sleep(ra)
                    continue
                err = RateLimited(f"IndianAPI rate/quota limit reached. Retry in ~{ra}s", retry_after=ra)
                self._block(err, ra)
                raise err
            if sc == 404:
                raise SymbolNotFound("Not found at provider")
            if sc >= 500:
                last = ProviderUnavailable(f"IndianAPI is unavailable (HTTP {sc})")
                if attempt < MAX_RETRIES:
                    self._sleep(0.5 * 2 ** attempt)
                    continue
                raise last
            raise ProviderError(f"IndianAPI rejected the request (HTTP {sc})")
        raise last or ProviderUnavailable("Market data provider is unreachable")

    # ---- quotes ---------------------------------------------------------
    def _lookup_name(self, symbol: str) -> str:
        return BY_SYMBOL.get(symbol, {}).get("name", symbol)

    def _stock_raw(self, symbol: str) -> dict:
        def fetch():
            d = self._get("/stock", name=self._lookup_name(symbol))
            if not isinstance(d, dict) or not d:
                raise SymbolNotFound(f"No data for {symbol}")
            return d
        try:
            return self._cached(f"s:{symbol}", settings.quote_cache_seconds, fetch)
        except SymbolNotFound:
            raise SymbolNotFound(f"Symbol '{symbol}' was not found at the provider") from None

    @staticmethod
    def _to_quote(d: dict, symbol: str, name: str) -> Quote:
        price = _f((d.get("currentPrice") or {}).get("NSE"))
        pct = _f(d.get("percentChange"))
        if price is None:
            raise DataUnavailable(f"No NSE price available for {symbol}")
        if pct is None or pct <= -100:
            raise DataUnavailable(f"Incomplete quote for {symbol} (no percent change)")
        # The documented /stock payload has no previous-close field: derive it from the provider's own
        # percentChange (prev = price / (1 + pct/100)). open/high/low/volume are not documented -> None.
        prev = price / (1 + pct / 100)
        return Quote(symbol=symbol, name=name, price=price, prev_close=round(prev, 2),
                     change=round(price - prev, 2), change_pct=round(pct, 2), as_of=None)

    def get_quotes(self, symbols: list[str]) -> dict[str, Quote]:
        symbols = sorted(set(symbols))
        if not symbols:
            return {}
        out: dict[str, Quote] = {}
        errors: list[ProviderError] = []

        def one(sym: str):
            try:
                return sym, self._to_quote(self._stock_raw(sym), sym, self._lookup_name(sym)), None
            except ProviderError as e:
                return sym, None, e

        with ThreadPoolExecutor(max_workers=min(5, len(symbols))) as ex:
            for sym, q, err in ex.map(one, symbols):
                if q:
                    out[sym] = q
                else:
                    errors.append(err)
        if not out:
            # Surface the most informative error (key/plan/limit before per-symbol problems)
            errors.sort(key=lambda e: isinstance(e, (SymbolNotFound, DataUnavailable)))
            raise errors[0]
        if errors:
            log.info("Quotes: %d/%d symbols unavailable", len(errors), len(symbols))
        return out

    def get_index(self) -> Quote:
        # IndianAPI documents no index endpoint; we try the stock lookup with the configured name and
        # report "unavailable" honestly if the provider has nothing for it.
        name = settings.index_name
        d = self._cached("idx", settings.quote_cache_seconds, lambda: self._get("/stock", name=name))
        if not isinstance(d, dict) or not d:
            raise DataUnavailable(f"{name} is not available from IndianAPI")
        return self._to_quote(d, name, name)

    # ---- history --------------------------------------------------------
    def _series(self, stock_name: str, range_: str) -> list[dict]:
        if range_ not in HISTORY_MAP:
            raise ProviderError(f"Unsupported range {range_}")
        period, n = HISTORY_MAP[range_]
        d = self._cached(f"h:{stock_name}:{period}", HISTORY_TTL, lambda: self._get(
            "/historical_data", stock_name=stock_name, period=period, filter="price"))
        sets = d.get("datasets") if isinstance(d, dict) else None
        price = next((s for s in sets or [] if str(s.get("metric", "")).lower() == "price"), None)
        pts = []
        for row in (price or {}).get("values") or []:
            try:
                close = _f(row[1])
                if close is not None:
                    pts.append({"date": str(row[0])[:10], "close": close})
            except (IndexError, TypeError):
                continue
        if not pts:
            raise DataUnavailable("No historical data returned for this symbol/range")
        pts.sort(key=lambda p: p["date"])
        return pts[-n:]

    def get_history(self, symbol: str, range_: str) -> list[dict]:
        return self._series(self._lookup_name(symbol), range_)

    def get_index_history(self, range_: str) -> list[dict]:
        return self._series(settings.index_name, range_)

    # ---- profile / fundamentals -----------------------------------------
    def get_profile(self, symbol: str) -> dict | None:
        try:
            d = self._stock_raw(symbol)
        except (SymbolNotFound, DataUnavailable):
            return None
        prof = d.get("companyProfile") if isinstance(d.get("companyProfile"), dict) else {}
        return {
            "name": d.get("companyName") or BY_SYMBOL.get(symbol, {}).get("name", symbol),
            "sector": d.get("industry") or BY_SYMBOL.get(symbol, {}).get("sector"),
            "exchange": "NSE", "description": prof.get("companyDescription"),
            "website": None, "employees": None, "ceo": None,
        }

    def _stats(self, symbol: str, stats: str) -> dict:
        name = self._lookup_name(symbol)
        return self._cached(f"hs:{name}:{stats}", FUNDAMENTALS_TTL,
                            lambda: self._get("/historical_stats", stock_name=name, stats=stats))

    @staticmethod
    def _period_key(label: str):
        for fmt in ("%b %Y", "%Y"):
            try:
                return datetime.strptime(label.strip(), fmt)
            except ValueError:
                pass
        return datetime.min

    def get_fundamentals(self, symbol: str) -> dict | None:
        def rows(stats: str, annual: bool, keep: int) -> list[dict]:
            try:
                d = self._stats(symbol, stats)
            except (SymbolNotFound, DataUnavailable):
                return []
            if not isinstance(d, dict):
                return []
            sales, profit = d.get("Sales") or {}, d.get("Net Profit") or {}
            if not isinstance(sales, dict) or not isinstance(profit, dict):
                return []
            periods = sorted((p for p in sales if p in profit), key=self._period_key)
            res = []
            for p in periods:
                rev, ni = _f(sales[p]), _f(profit[p])
                if rev is None or ni is None:
                    continue
                label = "FY" + p.strip()[-2:] if annual else p.strip()
                # IndianAPI statement tables are Screener-style, i.e. ₹ crore (unit taken from the docs' tables).
                res.append({"period": label, "revenue": round(rev), "net_profit": round(ni)})
            for i, row in enumerate(res):
                if i == 0:
                    row["revenue_growth_pct"] = row["profit_growth_pct"] = None
                else:
                    prev = res[i - 1]
                    row["revenue_growth_pct"] = round((row["revenue"] / prev["revenue"] - 1) * 100, 1) if prev["revenue"] else None
                    row["profit_growth_pct"] = round((row["net_profit"] / prev["net_profit"] - 1) * 100, 1) if prev["net_profit"] > 0 else None
            return res[-keep:]

        annual, quarterly = rows("yoy_results", True, 6), rows("quarter_results", False, 8)
        if not annual and not quarterly:
            return None
        # market cap / P-E have no documented field in IndianAPI's responses -> reported as unavailable (None)
        return {"market_cap": None, "currency": "INR", "unit": "crore",
                "annual": annual, "quarterly": quarterly, "pe_ratio": None}
