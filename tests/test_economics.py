from __future__ import annotations

import copy
import json
from decimal import Decimal

from deeptech.economics import calculate_economics


def test_worked_calculations_recompute_from_fixture_inputs(pack):
    result = calculate_economics(pack)
    calculations = {row["id"]: row for row in result["calculations"]}
    for approach in (entry for entry in pack["entries"] if entry["kind"] == "approach"):
        throughput = Decimal(approach["throughput_per_second"])
        utilization = Decimal(approach["utilization"])
        cost = Decimal(approach["hourly_hardware_cost_usd"])
        effective = throughput * utilization
        hourly_units = effective * 3600
        assert Decimal(calculations[f"{approach['id']}-throughput"]["result"]) == effective.quantize(Decimal("0.000000001"))
        assert Decimal(calculations[f"{approach['id']}-unit-cost"]["result"]) == (cost / hourly_units).quantize(Decimal("0.000000001"))
        assert Decimal(calculations[f"{approach['id']}-million-cost"]["result"]) == (cost / hourly_units * 1_000_000).quantize(Decimal("0.000000001"))
        assert len(calculations[f"{approach['id']}-unit-cost"]["steps"]) == 3
    assert len(calculations["approach-scaling-comparison"]["steps"]) == 5


def test_same_pack_produces_byte_identical_economics_json(pack):
    first = json.dumps(calculate_economics(pack), sort_keys=True, separators=(",", ":")).encode("utf-8")
    second = json.dumps(calculate_economics(copy.deepcopy(pack)), sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert first == second


def test_tampered_fixture_input_changes_the_result(pack):
    changed = copy.deepcopy(pack)
    approach = next(entry for entry in changed["entries"] if entry["kind"] == "approach")
    original_result = calculate_economics(pack)["calculations"][1]["result"]
    approach["throughput_per_second"] = str(Decimal(approach["throughput_per_second"]) / 10)
    changed_result = next(row["result"] for row in calculate_economics(changed)["calculations"] if row["id"] == f"{approach['id']}-unit-cost")
    assert changed_result != original_result
