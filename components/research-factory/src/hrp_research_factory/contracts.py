"""Strict, source-pinned publication contracts (standard library only)."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

SCHEMA = "hrp-publication-contract-v0.1"
TRACKS = {
    "COMP": "computational",
    "NEURO": "empirical_neuroscience",
    "TRANSFER": "learnability_transfer",
    "SHARED": "shared_intentionality",
    "PHIL": "philosophical",
    "PSYCH": "psychometric",
}
EXPLANANDA = {
    "adaptive_intelligence",
    "psychometric_g",
    "developmental_growth",
    "shared_reference",
    "normative_rationality",
}
DATA_TIERS = {"public_or_synthetic", "approved_public", "restricted_local"}


class ContractError(ValueError):
    """A publication contract is missing or contradicts a hard requirement."""


@dataclass(frozen=True)
class PublicationContract:
    paper_id: str
    track: str
    title: str
    explanandum: str
    source_repo: str
    source_path: str
    source_commit: str
    primary_hypothesis: str
    rival_models: tuple[str, ...]
    falsification_tests: tuple[str, ...]
    data_tier: str
    claim_status: str
    release_policy: str

    @classmethod
    def from_dict(cls, item: dict[str, Any]) -> "PublicationContract":
        if not isinstance(item, dict) or item.get("schema_version") != SCHEMA:
            raise ContractError("Unsupported publication contract schema.")
        expected = {
            "schema_version", "paper_id", "track", "title", "explanandum",
            "theory_source", "primary_hypothesis", "rival_models",
            "falsification_tests", "data_tier", "claim_status", "release_policy"
        }
        if set(item) != expected:
            raise ContractError(f"Missing or unexpected contract keys: {sorted(set(item) ^ expected)}")
        source = item["theory_source"]
        if not isinstance(source, dict) or set(source) != {"repo", "path", "commit"}:
            raise ContractError("theory_source must contain repo, path and immutable commit.")
        pid = item["paper_id"]
        if not isinstance(pid, str) or not re.fullmatch(r"TG-(COMP|NEURO|TRANSFER|SHARED|PHIL|PSYCH)-[0-9]{3}", pid):
            raise ContractError("Invalid paper_id.")
        prefix = pid.split("-")[1]
        if item["track"] != TRACKS[prefix]:
            raise ContractError("Paper ID and track disagree.")
        for field in ("title", "primary_hypothesis"):
            if not isinstance(item[field], str) or len(item[field].strip()) < 12:
                raise ContractError(f"{field} must be descriptive.")
        if item["explanandum"] not in EXPLANANDA:
            raise ContractError("Select one primary explanandum.")
        if not isinstance(source["repo"], str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", source["repo"]):
            raise ContractError("Source repository must be owner/repo.")
        if source["repo"] != "HRP-Transfer-Lab/Trident-G-theory":
            raise ContractError("M0 source allowlist contains only Trident-G-theory.")
        source_path = source["path"]
        if not isinstance(source_path, str) or not source_path.endswith(".md") or source_path.startswith("/") or ".." in Path(source_path).parts:
            raise ContractError("Theory source must be a safe relative Markdown path.")
        source_commit = source["commit"]
        if not isinstance(source_commit, str) or not re.fullmatch(r"[a-f0-9]{40}", source_commit):
            raise ContractError("A pinned 40-character Git commit SHA is required (not a branch).")
        for field, min_items in (("rival_models", 2), ("falsification_tests", 1)):
            values = item[field]
            if not isinstance(values, list) or len(values) < min_items:
                raise ContractError(f"{field} requires at least {min_items} entries.")
            if any(not isinstance(v, str) or not v.strip() for v in values):
                raise ContractError(f"{field} contains an empty or invalid item.")
            if len(set(values)) != len(values):
                raise ContractError(f"{field} contains duplicate entries.")
        if item["data_tier"] not in DATA_TIERS:
            raise ContractError("Invalid data_tier.")
        if item["claim_status"] != "hypothesis":
            raise ContractError("M0 contracts cannot assert published or empirical findings.")
        if item["release_policy"] != "human_only":
            raise ContractError("Only human-approved publication is allowed.")
        return cls(
            paper_id=pid,
            track=item["track"],
            title=item["title"].strip(),
            explanandum=item["explanandum"],
            source_repo=source["repo"],
            source_path=source_path,
            source_commit=source_commit,
            primary_hypothesis=item["primary_hypothesis"].strip(),
            rival_models=tuple(item["rival_models"]),
            falsification_tests=tuple(item["falsification_tests"]),
            data_tier=item["data_tier"],
            claim_status=item["claim_status"],
            release_policy=item["release_policy"],
        )

    @classmethod
    def from_file(cls, path: str | Path) -> "PublicationContract":
        try:
            value = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ContractError(f"Cannot read contract: {exc}") from exc
        return cls.from_dict(value)

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA,
            "paper_id": self.paper_id,
            "track": self.track,
            "title": self.title,
            "explanandum": self.explanandum,
            "theory_source": {
                "repo": self.source_repo,
                "path": self.source_path,
                "commit": self.source_commit,
            },
            "primary_hypothesis": self.primary_hypothesis,
            "rival_models": list(self.rival_models),
            "falsification_tests": list(self.falsification_tests),
            "data_tier": self.data_tier,
            "claim_status": self.claim_status,
            "release_policy": self.release_policy,
        }

    def fingerprint(self) -> str:
        raw = json.dumps(self.canonical_payload(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        return sha256(raw).hexdigest()
