"""Exact, deterministic worked calculations over fixture economics inputs."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any


def _d(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"Expected a numeric fixture value, got {value!r}") from exc


def _fmt(value: Decimal) -> str:
    rounded = value.quantize(Decimal("0.000000001"), rounding=ROUND_HALF_UP)
    return f"{rounded:.9f}"


def calculate_economics(pack: dict[str, Any]) -> dict[str, Any]:
    approaches = [entry for entry in pack["entries"] if entry.get("kind") == "approach"]
    if not approaches:
        raise ValueError("Source pack has no competing approaches for an economics example")
    calculations: list[dict[str, Any]] = []
    for approach in approaches:
        cost = _d(approach["hourly_hardware_cost_usd"])
        throughput = _d(approach["throughput_per_second"])
        utilization = _d(approach["utilization"])
        if cost < 0 or throughput <= 0 or not 0 < utilization <= 1:
            raise ValueError(f"Invalid economics inputs for {approach['id']}")
        effective_tps = throughput * utilization
        hourly_units = effective_tps * Decimal(3600)
        per_unit = cost / hourly_units
        per_million = per_unit * Decimal(1_000_000)
        common_inputs = {
            "hardware_cost_usd_per_hour": _fmt(cost),
            "peak_throughput_per_second": _fmt(throughput),
            "utilization_fraction": _fmt(utilization),
        }
        source_ids = [approach["id"]]
        calculations.extend([
            {
                "id": f"{approach['id']}-throughput", "name": f"Effective throughput: {approach['name']}",
                "source_ids": source_ids, "inputs": common_inputs,
                "formula": "peak throughput per second * utilization",
                "steps": [
                    {"expression": f"{_fmt(throughput)} * {_fmt(utilization)}", "result": _fmt(effective_tps), "unit": "units per second"},
                ],
                "result": _fmt(effective_tps), "unit": "units per second",
            },
            {
                "id": f"{approach['id']}-unit-cost", "name": f"Cost per workload unit: {approach['name']}",
                "source_ids": source_ids, "inputs": common_inputs,
                "formula": "hourly hardware cost / (peak throughput * utilization * 3600 seconds)",
                "steps": [
                    {"expression": f"{_fmt(throughput)} * {_fmt(utilization)}", "result": _fmt(effective_tps), "unit": "units per second"},
                    {"expression": f"{_fmt(effective_tps)} * 3600", "result": _fmt(hourly_units), "unit": "units per hour"},
                    {"expression": f"{_fmt(cost)} / {_fmt(hourly_units)}", "result": _fmt(per_unit), "unit": "USD per workload unit"},
                ],
                "result": _fmt(per_unit), "unit": "USD per workload unit",
            },
            {
                "id": f"{approach['id']}-million-cost", "name": f"Cost per million workload units: {approach['name']}",
                "source_ids": source_ids, "inputs": common_inputs,
                "formula": "cost per workload unit * 1,000,000",
                "steps": [
                    {"expression": f"{_fmt(per_unit)} * 1000000", "result": _fmt(per_million), "unit": "USD per million workload units"},
                ],
                "result": _fmt(per_million), "unit": "USD per million workload units",
            },
        ])
    if len(approaches) >= 2:
        first, second = approaches[:2]
        first_calc = next(row for row in calculations if row["id"] == f"{first['id']}-million-cost")
        second_calc = next(row for row in calculations if row["id"] == f"{second['id']}-million-cost")
        a, b = _d(first_calc["result"]), _d(second_calc["result"])
        ratio = a / b if b else Decimal(0)
        calculations.append({
            "id": "approach-scaling-comparison", "name": "Scaling cost comparison at 1, 10, and 100 million workload units",
            "source_ids": [first["id"], second["id"]],
            "inputs": {first["name"] + "_usd_per_million": _fmt(a), second["name"] + "_usd_per_million": _fmt(b)},
            "formula": "per-million cost * workload volume in millions",
            "steps": [
                {"expression": f"{_fmt(a)} * 1", "result": _fmt(a), "unit": "USD at 1 million units for " + first["name"]},
                {"expression": f"{_fmt(b)} * 1", "result": _fmt(b), "unit": "USD at 1 million units for " + second["name"]},
                {"expression": f"{_fmt(a)} / {_fmt(b)}", "result": _fmt(ratio), "unit": "cost ratio, first approach divided by second"},
                {"expression": f"{_fmt(a)} * 10 and {_fmt(b)} * 10", "result": f"{_fmt(a * 10)} vs {_fmt(b * 10)}", "unit": "USD at 10 million units, first vs second"},
                {"expression": f"{_fmt(a)} * 100 and {_fmt(b)} * 100", "result": f"{_fmt(a * 100)} vs {_fmt(b * 100)}", "unit": "USD at 100 million units, first vs second"},
            ],
            "result": f"{_fmt(a)} vs {_fmt(b)} at 1 million units", "unit": "USD",
        })
    return {"topic_id": pack["topic_id"], "fixture_seed": pack["fixture_seed"], "calculations": calculations}
