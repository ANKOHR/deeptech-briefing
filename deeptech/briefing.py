"""Fixed-order briefing assembly and markdown or HTML rendering."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from .economics import calculate_economics
from .core import ProvenanceError, validate_provenance

SECTION_ORDER = [
    ("science", "The science"),
    ("market", "The market"),
    ("economics", "The economics"),
    ("bottlenecks", "The bottlenecks"),
    ("competing_approaches", "Competing approaches"),
    ("uncertainties", "The uncertainties"),
]


def assemble(pack: dict[str, Any]) -> dict[str, Any]:
    entries = pack["entries"]
    by_kind: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        by_kind.setdefault(entry["kind"], []).append(entry)

    sections: dict[str, dict[str, Any]] = {
        "science": {"paragraphs": [{"text": item["text"], "source_ids": [item["id"]]} for item in by_kind.get("science", [])]},
        "market": {"paragraphs": [{"text": f"{item['label']}: {item['value']} {item['unit']}.", "source_ids": [item["id"]]} for item in by_kind.get("market", [])]},
        "economics": {"paragraphs": [], "calculations": []},
        "bottlenecks": {"paragraphs": [{"text": item["text"], "source_ids": [item["id"]]} for item in by_kind.get("bottleneck", [])]},
        "competing_approaches": {"paragraphs": [], "comparisons": []},
        "uncertainties": {"paragraphs": [{
            "text": f"{item['name']}: range {item['low']} to {item['high']} ({item['range_kind']}); stated confidence: {item['confidence']}. {item['note']}",
            "source_ids": [item["id"]],
        } for item in by_kind.get("uncertainty", [])]},
    }

    economics = calculate_economics(pack)
    sections["economics"]["calculations"] = economics["calculations"]
    for calculation in economics["calculations"]:
        step_summary = "; ".join(f"{step['expression']} = {step['result']} {step['unit']}" for step in calculation["steps"])
        sections["economics"]["paragraphs"].append({
            "text": f"{calculation['name']}: formula: {calculation['formula']}. Worked steps: {step_summary}. Result: {calculation['result']} {calculation['unit']}.",
            "source_ids": calculation["source_ids"],
        })

    groups: dict[str, list[dict[str, Any]]] = {}
    for approach in by_kind.get("approach", []):
        groups.setdefault(approach["conflict_group"], []).append(approach)
    for group_name, claims in groups.items():
        if len(claims) < 2:
            continue
        sections["competing_approaches"]["comparisons"].append({
            "conflict_group": group_name,
            "claims": [{"approach": item["name"], "attribution": item["attribution"], "text": item["text"],
                        "source_ids": [item["id"]]} for item in claims],
        })

    result = {
        "schema_version": 1,
        "topic_id": pack["topic_id"],
        "title": pack["title"],
        "synthetic": True,
        "fixture_seed": pack["fixture_seed"],
        "sections": [{"id": key, "heading": heading, **sections[key]} for key, heading in SECTION_ORDER],
        "calculations": economics["calculations"],
        "sources": [{"id": entry["id"], "kind": entry["kind"], "label": entry["label"], "entry": entry} for entry in entries],
    }
    validate_provenance(result)
    return result


def write_briefing(briefing: dict[str, Any], output_dir: str | Path) -> Path:
    path = Path(output_dir) / "briefing.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(briefing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return path


def _tags(source_ids: list[str], *, html_mode: bool) -> str:
    if html_mode:
        return " ".join(f'<span class="source-tag">[src: {html.escape(source_id)}]</span>' for source_id in source_ids)
    return " ".join(f"[src: {source_id}]" for source_id in source_ids)


def render_markdown(briefing: dict[str, Any]) -> str:
    validate_provenance(briefing)
    lines = [f"# {briefing['title']}", "", "Composed from synthetic fixture data. All diagrams are generated illustrations from fixture data, not measured data.", ""]
    for section in briefing["sections"]:
        lines.extend([f"## {section['heading']}", ""])
        for paragraph in section.get("paragraphs", []):
            lines.extend([f"{paragraph['text']} {_tags(paragraph['source_ids'], html_mode=False)}", ""])
        for comparison in section.get("comparisons", []):
            lines.extend([f"### Conflicting fixture claims: {comparison['conflict_group']}", ""])
            for claim in comparison["claims"]:
                lines.extend([f"- **{claim['approach']}**, attributed to {claim['attribution']}: {claim['text']} {_tags(claim['source_ids'], html_mode=False)}"])
            lines.append("")
    lines.extend(["## Worked calculation details", ""])
    for calculation in briefing["calculations"]:
        lines.extend([f"### {calculation['name']}", "", f"Inputs: `{json.dumps(calculation['inputs'], sort_keys=True)}`", "",
                      f"Formula: `{calculation['formula']}`", ""])
        for index, step in enumerate(calculation["steps"], 1):
            lines.append(f"{index}. `{step['expression']} = {step['result']}` {step['unit']}")
        lines.extend([f"", f"Result: **{calculation['result']} {calculation['unit']}** {_tags(calculation['source_ids'], html_mode=False)}", ""])
    lines.extend(["## Sources appendix", ""])
    for source in briefing["sources"]:
        lines.append(f"- [src: {source['id']}] {source['label']} ({source['kind']})")
    return "\n".join(lines).rstrip() + "\n"


def render_html(briefing: dict[str, Any]) -> str:
    validate_provenance(briefing)
    esc = html.escape
    out = ["<!doctype html>", '<html lang="en"><head><meta charset="utf-8">',
           f"<title>{esc(briefing['title'])}</title>",
           "<style>body{font:16px/1.55 system-ui,sans-serif;max-width:920px;margin:2rem auto;padding:0 1rem;color:#18202a}"
           ".banner{background:#fff3cd;border:1px solid #d6aa35;padding:1rem;margin:1rem 0}"
           ".source-tag{font:0.82em ui-monospace,monospace;color:#174a7e}"
           "table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccd3da;padding:.55rem;text-align:left}"
           "code{background:#f2f4f6;padding:.1rem .25rem}</style></head><body>",
           '<div class="banner"><strong>Provenance:</strong> This briefing is composed from synthetic fixture source packs, not live research. Diagrams are generated illustrations from fixture data, not measured data.</div>',
           f"<h1>{esc(briefing['title'])}</h1>"]
    for section in briefing["sections"]:
        out.append(f"<section><h2>{esc(section['heading'])}</h2>")
        for paragraph in section.get("paragraphs", []):
            out.append(f"<p>{esc(paragraph['text'])} {_tags(paragraph['source_ids'], html_mode=True)}</p>")
        for comparison in section.get("comparisons", []):
            out.append(f"<h3>Conflicting fixture claims: {esc(comparison['conflict_group'])}</h3><table><thead><tr><th>Approach</th><th>Attributed source</th><th>Claim and provenance</th></tr></thead><tbody>")
            for claim in comparison["claims"]:
                out.append(f"<tr><td>{esc(claim['approach'])}</td><td>{esc(claim['attribution'])}</td><td>{esc(claim['text'])} {_tags(claim['source_ids'], html_mode=True)}</td></tr>")
            out.append("</tbody></table>")
        out.append("</section>")
    out.append("<section><h2>Worked calculation details</h2>")
    for calculation in briefing["calculations"]:
        out.append(f"<h3>{esc(calculation['name'])}</h3><p>Inputs: <code>{esc(json.dumps(calculation['inputs'], sort_keys=True))}</code></p><p>Formula: <code>{esc(calculation['formula'])}</code></p><ol>")
        for step in calculation["steps"]:
            out.append(f"<li><code>{esc(step['expression'])} = {esc(step['result'])}</code> {esc(step['unit'])}</li>")
        out.append(f"</ol><p>Result: <strong>{esc(calculation['result'])} {esc(calculation['unit'])}</strong> {_tags(calculation['source_ids'], html_mode=True)}</p>")
    out.append("</section><section><h2>Sources appendix</h2><ul>")
    for source in briefing["sources"]:
        out.append(f"<li><span class=\"source-tag\">[src: {esc(source['id'])}]</span> {esc(source['label'])} ({esc(source['kind'])})</li>")
    out.extend(["</ul></section>", "</body></html>"])
    return "\n".join(out) + "\n"


def render(briefing: dict[str, Any], output_format: str) -> str:
    if output_format == "md":
        return render_markdown(briefing)
    if output_format == "html":
        return render_html(briefing)
    raise ValueError("format must be md or html")
