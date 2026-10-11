"""Thin SQLite layer. No ORM: the schema is small and read patterns are simple."""

import json
import sqlite3
from pathlib import Path

from .config import Config


def _db_path(db_path=None):
    """Prefer an explicit path, then the active app config, then the default."""
    if db_path:
        return db_path
    try:
        from flask import current_app

        return current_app.config["DB_PATH"]
    except Exception:
        return Config.DB_PATH


SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id              TEXT PRIMARY KEY,
    share_code      TEXT NOT NULL UNIQUE,
    quiz_version    TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    duration_ms     INTEGER,
    ip_hash         TEXT,
    user_agent      TEXT,
    hardware_json   TEXT NOT NULL,
    answers_json    TEXT NOT NULL,
    result_json     TEXT NOT NULL,
    top1_id         TEXT,
    top1_name       TEXT,
    top1_family     TEXT,
    top1_group      TEXT,
    top1_match      REAL,
    top_json        TEXT
);

CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions (created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_top1_family ON sessions (top1_family);
CREATE INDEX IF NOT EXISTS idx_sessions_top1_id ON sessions (top1_id);
"""


def connect(db_path=None):
    path = _db_path(db_path)
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path=None):
    conn = connect(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def insert_session(payload, db_path=None):
    conn = connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO sessions (
                id, share_code, quiz_version, created_at, duration_ms,
                ip_hash, user_agent, hardware_json, answers_json, result_json,
                top1_id, top1_name, top1_family, top1_group, top1_match, top_json
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                payload["id"],
                payload["share_code"],
                payload["quiz_version"],
                payload["created_at"],
                payload.get("duration_ms"),
                payload.get("ip_hash"),
                payload.get("user_agent"),
                json.dumps(payload["hardware"], ensure_ascii=False),
                json.dumps(payload["answers"], ensure_ascii=False),
                json.dumps(payload["result"], ensure_ascii=False),
                payload["top1_id"],
                payload["top1_name"],
                payload["top1_family"],
                payload["top1_group"],
                payload["top1_match"],
                json.dumps(payload["top"], ensure_ascii=False),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_by_share_code(code, db_path=None):
    conn = connect(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM sessions WHERE share_code = ?", (code,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def list_sessions(page=1, page_size=20, query=None, db_path=None):
    conn = connect(db_path)
    try:
        where, params = "", []
        if query:
            where = "WHERE share_code LIKE ? OR top1_name LIKE ? OR top1_family LIKE ?"
            like = f"%{query}%"
            params = [like, like, like]
        total = conn.execute(
            f"SELECT COUNT(*) FROM sessions {where}", params
        ).fetchone()[0]
        offset = max(0, (page - 1) * page_size)
        rows = conn.execute(
            f"""
            SELECT id, share_code, quiz_version, created_at, duration_ms,
                   top1_name, top1_family, top1_group, top1_match
            FROM sessions {where}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            [*params, page_size, offset],
        ).fetchall()
        return total, [dict(r) for r in rows]
    finally:
        conn.close()


def all_sessions_for_export(db_path=None):
    conn = connect(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def stats(db_path=None, days=14):
    """Aggregate numbers for the public stats page."""
    conn = connect(db_path)
    try:
        total = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]

        by_family = [
            {"family": row["top1_family"], "count": row["count"]}
            for row in conn.execute(
                """
                SELECT top1_family, COUNT(*) AS count
                FROM sessions
                WHERE top1_family IS NOT NULL
                GROUP BY top1_family
                ORDER BY count DESC
                """
            ).fetchall()
        ]

        top_candidates = [
            {
                "id": row["top1_id"],
                "name": row["top1_name"],
                "family": row["top1_family"],
                "group": row["top1_group"],
                "count": row["count"],
                "averageMatch": round(row["avg_match"] or 0, 1),
            }
            for row in conn.execute(
                """
                SELECT top1_id, top1_name, top1_family, top1_group,
                       COUNT(*) AS count, AVG(top1_match) AS avg_match
                FROM sessions
                WHERE top1_id IS NOT NULL
                GROUP BY top1_id
                ORDER BY count DESC, avg_match DESC
                LIMIT 12
                """
            ).fetchall()
        ]

        daily = [
            {"date": row["day"], "count": row["count"]}
            for row in conn.execute(
                """
                SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS count
                FROM sessions
                GROUP BY day
                ORDER BY day DESC
                LIMIT ?
                """,
                (days,),
            ).fetchall()
        ]
        daily.reverse()

        average_match = conn.execute(
            "SELECT AVG(top1_match) FROM sessions WHERE top1_match IS NOT NULL"
        ).fetchone()[0]

        distinct_families = conn.execute(
            "SELECT COUNT(DISTINCT top1_family) FROM sessions"
        ).fetchone()[0]

        return {
            "total": total,
            "averageMatch": round(average_match or 0, 1),
            "familyCount": distinct_families,
            "byFamily": by_family,
            "topCandidates": top_candidates,
            "daily": daily,
        }
    finally:
        conn.close()
