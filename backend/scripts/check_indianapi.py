"""Live smoke test for the IndianAPI integration. Run from backend/:  python scripts/check_indianapi.py
Needs INDIAN_API_KEY in backend/.env. Prints status/shape only (never the key)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import settings  # noqa: E402
from app.market.base import ProviderError  # noqa: E402
from app.market.indianapi import IndianApiProvider  # noqa: E402

if not settings.indian_api_key:
    sys.exit("INDIAN_API_KEY is not set in backend/.env")
p = IndianApiProvider(settings.indian_api_key)
checks = {
    "quote TCS": lambda: p.get_quotes(["TCS"])["TCS"].dict(),
    "profile TCS": lambda: p.get_profile("TCS"),
    "history TCS 1M": lambda: (lambda x: f"{len(x)} points, last={x[-1]}")(p.get_history("TCS", "1M")),
    "index NIFTY 50": lambda: p.get_index().dict(),
    "index history 1M": lambda: (lambda x: f"{len(x)} points, last={x[-1]}")(p.get_index_history("1M")),
    "fundamentals TCS": lambda: (lambda f: f and {"annual": f["annual"][-2:], "quarterly": f["quarterly"][-2:]})(p.get_fundamentals("TCS")),
}
for name, fn in checks.items():
    try:
        print(f"OK   {name}: {fn()}")
    except ProviderError as e:
        print(f"FAIL {name}: [{e.code}] {e}")
