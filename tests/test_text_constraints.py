from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_project_text_has_no_em_dash():
    files = [ROOT / "README.md", ROOT / "pyproject.toml", ROOT / ".gitignore"]
    files.extend((ROOT / "deeptech").glob("*.py"))
    files.extend((ROOT / "tests").glob("*.py"))
    forbidden = chr(0x2014)
    for path in files:
        assert forbidden not in path.read_text(encoding="utf-8"), path.name
