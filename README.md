# DeepTech Briefing

DeepTech Briefing is a deterministic Python CLI for composing structured briefings from fictional, locally generated source packs. It does not fetch research or make claims beyond the source entries and explicit calculations.

## Quickstart

Requires Python 3.10 or newer. The application has no runtime dependencies and uses CPU-only Python standard library code.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
deeptech fixtures --out demo\fixtures
deeptech assemble demo\fixtures\ai-accelerators.json --out demo\briefing
deeptech economics demo\fixtures\ai-accelerators.json
deeptech diagrams demo\fixtures\ai-accelerators.json --out demo\diagrams
deeptech render demo\briefing\briefing.json --format md --out demo\briefing.md
deeptech render demo\briefing\briefing.json --format html --out demo\briefing.html
```

Without installing the console command, replace `deeptech` with `python -m deeptech`. Run the suite with `python -m pytest`.

The `fixtures` command generates all three topics by default: `ai-accelerators`, `inference-economics`, and `robotics-foundation-models`. Pass one or more `--topic` values to limit generation. Every command appends a JSON record to `db-audit.jsonl` in its current working directory. The audit timestamp records the run time, so the audit log itself is intentionally not byte-deterministic.

## Architecture

```text
                  +------------------------+
                  | deeptech fixtures      |
                  | seed 1729, local JSON  |
                  +-----------+------------+
                              |
                              v
                  +------------------------+
                  | source-pack validator  |
                  | unique IDs, schema     |
                  +-----------+------------+
                              |
             +----------------+----------------+
             |                                 |
             v                                 v
+---------------------------+     +--------------------------+
| deterministic economics   |     | deterministic PNG maker  |
| Decimal arithmetic, steps |     | blocks, bars, cost lines |
+-------------+-------------+     +-------------+------------+
              |                                 |
              +----------------+----------------+
                               v
                  +------------------------+
                  | section assembler      |
                  | source IDs on claims   |
                  +-----------+------------+
                              |
                              v
                  +------------------------+
                  | provenance validator   |
                  +-----------+------------+
                              |
                              v
                  +------------------------+
                  | Markdown or HTML       |
                  | complete source list   |
                  +------------------------+

All CLI commands -----------------> db-audit.jsonl
```

## Source-pack schema

Each generated UTF-8 JSON pack has `schema_version` set to `1`, a `topic_id`, a human-readable `title`, `synthetic: true`, the fixed `fixture_seed` of `1729`, a description, and an ordered `entries` list. Entry IDs are unique within a pack. Entry kinds are:

| Kind | Main fields | Use in the briefing |
| --- | --- | --- |
| `science` | `id`, `label`, `text` | Science section |
| `market` | `id`, `label`, `metric`, `value`, `unit` | Market section |
| `bottleneck` | `id`, `label`, `text` | Bottlenecks section |
| `approach` | `id`, `name`, `attribution`, `conflict_group`, `text`, metric fields and economics inputs | Competing claims and economics |
| `uncertainty` | `id`, `name`, `low`, `high`, `confidence`, `note` | Uncertainty ranges |

Approach entries with a shared `conflict_group` are preserved as separate claims. The assembler never reconciles or averages them. It copies claim text and links it to the exact entry ID. The source appendix keeps each full source entry alongside its ID, label, and kind.

## Economics worked-example method

Economics values are fixture inputs, not observed prices or performance. For each approach, the calculator takes hourly hardware cost, peak workload throughput per second, and a utilization fraction. It then displays the arithmetic in this order:

1. Effective throughput = peak throughput per second multiplied by utilization.
2. Units served per hour = effective throughput multiplied by 3,600 seconds.
3. Cost per workload unit = hourly hardware cost divided by units served per hour.
4. Cost per million units = cost per unit multiplied by 1,000,000.
5. A comparison scales each approach to 1, 10, and 100 million units.

All inputs and results use decimal arithmetic, are formatted to nine decimal places, and show a formula and intermediate steps. Same pack inputs produce the same calculation JSON. Editing an input changes the derived result. The simplified method assumes the fixture utilization applies throughout the hour and excludes networking, staffing, capital depreciation beyond the fixture hourly cost, and other costs not supplied as inputs.

## Demo walkthrough

1. `deeptech fixtures --out demo/fixtures` writes all topic packs. Open `ai-accelerators.json` to inspect the labeled science, market, bottleneck, competing-approach, and uncertainty entries.
2. `deeptech assemble demo/fixtures/ai-accelerators.json --out demo/briefing` creates `briefing.json` with six fixed sections. Each paragraph has source IDs; competing claims remain separate.
3. `deeptech economics demo/fixtures/ai-accelerators.json` prints the exact worked calculations as JSON. The same records are included in the assembled briefing.
4. `deeptech diagrams demo/fixtures/ai-accelerators.json --out demo/diagrams` writes three deterministic PNGs and a `captions.json` index. PNG metadata and visible caption text label every image as a generated illustration from fixture data, not measured data.
5. `deeptech render demo/briefing/briefing.json --format html --out demo/briefing.html` creates a standalone HTML version with a provenance banner and complete source appendix. Use `--format md` for Markdown.

## HONESTY BOUNDARY

Briefings are composed from synthetic fixture source packs, not live research. Science claims are labelled with fixture provenance that points to the exact source-pack entry. Economics numbers are arithmetic on fixture inputs and show their worked steps. Diagrams are generated illustrations from fixture data, not measurements. Market figures, claims, ranges, and attributions are fictional and should not be treated as external evidence.

## Determinism and runtime

Fixture generation uses fixed local data and seed `1729`; it performs no external downloads. The PNG writer draws raw RGB pixels and encodes PNG chunks using the standard library. No GPU workloads, torch, tensorflow, CUDA, or GPU packages are used. Stable JSON documents and PNG files contain no run timestamp. Runtime timestamps appear only in the append-only audit trail.
