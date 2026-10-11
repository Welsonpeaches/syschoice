"""Public endpoints: quiz definition, catalog, assessment, result and stats."""

import hashlib
import json
import secrets
import time
from collections import defaultdict, deque
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request

from ..config import Config
from ..data.candidates import CANDIDATES, FAMILY_COLORS, FAMILY_LABELS, GROUP_ORDER
from ..data.cli_quiz import CLI_QUESTIONS
from ..data.dimensions import (
    DIMENSIONS,
    DIMENSION_IDS,
    DIMENSION_LABELS,
    DIMENSION_SHORT,
)
from ..data.questions import QUESTIONS, SECTIONS
from ..data.scenarios import SCENARIO_QUESTIONS
from ..data.software import CATEGORIES, SOFTWARE
from ..db import (
    get_by_share_code,
    get_feedback,
    insert_feedback,
    insert_session,
    set_insight,
    stats,
)
from ..services import llm
from ..services.scoring import build_result

public_bp = Blueprint("public", __name__, url_prefix="/api")

# Simple in-memory per-IP throttle. Good enough for a single-process deployment.
_HITS = defaultdict(deque)


def _client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _hash_ip(ip):
    salted = f"{Config.SECRET_KEY}:{ip}".encode("utf-8")
    return hashlib.sha256(salted).hexdigest()[:32]


def _rate_limited(ip):
    window = current_app.config.get("RATE_LIMIT_WINDOW_SECONDS", Config.RATE_LIMIT_WINDOW_SECONDS)
    limit = current_app.config.get("RATE_LIMIT_MAX_REQUESTS", Config.RATE_LIMIT_MAX_REQUESTS)
    now = time.time()
    bucket = _HITS[ip]
    while bucket and now - bucket[0] > window:
        bucket.popleft()
    if len(bucket) >= limit:
        return True
    bucket.append(now)
    return False


def _new_share_code():
    return secrets.token_hex(4)


@public_bp.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "quizVersion": Config.QUIZ_VERSION,
        "candidates": len(CANDIDATES),
        "llmEnabled": llm.is_enabled(),
    })


@public_bp.get("/quiz")
def quiz():
    return jsonify({
        "version": Config.QUIZ_VERSION,
        "sections": SECTIONS,
        "questions": QUESTIONS,
        "dimensions": [
            {"id": d[0], "label": d[1], "description": d[2], "short": DIMENSION_SHORT[d[0]]}
            for d in DIMENSIONS
        ],
    })


@public_bp.get("/catalog")
def catalog():
    # Answers are stripped so the client can never read the key.
    cli = [
        {"id": q["id"], "prompt": q["prompt"], "title": q["title"], "options": q["options"]}
        for q in CLI_QUESTIONS
    ]
    return jsonify({
        "software": SOFTWARE,
        "softwareCategories": [{"id": c[0], "label": c[1]} for c in CATEGORIES],
        "scenarios": SCENARIO_QUESTIONS,
        "cli": cli,
        "dimensions": [
            {"id": d, "label": DIMENSION_LABELS[d], "short": DIMENSION_SHORT[d]}
            for d in DIMENSION_IDS
        ],
        "groups": GROUP_ORDER,
        "families": [
            {"id": f, "label": FAMILY_LABELS[f], "color": FAMILY_COLORS[f]}
            for f in ("windows", "macos", "linux", "bsd")
        ],
        "candidates": [
            {
                "id": c["id"],
                "name": c["name"],
                "family": c["family"],
                "group": c["group"],
                "color": c["color"],
                "monogram": c["monogram"],
                "lineage": c["lineage"],
                "blurb": c["blurb"],
            }
            for c in CANDIDATES
        ],
    })


def _clean_hardware(raw):
    """Keep only fields we model, and never trust client-supplied nonsense."""
    if not isinstance(raw, dict):
        return {}
    cleaned = {}
    for key in ("cores", "memoryGB", "devicePixelRatio"):
        value = raw.get(key)
        if isinstance(value, (int, float)) and 0 < value < 100000:
            cleaned[key] = value
    for key in ("gpu", "platform", "vendor", "source"):
        value = raw.get(key)
        if isinstance(value, str) and len(value) <= 200:
            cleaned[key] = value
    touch = raw.get("touchPoints")
    if isinstance(touch, (int, float)) and 0 <= touch < 100:
        cleaned["touchPoints"] = touch
    return cleaned


@public_bp.post("/assess")
def assess():
    ip = _client_ip()
    if _rate_limited(ip):
        return jsonify({"error": "请求过于频繁，请稍后再试。"}), 429

    body = request.get_json(silent=True) or {}
    if not isinstance(body.get("answers"), dict) or not body["answers"]:
        return jsonify({"error": "缺少问卷答案。"}), 400

    result = build_result({
        "answers": body.get("answers") or {},
        "scenarios": body.get("scenarios") or {},
        "cli": body.get("cli") or {},
        "software": body.get("software") or [],
        "hardware": body.get("hardware") or {},
    })

    hardware = _clean_hardware(body.get("hardware"))
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    top1 = result["top"][0] if result["top"] else None

    payload = {
        "id": secrets.token_hex(8),
        "share_code": _new_share_code(),
        "quiz_version": Config.QUIZ_VERSION,
        "created_at": created_at,
        "duration_ms": body.get("durationMs") if isinstance(body.get("durationMs"), int) else None,
        "ip_hash": _hash_ip(ip),
        "user_agent": (request.headers.get("User-Agent") or "")[:300],
        "hardware": hardware,
        "answers": {
            "answers": body.get("answers") or {},
            "scenarios": body.get("scenarios") or {},
            "cli": body.get("cli") or {},
            "software": result["requiredSoftware"],
        },
        "result": result,
        "top1_id": top1["id"] if top1 else None,
        "top1_name": top1["name"] if top1 else None,
        "top1_family": top1["family"] if top1 else None,
        "top1_group": top1["group"] if top1 else None,
        "top1_match": top1["match"] if top1 else None,
        "top": [
            {"id": e["id"], "name": e["name"], "family": e["family"], "match": e["match"]}
            for e in result["top"]
        ],
    }

    # Share codes are 8 hex chars; collisions are vanishingly rare but retry anyway.
    for _ in range(5):
        try:
            insert_session(payload)
            break
        except Exception:
            payload["share_code"] = _new_share_code()
    else:
        return jsonify({"error": "保存结果失败，请重试。"}), 500

    return jsonify({
        "sessionId": payload["id"],
        "shareCode": payload["share_code"],
        "createdAt": created_at,
        "quizVersion": Config.QUIZ_VERSION,
        # The client renders the optional commentary panel straight after
        # submitting, so the same flags the result endpoint exposes are needed.
        "llmEnabled": llm.is_enabled(),
        "insight": None,
        "insightModel": None,
        "feedback": None,
        **result,
    })


@public_bp.get("/result/<code>")
def result_by_code(code):
    row = get_by_share_code(code)
    if not row:
        return jsonify({"error": "没有找到这份结果。"}), 404
    result = json.loads(row["result_json"])
    return jsonify({
        "sessionId": row["id"],
        "shareCode": row["share_code"],
        "createdAt": row["created_at"],
        "quizVersion": row["quiz_version"],
        "llmEnabled": llm.is_enabled(),
        "insight": row["insight_text"],
        "insightModel": row["insight_model"],
        "feedback": get_feedback(code),
        **result,
    })


@public_bp.post("/result/<code>/insight")
def result_insight(code):
    """Generate (and cache) the optional LLM commentary for one result."""
    row = get_by_share_code(code)
    if not row:
        return jsonify({"error": "没有找到这份结果。"}), 404
    if not llm.is_enabled():
        return jsonify({"error": "服务端未配置 LLM API Key，本功能未启用。"}), 503
    if row["insight_text"]:
        return jsonify({
            "insight": row["insight_text"],
            "model": row["insight_model"],
            "cached": True,
        })

    try:
        text = llm.generate_insight(json.loads(row["result_json"]))
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 502

    model = current_app.config.get("LLM_MODEL", Config.LLM_MODEL)
    set_insight(code, text, model)
    return jsonify({"insight": text, "model": model, "cached": False})


@public_bp.post("/result/<code>/feedback")
def result_feedback(code):
    """Record which system the person actually went with, and how it went."""
    row = get_by_share_code(code)
    if not row:
        return jsonify({"error": "没有找到这份结果。"}), 404

    body = request.get_json(silent=True) or {}
    chosen_id = body.get("chosenId")
    chosen_id = chosen_id if isinstance(chosen_id, str) and chosen_id else None

    candidates = {c["id"]: c["name"] for c in CANDIDATES}
    if chosen_id and chosen_id not in candidates:
        return jsonify({"error": "未知的系统标识。"}), 400

    satisfaction = body.get("satisfaction")
    if satisfaction is not None:
        if not isinstance(satisfaction, int) or not 1 <= satisfaction <= 5:
            return jsonify({"error": "满意度需要是 1 到 5 的整数。"}), 400

    note = body.get("note")
    note = note.strip()[:500] if isinstance(note, str) else None

    if not chosen_id and satisfaction is None and not note:
        return jsonify({"error": "请至少填写一项反馈。"}), 400

    insert_feedback({
        "id": secrets.token_hex(8),
        "share_code": code,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "chosen_id": chosen_id,
        "chosen_name": candidates.get(chosen_id) if chosen_id else None,
        "satisfaction": satisfaction,
        "note": note,
        "ip_hash": _hash_ip(_client_ip()),
    })
    return jsonify({"ok": True, "feedback": get_feedback(code)})


@public_bp.get("/stats")
def public_stats():
    data = stats()
    data["familyLabels"] = FAMILY_LABELS
    data["familyColors"] = FAMILY_COLORS
    return jsonify(data)
