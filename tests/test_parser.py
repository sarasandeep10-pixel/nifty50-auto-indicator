import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "collector" / "parse_nse_reports.py"


class ParserSmokeTest(unittest.TestCase):
    def test_parses_participant_oi_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "sample.csv"
            output = root / "out"
            with source.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Client Type", "Future Index Long", "Future Index Short"])
                writer.writerow(["FII", "100", "160"])
                writer.writerow(["DII", "75", "25"])

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--input", str(source),
                 "--output", str(output), "--report-date", "2026-10-14"],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads((output / "participant_oi_2026-10-14.json").read_text())
            self.assertEqual(report["participants"]["FII"]["net_long_minus_short"], -60)
            self.assertEqual(report["participants"]["DII"]["net_long_minus_short"], 50)
            self.assertFalse(report["validated"])

    def test_rejects_unknown_headers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "bad.csv"
            source.write_text("foo,bar\na,b\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--input", str(source)],
                check=False, capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Could not safely map required columns", result.stderr)


if __name__ == "__main__":
    unittest.main()
