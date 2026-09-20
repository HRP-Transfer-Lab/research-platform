import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("research_scout", HERE / "research_scout.py")
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class ResearchScoutTests(unittest.TestCase):
    def test_attention_anchor_rejects_generic_control_noise(self):
        topic = {"anchors": ["attention control", "cognitive control", "executive attention"]}
        self.assertTrue(module.title_relevant("Adaptive cognitive control under distraction", topic))
        self.assertFalse(module.title_relevant("AI-enabled force and torque control for human robot interaction", topic))

    def test_candidate_is_discovery_only(self):
        topic = {"consumers": ["IQM"], "anchors": ["cognitive control"]}
        item = module._candidate(
            source="TEST",
            title="Cognitive control and learning",
            topic_id="attention_control",
            topic=topic,
            external_id="123",
        )
        self.assertEqual(item["discovery_status"], "DISCOVERED_UNSCREENED")
        self.assertEqual(item["claim_status"], "NO_PUBLIC_CLAIM")
        self.assertTrue(item["human_review_required"])
        self.assertEqual(item["next_gate"], "SCREEN_IN_EVIDENCE_WORKBENCH")

    def test_dedupe_prefers_identifier(self):
        topic = {"consumers": ["IQM"], "anchors": ["cognitive control"]}
        a = module._candidate(source="TEST", title="A", topic_id="x", topic=topic, doi="10.1/x")
        b = module._candidate(source="OTHER", title="B", topic_id="y", topic=topic, doi="10.1/x")
        self.assertEqual(len(module.dedupe([a, b])), 1)

    def test_config_forbids_canonical_write(self):
        cfg = module.load_config(HERE / "scout-config.json")
        self.assertTrue(cfg["policy"]["discovery_only"])
        self.assertTrue(cfg["policy"]["human_review_required"])
        self.assertFalse(cfg["policy"]["canonical_write_enabled"])


if __name__ == "__main__":
    unittest.main()
