"""NIFTY 50 universe (static list used for search and the dashboard).

Constituents change over time - edit this list to match the current index.
The last column (demo_base) is ONLY used by the DEMO provider to simulate prices;
it is never shown or served when a real provider is active.
"""

UNIVERSE: list[dict] = [
    {"symbol": "RELIANCE", "name": "Reliance Industries", "sector": "Energy", "demo_base": 1290},
    {"symbol": "TCS", "name": "Tata Consultancy Services", "sector": "IT", "demo_base": 3350},
    {"symbol": "HDFCBANK", "name": "HDFC Bank", "sector": "Financial Services", "demo_base": 1000},
    {"symbol": "ICICIBANK", "name": "ICICI Bank", "sector": "Financial Services", "demo_base": 1400},
    {"symbol": "INFY", "name": "Infosys", "sector": "IT", "demo_base": 1550},
    {"symbol": "BHARTIARTL", "name": "Bharti Airtel", "sector": "Telecom", "demo_base": 1900},
    {"symbol": "ITC", "name": "ITC Ltd", "sector": "FMCG", "demo_base": 420},
    {"symbol": "SBIN", "name": "State Bank of India", "sector": "Financial Services", "demo_base": 820},
    {"symbol": "LT", "name": "Larsen & Toubro", "sector": "Construction", "demo_base": 3600},
    {"symbol": "HINDUNILVR", "name": "Hindustan Unilever", "sector": "FMCG", "demo_base": 2450},
    {"symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank", "sector": "Financial Services", "demo_base": 2100},
    {"symbol": "AXISBANK", "name": "Axis Bank", "sector": "Financial Services", "demo_base": 1150},
    {"symbol": "BAJFINANCE", "name": "Bajaj Finance", "sector": "Financial Services", "demo_base": 1000},
    {"symbol": "MARUTI", "name": "Maruti Suzuki India", "sector": "Automobile", "demo_base": 12500},
    {"symbol": "ASIANPAINT", "name": "Asian Paints", "sector": "Consumer Durables", "demo_base": 2400},
    {"symbol": "SUNPHARMA", "name": "Sun Pharmaceutical Industries", "sector": "Healthcare", "demo_base": 1700},
    {"symbol": "TITAN", "name": "Titan Company", "sector": "Consumer Durables", "demo_base": 3700},
    {"symbol": "ULTRACEMCO", "name": "UltraTech Cement", "sector": "Construction Materials", "demo_base": 12000},
    {"symbol": "NESTLEIND", "name": "Nestle India", "sector": "FMCG", "demo_base": 1250},
    {"symbol": "WIPRO", "name": "Wipro", "sector": "IT", "demo_base": 260},
    {"symbol": "HCLTECH", "name": "HCL Technologies", "sector": "IT", "demo_base": 1500},
    {"symbol": "ONGC", "name": "Oil & Natural Gas Corporation", "sector": "Energy", "demo_base": 240},
    {"symbol": "NTPC", "name": "NTPC Ltd", "sector": "Power", "demo_base": 340},
    {"symbol": "POWERGRID", "name": "Power Grid Corporation of India", "sector": "Power", "demo_base": 290},
    {"symbol": "TATAMOTORS", "name": "Tata Motors", "sector": "Automobile", "demo_base": 700},
    {"symbol": "TATASTEEL", "name": "Tata Steel", "sector": "Metals", "demo_base": 160},
    {"symbol": "JSWSTEEL", "name": "JSW Steel", "sector": "Metals", "demo_base": 1050},
    {"symbol": "M&M", "name": "Mahindra & Mahindra", "sector": "Automobile", "demo_base": 3300},
    {"symbol": "ADANIENT", "name": "Adani Enterprises", "sector": "Metals & Mining", "demo_base": 2300},
    {"symbol": "ADANIPORTS", "name": "Adani Ports & SEZ", "sector": "Services", "demo_base": 1400},
    {"symbol": "COALINDIA", "name": "Coal India", "sector": "Metals & Mining", "demo_base": 390},
    {"symbol": "BAJAJFINSV", "name": "Bajaj Finserv", "sector": "Financial Services", "demo_base": 2000},
    {"symbol": "TECHM", "name": "Tech Mahindra", "sector": "IT", "demo_base": 1500},
    {"symbol": "INDUSINDBK", "name": "IndusInd Bank", "sector": "Financial Services", "demo_base": 800},
    {"symbol": "GRASIM", "name": "Grasim Industries", "sector": "Construction Materials", "demo_base": 2700},
    {"symbol": "HINDALCO", "name": "Hindalco Industries", "sector": "Metals", "demo_base": 750},
    {"symbol": "CIPLA", "name": "Cipla", "sector": "Healthcare", "demo_base": 1500},
    {"symbol": "DRREDDY", "name": "Dr. Reddy's Laboratories", "sector": "Healthcare", "demo_base": 1250},
    {"symbol": "EICHERMOT", "name": "Eicher Motors", "sector": "Automobile", "demo_base": 6500},
    {"symbol": "APOLLOHOSP", "name": "Apollo Hospitals", "sector": "Healthcare", "demo_base": 7200},
    {"symbol": "BRITANNIA", "name": "Britannia Industries", "sector": "FMCG", "demo_base": 5800},
    {"symbol": "HEROMOTOCO", "name": "Hero MotoCorp", "sector": "Automobile", "demo_base": 5200},
    {"symbol": "BPCL", "name": "Bharat Petroleum Corporation", "sector": "Energy", "demo_base": 340},
    {"symbol": "SBILIFE", "name": "SBI Life Insurance", "sector": "Financial Services", "demo_base": 1900},
    {"symbol": "HDFCLIFE", "name": "HDFC Life Insurance", "sector": "Financial Services", "demo_base": 760},
    {"symbol": "TATACONSUM", "name": "Tata Consumer Products", "sector": "FMCG", "demo_base": 1100},
    {"symbol": "DIVISLAB", "name": "Divi's Laboratories", "sector": "Healthcare", "demo_base": 6000},
    {"symbol": "SHRIRAMFIN", "name": "Shriram Finance", "sector": "Financial Services", "demo_base": 650},
    {"symbol": "BAJAJ-AUTO", "name": "Bajaj Auto", "sector": "Automobile", "demo_base": 8500},
    {"symbol": "TRENT", "name": "Trent Ltd", "sector": "Consumer Services", "demo_base": 5000},
]

BY_SYMBOL = {s["symbol"]: s for s in UNIVERSE}


def search(query: str, limit: int = 10) -> list[dict]:
    q = query.strip().lower()
    if not q:
        return []
    scored = []
    for s in UNIVERSE:
        sym, name = s["symbol"].lower(), s["name"].lower()
        if sym == q:
            score = 0
        elif sym.startswith(q):
            score = 1
        elif name.startswith(q):
            score = 2
        elif q in sym or q in name:
            score = 3
        else:
            continue
        scored.append((score, s["symbol"], s))
    scored.sort(key=lambda t: (t[0], t[1]))
    return [{"symbol": s["symbol"], "name": s["name"], "sector": s["sector"]} for _, _, s in scored[:limit]]
