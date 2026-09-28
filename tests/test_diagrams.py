from __future__ import annotations

from deeptech.diagrams import CAPTION, generate_diagrams


def test_diagrams_are_identical_pngs_with_generated_illustration_caption(pack, tmp_path):
    first = generate_diagrams(pack, tmp_path / "one")
    second = generate_diagrams(pack, tmp_path / "two")
    assert [path.name for path in first] == ["briefing-flow.png", "approach-comparison.png", "workload-cost-curves.png"]
    for left, right in zip(first, second):
        data = left.read_bytes()
        assert data == right.read_bytes()
        assert data.startswith(b"\x89PNG\r\n\x1a\n")
        assert CAPTION.encode("ascii") in data
    assert len(CAPTION) > 20
