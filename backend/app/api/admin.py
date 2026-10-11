"""Token-protected admin endpoints: session list, detail and CSV export."""

import csv
import io
import json
import secrets

from flask import Blueprint, Response, current_app, jsonify, request

from ..config import Config
from ..db import all_sessions_for_export, list_sessions

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def _authorised():
    supplied = request.headers.get("X-Admin-Token", "")
    expected = current_app.config.get("ADMIN_TOKEN", Config.ADMIN_TOKEN)
    if not supplied or not expected:
        return False
    return secrets.compare_digest(supplied, expected)


@admin_bp.before_request
def _guard():
    if not _authorised():
        return jsonify({"error": "需要有效的管理令牌。"}), 401
    return None


@admin_bp.get("/sessions")
def sessions():
    page = max(1, request.args.get("page", 1, type=int))
    page_size = min(100, max(1, request.args.get("pageSize", 20, type=int)))
    query = (request.args.get("q") or "").strip() or None
    total, rows = list_sessions(page=page, page_size=page_size, query=query)
    return jsonify({
        "total": total,
        "page": page,
        "pageSize": page_size,
        "items": rows,
    })


@admin_bp.get("/sessions/<session_id>")
def session_detail(session_id):
    for row in all_sessions_for_export():
        if row["id"] == session_id:
            return jsonify({
                **row,
                "hardware": json.loads(row["hardware_json"]),
                "answers": json.loads(row["answers_json"]),
                "result": json.loads(row["result_json"]),
            })
    return jsonify({"error": "没有找到这条记录。"}), 404


CSV_COLUMNS = [
    "id", "share_code", "quiz_version", "created_at", "duration_ms",
    "top1_name", "top1_family", "top1_group", "top1_match",
    "top2_name", "top2_family", "top2_match",
    "top3_name", "top3_family", "top3_match",
    "hardware_json", "answers_json",
]


@admin_bp.get("/export.csv")
def export_csv():
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_COLUMNS)
    for row in all_sessions_for_export():
        top = json.loads(row["top_json"] or "[]")
        top = (top + [{}, {}, {}])[:3]
        writer.writerow([
            row["id"], row["share_code"], row["quiz_version"], row["created_at"],
            row["duration_ms"], row["top1_name"], row["top1_family"],
            row["top1_group"], row["top1_match"],
            top[0].get("name"), top[0].get("family"), top[0].get("match"),
            top[1].get("name"), top[1].get("family"), top[1].get("match"),
            top[2].get("name"), top[2].get("family"), top[2].get("match"),
            row["hardware_json"], row["answers_json"],
        ])
    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=syschoice-sessions.csv"},
    )
