"""The interview layer must only ever add safe, known evidence."""

from app.services.evidence import merge_evidence, sanitize_evidence
from app.services.scoring import build_result


def test_sanitize_drops_unknown_keys_and_clamps():
    clean = sanitize_evidence({
        "traits": {"gaming_intensity": 3.5, "made_up_trait": 1, "tinker": -2},
        "device": "toaster",
        "dimensionWeights": {"gaming": 2, "nonsense": 1},
        "dimensionTargets": {"gaming": 480, "nonsense": 50},
        "software": ["steam", "not-a-software", 42],
        "notes": ["ok", "", 7],
    })
    assert clean["traits"] == {"gaming_intensity": 1.0, "tinker": 0.0}
    assert clean["device"] is None
    assert clean["dimensionWeights"] == {"gaming": 1.0}
    assert clean["dimensionTargets"] == {"gaming": 100.0}
    assert clean["software"] == ["steam"]
    assert clean["notes"] == ["ok"]


def test_sanitize_survives_garbage():
    assert sanitize_evidence(None)["traits"] == {}
    assert sanitize_evidence("hello")["traits"] == {}
    assert sanitize_evidence({"traits": [1, 2]})["traits"] == {}
    assert sanitize_evidence({"software": "steam"})["software"] == []


def test_merge_applies_later_rounds_and_unions_software():
    merged = merge_evidence([
        {"traits": {"tinker": 0.2}, "software": ["steam"], "notes": ["第一轮"]},
        {"traits": {"tinker": 0.9}, "software": ["docker", "steam"], "notes": ["第二轮"]},
    ])
    assert merged["traits"]["tinker"] == 0.9
    assert merged["software"] == ["steam", "docker"]
    assert merged["notes"] == ["第一轮", "第二轮"]


def test_merge_caps_software_and_weights():
    merged = merge_evidence([
        {"dimensionWeights": {"gaming": 0.8}},
        {"dimensionWeights": {"gaming": 0.8}},
    ])
    # Weights accumulate but never exceed 1.
    assert merged["dimensionWeights"]["gaming"] == 1.0


def test_interview_changes_the_ranking(base_payload):
    plain = build_result(base_payload())
    steered = build_result(base_payload(interview=[{
        "traits": {"gaming_intensity": 0.95, "tinker": 0.9, "tech_level": 0.85},
        "device": "desktop",
        "dimensionWeights": {"gaming": 0.9, "customization": 0.8},
        "dimensionTargets": {"gaming": 95, "customization": 90},
        "software": ["steam", "aaa-games"],
        "notes": ["用户说每天都在打游戏"],
    }]))

    assert plain["top"][0]["name"] != steered["top"][0]["name"]
    assert steered["evidenceNotes"] == ["用户说每天都在打游戏"]
    gaming = {"SteamOS", "Bazzite", "Nobara", "CachyOS", "Windows 11", "Pop!_OS"}
    assert gaming & {entry["name"] for entry in steered["top"]}


def test_interview_is_ignored_when_absent(base_payload):
    without = build_result(base_payload())
    with_empty = build_result(base_payload(interview=[]))
    assert [e["id"] for e in without["top"]] == [e["id"] for e in with_empty["top"]]
    assert without["evidenceNotes"] == []


def test_interview_endpoint_requires_a_key(client, base_payload):
    response = client.post("/api/interview", json={"text": "我想装机"})
    assert response.status_code == 503


def test_interview_endpoint_validates_input(client, app, monkeypatch):
    from app.services import llm

    app.config["LLM_API_KEY"] = "test-key"
    assert client.post("/api/interview", json={}).status_code == 400
    assert client.post("/api/interview", json={"text": "   "}).status_code == 400


def test_interview_endpoint_returns_sanitized_evidence(client, app, monkeypatch):
    from app.services import llm

    app.config["LLM_API_KEY"] = "test-key"

    def fake_chat(messages, **kwargs):
        return """```json
        {"traits": {"gaming_intensity": 0.9, "bogus": 1},
         "device": "laptop",
         "dimensionWeights": {"gaming": 0.8},
         "dimensionTargets": {"gaming": 92},
         "software": ["steam", "made-up"],
         "notes": ["爱打游戏"],
         "followups": ["你平时玩什么类型的游戏？", "在意续航吗？"]}
        ```"""

    monkeypatch.setattr(llm, "_chat", fake_chat)

    body = client.post("/api/interview", json={"text": "我主要打游戏"}).get_json()
    assert body["evidence"]["device"] == "laptop"
    assert "bogus" not in body["evidence"]["traits"]
    assert body["evidence"]["software"] == ["steam"]
    assert len(body["followups"]) == 2


def test_interview_endpoint_reports_bad_json(client, app, monkeypatch):
    from app.services import llm

    app.config["LLM_API_KEY"] = "test-key"
    monkeypatch.setattr(llm, "_chat", lambda *a, **k: "抱歉，我无法回答。")

    response = client.post("/api/interview", json={"text": "随便说说"})
    assert response.status_code == 502
    assert "JSON" in response.get_json()["error"]


def test_evidence_reaches_the_assessment(client, base_payload):
    plain = client.post("/api/assess", json=base_payload()).get_json()
    payload = base_payload(interview=[{
        "traits": {"gaming_intensity": 0.9},
        "dimensionWeights": {"gaming": 0.9},
        "dimensionTargets": {"gaming": 95},
        "notes": ["来自访谈"],
    }])
    body = client.post("/api/assess", json=payload).get_json()
    assert body["evidenceNotes"] == ["来自访谈"]
    # The interview must raise how much the gaming dimension matters.
    assert body["profile"]["weights"]["gaming"] > plain["profile"]["weights"]["gaming"]
