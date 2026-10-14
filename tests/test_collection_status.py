import csv
import json
import tempfile
import unittest
from pathlib import Path
from collector.validate_collection_status import inspect, validate_participant_csv

class CollectionStatusTest(unittest.TestCase):
    def test_missing_reports_are_reported_as_issues(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issues = inspect(root / "processed", root / "official")
            self.assertTrue(any("FII/DII" in issue for issue in issues))
            self.assertTrue(any("Participant-wise OI report was not downloaded" in issue for issue in issues))

    def test_valid_participant_csv_passes_schema_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            processed = root / "processed"
            official = root / "official"
            processed.mkdir()
            official.mkdir()
            (processed / "fii_dii_latest.json").write_text(json.dumps({
                "validated": True,
                "rows": [{"date": "14-Oct-2026", "net_matches_buy_minus_sell": True}]
            }), encoding="utf-8")
            oi = official / "participant_oi.csv"
            oi.write_text("Client Type,Future Index Long,Future Index Short\nFII,100,160\nDII,75,25\n", encoding="utf-8")
            (official / "collection_status.json").write_text(json.dumps({
                "sources": [{"name": "participant_oi", "downloaded": True, "file": str(oi)}]
            }), encoding="utf-8")
            self.assertIsNone(validate_participant_csv(oi))
            self.assertEqual(inspect(processed, official), [])

    def test_unknown_columns_fail_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            oi = Path(tmp) / "bad.csv"
            oi.write_text("foo,bar\na,b\n", encoding="utf-8")
            self.assertIn("missing required columns", validate_participant_csv(oi))

if __name__ == "__main__":
    unittest.main()
