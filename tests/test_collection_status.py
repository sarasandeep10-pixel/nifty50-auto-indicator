import json
import tempfile
import unittest
from pathlib import Path
from collector.validate_collection_status import inspect

class CollectionStatusTest(unittest.TestCase):
    def test_missing_reports_are_reported_as_issues(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issues = inspect(root / "processed", root / "official")
            self.assertTrue(any("FII/DII" in issue for issue in issues))
            self.assertTrue(any("participant-wise OI" in issue for issue in issues))

    def test_valid_fii_rows_still_require_participant_schema_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            processed = root / "processed"
            official = root / "official"
            processed.mkdir()
            official.mkdir()
            (processed / "fii_dii_latest.json").write_text(json.dumps({
                "validated": True,
                "rows": [{"net_matches_buy_minus_sell": True}]
            }), encoding="utf-8")
            (official / "collection_status.json").write_text(json.dumps({
                "sources": [{
                    "name": "participant_oi",
                    "downloaded": True,
                    "file": str(official / "participant_oi.csv")
                }]
            }), encoding="utf-8")
            (official / "participant_oi.csv").write_text("sample", encoding="utf-8")
            issues = inspect(processed, official)
            self.assertTrue(any("schema validation is not implemented" in issue for issue in issues))

if __name__ == "__main__":
    unittest.main()
