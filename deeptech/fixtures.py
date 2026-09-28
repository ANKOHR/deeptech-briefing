"""Deterministic synthetic source-pack generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURE_SEED = 1729

TOPICS: dict[str, dict[str, Any]] = {
    "ai-accelerators": {
        "title": "AI Accelerators: A Fictional Systems Brief",
        "science": [
            ("acc-01", "A matrix engine can reuse a tile of weights across several input vectors, reducing repeated weight reads in this fixture model."),
            ("acc-02", "The fictional accelerator uses 16-bit multiply-accumulate units and a local 48 MiB scratchpad."),
        ],
        "market": [("acc-03", "Fictional accelerator market estimate", "market_size_usd_billion", "USD billion", "18.4")],
        "bottlenecks": [("acc-04", "Power delivery and memory bandwidth constrain sustained throughput in the synthetic system profile.")],
        "approaches": [
            ("acc-05", "Tile-first accelerator", "fixture team alpha", "inference_throughput_claim", "This approach sustains 820 tokens per second on the reference workload.", "820", "tokens_per_second", "2.40", "820", "0.72"),
            ("acc-06", "Memory-first accelerator", "fixture team beta", "inference_throughput_claim", "This approach sustains 610 tokens per second on the same reference workload.", "610", "tokens_per_second", "1.65", "610", "0.81"),
        ],
        "uncertainty": [("acc-07", "Reference workload demand", "range", "4.0", "9.0", "medium", "Synthetic demand is stated as a range because fixture scenarios differ.")],
    },
    "inference-economics": {
        "title": "Inference Economics: A Fictional Unit-Cost Brief",
        "science": [
            ("inf-01", "Batching combines requests so a fixed accelerator can spend less time idle between small workloads in this fixture model."),
            ("inf-02", "The synthetic service measures output throughput separately from request latency, so higher throughput does not by itself imply lower latency."),
        ],
        "market": [("inf-03", "Fictional annual inference spend estimate", "annual_spend_usd_billion", "USD billion", "6.8")],
        "bottlenecks": [("inf-04", "Low utilization and memory traffic are the stated bottlenecks for the fictional inference service.")],
        "approaches": [
            ("inf-05", "Large-batch serving", "fixture team alpha", "inference_throughput_claim", "This approach serves 1450 output tokens per second at the stated operating point.", "1450", "tokens_per_second", "3.10", "1450", "0.68"),
            ("inf-06", "Latency-first serving", "fixture team beta", "inference_throughput_claim", "This approach serves 980 output tokens per second at the same stated operating point.", "980", "tokens_per_second", "2.35", "980", "0.84"),
        ],
        "uncertainty": [("inf-07", "Fleet utilization", "range", "0.42", "0.86", "medium", "Utilization spans a range across the fictional daily workload profile.")],
    },
    "robotics-foundation-models": {
        "title": "Robotics Foundation Models: A Fictional Deployment Brief",
        "science": [
            ("rob-01", "The fictional policy model maps camera frames and language instructions to a short sequence of robot actions."),
            ("rob-02", "The synthetic training set pairs 2.4 million image-language observations with action labels collected in simulation."),
        ],
        "market": [("rob-03", "Fictional addressable robotics software estimate", "market_size_usd_billion", "USD billion", "3.7")],
        "bottlenecks": [("rob-04", "Reliable contact handling and safe recovery from out-of-distribution scenes are the stated deployment bottlenecks.")],
        "approaches": [
            ("rob-05", "Generalist policy", "fixture team alpha", "task_success_claim", "This approach completes 74 percent of the reference manipulation tasks.", "74", "percent_task_success", "4.80", "74", "0.64"),
            ("rob-06", "Specialist policy", "fixture team beta", "task_success_claim", "This approach completes 89 percent of the same reference manipulation tasks.", "89", "percent_task_success", "3.60", "89", "0.77"),
        ],
        "uncertainty": [("rob-07", "Task success on unseen objects", "range", "0.38", "0.73", "low", "The fixture reports a broad range because unseen-object performance is uncertain.")],
    },
}


def make_pack(topic_id: str) -> dict[str, Any]:
    """Build a byte-stable JSON-ready fixture pack for a known topic."""
    if topic_id not in TOPICS:
        raise ValueError(f"Unknown topic {topic_id!r}. Choose from: {', '.join(TOPICS)}")
    spec = TOPICS[topic_id]
    entries: list[dict[str, Any]] = []
    for entry_id, text in spec["science"]:
        entries.append({"id": entry_id, "kind": "science", "label": f"Synthetic science fixture {entry_id}", "text": text})
    for entry_id, label, key, unit, value in spec["market"]:
        entries.append({"id": entry_id, "kind": "market", "label": label, "metric": key, "value": value, "unit": unit})
    for entry_id, text in spec["bottlenecks"]:
        entries.append({"id": entry_id, "kind": "bottleneck", "label": f"Synthetic bottleneck fixture {entry_id}", "text": text})
    for entry_id, name, source, group, text, metric_value, metric_unit, hourly_cost, throughput, utilization in spec["approaches"]:
        entries.append({
            "id": entry_id, "kind": "approach", "label": f"Synthetic competing-approach fixture {entry_id}",
            "name": name, "attribution": source, "conflict_group": group, "text": text,
            "metric_value": metric_value, "metric_unit": metric_unit,
            "hourly_hardware_cost_usd": hourly_cost, "throughput_per_second": throughput,
            "utilization": utilization,
        })
    for entry_id, name, kind, low, high, confidence, note in spec["uncertainty"]:
        entries.append({"id": entry_id, "kind": "uncertainty", "label": f"Synthetic uncertainty fixture {entry_id}",
                        "name": name, "range_kind": kind, "low": low, "high": high,
                        "confidence": confidence, "note": note})
    return {
        "schema_version": 1,
        "topic_id": topic_id,
        "title": spec["title"],
        "synthetic": True,
        "fixture_seed": FIXTURE_SEED,
        "description": "All entries are fictional fixture data generated locally. No live research was performed.",
        "entries": entries,
    }


def write_packs(output_dir: str | Path, topics: list[str] | None = None) -> list[Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    selected = topics or list(TOPICS)
    paths: list[Path] = []
    for topic_id in selected:
        pack = make_pack(topic_id)
        path = output / f"{topic_id}.json"
        path.write_text(json.dumps(pack, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        paths.append(path)
    return paths
