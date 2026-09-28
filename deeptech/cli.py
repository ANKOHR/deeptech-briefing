"""Command line interface for DeepTech Briefing."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from . import __version__
from .briefing import assemble, render, write_briefing
from .core import DeepTechError, append_audit, load_pack, validate_provenance
from .diagrams import generate_diagrams
from .economics import calculate_economics
from .fixtures import TOPICS, write_packs


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deeptech", description="Compose deterministic briefings from synthetic fixture packs.")
    parser.add_argument("--version", action="version", version=f"deeptech {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    fixtures = commands.add_parser("fixtures", help="generate synthetic source-pack JSON fixtures")
    fixtures.add_argument("--out", required=True, help="output directory")
    fixtures.add_argument("--topic", action="append", choices=sorted(TOPICS), help="topic to generate, repeat for multiple topics")

    assembler = commands.add_parser("assemble", help="assemble a structured briefing JSON document")
    assembler.add_argument("pack", help="source-pack JSON file")
    assembler.add_argument("--out", required=True, help="output directory")

    economics = commands.add_parser("economics", help="print deterministic worked economics calculations as JSON")
    economics.add_argument("pack", help="source-pack JSON file")

    diagrams = commands.add_parser("diagrams", help="generate deterministic PNG illustrations")
    diagrams.add_argument("pack", help="source-pack JSON file")
    diagrams.add_argument("--out", required=True, help="output directory")

    renderer = commands.add_parser("render", help="render briefing JSON as Markdown or HTML")
    renderer.add_argument("briefing", help="assembled briefing JSON file")
    renderer.add_argument("--format", required=True, choices=["md", "html"])
    renderer.add_argument("--out", help="write to a file instead of stdout")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "fixtures":
            paths = write_packs(args.out, args.topic)
            topic_ids = [path.stem for path in paths]
            append_audit(command="fixtures", packs=topic_ids)
            for path in paths:
                print(path)
            return 0
        if args.command == "assemble":
            pack = load_pack(args.pack)
            briefing = assemble(pack)
            path = write_briefing(briefing, args.out)
            claims = sum(len(section.get("paragraphs", [])) + sum(len(c["claims"]) for c in section.get("comparisons", [])) for section in briefing["sections"])
            append_audit(command="assemble", packs=[pack["topic_id"]], sections_built=len(briefing["sections"]), claims_linked=claims)
            print(path)
            return 0
        if args.command == "economics":
            pack = load_pack(args.pack)
            result = calculate_economics(pack)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            append_audit(command="economics", packs=[pack["topic_id"]], calculations_performed=len(result["calculations"]))
            return 0
        if args.command == "diagrams":
            pack = load_pack(args.pack)
            paths = generate_diagrams(pack, args.out)
            append_audit(command="diagrams", packs=[pack["topic_id"]], diagrams_generated=len(paths))
            for path in paths:
                print(path)
            return 0
        if args.command == "render":
            try:
                briefing = json.loads(Path(args.briefing).read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise DeepTechError(f"Could not read briefing {args.briefing}: {exc}") from exc
            validate_provenance(briefing)
            rendered = render(briefing, args.format)
            if args.out:
                path = Path(args.out); path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(rendered, encoding="utf-8", newline="\n")
            else:
                sys.stdout.write(rendered)
            append_audit(command=f"render --format {args.format}", packs=[briefing.get("topic_id", "unknown")],
                         sections_built=len(briefing.get("sections", [])),
                         claims_linked=sum(len(s.get("paragraphs", [])) + sum(len(c.get("claims", [])) for c in s.get("comparisons", []))
                                            for s in briefing.get("sections", [])),
                         calculations_performed=len(briefing.get("calculations", [])))
            return 0
    except (DeepTechError, ValueError, OSError, KeyError) as exc:
        print(f"deeptech: {exc}", file=sys.stderr)
        return 2
    return 2
