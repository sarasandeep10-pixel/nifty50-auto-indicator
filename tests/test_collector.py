import unittest
from collector.fetch_official_reports import find_csv_link

class PublicLinkDiscoveryTest(unittest.TestCase):
    def test_finds_direct_csv_link_with_matching_label(self):
        html = b'<html><body><a href="/reports/fii-dii.csv">FII DII Download CSV</a></body></html>'
        link = find_csv_link("https://www.nseindia.com/reports/fii-dii", html, ("fii", "dii", "download"))
        self.assertIsNotNone(link)
        self.assertEqual(link[0], "https://www.nseindia.com/reports/fii-dii.csv")

    def test_does_not_guess_when_no_direct_csv_link_exists(self):
        html = b'<html><body><a href="/reports/fii-dii">FII DII page</a></body></html>'
        self.assertIsNone(find_csv_link("https://www.nseindia.com/reports/fii-dii", html, ("fii", "dii", "download")))

if __name__ == "__main__":
    unittest.main()
