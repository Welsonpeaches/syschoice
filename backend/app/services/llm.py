"""Optional, OpenAI-compatible commentary on a finished assessment.

This is deliberately a thin layer: the deterministic scorer decides the
ranking, and the model only turns that outcome into prose. It never picks a
system and never sees or invents scores.
"""

import json
import urllib.error
import urllib.request

from flask import current_app

from ..config import Config

SYSTEM_PROMPT = (
    "你是一个克制、诚实的操作系统选型顾问。你会拿到一份已经算好的测评结果，"
    "你的任务只是把它讲清楚，不能改变排名，也不能编造没有给出的数据。"
    "用简体中文回答，120 到 180 字，直接写结论，不要用标题、列表或 markdown 标记。"
)


def is_enabled() -> bool:
    return bool(_cfg("LLM_API_KEY"))


def _cfg(name):
    try:
        return current_app.config.get(name, getattr(Config, name))
    except Exception:
        return getattr(Config, name, None)


def build_prompt(result):
    """Ground the model in exactly what the scorer produced."""
    profile = result.get("profile", {})
    traits = profile.get("traits", {})
    top = result.get("top", [])

    wanted = sorted(
        profile.get("weights", {}).items(), key=lambda item: -item[1]
    )[:4]
    dims = profile.get("dims", {})

    lines = [
        "用户最看重的维度（按权重从高到低）与期望值：",
        "、".join(f"{name}={round(dims.get(name, 0))}" for name, _ in wanted),
        "",
        "用户画像特征：",
        f"设备={traits.get('device')}，技术水平={round(float(traits.get('tech_level', 0)), 2)}，"
        f"折腾意愿={round(float(traits.get('tinker', 0)), 2)}，"
        f"游戏强度={round(float(traits.get('gaming_intensity', 0)), 2)}，"
        f"办公需求={round(float(traits.get('office_need', 0)), 2)}，"
        f"隐私需求={round(float(traits.get('privacy_need', 0)), 2)}",
        "",
        "排名前三位（已经算好，不要改动顺序）：",
    ]
    for entry in top:
        lines.append(
            f"{entry['rank']}. {entry['name']}（{entry['familyLabel']}，"
            f"匹配度 {entry['match']}%，血统：{entry.get('lineage') or '独立'}）"
        )
        for note in entry.get("notes", [])[:3]:
            lines.append(f"   - {note['text']}")

    lines += [
        "",
        "请说明：首选为什么适合这个人、它最需要注意的一点是什么。"
        "如果第二、三名与首选差距很小，也要提一句。",
    ]
    return "\n".join(lines)


def _chat(messages):
    base_url = str(_cfg("LLM_BASE_URL")).rstrip("/")
    payload = {
        "model": _cfg("LLM_MODEL"),
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 500,
    }
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_cfg('LLM_API_KEY')}",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=_cfg("LLM_TIMEOUT")) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"].strip()


def generate_insight(result):
    """Returns the prose summary, or raises RuntimeError with a friendly message."""
    if not is_enabled():
        raise RuntimeError("未配置 LLM API Key，本功能未启用。")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_prompt(result)},
    ]
    try:
        return _chat(messages)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "ignore")[:200]
        raise RuntimeError(f"模型接口返回 {exc.code}：{detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"无法连接模型接口：{exc.reason}") from exc
    except (KeyError, IndexError, ValueError) as exc:
        raise RuntimeError("模型返回的内容无法解析。") from exc
