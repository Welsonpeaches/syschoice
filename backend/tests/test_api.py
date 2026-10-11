import json

from app.config import Config


def test_health(client):
    body = client.get("/api/health").get_json()
    assert body["status"] == "ok"
    assert body["candidates"] == 72


def test_quiz_shape(client):
    body = client.get("/api/quiz").get_json()
    assert len(body["sections"]) == 5
    assert len(body["questions"]) == 28
    assert len(body["dimensions"]) == 9


def test_catalog_never_leaks_cli_answers(client):
    body = client.get("/api/catalog").get_json()
    assert len(body["cli"]) == 6
    assert len(body["candidates"]) == 72
    for item in body["cli"]:
        assert "answer" not in item
        assert "explain" not in item


def test_assess_stores_and_round_trips(client, base_payload):
    response = client.post("/api/assess", json=base_payload(answers={"A2": ["gaming"]}))
    assert response.status_code == 200
    body = response.get_json()
    assert body["shareCode"]
    assert len(body["top"]) == 3
    assert len(body["full"]) == 72
    assert len(body["radar"]["values"]) == 9

    stored = client.get(f"/api/result/{body['shareCode']}")
    assert stored.status_code == 200
    assert stored.get_json()["top"][0]["id"] == body["top"][0]["id"]


def test_assess_rejects_empty_answers(client):
    assert client.post("/api/assess", json={}).status_code == 400
    assert client.post("/api/assess", json={"answers": {}}).status_code == 400


def test_assess_ignores_unknown_hardware_fields(client, base_payload):
    response = client.post("/api/assess", json=base_payload(
        hardware={"memoryGB": 8, "evil": "<script>", "cores": "many"},
    ))
    assert response.status_code == 200
    code = response.get_json()["shareCode"]
    detail = client.get(
        "/api/admin/sessions",
        headers={"X-Admin-Token": Config.ADMIN_TOKEN},
    )
    assert detail.status_code == 401  # default token differs from the test token


def test_missing_result_returns_404(client):
    assert client.get("/api/result/deadbeef").status_code == 404


def test_stats_reflects_submissions(client, base_payload):
    empty = client.get("/api/stats").get_json()
    assert empty["total"] == 0
    client.post("/api/assess", json=base_payload())
    body = client.get("/api/stats").get_json()
    assert body["total"] == 1
    assert body["topCandidates"]
    assert body["byFamily"]
    assert body["familyLabels"]["linux"] == "Linux"


def test_admin_requires_token(client, app, base_payload):
    client.post("/api/assess", json=base_payload())
    assert client.get("/api/admin/sessions").status_code == 401
    assert client.get(
        "/api/admin/sessions", headers={"X-Admin-Token": "wrong"}
    ).status_code == 401

    token = app.config["ADMIN_TOKEN"]
    ok = client.get("/api/admin/sessions", headers={"X-Admin-Token": token})
    assert ok.status_code == 200
    body = ok.get_json()
    assert body["total"] == 1
    assert body["items"][0]["top1_name"]


def test_admin_detail_and_export(client, app, base_payload):
    client.post("/api/assess", json=base_payload())
    token = app.config["ADMIN_TOKEN"]
    headers = {"X-Admin-Token": token}

    session_id = client.get("/api/admin/sessions", headers=headers).get_json()["items"][0]["id"]
    detail = client.get(f"/api/admin/sessions/{session_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.get_json()["result"]["top"]

    export = client.get("/api/admin/export.csv", headers=headers)
    assert export.status_code == 200
    text = export.get_data(as_text=True)
    header = text.splitlines()[0]
    for column in ("share_code", "top1_name", "top2_name", "top3_match"):
        assert column in header
    assert len(text.splitlines()) == 2


def test_admin_search_filters(client, app, base_payload):
    client.post("/api/assess", json=base_payload())
    token = app.config["ADMIN_TOKEN"]
    headers = {"X-Admin-Token": token}
    code = client.get("/api/admin/sessions", headers=headers).get_json()["items"][0]["share_code"]
    hit = client.get(f"/api/admin/sessions?q={code}", headers=headers).get_json()
    assert hit["total"] == 1
    miss = client.get("/api/admin/sessions?q=zzzzzzzz", headers=headers).get_json()
    assert miss["total"] == 0


def test_rate_limit_returns_429(client, app, base_payload, monkeypatch):
    app.config["RATE_LIMIT_MAX_REQUESTS"] = 3
    app.config["RATE_LIMIT_WINDOW_SECONDS"] = 60
    payload = base_payload()
    codes = [client.post("/api/assess", json=payload).status_code for _ in range(5)]
    assert 429 in codes
    assert codes[0] == 200
