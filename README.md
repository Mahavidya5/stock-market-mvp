# NSE Stock Market Dashboard — Phase 1

React + TypeScript + Tailwind + Recharts frontend, FastAPI backend, SQLite (PostgreSQL optional).

**Modules:** live market dashboard (NIFTY 50, top 5 gainers/losers, trend charts) · stock search & watchlist ·
company fundamentals (market cap, revenue, net profit, growth, historical charts) · price alerts with in-app notifications.
Out of scope (Phase 2): trading, brokerage, portfolios, predictions.

## Run locally

Requirements: Python 3.11+, Node 18+.

```bash
# 1) Backend  (http://127.0.0.1:8000, API docs at /docs)
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env                                 # optional; works without it in DEMO mode
uvicorn app.main:app --reload

# 2) Frontend  (http://localhost:5173, proxies /api to the backend)
cd frontend
npm install
npm run dev
```

Tests: `cd backend && python -m pytest -q` · Frontend check: `cd frontend && npm run build`.

## Data modes (never mixed up)

| Badge | Meaning |
|---|---|
| **DEMO DATA** (amber) | Simulated prices/financials, used when no API key is configured. A banner shows on every page with prices; alert notifications are tagged `[DEMO data]`. |
| **DELAYED** (blue) | Real provider data, labelled delayed (default for provider data). |
| **LIVE** (green) | Real-time; only shown if you set `MARKET_DATA_LATENCY=realtime`. |

If the provider fails, the API returns HTTP 502 and the UI shows the error — it **never silently falls back to demo data**.

### Connecting real data (IndianAPI)
1. Get a key at [indianapi.in](https://indianapi.in), put `INDIAN_API_KEY=...` in `backend/.env` (server-side only; sent as the `x-api-key` header), restart the backend.
2. Endpoints used: `/stock?name=` (price, profile), `/historical_data` (charts), `/historical_stats` (revenue/profit). Your plan decides access and quota.
3. **Quota:** the overview needs one `/stock` call per NIFTY 50 stock (~50 per refresh); responses are cached for `QUOTE_CACHE_SECONDS` (60) and concurrent identical requests share one call. Raise the cache/refresh values if your plan is small.
4. Provider errors are reported separately: invalid key / plan not permitted (HTTP 502), rate limit (429 + `Retry-After`), provider down (503), unknown symbol or no data (404). The JSON body has `detail` and a `code`.
5. Verify against your key: `cd backend && python scripts/check_indianapi.py`.

Known IndianAPI gaps: no documented NIFTY index endpoint (the dashboard shows "not available" if the lookup fails), no open/high/low/volume or market cap/P-E in the documented `/stock` fields (shown as unavailable), previous close is derived from the provider's `percentChange`, and prices are labelled DELAYED.

> The IndianAPI integration is covered by mocked-HTTP unit tests only; it has **not** been run against the live API. Run the script above with your key before relying on it.

## API (REST, prefix `/api`)
`GET /health` · `GET /market/overview` · `GET /market/index/history?range=1M` · `GET /stocks/search?q=` ·
`GET /stocks/{symbol}` · `/history?range=` · `/fundamentals` · `GET|POST /watchlist` · `DELETE /watchlist/{symbol}` ·
`GET|POST /alerts` · `PUT|DELETE /alerts/{id}` · `GET /notifications` · `POST /notifications/read-all` · `POST|DELETE /notifications/{id}`.
Ranges: `1W 1M 3M 6M 1Y`.

## How alerts work
An asyncio task in the API process checks enabled alerts every `ALERT_CHECK_INTERVAL_SECONDS`. When a price crosses the target it
creates a notification, stores the trigger time/price, and disables the alert in one transaction, so each crossing notifies once.
Editing the target/condition, or pressing **Re-arm**, resets it. With a real provider, checks are skipped while NSE is closed.

## Known limitations
- Single user, no login: one shared watchlist and alert set.
- Search covers the static NIFTY 50 list in `backend/app/market/universe.py`; constituents change, so update it periodically.
- Market open/closed uses NSE hours (Mon–Fri 09:15–15:30 IST); exchange holidays are not modelled.
- Tables are created at startup (`create_all`); no migration tool yet.
- Frontend was verified by TypeScript/production build and API calls through the dev proxy, not by automated browser tests.
