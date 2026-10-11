"""Human-readable notes explaining why a candidate ranked where it did."""

from ..data.dimensions import DIMENSION_LABELS
from ..data.software import SOFTWARE_MAP

# Notes are ranked by how much the user cares about the dimension.
MAX_NOTES = 4


def _closeness(user_value, candidate_value):
    return 1.0 - abs(user_value - candidate_value) / 100.0


def build_notes(candidate, detail, profile):
    user = profile["dims"]
    weights = profile["weights"]
    notes = []

    # 1. Blocked required software is the most concrete reason to look elsewhere.
    for blocked in detail["blockingSoftware"][:2]:
        notes.append({
            "type": "mismatch",
            "text": f"你需要的「{blocked['name']}」在这个系统上没有可用的原生版本。",
        })

    # 2. Dimensions the user cares about where this candidate is far off.
    mismatches = []
    matches = []
    for dim, weight in weights.items():
        gap = user[dim] - candidate["dims"][dim]
        matches.append((weight * _closeness(user[dim], candidate["dims"][dim]), dim))
        if gap >= 18:
            mismatches.append((weight * gap, dim, gap))

    mismatches.sort(key=lambda item: -item[0])
    for _, dim, gap in mismatches:
        if len(notes) >= MAX_NOTES - 1:
            break
        notes.append({
            "type": "mismatch",
            "text": (
                f"在「{DIMENSION_LABELS[dim]}」上可能不够：你需要 {round(user[dim])} 分，"
                f"它大约是 {candidate['dims'][dim]} 分。"
            ),
        })

    # 3. Weak-but-usable software (Wine / partial ports) is worth flagging.
    for weak in detail["weakSoftware"][:1]:
        if len(notes) >= MAX_NOTES:
            break
        item = SOFTWARE_MAP.get(weak["id"])
        note = item["note"] if item else "需要额外配置或替代方案才能使用。"
        notes.append({"type": "mismatch", "text": f"「{weak['name']}」需要额外折腾：{note}"})

    # 4. Fill remaining space with the strongest genuine matches.
    matches.sort(key=lambda item: -item[0])
    for _, dim in matches:
        if len(notes) >= MAX_NOTES:
            break
        notes.append({
            "type": "match",
            "text": (
                f"「{DIMENSION_LABELS[dim]}」契合度高：你期望 {round(user[dim])} 分，"
                f"它能给到 {candidate['dims'][dim]} 分。"
            ),
        })

    return notes
