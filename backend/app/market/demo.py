"""DEMO provider: deterministic SIMULATED data. Never real market data.

Every response served from here is tagged data_mode="demo" so the UI labels it clearly.
"""
import math
import random
import time
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache

from .base import RANGES, ProviderError, Quote
from .universe import BY_SYMBOL

IST = timezone(timedelta(hours=5, minutes=30))
HISTORY_DAYS = 400
INDEX_BASE = 24000.0


def _last_weekday(d: date) -> date:
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


@lru_cache(maxsize=256)
def _closes(symbol: str, anchor: date) -> list[tuple[date, float]]:
    """AR(1) mean-reverting walk of daily closes ending on `anchor` (a weekday)."""
    base = BY_SYMBOL[symbol]["demo_base"]
    days: list[date] = []
    d = anchor
    while len(days) < HISTORY_DAYS:
        if d.weekday() < 5:
            days.append(d)
        d -= timedelta(days=1)
    days.reverse()
    x, out = 0.0, []
    for day in days:
        rng = random.Random(f"{symbol}:{day.isoformat()}")
        x = 0.97 * x + rng.gauss(0, 0.014)
        out.append((day, round(base * math.exp(x), 2)))
    return out


def _anchor() -> date:
    return _last_weekday(datetime.now(IST).date())


class DemoProvider:
    name = "Demo (simulated data)"
    data_mode = "demo"

    def _quote(self, symbol: str) -> Quote:
        meta = BY_SYMBOL.get(symbol)
        if not meta:
            raise ProviderError(f"Unknown symbol {symbol}")
        closes = _closes(symbol, _anchor())
        prev_close = closes[-2][1]
        day_close = closes[-1][1]
        bucket = int(time.time() // 10)
        jitter = random.Random(f"{symbol}:{bucket}").uniform(-0.0015, 0.0015)
        price = round(day_close * (1 + jitter), 2)
        open_ = round(prev_close * (1 + (day_close / prev_close - 1) * 0.25), 2)
        high = round(max(price, open_, day_close) * 1.004, 2)
        low = round(min(price, open_, day_close) * 0.996, 2)
        change = round(price - prev_close, 2)
        return Quote(
            symbol=symbol, name=meta["name"], price=price, prev_close=prev_close,
            change=change, change_pct=round(change / prev_close * 100, 2),
            open=open_, high=high, low=low,
            volume=random.Random(f"vol:{symbol}:{_anchor()}").randint(800_000, 9_000_000),
            as_of=datetime.now(IST).isoformat(timespec="seconds"),
        )

    def get_quotes(self, symbols: list[str]) -> dict[str, Quote]:
        return {s: self._quote(s) for s in symbols if s in BY_SYMBOL}

    def _index_series(self) -> list[tuple[date, float]]:
        per = [_closes(s, _anchor()) for s in BY_SYMBOL]
        series = []
        for i in range(HISTORY_DAYS):
            avg = sum(p[i][1] / BY_SYMBOL[s]["demo_base"] for p, s in zip(per, BY_SYMBOL)) / len(per)
            series.append((per[0][i][0], round(INDEX_BASE * avg, 2)))
        return series

    def get_index(self) -> Quote:
        series = self._index_series()
        prev = series[-2][1]
        quotes = self.get_quotes(list(BY_SYMBOL))
        live_ratio = sum(q.price / BY_SYMBOL[q.symbol]["demo_base"] for q in quotes.values()) / len(quotes)
        price = round(INDEX_BASE * live_ratio, 2)
        change = round(price - prev, 2)
        return Quote(
            symbol="NIFTY 50", name="NIFTY 50 (simulated)", price=price, prev_close=prev,
            change=change, change_pct=round(change / prev * 100, 2),
            high=max(price, series[-1][1]), low=min(price, series[-1][1]),
            as_of=datetime.now(IST).isoformat(timespec="seconds"),
        )

    @staticmethod
    def _slice(series: list[tuple[date, float]], range_: str) -> list[dict]:
        if range_ not in RANGES:
            raise ProviderError(f"Unsupported range {range_}")
        return [{"date": d.isoformat(), "close": c} for d, c in series[-RANGES[range_]:]]

    def get_history(self, symbol: str, range_: str) -> list[dict]:
        if symbol not in BY_SYMBOL:
            raise ProviderError(f"Unknown symbol {symbol}")
        return self._slice(_closes(symbol, _anchor()), range_)

    def get_index_history(self, range_: str) -> list[dict]:
        return self._slice(self._index_series(), range_)

    def get_profile(self, symbol: str) -> dict | None:
        meta = BY_SYMBOL.get(symbol)
        if not meta:
            return None
        return {
            "name": meta["name"], "sector": meta["sector"], "exchange": "NSE",
            "description": (
                f"{meta['name']} is a NIFTY 50 constituent in the {meta['sector']} sector. "
                "This profile text is a generic DEMO placeholder; connect a data provider "
                "with company-profile access for real descriptions."
            ),
            "website": None, "employees": None, "ceo": None,
        }

    def get_fundamentals(self, symbol: str) -> dict | None:
        """SIMULATED financials in INR crore. Deterministic per symbol."""
        meta = BY_SYMBOL.get(symbol)
        if not meta:
            return None
        rng = random.Random(f"fund:{symbol}")
        price = self._quote(symbol).price
        shares_cr = rng.uniform(40, 700)  # crore shares
        market_cap = round(price * shares_cr, 0)
        margin = rng.uniform(0.06, 0.24)
        rev_latest = market_cap / rng.uniform(1.6, 5.5)
        growth = rng.uniform(0.03, 0.18)

        def build(n: int, step_growth: float, labels: list[str]) -> list[dict]:
            rows, rev = [], rev_latest * (0.25 if step_growth < growth / 2 else 1)
            for i in range(n - 1, -1, -1):
                r = rev / ((1 + step_growth) ** i) * rng.uniform(0.97, 1.03)
                m = max(0.02, margin + rng.uniform(-0.02, 0.02))
                rows.append({"period": labels[n - 1 - i], "revenue": round(r), "net_profit": round(r * m)})
            return rows

        today = _anchor()
        fy = today.year if today.month >= 4 else today.year - 1
        annual = build(5, growth, [f"FY{str(y)[2:]}" for y in range(fy - 4, fy + 1)])
        q_labels = []
        y, q = fy, 4  # walk back from latest completed quarters
        for _ in range(8):
            q_labels.append(f"Q{q} FY{str(y)[2:]}")
            q -= 1
            if q == 0:
                q, y = 4, y - 1
        q_labels.reverse()
        quarterly = build(8, growth / 4, q_labels)
        return {
            "market_cap": market_cap, "currency": "INR", "unit": "crore",
            "annual": _with_growth(annual), "quarterly": _with_growth(quarterly),
            "pe_ratio": round(market_cap / max(annual[-1]["net_profit"], 1), 1),
        }


def _with_growth(rows: list[dict]) -> list[dict]:
    for i, r in enumerate(rows):
        if i == 0:
            r["revenue_growth_pct"] = r["profit_growth_pct"] = None
        else:
            p = rows[i - 1]
            r["revenue_growth_pct"] = round((r["revenue"] / p["revenue"] - 1) * 100, 1)
            r["profit_growth_pct"] = round((r["net_profit"] / p["net_profit"] - 1) * 100, 1)
    return rows
