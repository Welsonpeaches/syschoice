"""Optional, OpenAI-compatible commentary on a finished assessment.

This is deliberately a thin layer: the deterministic scorer decides the
ranking, and the model only turns that outcome into prose. It never picks a
system and never sees or invents scores.
"""

import json
import re
import urllib.error
import urllib.request

from flask import current_app

from ..config import Config
from .evidence import evidence_prompt_blocks

SYSTEM_PROMPT = (
    "你是一个克制、诚实的操作系统选型顾问。你会拿到一份已经算好的测评结果，"
    "你的任务只是把它讲清楚，不能改变排名，也不能编造没有给出的数据。"
    "用简体中文回答，120 到 180 字，直接写结论，不要用标题、列表或 markdown 标记。"
)

INTERVIEW_SYSTEM_PROMPT = """你是一个操作系统选型顾问，正在对用户做需求访谈。
你的任务只有两件：把用户的原话翻译成结构化证据，以及找出最该追问的问题。
你不负责打分，也不要下结论说该用哪个系统。

只允许使用下面给定的取值，不允许发明新的键或新的取值：
- traits 键：{traits}
  这些是 0 到 1 的强度，1 表示非常强烈。
- 维度键：{dimensions}
  dimensionTargets 是 0 到 100 的期望值；dimensionWeights 是 0 到 1 的重要程度。
  两者必须成对出现，只写其中一个不会生效。
- device 取值：{devices}
- software 取值（只能填 id）：{software}

只输出一个 JSON 对象，不要输出任何解释、前后缀或 markdown 代码块。结构如下：
{{
  "traits": {{"gaming_intensity": 0.8}},
  "device": "laptop",
  "dimensionWeights": {{"gaming": 0.9}},
  "dimensionTargets": {{"gaming": 95}},
  "software": ["steam"],
  "notes": ["用户提到每天要用 Steam 打两小时游戏"]
}}

规则：
1. 用户没有提到的内容一律不要输出，宁可少写也不要猜。
2. notes 用一句中文记录你判断的依据，最多 4 条，每条不超过 40 字。
3. followups 里放 2 到 3 个最可能改变推荐结果的问题，用中文，直接问，不要编号。
4. 输出必须是合法 JSON，所有键都要出现，没有内容就用空对象或空数组。"""


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


def _chat(messages, temperature=0.5, max_tokens=500):
    base_url = str(_cfg("LLM_BASE_URL")).rstrip("/")
    payload = {
        "model": _cfg("LLM_MODEL"),
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
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


def _extract_json(text):
    """Models sometimes wrap JSON in prose or fences; pull out the object."""
    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*(.+?)```", cleaned, re.S)
    if fence:
        cleaned = fence.group(1).strip()
    if not cleaned.startswith("{"):
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("no JSON object in response")
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def run_interview(text, history=None):
    """Turn free-form answers into raw evidence plus the next questions.

    Returns the model's dict untouched; the caller sanitises it against the
    whitelists before anything reaches the scorer.
    """
    if not is_enabled():
        raise RuntimeError("未配置 LLM API Key，本功能未启用。")

    blocks = evidence_prompt_blocks()
    system = INTERVIEW_SYSTEM_PROMPT.format(**blocks)

    transcript = []
    for turn in history or []:
        question = str(turn.get("question", "")).strip()
        answer = str(turn.get("answer", "")).strip()
        if question and answer:
            transcript.append(f"问：{question}\n答：{answer}")

    user_content = f"用户描述：\n{text.strip()}"
    if transcript:
        user_content += "\n\n追问与回答：\n" + "\n\n".join(transcript)
    user_content += '\n\n请输出 JSON，其中 followups 字段是接下来要问的问题。'

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]
    try:
        raw = _chat(messages, temperature=0.2, max_tokens=900)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "ignore")[:200]
        raise RuntimeError(f"模型接口返回 {exc.code}：{detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"无法连接模型接口：{exc.reason}") from exc

    try:
        parsed = _extract_json(raw)
    except (ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError("模型返回的不是合法 JSON。") from exc

    followups = [
        item.strip()[:120]
        for item in (parsed.get("followups") or [])
        if isinstance(item, str) and item.strip()
    ][:3]
    parsed["followups"] = followups
    return parsed
