"""Read-only inspection of an existing, *public* HRP Evidence Registry release.

This module does not access live Supabase reviewer tables, mutate release records,
or reclassify intervention evidence as confirmation of general-intelligence theory.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


class RegistrySnapshotError(ValueError):
    """The supplied published release is absent, incomplete or inconsistent."""


def inspect_public_release(release_dir: str | Path) -> dict:
    """Validate a local public release manifest and return provenance/counts only."""
    root = Path(release_dir).expanduser().resolve(strict=True)
    manifest = root / "manifest.json"
    records_dir = root / "records"
    if not manifest.is_file() or not records_dir.is_dir():
        raise RegistrySnapshotError("Expect manifest.json and records/ under the public release.")
    raw = manifest.read_bytes()
    try:
        head = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise RegistrySnapshotError("Invalid public release manifest.") from exc
    if not isinstance(head, dict) or head.get("status") not in {"approved_seed", "approved"}:
        raise RegistrySnapshotError("Registry snapshot is not an approved public release.")
    release_id = head.get("release_id")
    count = head.get("record_count")
    if not isinstance(release_id, str) or not isinstance(count, int) or count < 0:
        raise RegistrySnapshotError("Invalid release identity or expected record count.")
    files = sorted(records_dir.glob("*.json"))
    if len(files) != count:
        raise RegistrySnapshotError("Public release record count mismatch.")
    dois: dict[str, str] = {}
    for p in files:
        if not p.is_file() or p.is_symlink() or p.resolve().parent != records_dir.resolve():
            raise RegistrySnapshotError("A registry record is unsafe.")
        try:
            record = json.loads(p.read_text(encoding="utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise RegistrySnapshotError("Malformed public registry JSON.") from exc
        if not isinstance(record, dict) or record.get("release_id") != release_id:
            raise RegistrySnapshotError("Registry record release_id mismatch.")
        bibliography = record.get("bibliography", {})
        doi = bibliography.get("doi") if isinstance(bibliography, dict) else None
        if isinstance(doi, str) and doi:
            if doi.lower() in dois:
                raise RegistrySnapshotError("Duplicate registry DOI.")
            dois[doi.lower()] = record.get("record_id", "unknown")
    return {
        "release_id": release_id,
        "status": head["status"],
        "taxonomy_version": head.get("taxonomy_version"),
        "record_count": count,
        "manifest_sha256": sha256(raw).hexdigest(),
        "indexed_dois_to_record_ids": dois,
        "read_only": True,
        "interpretation_boundary": "Intervention-route reviews are NOT general-intelligence mechanism validation.",
        "original_full_text_checked_by_factory": False,
    }
