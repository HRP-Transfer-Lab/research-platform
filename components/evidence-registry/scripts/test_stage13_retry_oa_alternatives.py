#!/usr/bin/env python3
from __future__ import annotations

import unittest

import stage13_retry_oa_alternatives as retry


class AlternativeCandidateTests(unittest.TestCase):
    def test_skips_failed_url_and_prefers_epmc_repository(self) -> None:
        discovery = {
            "preferred_candidate": {
                "provider": "unpaywall",
                "url": "https://publisher.example/failed.pdf",
                "host_type": "publisher",
            },
            "unpaywall": {
                "locations": [
                    {
                        "url_for_pdf": "https://publisher.example/failed.pdf",
                        "host_type": "publisher",
                        "version": "publishedVersion",
                        "license": "cc-by",
                    },
                    {
                        "url_for_pdf": "https://repo.example/manuscript.pdf",
                        "host_type": "repository",
                        "version": "acceptedVersion",
                        "license": "cc-by",
                    },
                ]
            },
            "europe_pmc": {
                "full_text_urls": [
                    {
                        "url": "https://pmc.example/main.pdf",
                        "document_style": "pdf",
                    }
                ]
            },
        }
        rows = retry.collect_alternative_candidates(
            discovery,
            failed_url="https://publisher.example/failed.pdf",
            include_original=False,
        )
        self.assertEqual(
            [row["url"] for row in rows],
            [
                "https://pmc.example/main.pdf",
                "https://repo.example/manuscript.pdf",
            ],
        )

    def test_deduplicates_urls(self) -> None:
        discovery = {
            "unpaywall": {
                "locations": [
                    {
                        "url_for_pdf": "https://repo.example/paper.pdf",
                        "host_type": "repository",
                    },
                    {
                        "url_for_pdf": "https://repo.example/paper.pdf",
                        "host_type": "publisher",
                    },
                ]
            },
            "europe_pmc": {"full_text_urls": []},
        }
        rows = retry.collect_alternative_candidates(
            discovery, failed_url=None, include_original=False
        )
        self.assertEqual(len(rows), 1)

    def test_ignores_non_pdf_epmc_links(self) -> None:
        discovery = {
            "unpaywall": {"locations": []},
            "europe_pmc": {
                "full_text_urls": [
                    {
                        "url": "https://pmc.example/article",
                        "document_style": "html",
                    },
                    {
                        "url": "https://pmc.example/article.pdf",
                        "document_style": "pdf",
                    },
                ]
            },
        }
        rows = retry.collect_alternative_candidates(
            discovery, failed_url=None, include_original=False
        )
        self.assertEqual(
            [row["url"] for row in rows],
            ["https://pmc.example/article.pdf"],
        )

    def test_can_include_original_candidate_deliberately(self) -> None:
        original = {
            "provider": "unpaywall",
            "url": "https://publisher.example/original.pdf",
            "host_type": "publisher",
        }
        discovery = {
            "preferred_candidate": original,
            "unpaywall": {"locations": []},
            "europe_pmc": {"full_text_urls": []},
        }
        rows = retry.collect_alternative_candidates(
            discovery,
            failed_url=original["url"],
            include_original=True,
        )
        self.assertEqual([row["url"] for row in rows], [original["url"]])


if __name__ == "__main__":
    unittest.main()
