#!/usr/bin/env python3
"""Minimal, model-agnostic CLI for the UoE Module Knowledge Graph Engine.

Milestone 1 deliberately handles:
- unit manifest loading
- structure-preserving plain-text/Markdown passage ingestion
- stable passage ids and SHA-256 hashes
- graph JSON initialisation
- simple reviewed-graph projections

Embedding and LLM adapters are added separately so the canonical graph format
is not coupled to a particular model provider.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Iterable

try:
    import yaml
except ImportError as exc:
    raise SystemExit("PyYAML is required: pip install pyyaml") from exc


def slug(text: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip()).strip("-").lower()
    return value or "item"


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def split_passages(text: str) -> Iterable[tuple[str | None, str]]:
    """Split Markdown/plain text while preserving the nearest heading."""
    heading = None
    buffer: list[str] = []

    def flush():
        nonlocal buffer
        paragraph = "\n".join(buffer).strip()
        buffer = []
        if paragraph:
            return heading, paragraph
        return None

    for line in text.splitlines():
        if re.match(r"^#{1,6}\s+", line):
            item = flush()
            if item:
                yield item
            heading = re.sub(r"^#{1,6}\s+", "", line).strip()
            continue
        if not line.strip():
            item = flush()
            if item:
                yield item
        else:
            buffer.append(line.rstrip())

    item = flush()
    if item:
        yield item


def load_manifest(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def ingest(manifest_path: Path, output_path: Path) -> None:
    manifest = load_manifest(manifest_path)
    root = manifest_path.parent
    nodes = []

    for reading in manifest["readings"]:
        rid = reading["reading_id"]
        source = root / reading["source_path"]
        raw = source.read_text(encoding="utf-8")

        nodes.append(
            {
                "id": f"reading:{rid}",
                "type": "reading",
                "label": reading["title"],
                "definition": None,
                "aliases": [],
                "importance": None,
                "review_status": "reviewed",
                "provenance": [],
            }
        )

        for index, (section, passage) in enumerate(split_passages(raw), start=1):
            pid = f"{rid}-p{index:04d}"
            nodes.append(
                {
                    "id": f"passage:{pid}",
                    "type": "passage",
                    "label": passage[:120],
                    "definition": passage,
                    "aliases": [],
                    "importance": None,
                    "review_status": "reviewed",
                    "provenance": [
                        {
                            "reading_id": rid,
                            "source_path": reading["source_path"],
                            "citation_id": reading.get("citation_id"),
                            "section": section,
                            "page": None,
                            "passage_id": pid,
                            "text_hash": text_hash(passage),
                            "quote": None,
                        }
                    ],
                }
            )

    graph = {
        "graph_id": f"{manifest['unit_id']}-graph",
        "unit_id": manifest["unit_id"],
        "version": "0.1",
        "nodes": nodes,
        "edges": [],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(graph, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def export_reading_map(graph_path: Path, output_path: Path) -> None:
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    by_reading: dict[str, list[str]] = {}

    node_by_id = {node["id"]: node for node in graph["nodes"]}
    for edge in graph["edges"]:
        if edge["review_status"] != "reviewed":
            continue
        if edge["relation"] not in {"DISCUSSES", "CENTRAL_TO"}:
            continue
        source = node_by_id.get(edge["source"])
        target = node_by_id.get(edge["target"])
        if not source or not target:
            continue
        if source["type"] == "reading":
            by_reading.setdefault(source["label"], []).append(target["label"])

    lines = ["# Reading map", ""]
    for reading, concepts in sorted(by_reading.items()):
        lines.append(f"## {reading}")
        for concept in sorted(set(concepts)):
            lines.append(f"- {concept}")
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(prog="module-graph")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest_cmd = sub.add_parser("ingest", help="Create passage-level graph skeleton from a unit manifest")
    ingest_cmd.add_argument("manifest", type=Path)
    ingest_cmd.add_argument("--out", type=Path, required=True)

    reading_cmd = sub.add_parser("reading-map", help="Export a reviewed reading-to-concept projection")
    reading_cmd.add_argument("graph", type=Path)
    reading_cmd.add_argument("--out", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "ingest":
        ingest(args.manifest, args.out)
    elif args.command == "reading-map":
        export_reading_map(args.graph, args.out)


if __name__ == "__main__":
    main()
