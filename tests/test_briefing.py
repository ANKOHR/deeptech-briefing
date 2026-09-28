from __future__ import annotations

import copy
import json
import re

import pytest

from deeptech.briefing import SECTION_ORDER, assemble, render_html, render_markdown
from deeptech.core import ProvenanceError, validate_provenance


def test_assembler_has_fixed_section_order_and_source_resolvable_paragraphs(pack):
    briefing = assemble(pack)
    assert [(section["id"], section["heading"]) for section in briefing["sections"]] == SECTION_ORDER
    source_ids = {source["id"] for source in briefing["sources"]}
    assert source_ids == {entry["id"] for entry in pack["entries"]}
    for section in briefing["sections"]:
        for paragraph in section.get("paragraphs", []):
            assert paragraph["source_ids"]
            assert set(paragraph["source_ids"]) <= source_ids
    validate_provenance(briefing)


def test_assembled_and_rendered_briefing_bytes_are_deterministic(pack):
    first = assemble(pack)
    second = assemble(copy.deepcopy(pack))
    assert (json.dumps(first, ensure_ascii=False, indent=2) + "\n").encode("utf-8") == (json.dumps(second, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    assert render_markdown(first).encode("utf-8") == render_markdown(second).encode("utf-8")


def test_competing_claims_remain_side_by_side_with_individual_sources(pack):
    briefing = assemble(pack)
    section = next(s for s in briefing["sections"] if s["id"] == "competing_approaches")
    comparison = section["comparisons"][0]
    assert len(comparison["claims"]) == 2
    assert comparison["claims"][0]["text"] != comparison["claims"][1]["text"]
    assert comparison["claims"][0]["source_ids"] != comparison["claims"][1]["source_ids"]
    markdown = render_markdown(briefing)
    assert markdown.index(comparison["claims"][0]["text"]) < markdown.index(comparison["claims"][1]["text"])
    assert all(f"[src: {claim['source_ids'][0]}]" in markdown for claim in comparison["claims"])


def test_unresolvable_source_tag_is_caught(pack):
    briefing = assemble(pack)
    briefing = copy.deepcopy(briefing)
    briefing["sections"][0]["paragraphs"][0]["source_ids"] = ["ghost-999"]
    with pytest.raises(ProvenanceError, match="ghost-999"):
        validate_provenance(briefing)


def test_renderer_outputs_inline_source_tags_for_all_paragraphs(pack):
    briefing = assemble(pack)
    markdown = render_markdown(briefing)
    for section in briefing["sections"]:
        for paragraph in section.get("paragraphs", []):
            for source_id in paragraph["source_ids"]:
                assert f"[src: {source_id}]" in markdown
    rendered_tags = re.findall(r"\[src: ([a-z]+-\d+)\]", markdown)
    assert rendered_tags
