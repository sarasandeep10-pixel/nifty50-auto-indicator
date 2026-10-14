import unittest
from collector.collect_fii_dii import parse_page

class FiiDiiParserTest(unittest.TestCase):
    def test_parses_rows_and_checks_net_arithmetic(self):
        html = b"""<html><table>
        <tr><th>Category</th><th>Date</th><th>Buy Value (Rs Crores)</th><th>Sell Value (Rs Crores)</th><th>Net Value (Rs Crores)</th></tr>
        <tr><td>DII</td><td>14-Oct-2026</td><td>1,200.50</td><td>900.25</td><td>300.25</td></tr>
        <tr><td>FII/FPI</td><td>14-Oct-2026</td><td>800</td><td>1,050</td><td>-250</td></tr>
        </table></html>"""
        rows, rejected = parse_page(html)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rejected, [])
        self.assertTrue(all(r["net_matches_buy_minus_sell"] for r in rows))
        self.assertEqual(rows[0]["net_crore_calculated"], 300.25)

    def test_rejects_arithmetic_mismatch(self):
        html = b"""<table>
        <tr><td>FII/FPI</td><td>14-Oct-2026</td><td>800</td><td>1,050</td><td>-100</td></tr>
        </table>"""
        rows, _ = parse_page(html)
        self.assertEqual(len(rows), 1)
        self.assertFalse(rows[0]["net_matches_buy_minus_sell"])

if __name__ == "__main__":
    unittest.main()
