"""The declarative agent plan must not silently grant runtime authority."""

import json
from pathlib import Path

from hrp_research_factory.pipeline import ROLES

PLAN = Path(__file__).resolve().parents[1] / "configs" / "agent_assignments.v0.2.json"


def load_plan():
    return json.loads(PLAN.read_text(encoding="utf-8"))


def test_plan_is_not_executable_registration():
    plan = load_plan()
    assert plan["schema_version"] == "hrp-factory-agent-assignment-plan-v0.2"
    assert plan["status"] == "declarative_planning_only_not_runtime_agent_registration"
    assert all(role["approval_authority"] is False for role in plan["roles"])
    assert all(role["publish_authority"] is False for role in plan["roles"])
    assert all(g["auto_approve"] is False for g in plan["gates"])


def test_role_ids_unique_and_existing_agno_roles_are_only_m0():
    plan = load_plan()
    roles = {role["id"]: role for role in plan["roles"]}
    assert len(roles) == len(plan["roles"])
    actual = {role["id"] for role in plan["roles"] if role["status"] == "m0_constructor_no_tools"}
    assert actual == {"A01", "A05", "A06"}
    assert {role["first_milestone"] for role in plan["roles"]} <= {"M0", "M1", "M2", "M3", "M4"}


def test_publication_tracks_are_complete_and_roles_exist():
    plan = load_plan()
    roles = {r["id"] for r in plan["roles"]}
    assignments = plan["publication_assignments"]
    assert {a["track"] for a in assignments} == set(ROLES)
    assert len({a["paper_id"] for a in assignments}) == len(assignments)
    for paper in assignments:
        assert paper["lead"]
        assert paper["independent_review"]
        referenced = set()
        for group in ("lead", "evidence", "implementation", "independent_review", "manuscript"):
            referenced.update(paper[group])
        assert referenced <= roles
        assert not set(paper["lead"]).intersection(paper["independent_review"])
        assert not set(paper["implementation"]).intersection(paper["independent_review"])


def test_release_requires_human_owner():
    plan = load_plan()
    publication = [g for g in plan["gates"] if g["stage"] == "public_release"]
    assert len(publication) == 1
    assert publication[0]["owner"] == "PI_only"
