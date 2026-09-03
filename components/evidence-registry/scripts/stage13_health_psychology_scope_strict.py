#!/usr/bin/env python3
"""Strict pre-LLM health-scope gate for the three-domain evidence pilot.

The base gate removes unsupported health query hits but keeps a candidate when it
also matched a work or personal query. That is normally useful, but broad search
terms such as ``occupational`` can make a general medical/allied-health service
paper appear cross-domain. This wrapper removes a candidate entirely when:

- the title is identified as a general medical, nursing, occupational-therapy,
  physical-rehabilitation or disease-service title; and
- no explicit psychology-related intervention basis qualifies it.

This is a discovery-screening operation only. It downloads no PDFs, calls no LLM
and mutates no Registry, scientific, release or Gateway state.
"""
from __future__ import annotations

from typing import Any

import stage13_health_psychology_scope as scope

_original_filter_candidates = scope.filter_candidates


def strict_filter_candidates(
    manifest: dict[str, Any],
    *,
    config: dict[str, Any],
    policy: dict[str, Any],
    target: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    raw_rows = [
        row for row in manifest.get("candidates") or [] if isinstance(row, dict)
    ]
    all_kept, excluded, counts = _original_filter_candidates(
        manifest,
        config=config,
        policy=policy,
        target=max(len(raw_rows), target),
    )

    kept: dict[str, dict[str, Any]] = {}
    cross_domain_medical_excluded = 0
    for candidate in all_kept:
        gate = candidate.get("health_psychology_gate") or {}
        medical_title_hits = gate.get("general_medical_service_title_hits") or []
        qualifies = gate.get("qualifies_for_health_clinical_adjacent") is True
        if medical_title_hits and not qualifies:
            cross_domain_medical_excluded += 1
            excluded.append(
                {
                    "candidate_id": candidate.get("candidate_id"),
                    "title": candidate.get("title"),
                    "reason": (
                        "general_medical_or_rehabilitation_service_without_"
                        "specific_psychology_intervention"
                    ),
                    "assessment": gate,
                    "cross_domain_false_positive_removed": True,
                }
            )
            continue
        kept[str(candidate.get("candidate_id"))] = candidate

    query_ids = [
        str(row.get("query_id"))
        for row in config.get("query_families") or []
        if isinstance(row, dict) and row.get("query_id")
    ]
    selected = scope.discovery.balanced_selection(kept, query_ids, target)
    counts["general_medical_cross_domain_excluded"] = (
        cross_domain_medical_excluded
    )
    counts["eligible_after_health_gate"] = len(kept)
    counts["selected_after_health_gate"] = len(selected)
    return selected, excluded, counts


scope.filter_candidates = strict_filter_candidates


if __name__ == "__main__":
    raise SystemExit(scope.main())
