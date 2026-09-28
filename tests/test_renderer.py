from __future__ import annotations

from deeptech.briefing import assemble, render_html, render_markdown


def test_html_banner_states_fixture_boundary_and_sources_appendix_is_complete(pack):
    briefing = assemble(pack)
    output = render_html(briefing)
    assert "composed from synthetic fixture source packs, not live research" in output
    assert "Diagrams are generated illustrations from fixture data, not measured data" in output
    assert "<h2>Sources appendix</h2>" in output
    for source in briefing["sources"]:
        assert f"[src: {source['id']}]" in output
        assert source["label"] in output


def test_markdown_has_complete_appendix_and_worked_steps(pack):
    briefing = assemble(pack)
    output = render_markdown(briefing)
    assert "## Sources appendix" in output
    assert "## Worked calculation details" in output
    assert "Formula:" in output
    for source in briefing["sources"]:
        assert f"[src: {source['id']}] {source['label']}" in output
