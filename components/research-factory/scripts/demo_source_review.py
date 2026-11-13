"""Create a fictional offline original-text review packet for CI inspection.

NO real paper, model, network access or claim of scientific evidence is involved.
The artificial source is deliberately marked as fabricated and remains local.
"""

from hashlib import sha256
import json
from pathlib import Path

from hrp_research_factory.contracts import PublicationContract
from hrp_research_factory.source_review import run_source_review

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs"
DOCS = OUT / "fictional-source-input"

ARTIFICIAL_TEXT = (
    "# FICTIONAL SOFTWARE TEST ARTICLE — NOT A SCIENTIFIC SOURCE\n\n"
    "This is generated test material, not the contents of the DOI-linked work. "
    "It should never be cited as a scientific publication or presented as empirical evidence.\n\n"
    "An invented controller switches to a new policy following a fictional contingency change. "
    "An equally fictional smooth controller also recovers after perturbation, demonstrating "
    "only that different model families can be represented in synthetic tests.\n\n"
    "No participants, real data, experiments, literature interpretation, licence grants "
    "or scientific conclusions are used in this demonstration.\n"
)


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    sample = DOCS / "SRC-004.txt"
    raw = ARTIFICIAL_TEXT.encode("utf-8")
    sample.write_bytes(raw)
    bundle = {
        "schema_version": "hrp-local-source-bundle-v0.1",
        "paper_id": "TG-COMP-001",
        "sources": [{
            "source_id": "SRC-004",
            "doi": "10.1038/ncomms3521",
            "title": "FICTIONAL software-only test article",
            "file": sample.name,
            "sha256": sha256(raw).hexdigest(),
            "access_basis": "authorised_user_copy",
            "data_tier": "restricted_local",
            "hosted_approved": False,
        }],
    }
    manifest = DOCS / "source-bundle.json"
    manifest.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    c = PublicationContract.from_file(ROOT / "configs" / "TG-COMP-001.json")
    folder = run_source_review(
        c, ROOT / "configs" / "TG-COMP-001-evidence-candidates.json",
        manifest, OUT,
    )
    print("FICTIONAL OFFLINE SOURCE AUDIT:", folder / "source_review" / "REVIEW.md")
    print("All interpretations and scientific claims remain UNVERIFIED.")


if __name__ == "__main__":
    main()
