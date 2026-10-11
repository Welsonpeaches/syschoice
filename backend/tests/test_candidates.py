from collections import Counter

from app.data.candidates import (
    CANDIDATES,
    FAMILY_COLORS,
    FAMILY_LABELS,
    GROUP_ORDER,
    candidate_map,
)
from app.data.dimensions import DIMENSION_IDS


def test_candidate_count_and_uniqueness():
    assert len(CANDIDATES) == 72
    assert len(candidate_map()) == 72


def test_every_candidate_has_nine_dimensions():
    for candidate in CANDIDATES:
        assert set(candidate["dims"]) == set(DIMENSION_IDS), candidate["id"]
        for value in candidate["dims"].values():
            assert 0 <= value <= 100, candidate["id"]


def test_copy_is_populated_and_placeholder_free():
    for candidate in CANDIDATES:
        assert candidate["blurb"].strip(), candidate["id"]
        assert candidate["blurb"] != "[]"
        assert candidate["pros"], candidate["id"]
        assert candidate["cons"], candidate["id"]
        # macOS intentionally ships an empty monogram and renders a glyph instead.
        assert isinstance(candidate["monogram"], str), candidate["id"]


def test_linux_and_bsd_candidates_declare_a_lineage():
    for candidate in CANDIDATES:
        if candidate["family"] in ("linux", "bsd"):
            assert candidate["lineage"].strip(), candidate["id"]


def test_families_and_groups_are_known():
    families = Counter(c["family"] for c in CANDIDATES)
    assert families["windows"] == 1
    assert families["macos"] == 1
    assert families["bsd"] == 3
    assert families["linux"] == 67
    for candidate in CANDIDATES:
        assert candidate["family"] in FAMILY_LABELS
        assert candidate["family"] in FAMILY_COLORS
        assert candidate["group"] in GROUP_ORDER, candidate["group"]


def test_bsd_candidates_are_gated_for_desktop_users():
    """BSD entries must carry gates so everyday users are not sent to them."""
    for candidate in CANDIDATES:
        if candidate["family"] == "bsd":
            assert candidate["gates"], candidate["id"]
