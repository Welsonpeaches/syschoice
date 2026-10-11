"""Deterministic, explainable scoring.

User side  : questionnaire + CLI quiz + scenario + software answers become
             a desired vector u[d], a per-dimension importance w[d] and traits.
Candidate  : nine 0-100 dimension scores, tags and gates.
Final score: weighted dimension similarity, multiplied by hard penalties
             (gates + required-software compatibility) and lifted by tag bonuses.
"""

from ..data.candidates import CANDIDATES, FAMILY_COLORS, FAMILY_LABELS
from ..data.cli_quiz import CLI_QUESTIONS_MAP
from ..data.dimensions import DIMENSION_IDS
from ..data.questions import QUESTIONS, QUESTION_MAP, TRAIT_DEFAULTS
from ..data.scenarios import SCENARIO_MAP
from ..data.software import SOFTWARE_MAP
from .evidence import merge_evidence

# How usable a family is for a piece of software, on a 0-1 scale.
COMPAT_SCORE = {
    "native": 1.0,
    "good": 0.88,
    "web": 0.72,
    "partial": 0.5,
    "none": 0.08,
}

# Floors stop a dimension from dropping out entirely, applied before the final
# normalisation so dimensions the user actually cares about still dominate.
MIN_DIM_WEIGHT = 0.03

# An option may state a desired value for a dimension without declaring how much
# it matters; that gets a light weight instead of silently skewing the average.
DEFAULT_D_VALUE_WEIGHT = 0.15

# When the interview states a target without stating how much it matters.
EVIDENCE_TARGET_WEIGHT = 0.45


def _blank_vector():
    return {d: 0.0 for d in DIMENSION_IDS}


def _selected_options(question, answer):
    """Return the option dicts the user picked for one question."""
    if answer is None:
        return []
    options = question.get("options", [])
    if question["type"] == "multi":
        chosen = answer if isinstance(answer, list) else [answer]
        by_id = {o["id"]: o for o in options}
        return [by_id[c] for c in chosen if c in by_id]
    by_id = {o["id"]: o for o in options}
    key = str(answer)
    return [by_id[key]] if key in by_id else []


def _apply_option(option, weights, desired, traits):
    """Importance and target must travel together.

    An option that only says "this dimension matters" without saying what the
    user wants would otherwise drag the desired value toward zero, so a
    dimension only counts once the option states a target for it.
    """
    option_weights = option.get("w") or {}
    for dim, value in (option.get("d") or {}).items():
        dim_weight = float(option_weights.get(dim, DEFAULT_D_VALUE_WEIGHT))
        weights[dim] = weights.get(dim, 0.0) + dim_weight
        desired[dim] = desired.get(dim, 0.0) + dim_weight * float(value)
    for trait, value in (option.get("traits") or {}).items():
        if isinstance(value, (int, float)) and isinstance(TRAIT_DEFAULTS.get(trait), (int, float)):
            traits[trait] = max(traits.get(trait, 0.0), float(value))
        else:
            traits[trait] = value


def _cli_score(cli_answers):
    if not cli_answers:
        return None, 0
    correct = 0
    answered = 0
    for qid, choice in cli_answers.items():
        question = CLI_QUESTIONS_MAP.get(qid)
        if not question:
            continue
        answered += 1
        if choice == question["answer"]:
            correct += 1
    if answered == 0:
        return None, 0
    return correct / answered, answered


def build_profile(payload):
    """Turn raw answers into a user vector, dimension weights and traits."""
    answers = payload.get("answers") or {}
    scenarios = payload.get("scenarios") or {}
    traits = dict(TRAIT_DEFAULTS)
    weights = _blank_vector()
    desired_sum = _blank_vector()

    for question in QUESTIONS:
        for option in _selected_options(question, answers.get(question["id"])):
            _apply_option(option, weights, desired_sum, traits)

    for qid, answer in scenarios.items():
        question = SCENARIO_MAP.get(qid)
        if not question:
            continue
        for option in _selected_options(question, answer):
            _apply_option(option, weights, desired_sum, traits)

    # CLI quiz nudges the technical level rather than a dimension.
    ratio, answered = _cli_score(payload.get("cli") or {})
    if ratio is not None:
        traits["cli_score"] = round(ratio, 3)
        traits["cli_answered"] = answered
        traits["tech_level"] = min(1.0, 0.55 * traits.get("tech_level", 0.4) + 0.45 * ratio)
        if ratio >= 0.8:
            traits["tinker"] = min(1.0, traits.get("tinker", 0.4) + 0.15)

    apply_hardware(traits, weights, payload.get("hardware") or {})

    evidence = merge_evidence(payload.get("interview"))
    apply_evidence(evidence, weights, desired_sum, traits)

    user_vector = {}
    for dim in DIMENSION_IDS:
        total_weight = weights[dim]
        user_vector[dim] = round(desired_sum[dim] / total_weight, 1) if total_weight > 0 else 50.0

    # Raise every dimension to the floor first, then normalise to sum to 1.
    raw_total = sum(weights.values()) or 1.0
    floored = {
        dim: max(weights[dim] / raw_total, MIN_DIM_WEIGHT) for dim in DIMENSION_IDS
    }
    floor_total = sum(floored.values()) or 1.0
    final_weights = {dim: round(floored[dim] / floor_total, 4) for dim in DIMENSION_IDS}

    return {
        "dims": user_vector,
        "weights": final_weights,
        "traits": traits,
        "evidence": evidence,
    }


def apply_hardware(traits, weights, hardware):
    """Hardware probe only ever *adds* signal; unknown fields are ignored."""
    if not isinstance(hardware, dict) or not hardware:
        return

    memory = hardware.get("memoryGB")
    if isinstance(memory, (int, float)) and memory > 0:
        if memory <= 4:
            traits["hardware_weak"] = max(traits.get("hardware_weak", 0.0), 0.9)
            weights["lightweight"] += 0.7
        elif memory <= 8:
            traits["hardware_weak"] = max(traits.get("hardware_weak", 0.0), 0.45)
            weights["lightweight"] += 0.3
        else:
            traits["hardware_weak"] = max(traits.get("hardware_weak", 0.0), 0.15)

    cores = hardware.get("cores")
    if isinstance(cores, (int, float)) and 0 < cores <= 2:
        traits["hardware_weak"] = min(1.0, traits.get("hardware_weak", 0.0) + 0.25)
        weights["lightweight"] += 0.2

    platform = str(hardware.get("platform") or "")
    if "Mac" in platform:
        traits["apple_ecosystem"] = max(traits.get("apple_ecosystem", 0.0), 0.6)


def apply_evidence(evidence, weights, desired, traits):
    """Fold interview evidence into the model the questionnaire builds.

    Traits come from the person's own words, so they override form defaults;
    dimension importance stacks additively, exactly like answers do.
    """
    if not evidence:
        return

    for key, value in evidence["traits"].items():
        traits[key] = value
    if evidence["device"]:
        traits["device"] = evidence["device"]

    for dim, target in evidence["dimensionTargets"].items():
        dim_weight = evidence["dimensionWeights"].get(dim, EVIDENCE_TARGET_WEIGHT)
        weights[dim] = weights.get(dim, 0.0) + dim_weight
        desired[dim] = desired.get(dim, 0.0) + dim_weight * target


def _gate_multiplier(candidate, traits):
    multiplier = 1.0
    triggered = []
    for gate in candidate.get("gates") or []:
        penalty = float(gate.get("penalty", 1.0))
        hit = False
        if "device_any" in gate:
            hit = traits.get("device") not in gate["device_any"]
        elif "trait" in gate:
            value = traits.get(gate["trait"], 0.0)
            op = gate.get("op", ">=")
            if not isinstance(value, (int, float)):
                value = 0.0
            if op == ">=":
                hit = value >= float(gate.get("value", 0))
            else:
                hit = value < float(gate.get("value", 0))
        if hit:
            multiplier *= penalty
            triggered.append(gate)
    return multiplier, triggered


def _software_penalty(family, required_software):
    """Returns (multiplier, blocking, weak) for a family given required software."""
    if not required_software:
        return 1.0, [], []
    scores = []
    blocking, weak = [], []
    for sid in required_software:
        item = SOFTWARE_MAP.get(sid)
        if not item:
            continue
        level = item["compat"].get(family, "none")
        scores.append(COMPAT_SCORE.get(level, 0.08))
        if level == "none":
            blocking.append({"id": sid, "name": item["name"], "level": level})
        elif level == "partial":
            weak.append({"id": sid, "name": item["name"], "level": level})
    if not scores:
        return 1.0, [], []
    average = sum(scores) / len(scores)
    # Even a fully blocked family keeps a floor so the ranking stays readable.
    return 0.22 + 0.78 * average, blocking, weak


def _tag_bonus(candidate, traits):
    bonus = 0.0
    tags = set(candidate.get("tags") or [])
    if "gaming" in tags and traits.get("gaming_intensity", 0) >= 0.6:
        bonus += 3.0
    if "beginner" in tags and traits.get("tech_level", 1) <= 0.35:
        bonus += 4.0
    if {"lightweight", "old-hardware"} & tags and traits.get("hardware_weak", 0) >= 0.6:
        bonus += 3.0
    if "security" in tags and traits.get("security_interest", 0) >= 0.6:
        bonus += 3.0
    if "server" in tags and traits.get("server_interest", 0) >= 0.6:
        bonus += 3.0
    if "rolling" in tags and traits.get("stability_pref", 1) <= 0.3:
        bonus += 2.0
    if "windows-like" in tags and traits.get("tech_level", 1) <= 0.4:
        bonus += 2.0
    if "china" in tags and traits.get("office_need", 0) >= 0.7:
        bonus += 1.5
    return min(bonus, 9.0)


def score_candidate(candidate, profile, required_software):
    user = profile["dims"]
    weights = profile["weights"]
    traits = profile["traits"]

    weight_total = sum(weights.values()) or 1.0
    similarity = 0.0
    for dim in DIMENSION_IDS:
        gap = abs(user[dim] - candidate["dims"][dim]) / 100.0
        similarity += weights[dim] * (1.0 - gap)
    base = similarity / weight_total

    software_multiplier, blocking, weak = _software_penalty(
        candidate["family"], required_software
    )
    gate_multiplier, gates = _gate_multiplier(candidate, traits)

    score = base * software_multiplier * gate_multiplier * 100.0
    score += _tag_bonus(candidate, traits)
    score = max(0.0, min(100.0, score))

    return {
        "score": score,
        "base": round(base * 100, 2),
        "softwareMultiplier": round(software_multiplier, 3),
        "gateMultiplier": round(gate_multiplier, 3),
        "blockingSoftware": blocking,
        "weakSoftware": weak,
        "triggeredGates": gates,
    }


def rank_candidates(profile, required_software):
    results = []
    for candidate in CANDIDATES:
        detail = score_candidate(candidate, profile, required_software)
        results.append((candidate, detail))
    results.sort(key=lambda pair: (-pair[1]["score"], pair[0]["name"]))
    return results


def family_summary(ranked):
    """Average score per family, plus how many candidates each family has."""
    buckets = {}
    for candidate, detail in ranked:
        bucket = buckets.setdefault(
            candidate["family"],
            {"family": candidate["family"], "label": FAMILY_LABELS[candidate["family"]],
             "color": FAMILY_COLORS[candidate["family"]], "total": 0.0, "count": 0, "best": None},
        )
        bucket["total"] += detail["score"]
        bucket["count"] += 1
        if bucket["best"] is None or detail["score"] > bucket["best"]["match"]:
            bucket["best"] = {"id": candidate["id"], "name": candidate["name"],
                              "match": round(detail["score"], 1)}

    summary = []
    for bucket in buckets.values():
        summary.append({
            "family": bucket["family"],
            "label": bucket["label"],
            "color": bucket["color"],
            "average": round(bucket["total"] / bucket["count"], 1),
            "count": bucket["count"],
            "best": bucket["best"],
        })
    summary.sort(key=lambda item: -item["average"])
    return summary


def build_result(payload):
    """Full assessment: profile, ranked candidates, radar data and summary."""
    profile = build_profile(payload)
    required_software = [s for s in (payload.get("software") or []) if s in SOFTWARE_MAP]
    required_software = [s for s in required_software if s != "none"]

    ranked = rank_candidates(profile, required_software)

    from .reasons import build_notes  # local import keeps the module graph flat

    entries = []
    for rank, (candidate, detail) in enumerate(ranked, start=1):
        entries.append({
            "rank": rank,
            "id": candidate["id"],
            "name": candidate["name"],
            "family": candidate["family"],
            "familyLabel": FAMILY_LABELS[candidate["family"]],
            "familyColor": FAMILY_COLORS[candidate["family"]],
            "group": candidate["group"],
            "color": candidate["color"],
            "monogram": candidate["monogram"],
            "lineage": candidate["lineage"],
            "blurb": candidate["blurb"],
            "match": round(detail["score"], 1),
            "pros": candidate["pros"],
            "cons": candidate["cons"],
            "dims": candidate["dims"],
            "notes": build_notes(candidate, detail, profile),
        })

    return {
        "radar": {
            "labels": [d for d in DIMENSION_IDS],
            "values": [profile["dims"][d] for d in DIMENSION_IDS],
        },
        "profile": profile,
        "evidenceNotes": profile["evidence"]["notes"],
        "top": entries[:3],
        "full": entries,
        "families": family_summary(ranked),
        "requiredSoftware": required_software,
    }
