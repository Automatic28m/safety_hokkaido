import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from evaluate import evaluate
from service import AuditStore, ValidationError


def event(request_id=None, **changes):
    value = {
        "request_id": request_id or str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "route": "rag",
        "degraded": False,
        "evidence_ids": ["chunk-1"],
        "source_versions": ["corpus-v1"],
        "evaluation_schema_version": "1",
        "index_version": "index-v1",
    }
    value.update(changes)
    return value


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = AuditStore(Path(self.temp.name) / "audit.sqlite3")

    def tearDown(self):
        self.temp.cleanup()

    def test_audit_and_feedback_round_trip(self):
        item = event()
        self.store.record_audit(item)
        self.assertEqual(self.store.get_audit(item["request_id"])["evidence_ids"], ["chunk-1"])
        self.store.record_feedback({"request_id": item["request_id"], "rating": "up"})
        self.store.record_feedback({"request_id": item["request_id"], "rating": "down"})
        with self.store._connect() as db:
            self.assertEqual(db.execute("SELECT rating FROM feedback").fetchone()[0], "down")

    def test_rejects_raw_query_and_bad_route(self):
        with self.assertRaises(ValidationError):
            self.store.record_audit(event(original_query="private"))
        with self.assertRaises(ValidationError):
            self.store.record_audit(event(route="safe"))

    def test_feedback_requires_existing_request_and_no_text(self):
        with self.assertRaises(ValidationError):
            self.store.record_feedback({"request_id": str(uuid4()), "rating": "up"})
        with self.assertRaises(ValidationError):
            self.store.record_feedback({"request_id": str(uuid4()), "rating": "up", "comment": "private"})

    def test_retention_removes_feedback_with_old_audit(self):
        old = event(timestamp=(datetime.now(timezone.utc) - timedelta(days=31)).isoformat())
        self.store.record_audit(old)
        self.store.record_feedback({"request_id": old["request_id"], "rating": "up"})
        self.assertEqual(self.store.prune(30), 1)
        self.assertIsNone(self.store.get_audit(old["request_id"]))
        with self.store._connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM feedback").fetchone()[0], 0)


class EvaluationTests(unittest.TestCase):
    def test_metrics_and_missing_case(self):
        golden = [
            {"question": "a", "expected_chunk_ids": ["x"]},
            {"question": "b", "expected_chunk_ids": ["y"]},
        ]
        predictions = [{
            "question": "a", "retrieved_chunk_ids": ["z", "x"],
            "judge_scores": {"faithfulness": 9, "relevance": 8},
        }]
        report = evaluate(golden, predictions)
        self.assertEqual(report["hit_rate"], 0.5)
        self.assertEqual(report["mrr"], 0.25)
        self.assertEqual(report["judged_count"], 1)
        self.assertEqual(len(report["failures"]), 1)


if __name__ == "__main__":
    unittest.main()
