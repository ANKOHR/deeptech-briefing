from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str, cwd: Path):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run([sys.executable, "-m", "deeptech", *args], cwd=cwd, env=env,
                          text=True, capture_output=True, check=False)


def test_fixtures_subcommand_smoke(tmp_path):
    result = run_cli("fixtures", "--out", str(tmp_path / "packs"), cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert len(list((tmp_path / "packs").glob("*.json"))) == 3


def test_assemble_subcommand_smoke(tmp_path):
    pack_dir = tmp_path / "packs"
    assert run_cli("fixtures", "--out", str(pack_dir), "--topic", "ai-accelerators", cwd=tmp_path).returncode == 0
    result = run_cli("assemble", str(pack_dir / "ai-accelerators.json"), "--out", str(tmp_path / "brief"), cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert json.loads((tmp_path / "brief" / "briefing.json").read_text())["sections"]


def test_economics_subcommand_smoke_and_stable_stdout(tmp_path):
    pack_dir = tmp_path / "packs"
    run_cli("fixtures", "--out", str(pack_dir), "--topic", "ai-accelerators", cwd=tmp_path)
    args = ("economics", str(pack_dir / "ai-accelerators.json"))
    first, second = run_cli(*args, cwd=tmp_path), run_cli(*args, cwd=tmp_path)
    assert first.returncode == second.returncode == 0
    assert first.stdout.encode() == second.stdout.encode()
    assert json.loads(first.stdout)["calculations"]


def test_diagrams_subcommand_smoke(tmp_path):
    pack_dir = tmp_path / "packs"
    run_cli("fixtures", "--out", str(pack_dir), "--topic", "ai-accelerators", cwd=tmp_path)
    result = run_cli("diagrams", str(pack_dir / "ai-accelerators.json"), "--out", str(tmp_path / "images"), cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert len(list((tmp_path / "images").glob("*.png"))) == 3


def test_render_subcommand_smoke(tmp_path):
    pack_dir = tmp_path / "packs"
    run_cli("fixtures", "--out", str(pack_dir), "--topic", "ai-accelerators", cwd=tmp_path)
    run_cli("assemble", str(pack_dir / "ai-accelerators.json"), "--out", str(tmp_path / "brief"), cwd=tmp_path)
    result = run_cli("render", str(tmp_path / "brief" / "briefing.json"), "--format", "html", "--out", str(tmp_path / "brief.html"), cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "synthetic fixture source packs" in (tmp_path / "brief.html").read_text()


def test_audit_trail_records_counts_and_timestamp(tmp_path):
    pack_dir = tmp_path / "packs"
    run_cli("fixtures", "--out", str(pack_dir), "--topic", "ai-accelerators", cwd=tmp_path)
    run_cli("assemble", str(pack_dir / "ai-accelerators.json"), "--out", str(tmp_path / "brief"), cwd=tmp_path)
    run_cli("economics", str(pack_dir / "ai-accelerators.json"), cwd=tmp_path)
    run_cli("diagrams", str(pack_dir / "ai-accelerators.json"), "--out", str(tmp_path / "images"), cwd=tmp_path)
    run_cli("render", str(tmp_path / "brief" / "briefing.json"), "--format", "md", "--out", str(tmp_path / "brief.md"), cwd=tmp_path)
    rows = [json.loads(line) for line in (tmp_path / "db-audit.jsonl").read_text().splitlines()]
    assert [row["command"] for row in rows] == ["fixtures", "assemble", "economics", "diagrams", "render --format md"]
    assert rows[1]["sections_built"] == 6
    assert rows[1]["claims_linked"] > 0
    assert rows[1]["timestamp_utc"].endswith("+00:00")
    assert rows[2]["calculations_performed"] > 0
    assert rows[3]["diagrams_generated"] == 3
    assert rows[4]["sections_built"] == 6
