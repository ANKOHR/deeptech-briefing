from __future__ import annotations

import json
from decimal import Decimal

from deeptech.briefing import assemble, render_markdown
from deeptech.economics import calculate_economics
from deeptech.fixtures import FIXTURE_SEED, TOPICS, make_pack, write_packs


def test_generation_is_deterministic_and_emits_every_topic(tmp_path):
    first = write_packs(tmp_path / "first")
    second = write_packs(tmp_path / "second")
    assert [path.name for path in first] == [f"{topic}.json" for topic in TOPICS]
    assert [path.read_bytes() for path in first] == [path.read_bytes() for path in second]
    for path in first:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["synthetic"] is True
        assert data["fixture_seed"] == FIXTURE_SEED
        assert {entry["kind"] for entry in data["entries"]} >= {"science", "market", "bottleneck", "approach", "uncertainty"}


def test_fixture_has_planted_conflicting_approach_claims():
    pack = make_pack("inference-economics")
    claims = [entry for entry in pack["entries"] if entry["kind"] == "approach"]
    assert len(claims) == 2
    assert claims[0]["conflict_group"] == claims[1]["conflict_group"]
    assert claims[0]["id"] != claims[1]["id"]
    assert claims[0]["text"] != claims[1]["text"]
    assert claims[0]["metric_value"] != claims[1]["metric_value"]


def test_uncertainty_ranges_have_bounds_and_stated_confidence():
    for topic in TOPICS:
        ranges = [entry for entry in make_pack(topic)["entries"] if entry["kind"] == "uncertainty"]
        assert ranges
        for entry in ranges:
            assert Decimal(entry["low"]) <= Decimal(entry["high"])
            assert entry["confidence"] in {"low", "medium", "high"}
            assert entry["note"]


def test_every_topic_can_be_assembled_and_calculated():
    for topic in TOPICS:
        pack = make_pack(topic)
        assert len(assemble(pack)["sections"]) == 6
        assert calculate_economics(pack)["calculations"]
