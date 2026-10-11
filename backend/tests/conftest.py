import pytest

from app import create_app
from app.config import Config


class TestConfig(Config):
    ADMIN_TOKEN = "test-token"
    RATE_LIMIT_WINDOW_SECONDS = 60
    RATE_LIMIT_MAX_REQUESTS = 1000


@pytest.fixture()
def app(tmp_path):
    class Cfg(TestConfig):
        DB_PATH = str(tmp_path / "test.db")

    # The throttle keeps a module-level bucket; isolate it between tests.
    from app.api import public

    public._HITS.clear()

    application = create_app(Cfg, serve_frontend=False)
    application.config["TESTING"] = True
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


BASE_ANSWERS = {
    "A1": "desktop", "A2": ["gaming"], "A3": "medium", "A4": "self-casual",
    "A5": "some", "A6": "none", "B1": "search", "B2": "copy", "B3": 3,
    "B4": "balance", "B5": "yes", "B6": "rollback", "C1": ["none"],
    "C2": ["indie"], "C3": "wps", "C4": "16", "C5": "igpu", "C6": "new",
    "C7": "none", "D1": "monthly", "D2": "ok", "D3": ["interrupt"],
    "D4": "newer", "D5": "when-broken", "E1": "normal", "E2": "meh",
    "E3": "once", "E4": "self",
}


@pytest.fixture()
def base_payload():
    def make(**overrides):
        payload = {
            "answers": dict(BASE_ANSWERS),
            "scenarios": {},
            "cli": {},
            "software": [],
            "hardware": {},
        }
        for key, value in overrides.items():
            if key == "answers":
                payload["answers"].update(value)
            else:
                payload[key] = value
        return payload

    return make
