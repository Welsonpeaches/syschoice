from app.services.scoring import build_profile, build_result


def _top_names(result, count=3):
    # `top` is truncated to three; the ranked list lives in `full`.
    return [entry["name"] for entry in result["full"][:count]]


def test_scoring_is_deterministic(base_payload):
    payload = base_payload(software=["steam", "aaa-games"], cli={"cli1": "a"})
    first = build_result(payload)
    second = build_result(payload)
    assert _top_names(first) == _top_names(second)
    assert first["top"][0]["match"] == second["top"][0]["match"]


def test_user_vector_stays_within_bounds(base_payload):
    profile = build_profile(base_payload(answers={"B3": 5, "A1": "old-machine"}))
    for dim, value in profile["dims"].items():
        assert 0 <= value <= 100, dim
    assert abs(sum(profile["weights"].values()) - 1.0) < 0.01


def test_macos_is_penalised_without_apple_hardware(base_payload):
    on_desktop = build_result(base_payload(
        answers={"A1": "desktop", "A6": "many", "A2": ["design"], "C1": ["adobe"]},
        software=["photoshop"],
    ))
    on_apple = build_result(base_payload(
        answers={"A1": "apple", "A6": "many", "A2": ["design"], "C1": ["adobe"]},
        software=["photoshop"],
    ))
    desktop_scores = {e["id"]: e["match"] for e in on_desktop["full"]}
    apple_scores = {e["id"]: e["match"] for e in on_apple["full"]}
    assert apple_scores["macos"] > desktop_scores["macos"]
    assert on_apple["top"][0]["id"] == "macos"


def test_required_windows_only_software_lifts_windows(base_payload):
    result = build_result(base_payload(
        answers={"C1": ["office-suite", "bank"], "C3": "must", "A2": ["office"]},
        software=["microsoft-office", "bank-usbkey", "gov-app"],
    ))
    assert result["top"][0]["id"] == "windows-11"
    blocking = result["top"][0]["notes"]
    assert result["top"][0]["family"] == "windows"


def test_security_profile_surfaces_security_focused_systems(base_payload):
    result = build_result(base_payload(
        answers={"A1": "desktop", "A2": ["study", "server"], "A4": "self-pro",
                 "B1": "search", "B2": "expert", "B3": 5, "B4": "control",
                 "B5": "yes", "B6": "fix", "C1": ["security"], "C2": ["none"],
                 "D1": "monthly", "D2": "ok", "D4": "newest", "D5": "often"},
        cli={f"cli{i}": "a" for i in range(1, 7)},
    ))
    names = _top_names(result, 3)
    focused = {"Kali Linux", "Parrot OS", "Qubes OS", "OpenBSD", "FreeBSD", "Tails"}
    assert focused & set(names), names


def test_old_weak_machine_prefers_lightweight(base_payload):
    result = build_result(base_payload(
        answers={"A1": "old-machine", "A2": ["web"], "B2": "never", "B3": 1,
                 "C4": "4", "C6": "8y", "D1": "rare", "D2": "no", "E3": "free"},
        hardware={"memoryGB": 4, "cores": 2},
    ))
    names = _top_names(result, 8)
    light = {"Lubuntu", "MX Linux", "antiX", "Xubuntu", "Puppy Linux", "Bodhi Linux",
             "Linux Lite", "Ubuntu MATE", "Peppermint OS", "SparkyLinux"}
    assert len(light & set(names)) >= 4, names


def test_family_summary_covers_every_family(base_payload):
    result = build_result(base_payload())
    families = {item["family"] for item in result["families"]}
    assert families == {"windows", "macos", "linux", "bsd"}
    assert len(result["full"]) == 72


def test_result_entries_carry_lineage_and_notes(base_payload):
    result = build_result(base_payload())
    linux_entries = [e for e in result["full"] if e["family"] == "linux"]
    assert linux_entries
    for entry in linux_entries:
        assert entry["lineage"].strip()
        assert entry["notes"]
