from datetime import datetime, timedelta, timezone

from app.market.base import ProviderError, Quote
from app.market.service import market_status, set_provider
from app.scheduler import check_alerts

IST = timezone(timedelta(hours=5, minutes=30))


class StubProvider:
    name, data_mode = "Stub", "delayed"

    def __init__(self, prices):
        self.prices = prices

    def get_quotes(self, symbols):
        return {s: Quote(s, s, self.prices[s], 100, 0, 0) for s in symbols if s in self.prices}


# ---- market dashboard -----------------------------------------------------
def test_health_reports_demo(client):
    r = client.get("/api/health").json()
    assert r["status"] == "ok" and r["data_mode"] == "demo"


def test_overview(client):
    d = client.get("/api/market/overview").json()
    assert d["data_mode"] == "demo"
    assert len(d["gainers"]) == 5 and len(d["losers"]) == 5
    pcts = [g["change_pct"] for g in d["gainers"]]
    assert pcts == sorted(pcts, reverse=True)
    assert max(l["change_pct"] for l in d["losers"]) <= min(pcts)
    assert d["index"]["price"] > 0 and "status" in d and d["status"]["state"] in ("open", "closed", "pre_open")


def test_index_history_and_bad_range(client):
    assert len(client.get("/api/market/index/history?range=1M").json()["points"]) == 21
    assert client.get("/api/market/index/history?range=9Y").status_code == 422


def test_market_status_windows():
    mon_open = datetime(2026, 11, 2, 10, 0, tzinfo=IST)
    assert market_status(mon_open)["is_open"]
    assert not market_status(datetime(2026, 11, 2, 16, 0, tzinfo=IST))["is_open"]
    assert not market_status(datetime(2026, 11, 1, 11, 0, tzinfo=IST))["is_open"]  # Sunday


# ---- search / stock / fundamentals ---------------------------------------
def test_search_by_symbol_and_name(client):
    assert client.get("/api/stocks/search?q=tcs").json()["results"][0]["symbol"] == "TCS"
    names = [r["symbol"] for r in client.get("/api/stocks/search?q=hdfc").json()["results"]]
    assert "HDFCBANK" in names and "HDFCLIFE" in names
    assert client.get("/api/stocks/search?q=zzzzqq").json()["results"] == []


def test_stock_detail_history_fundamentals(client):
    d = client.get("/api/stocks/RELIANCE").json()
    assert d["quote"]["symbol"] == "RELIANCE" and d["profile"]["name"]
    assert len(client.get("/api/stocks/RELIANCE/history?range=3M").json()["points"]) == 63
    f = client.get("/api/stocks/RELIANCE/fundamentals").json()
    assert f["available"] and f["market_cap"] > 0 and len(f["annual"]) == 5 and len(f["quarterly"]) == 8
    assert f["annual"][-1]["revenue_growth_pct"] is not None
    assert client.get("/api/stocks/NOPE").status_code == 404
    assert client.get("/api/stocks/M%26M").status_code == 200


# ---- watchlist --------------------------------------------------------------
def test_watchlist_flow(client):
    assert client.post("/api/watchlist", json={"symbol": "infy"}).status_code == 201
    assert client.post("/api/watchlist", json={"symbol": "INFY"}).status_code == 409
    assert client.post("/api/watchlist", json={"symbol": "FAKE"}).status_code == 404
    items = client.get("/api/watchlist").json()["items"]
    assert [i["symbol"] for i in items] == ["INFY"] and items[0]["quote"]["price"] > 0
    assert client.delete("/api/watchlist/INFY").status_code == 204
    assert client.delete("/api/watchlist/INFY").status_code == 404
    assert client.get("/api/watchlist").json()["items"] == []


# ---- alerts + notifications -------------------------------------------------
def test_alert_validation(client):
    assert client.post("/api/alerts", json={"symbol": "TCS", "condition": "UP", "target_price": 10}).status_code == 422
    assert client.post("/api/alerts", json={"symbol": "TCS", "condition": "ABOVE", "target_price": -5}).status_code == 422
    assert client.post("/api/alerts", json={"symbol": "XXX", "condition": "ABOVE", "target_price": 5}).status_code == 404


def test_alert_lifecycle_and_no_duplicates(client):
    set_provider(StubProvider({"TCS": 3000.0}))
    a = client.post("/api/alerts", json={"symbol": "TCS", "condition": "ABOVE", "target_price": 3100}).json()
    assert a["enabled"] and a["triggered_at"] is None and a["current_price"] == 3000.0

    assert check_alerts() == 0  # not crossed
    set_provider(StubProvider({"TCS": 3150.0}))
    assert check_alerts() == 1  # crossed
    assert check_alerts() == 0  # no duplicate

    n = client.get("/api/notifications").json()
    assert n["unread"] == 1 and "TCS" in n["items"][0]["message"] and n["items"][0]["data_mode"] == "delayed"
    alert = client.get("/api/alerts").json()[0]
    assert alert["triggered_at"] and alert["enabled"] is False and alert["triggered_price"] == 3150.0

    # edit re-arms (target moved up -> not crossed)
    upd = client.put(f"/api/alerts/{a['id']}", json={"target_price": 3200}).json()
    assert upd["enabled"] and upd["triggered_at"] is None
    assert check_alerts() == 0
    set_provider(StubProvider({"TCS": 3250.0}))
    assert check_alerts() == 1
    assert client.get("/api/notifications").json()["unread"] == 2

    client.post("/api/notifications/read-all")
    assert client.get("/api/notifications").json()["unread"] == 0
    assert client.delete(f"/api/alerts/{a['id']}").status_code == 204
    assert client.delete(f"/api/alerts/{a['id']}").status_code == 404
    # notification history survives alert deletion
    assert len(client.get("/api/notifications").json()["items"]) == 2


def test_below_alert_and_disable(client):
    set_provider(StubProvider({"INFY": 1500.0}))
    b = client.post("/api/alerts", json={"symbol": "INFY", "condition": "BELOW", "target_price": 1400}).json()
    off = client.put(f"/api/alerts/{b['id']}", json={"enabled": False}).json()
    assert off["enabled"] is False
    set_provider(StubProvider({"INFY": 1390.0}))
    assert check_alerts() == 0  # disabled alerts never fire
    assert client.put(f"/api/alerts/{b['id']}", json={"enabled": True}).json()["enabled"]
    assert check_alerts() == 1


def test_provider_failure_returns_502_not_fake_data(client):
    class Broken(StubProvider):
        def get_quotes(self, symbols):
            raise ProviderError("down")
    set_provider(Broken({}))
    r = client.get("/api/market/overview")
    assert r.status_code == 502 and "down" in r.json()["detail"]
