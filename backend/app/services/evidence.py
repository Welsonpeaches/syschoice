"""Structured evidence extracted from free-form interview answers.

The model never scores anything. It only fills in this shape, which is then
merged into the same trait / dimension model the questionnaire uses. Anything
the model invents outside these whitelists is dropped before it can reach the
scorer, so a bad completion degrades rather than corrupts.
"""

from ..data.candidates import CANDIDATES
from ..data.dimensions import DIMENSION_IDS
from ..data.questions import DEVICES, TRAIT_DEFAULTS
from ..data.software import SOFTWARE_MAP

MAX_SOFTWARE = 12
MAX_NOTES = 8
MAX_NOTE_LENGTH = 120

NUMERIC_TRAITS = {
    key for key, value in TRAIT_DEFAULTS.items() if isinstance(value, (int, float))
}
SOFTWARE_IDS = set(SOFTWARE_MAP)
CANDIDATE_IDS = {c["id"] for c in CANDIDATES}

# Traits the interview is allowed to move. Device and GPU stay with the
# hardware probe and the questionnaire, which can actually observe them.
EVIDENCE_TRAITS = NUMERIC_TRAITS - {"hardware_weak"}

EMPTY_EVIDENCE = {
    "traits": {},
    "device": None,
    "dimensionWeights": {},
    "dimensionTargets": {},
    "software": [],
    "notes": [],
}


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _clamp(value, low, high):
    return max(low, min(high, value))


def _mapping(value):
    """Models sometimes return a list or a string where an object was asked for."""
    return value if isinstance(value, dict) else {}


def _sequence(value):
    return value if isinstance(value, list) else []


def sanitize_evidence(raw):
    """Coerce one model response into safe, known-only evidence."""
    if not isinstance(raw, dict):
        return dict(EMPTY_EVIDENCE)

    traits = {}
    for key, value in _mapping(raw.get("traits")).items():
        if key not in EVIDENCE_TRAITS:
            continue
        number = _number(value)
        if number is None:
            continue
        traits[key] = round(_clamp(number, 0.0, 1.0), 3)

    device = raw.get("device")
    device = device if device in DEVICES else None

    weights = {}
    for key, value in _mapping(raw.get("dimensionWeights")).items():
        if key not in DIMENSION_IDS:
            continue
        number = _number(value)
        if number is None or number <= 0:
            continue
        weights[key] = round(_clamp(number, 0.0, 1.0), 3)

    targets = {}
    for key, value in _mapping(raw.get("dimensionTargets")).items():
        if key not in DIMENSION_IDS:
            continue
        number = _number(value)
        if number is None:
            continue
        targets[key] = round(_clamp(number, 0.0, 100.0), 1)

    software = []
    for item in _sequence(raw.get("software")):
        if isinstance(item, str) and item in SOFTWARE_IDS and item not in software:
            software.append(item)
    software = software[:MAX_SOFTWARE]

    notes = []
    for item in _sequence(raw.get("notes")):
        if isinstance(item, str) and item.strip():
            notes.append(item.strip()[:MAX_NOTE_LENGTH])
    notes = notes[:MAX_NOTES]

    return {
        "traits": traits,
        "device": device,
        "dimensionWeights": weights,
        "dimensionTargets": targets,
        "software": software,
        "notes": notes,
    }


def merge_evidence(items):
    """Combine several interview rounds. Later rounds win on traits."""
    merged = dict(EMPTY_EVIDENCE)
    merged["traits"] = {}
    merged["dimensionWeights"] = {}
    merged["dimensionTargets"] = {}
    merged["software"] = []
    merged["notes"] = []

    for item in items or []:
        clean = sanitize_evidence(item)
        merged["traits"].update(clean["traits"])
        if clean["device"]:
            merged["device"] = clean["device"]
        for dim, weight in clean["dimensionWeights"].items():
            merged["dimensionWeights"][dim] = round(
                min(1.0, merged["dimensionWeights"].get(dim, 0.0) + weight), 3
            )
        merged["dimensionTargets"].update(clean["dimensionTargets"])
        for sid in clean["software"]:
            if sid not in merged["software"] and len(merged["software"]) < MAX_SOFTWARE:
                merged["software"].append(sid)
        for note in clean["notes"]:
            if note not in merged["notes"] and len(merged["notes"]) < MAX_NOTES:
                merged["notes"].append(note)

    return merged


def is_empty(evidence):
    return not any(
        (
            evidence.get("traits"),
            evidence.get("device"),
            evidence.get("dimensionWeights"),
            evidence.get("dimensionTargets"),
            evidence.get("software"),
        )
    )


def evidence_prompt_blocks():
    """The whitelists handed to the model so it can only pick real values."""
    from ..data.dimensions import DIMENSIONS

    traits = ", ".join(sorted(EVIDENCE_TRAITS))
    dims = ", ".join(f"{d[0]}（{d[1]}）" for d in DIMENSIONS)
    software = ", ".join(f"{sid}（{item['name']}）" for sid, item in SOFTWARE_MAP.items())
    return {
        "traits": traits,
        "dimensions": dims,
        "devices": ", ".join(DEVICES),
        "software": software,
    }
