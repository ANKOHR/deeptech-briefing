"""Pack loading, validation, provenance, and audit helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class DeepTechError(ValueError):
    """A user-facing input or provenance error."""


class ProvenanceError(DeepTechError):
    """A briefing refers to a source entry that cannot be resolved."""


def load_pack(path: str | Path) -> dict[str, Any]:
    try:
        pack = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DeepTechError(f"Could not read source pack {path}: {exc}") from exc
    if not isinstance(pack, dict) or pack.get("schema_version") != 1 or pack.get("synthetic") is not True:
        raise DeepTechError("Source pack must use schema_version 1 and synthetic=true")
    entries = pack.get("entries")
    if not isinstance(entries, list) or not entries:
        raise DeepTechError("Source pack entries must be a non-empty list")
    ids = [entry.get("id") for entry in entries if isinstance(entry, dict)]
    if len(ids) != len(entries) or any(not isinstance(value, str) or not value for value in ids):
        raise DeepTechError("Every source entry must have a non-empty string id")
    if len(ids) != len(set(ids)):
        raise DeepTechError("Source entry ids must be unique")
    return pack


def validate_provenance(briefing: dict[str, Any]) -> None:
    """Ensure every paragraph and calculation resolves to an embedded source."""
    sources = briefing.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ProvenanceError("Briefing has no source appendix")
    source_ids: set[str] = set()
    for item in sources:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not isinstance(item.get("label"), str):
            raise ProvenanceError("Briefing source appendix has a malformed entry")
        source_id = item["id"]
        if source_id in source_ids:
            raise ProvenanceError("Briefing source appendix has duplicate entries")
        embedded = item.get("entry")
        if not isinstance(embedded, dict) or embedded.get("id") != source_id or embedded.get("label") != item["label"]:
            raise ProvenanceError(f"Source appendix entry does not match source tag {source_id}")
        source_ids.add(source_id)
    sections = briefing.get("sections")
    if not isinstance(sections, list):
        raise ProvenanceError("Briefing sections must be a list")
    for section in sections:
        for paragraph in section.get("paragraphs", []):
            refs = paragraph.get("source_ids")
            if not isinstance(refs, list) or not refs:
                raise ProvenanceError(f"Paragraph in {section.get('id')} has no source ids")
            missing = [ref for ref in refs if ref not in source_ids]
            if missing:
                raise ProvenanceError(f"Unresolvable source tag(s): {', '.join(map(str, missing))}")
        for comparison in section.get("comparisons", []):
            claims = comparison.get("claims", [])
            if len(claims) < 2:
                raise ProvenanceError("A competing-claims comparison must preserve at least two claims")
            for claim in claims:
                refs = claim.get("source_ids")
                if not isinstance(refs, list) or not refs:
                    raise ProvenanceError("A competing claim has no source ids")
                missing = [ref for ref in refs if ref not in source_ids]
                if missing:
                    raise ProvenanceError(f"Unresolvable source tag(s): {', '.join(map(str, missing))}")
    for calculation in briefing.get("calculations", []):
        missing = [ref for ref in calculation.get("source_ids", []) if ref not in source_ids]
        if not calculation.get("source_ids") or missing:
            raise ProvenanceError(f"Unresolvable calculation source tag(s): {', '.join(map(str, missing)) or 'none'}")


def append_audit(*, command: str, packs: list[str], sections_built: int = 0,
                 claims_linked: int = 0, calculations_performed: int = 0,
                 diagrams_generated: int = 0, audit_path: str | Path | None = None) -> None:
    path = Path(audit_path) if audit_path else Path.cwd() / "db-audit.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "command": command,
        "pack": ",".join(packs),
        "sections_built": sections_built,
        "claims_linked": claims_linked,
        "calculations_performed": calculations_performed,
        "diagrams_generated": diagrams_generated,
    }
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
