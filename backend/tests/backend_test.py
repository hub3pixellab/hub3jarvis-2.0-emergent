"""Hub3 JARVIS v4.2 backend API tests."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://hub3-consensus.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@hub3.ai"
ADMIN_PASSWORD = "Hub3Admin!2026"


@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    data = r.json()
    assert "token" in data and data["email"] == ADMIN_EMAIL
    return data["token"]


@pytest.fixture(scope="session")
def new_user():
    email = f"test_{uuid.uuid4().hex[:8]}@hub3test.ai"
    r = requests.post(f"{API}/auth/register", json={"email": email, "password": "TestPass123!", "name": "Test User"}, timeout=15)
    assert r.status_code == 200, f"register failed: {r.status_code} {r.text}"
    data = r.json()
    assert data["email"] == email and "token" in data
    return {"email": email, "password": "TestPass123!", "token": data["token"], "id": data["id"]}


def auth(t): return {"Authorization": f"Bearer {t}"}


# --- Root / health ---
def test_root():
    r = requests.get(f"{API}/", timeout=10)
    assert r.status_code == 200
    assert r.json().get("status") == "online"


# --- Auth ---
def test_login_invalid():
    r = requests.post(f"{API}/auth/login", json={"email": "nope@x.com", "password": "bad"}, timeout=10)
    assert r.status_code == 401


def test_register_duplicate(new_user):
    r = requests.post(f"{API}/auth/register", json={"email": new_user["email"], "password": "TestPass123!", "name": "Dup"}, timeout=10)
    assert r.status_code == 400


def test_me_bearer(admin_token):
    r = requests.get(f"{API}/auth/me", headers=auth(admin_token), timeout=10)
    assert r.status_code == 200
    assert r.json()["email"] == ADMIN_EMAIL


def test_me_unauth():
    r = requests.get(f"{API}/auth/me", timeout=10)
    assert r.status_code == 401


def test_me_cookie():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200
    r2 = s.get(f"{API}/auth/me", timeout=10)
    assert r2.status_code == 200
    assert r2.json()["email"] == ADMIN_EMAIL


# --- Dashboard ---
def test_dashboard_overview(admin_token):
    r = requests.get(f"{API}/dashboard/overview", headers=auth(admin_token), timeout=10)
    assert r.status_code == 200
    d = r.json()
    assert len(d["life_areas"]) == 8
    assert d["life_balance"]["score"] == 78
    assert len(d["metrics"]) == 4
    assert d["top_recommendation"]["consensus"] == 92
    assert len(d["ai_models_breakdown"]) == 8


# --- Smart Home ---
def test_smart_home_state(admin_token):
    r = requests.get(f"{API}/smart-home/state", headers=auth(admin_token), timeout=10)
    assert r.status_code == 200
    d = r.json()
    for k in ["lights", "thermostat", "cameras", "tv", "lock", "speaker", "wearable", "plugs"]:
        assert k in d["devices"]


def test_smart_home_toggle_persistence(new_user):
    t = new_user["token"]
    # Get current lights state
    r = requests.get(f"{API}/smart-home/state", headers=auth(t), timeout=10)
    lights = r.json()["devices"]["lights"]
    new_on = not lights["on"]
    r2 = requests.post(f"{API}/smart-home/toggle", headers=auth(t), json={"device_id": "lights", "state": {"on": new_on}}, timeout=10)
    assert r2.status_code == 200
    assert r2.json()["state"]["on"] == new_on
    # persist check
    r3 = requests.get(f"{API}/smart-home/state", headers=auth(t), timeout=10)
    assert r3.json()["devices"]["lights"]["on"] == new_on


def test_smart_home_toggle_404(admin_token):
    r = requests.post(f"{API}/smart-home/toggle", headers=auth(admin_token), json={"device_id": "unknown", "state": {}}, timeout=10)
    assert r.status_code == 404


# --- Chat ---
def test_chat_conversations(admin_token):
    r = requests.get(f"{API}/chat/conversations", headers=auth(admin_token), timeout=10)
    assert r.status_code == 200
    convs = r.json()
    assert any(c["id"] == "jarvis" for c in convs)
    assert len(convs) >= 7


def test_chat_send_and_history(admin_token):
    r = requests.post(f"{API}/chat/send", headers=auth(admin_token),
                     json={"text": "Ei Hub, acenda as luzes", "conversation_id": "jarvis"}, timeout=60)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["conversation_id"] == "jarvis"
    assert d["inline_card"] == "devices_snapshot"
    assert isinstance(d["reply"], str) and len(d["reply"]) > 0

    r2 = requests.get(f"{API}/chat/history/jarvis", headers=auth(admin_token), timeout=10)
    assert r2.status_code == 200
    msgs = r2.json()
    assert len(msgs) >= 2
    assert any(m["role"] == "user" for m in msgs)
    assert any(m["role"] == "assistant" for m in msgs)


# --- Consensus ---
def test_consensus_query(admin_token):
    r = requests.post(f"{API}/consensus/query", headers=auth(admin_token),
                     json={"question": "What is 2+2? Answer in one sentence."}, timeout=90)
    assert r.status_code == 200, r.text
    d = r.json()
    assert len(d["results"]) == 3
    assert len(d["ranked"]) == 3
    assert d["metrics"]["models_total"] == 3
    # at least one succeeded
    assert d["metrics"]["models_responded"] >= 1
    assert d["winner"] is not None


def test_consensus_unauth():
    r = requests.post(f"{API}/consensus/query", json={"question": "hi"}, timeout=10)
    assert r.status_code == 401
