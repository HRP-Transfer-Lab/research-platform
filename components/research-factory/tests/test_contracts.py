"""Publication contracts refuse mutable sources and unsupported claims."""

from copy import deepcopy
from pathlib import Path
import json

import pytest

from hrp_research_factory.contracts import ContractError, PublicationContract

SAMPLE = Path(__file__).resolve().parents[1] / "configs" / "TG-COMP-001.json"


def sample_dict():
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def test_load_valid_contract_and_fingerprint_is_stable():
    a = PublicationContract.from_file(SAMPLE)
    b = PublicationContract.from_dict(sample_dict())
    assert a.paper_id == "TG-COMP-001"
    assert a.source_commit == "f74576bfae66c28e02ba75e61037a8adb522bb03"
    assert a.fingerprint() == b.fingerprint()
    assert len(a.fingerprint()) == 64


@pytest.mark.parametrize("change", [
    ("track", "philosophical"),
    ("explanandum", "science_proven"),
    ("claim_status", "empirically_proven"),
    ("release_policy", "auto_submit"),
    ("data_tier", "automatic_cloud"),
])
def test_reject_unapproved_categories(change):
    item = sample_dict()
    item[change[0]] = change[1]
    with pytest.raises(ContractError):
        PublicationContract.from_dict(item)


def test_require_immutable_commit_and_valid_source():
    for sha in ("main", "feature/theory", "f74576bf", "Z" * 40):
        item = sample_dict()
        item["theory_source"]["commit"] = sha
        with pytest.raises(ContractError):
            PublicationContract.from_dict(item)


def test_reject_mismatched_or_unexpected_sources():
    for repo in ("Elsewhere/Trident-G-theory", "HRP-Transfer-Lab/other"):
        item = sample_dict()
        item["theory_source"]["repo"] = repo
        with pytest.raises(ContractError):
            PublicationContract.from_dict(item)
    item = sample_dict()
    item["theory_source"]["path"] = "../private.md"
    with pytest.raises(ContractError):
        PublicationContract.from_dict(item)


def test_require_rivals_and_falsification():
    item = sample_dict()
    item["rival_models"] = ["preferred_model"]
    with pytest.raises(ContractError):
        PublicationContract.from_dict(item)
    item = sample_dict()
    item["falsification_tests"] = []
    with pytest.raises(ContractError):
        PublicationContract.from_dict(item)
    item = sample_dict()
    item["rival_models"] = ["same", "same"]
    with pytest.raises(ContractError):
        PublicationContract.from_dict(item)


def test_reject_unrecognised_fields():
    item = deepcopy(sample_dict())
    item["publication_approved"] = True
    with pytest.raises(ContractError):
        PublicationContract.from_dict(item)
