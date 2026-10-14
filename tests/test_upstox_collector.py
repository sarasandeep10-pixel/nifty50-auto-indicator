import unittest
from collector.fetch_upstox_institutional_data import normalize

class UpstoxNormalizeTest(unittest.TestCase):
    def test_normalizes_amounts_and_net(self):
        data = {
            "NSE_EQ|CASH": [{
                "time_stamp": 1791849600000,
                "buy_amount": 12_000_000_000,
                "sell_amount": 9_000_000_000,
                "buy_contracts": 0,
                "sell_contracts": 0,
            }]
        }
        rows = normalize("dii", data)["NSE_EQ|CASH"]
        self.assertEqual(rows[0]["buy_crore"], 1200.0)
        self.assertEqual(rows[0]["sell_crore"], 900.0)
        self.assertEqual(rows[0]["net_crore_calculated"], 300.0)
        self.assertTrue(rows[0]["date"])

    def test_rejects_missing_timestamp(self):
        with self.assertRaises(RuntimeError):
            normalize("fii", {"NSE_EQ|CASH": [{"buy_amount": 10, "sell_amount": 5}]})

    def test_rejects_missing_buy_sell(self):
        with self.assertRaises(RuntimeError):
            normalize("fii", {"NSE_EQ|CASH": [{"time_stamp": 1791849600000, "buy_amount": 10}]})

if __name__ == "__main__":
    unittest.main()
