import threading
import time

import httpx
import pytest

from app.market.base import (DataUnavailable, InvalidApiKey, PermissionDenied, ProviderUnavailable,
                             RateLimited, SymbolNotFound)
from app.market.indianapi import IndianApiProvider


def make(handler, **kw):
    c = httpx.Client(base_url="https://stock.indianapi.in", transport=httpx.MockTransport(handler))
    return IndianApiProvider("SECRET", c, sleep=lambda s: None, **kw)


def stock(price="3300.5", pct="1.5"):
    return {"companyName": "TCS", "industry": "IT", "currentPrice": {"BSE": "3301", "NSE": price},
            "percentChange": pct, "companyProfile": {"companyDescription": "Desc"}}


def test_auth_header_and_quote_parsing():
    seen = []
    def h(req):
        seen.append(req)
        return httpx.Response(200, json=stock())
    p = make(h)
    q = p.get_quotes(["TCS"])["TCS"]
    assert seen[0].headers["x-api-key"] == "SECRET" and "SECRET" not in str(seen[0].url)
    assert q.price == 3300.5 and q.change_pct == 1.5 and round(q.change, 2) == round(q.price - q.prev_close, 2)
    assert p.data_mode == "delayed"


def test_cache_and_single_flight():
    calls = []
    def h(req):
        calls.append(1)
        time.sleep(0.05)
        return httpx.Response(200, json=stock())
    p = make(h)
    ts = [threading.Thread(target=lambda: p.get_quotes(["TCS"])) for _ in range(8)]
    [t.start() for t in ts]; [t.join() for t in ts]
    p.get_quotes(["TCS"])
    assert len(calls) == 1


@pytest.mark.parametrize("status,exc", [(401, InvalidApiKey), (403, PermissionDenied), (404, SymbolNotFound),
                                        (429, RateLimited), (503, ProviderUnavailable)])
def test_distinct_errors(status, exc):
    p = make(lambda r: httpx.Response(status, headers={"retry-after": "30"}, json={}))
    with pytest.raises(exc):
        p.get_quotes(["TCS"])


def test_retry_on_5xx_then_success():
    n = {"c": 0}
    def h(req):
        n["c"] += 1
        return httpx.Response(502) if n["c"] < 3 else httpx.Response(200, json=stock())
    assert make(h).get_quotes(["TCS"])["TCS"].price == 3300.5 and n["c"] == 3


def test_network_error_is_unavailable():
    def boom(r):
        raise httpx.ConnectError("x")
    with pytest.raises(ProviderUnavailable):
        make(boom).get_quotes(["TCS"])


def test_rate_limit_cooldown_stops_hammering():
    n = {"c": 0}
    def h(req):
        n["c"] += 1
        return httpx.Response(429, headers={"retry-after": "30"})
    p = make(h)
    for _ in range(3):
        with pytest.raises(RateLimited):
            p.get_quotes(["TCS"])
    assert n["c"] == 1


def test_partial_results_and_missing_price():
    def h(req):
        if req.url.params["name"].startswith("Infosys"):
            return httpx.Response(200, json={"currentPrice": {"NSE": None}, "percentChange": "1"})
        return httpx.Response(200, json=stock())
    q = make(h).get_quotes(["TCS", "INFY"])
    assert set(q) == {"TCS"}
    with pytest.raises(DataUnavailable):
        make(h).get_quotes(["INFY"])


def test_history_maps_period_slices_and_sorts():
    vals = [[f"2026-10-{d:02d}", str(100 + d)] for d in range(30, 0, -1)]
    def h(req):
        assert req.url.params["period"] == "1m" and req.url.params["filter"] == "price"
        return httpx.Response(200, json={"datasets": [{"metric": "DMA50", "values": [["2026-10-01", "1"]]},
                                                      {"metric": "Price", "values": vals}]})
    pts = make(h).get_history("TCS", "1W")
    assert len(pts) == 5 and pts[-1]["date"] == "2026-10-30" and pts[0]["date"] < pts[-1]["date"]


def test_history_missing_data():
    with pytest.raises(DataUnavailable):
        make(lambda r: httpx.Response(200, json={"datasets": []})).get_history("TCS", "1M")


def test_fundamentals_and_unavailable():
    def h(req):
        if req.url.params["stats"] == "yoy_results":
            return httpx.Response(200, json={"Sales": {"Mar 2024": "1,000", "Mar 2025": "1,200"},
                                             "Net Profit": {"Mar 2024": "100", "Mar 2025": "150"}})
        return httpx.Response(404)
    f = make(h).get_fundamentals("TCS")
    assert [r["period"] for r in f["annual"]] == ["FY24", "FY25"] and f["annual"][1]["revenue_growth_pct"] == 20.0
    assert f["quarterly"] == [] and f["market_cap"] is None
    assert make(lambda r: httpx.Response(404)).get_fundamentals("TCS") is None
    with pytest.raises(InvalidApiKey):
        make(lambda r: httpx.Response(401)).get_fundamentals("TCS")


def test_api_maps_error_codes(client, monkeypatch):
    from app.market.service import set_provider
    set_provider(make(lambda r: httpx.Response(401)))
    r = client.get("/api/watchlist")
    assert r.status_code == 200  # empty watchlist makes no provider call
    r = client.get("/api/stocks/TCS")
    assert r.status_code == 502 and r.json()["code"] == "invalid_api_key"
    set_provider(make(lambda r: httpx.Response(429, headers={"retry-after": "30"})))
    r = client.get("/api/market/overview")
    assert r.status_code == 429 and r.json()["code"] == "rate_limited" and r.headers["retry-after"]
    set_provider(None)
