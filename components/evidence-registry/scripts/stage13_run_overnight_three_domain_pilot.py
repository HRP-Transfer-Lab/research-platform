#!/usr/bin/env python3
"""Run/resume the strict three-domain Stage 13 overnight evidence pilot.

Pipeline:
  balanced Europe PMC discovery
  -> deterministic psychology-only health-scope gate
  -> local Qwen abstract classification
  -> post-classification psychology-only health enforcement
  -> domain-balanced full-text acquisition portfolio.

Candidate-only: no PDF acquisition and no Registry/scientific/release/Gateway or
machine-screened mutation.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = REPO_ROOT / "components/evidence-registry/scripts"
DEFAULT_CONFIG = (
    REPO_ROOT
    / "components/evidence-registry/config/"
    / "stage13_overnight_psychology_search.v1.json"
)
DEFAULT_HEALTH_POLICY = (
    REPO_ROOT
    / "components/evidence-registry/config/"
    / "stage13_health_psychology_scope_policy.v1.json"
)
DEFAULT_ROOT = Path.home() / "hrp-lab/source-corpus/_overnight"
DISCOVERY_SCRIPT = SCRIPTS / "stage13_discover_psychology_interventions.py"
HEALTH_FILTER_SCRIPT = SCRIPTS / "stage13_health_psychology_scope.py"
CLASSIFY_SCRIPT = SCRIPTS / "stage13_classify_csi_domain_candidates.py"
HEALTH_ENFORCE_SCRIPT = (
    SCRIPTS / "stage13_enforce_psychology_health_classifications.py"
)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"File not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"Expected a JSON object in {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def execute(command: list[str]) -> int:
    print("command|" + " ".join(command), flush=True)
    return subprocess.run(command, check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run/resume the strict Stage 13 three-domain overnight pilot."
    )
    parser.add_argument("--email", required=True)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--health-policy", type=Path, default=DEFAULT_HEALTH_POLICY)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--target-candidates", type=int)
    parser.add_argument("--max-items", type=int)
    parser.add_argument("--model")
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    parser.add_argument("--force-discovery", action="store_true")
    parser.add_argument("--force-classification", action="store_true")
    args = parser.parse_args()

    if "@" not in args.email:
        raise SystemExit("Supply a valid contact email")
    config_path = args.config.expanduser().resolve()
    health_policy_path = args.health_policy.expanduser().resolve()
    config = load_json(config_path)
    health_policy = load_json(health_policy_path)
    if config.get("schema_version") != "stage13-overnight-psychology-search-v1":
        raise SystemExit("Unsupported overnight-pilot configuration")
    if (
        health_policy.get("schema_version")
        != "stage13-health-psychology-scope-policy-v1"
    ):
        raise SystemExit("Unsupported health psychology scope policy")

    configured_domains = {
        str(row.get("domain_id"))
        for row in config.get("csi_domains") or []
        if isinstance(row, dict) and row.get("domain_id")
    }
    expected_domains = {
        "performance_work",
        "personal",
        "health_clinical_adjacent",
    }
    if configured_domains != expected_domains:
        raise SystemExit(
            "Configuration must define performance_work, personal and "
            "health_clinical_adjacent domains"
        )

    timestamp = datetime.now(timezone.utc)
    run_dir = (
        args.run_dir.expanduser().resolve()
        if args.run_dir
        else DEFAULT_ROOT
        / f"three-domain-{timestamp.strftime('%Y%m%d-%H%M%S')}"
    )
    run_dir.mkdir(parents=True, exist_ok=True)
    raw_discovery_path = run_dir / "discovery.raw.json"
    discovery_path = run_dir / "discovery.json"
    raw_classification_dir = run_dir / "classification-raw"
    classification_dir = run_dir / "classification"
    state_path = run_dir / "run-state.json"

    target_candidates = int(
        args.target_candidates or config.get("candidate_target") or 180
    )
    raw_target_candidates = min(max(target_candidates * 2, target_candidates), 500)
    max_items = int(
        args.max_items or config.get("classification_target") or 100
    )
    model = str(
        args.model
        or (config.get("classification") or {}).get("model")
        or "qwen3.5:4b"
    )
    if target_candidates < 3 or max_items < 3:
        raise SystemExit(
            "Three-domain pilot requires at least three candidates/items"
        )

    state: dict[str, Any] = {
        "schema_version": "stage13-three-domain-overnight-run-state-v2",
        "run_dir": str(run_dir),
        "config_path": str(config_path),
        "health_policy_path": str(health_policy_path),
        "target_candidates": target_candidates,
        "raw_candidate_target": raw_target_candidates,
        "classification_target": max_items,
        "model": model,
        "domains": sorted(expected_domains),
        "started_at": timestamp.isoformat(),
        "discovery": {
            "status": "pending",
            "raw_path": str(raw_discovery_path),
            "filtered_path": str(discovery_path),
        },
        "classification": {
            "status": "pending",
            "raw_directory": str(raw_classification_dir),
            "strict_directory": str(classification_dir),
        },
        "governance": {
            "abstract_screening_only": True,
            "psychology_only_health_scope": True,
            "pdf_downloads": 0,
            "registry_mutated": False,
            "scientific_state_mutated": False,
            "historical_release_mutated": False,
            "csi_gateway_mutated": False,
            "machine_screened_status_created": False,
            "human_authority_created": False,
        },
    }
    if state_path.exists():
        prior = load_json(state_path)
        state["resumed_from"] = prior.get("started_at")
    write_json(state_path, state)

    print("=== STAGE 13 STRICT THREE-DOMAIN OVERNIGHT PILOT ===")
    print(f"run_dir|{run_dir}")
    print(f"raw_candidate_target|{raw_target_candidates}")
    print(f"filtered_candidate_target|{target_candidates}")
    print(f"classification_target|{max_items}")
    print(f"model|{model}")
    print("domains|performance_work,personal,health_clinical_adjacent")
    print("health_scope|psychology_related_only")

    filtered_reusable = False
    if discovery_path.exists() and not args.force_discovery:
        existing = load_json(discovery_path)
        gate = existing.get("health_psychology_gate") or {}
        filtered_reusable = (
            existing.get("schema_version")
            == "stage13-psychology-candidate-discovery-v1"
            and gate.get("policy_id") == health_policy.get("policy_id")
        )

    if filtered_reusable:
        manifest = load_json(discovery_path)
        selected_count = int(
            (manifest.get("summary") or {}).get("selected_candidates") or 0
        )
        state["discovery"] = {
            "status": "reused_strict",
            "raw_path": str(raw_discovery_path),
            "filtered_path": str(discovery_path),
            "selected_candidates": selected_count,
        }
        write_json(state_path, state)
        print(f"strict_discovery_reused|{discovery_path}")
    else:
        if not raw_discovery_path.exists() or args.force_discovery:
            discovery_command = [
                sys.executable,
                "-u",
                str(DISCOVERY_SCRIPT),
                "--config",
                str(config_path),
                "--email",
                args.email,
                "--target-candidates",
                str(raw_target_candidates),
                "--output",
                str(raw_discovery_path),
            ]
            discovery_code = execute(discovery_command)
            if not raw_discovery_path.is_file():
                state["discovery"] = {
                    "status": "raw_discovery_failed",
                    "raw_path": str(raw_discovery_path),
                    "filtered_path": str(discovery_path),
                    "return_code": discovery_code,
                }
                write_json(state_path, state)
                print("STAGE 13 STRICT THREE-DOMAIN OVERNIGHT PILOT|DISCOVERY_FAILED")
                return 1
        else:
            discovery_code = 0
            print(f"raw_discovery_reused|{raw_discovery_path}")

        filter_command = [
            sys.executable,
            "-u",
            str(HEALTH_FILTER_SCRIPT),
            "--manifest",
            str(raw_discovery_path),
            "--config",
            str(config_path),
            "--policy",
            str(health_policy_path),
            "--target-candidates",
            str(target_candidates),
            "--output",
            str(discovery_path),
        ]
        filter_code = execute(filter_command)
        if not discovery_path.is_file():
            state["discovery"] = {
                "status": "health_scope_filter_failed",
                "raw_path": str(raw_discovery_path),
                "filtered_path": str(discovery_path),
                "return_code": filter_code,
            }
            write_json(state_path, state)
            print("STAGE 13 STRICT THREE-DOMAIN OVERNIGHT PILOT|HEALTH_FILTER_FAILED")
            return 1
        manifest = load_json(discovery_path)
        selected_count = int(
            (manifest.get("summary") or {}).get("selected_candidates") or 0
        )
        state["discovery"] = {
            "status": "complete" if filter_code == 0 else "partial",
            "raw_path": str(raw_discovery_path),
            "filtered_path": str(discovery_path),
            "raw_return_code": discovery_code,
            "filter_return_code": filter_code,
            "selected_candidates": selected_count,
            "health_psychology_gate": manifest.get("health_psychology_gate"),
        }
        write_json(state_path, state)
        if selected_count < 3:
            print("STAGE 13 STRICT THREE-DOMAIN OVERNIGHT PILOT|INSUFFICIENT_CANDIDATES")
            return 1

    classification_command = [
        sys.executable,
        "-u",
        str(CLASSIFY_SCRIPT),
        "--manifest",
        str(discovery_path),
        "--config",
        str(config_path),
        "--model",
        model,
        "--max-items",
        str(max_items),
        "--output-dir",
        str(raw_classification_dir),
        "--ollama-url",
        args.ollama_url,
    ]
    if args.force_classification:
        classification_command.append("--force")
    raw_classification_code = execute(classification_command)

    raw_classified_path = raw_classification_dir / "classified-candidates.jsonl"
    if not raw_classified_path.is_file():
        state["classification"] = {
            "status": "raw_classification_failed",
            "raw_directory": str(raw_classification_dir),
            "strict_directory": str(classification_dir),
            "return_code": raw_classification_code,
        }
        write_json(state_path, state)
        print("STAGE 13 STRICT THREE-DOMAIN OVERNIGHT PILOT|CLASSIFICATION_FAILED")
        return 1

    enforce_command = [
        sys.executable,
        "-u",
        str(HEALTH_ENFORCE_SCRIPT),
        "--raw-output-dir",
        str(raw_classification_dir),
        "--manifest",
        str(discovery_path),
        "--config",
        str(config_path),
        "--policy",
        str(health_policy_path),
        "--output-dir",
        str(classification_dir),
    ]
    strict_code = execute(enforce_command)

    summary_path = classification_dir / "summary.json"
    portfolio_path = (
        classification_dir / "domain-balanced-fulltext-portfolio.json"
    )
    if summary_path.is_file():
        summary = load_json(summary_path)
        counts = summary.get("summary") or {}
        enforcement = summary.get("health_psychology_enforcement") or {}
        state["classification"] = {
            "status": "complete" if strict_code == 0 else "partial",
            "raw_directory": str(raw_classification_dir),
            "strict_directory": str(classification_dir),
            "raw_return_code": raw_classification_code,
            "strict_return_code": strict_code,
            "summary_path": str(summary_path),
            "classified": counts.get("classified"),
            "failures": counts.get("failures"),
            "domain_gate_pass": counts.get("domain_gate_pass"),
            "semantic_domain_counts": counts.get("semantic_domain_counts"),
            "portfolio_assigned_counts": counts.get(
                "portfolio_assigned_counts"
            ),
            "health_psychology_enforcement": enforcement,
            "domain_balanced_portfolio": str(portfolio_path),
        }
    else:
        state["classification"] = {
            "status": "strict_enforcement_failed",
            "raw_directory": str(raw_classification_dir),
            "strict_directory": str(classification_dir),
            "raw_return_code": raw_classification_code,
            "strict_return_code": strict_code,
        }
    state["completed_at"] = datetime.now(timezone.utc).isoformat()
    write_json(state_path, state)

    print(f"run_state|{state_path}")
    print(f"raw_discovery_manifest|{raw_discovery_path}")
    print(f"strict_discovery_manifest|{discovery_path}")
    print(f"raw_classification_dir|{raw_classification_dir}")
    print(f"classification_summary|{summary_path}")
    print(f"ranked_csv|{classification_dir / 'ranked-candidates.csv'}")
    print(f"domain_balanced_portfolio|{portfolio_path}")
    print("HEALTH_SCOPE|PSYCHOLOGY_RELATED_ONLY")
    print("PDF_DOWNLOADS|0")
    print("REGISTRY_MUTATED|0")
    print("SCIENTIFIC_STATE_MUTATED|0")
    print("HISTORICAL_RELEASE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")
    print("MACHINE_SCREENED_STATUS_CREATED|0")
    print("HUMAN_AUTHORITY_CREATED|0")

    if strict_code == 0:
        status = "PASS"
        exit_code = 0
    elif summary_path.is_file():
        status = "PARTIAL"
        exit_code = 2
    else:
        status = "FAIL"
        exit_code = 1
    print(f"STAGE 13 STRICT THREE-DOMAIN OVERNIGHT PILOT|{status}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
