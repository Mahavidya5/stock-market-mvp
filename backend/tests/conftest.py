import os
import tempfile

_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["MARKET_DATA_PROVIDER"] = "demo"
os.environ["INDIAN_API_KEY"] = ""
os.environ["ALERT_CHECK_INTERVAL_SECONDS"] = "3600"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.market.service import set_provider  # noqa: E402


@pytest.fixture()
def client():
    set_provider(None)
    with TestClient(app) as c:
        yield c
