import unittest

import data_utils as du


class SalesDataTests(unittest.TestCase):
    def test_dataset_is_valid_and_complete(self):
        data = du._load()
        self.assertEqual(data["record_count"], 1_000)
        self.assertEqual(len(data["records"]), 1_000)
        self.assertEqual(len({record["id"] for record in data["records"]}), 1_000)

    def test_summary_uses_every_record(self):
        summary = du.team_target_summary()
        self.assertEqual(summary["record_count"], 1_000)
        self.assertGreater(summary["team_target"], 0)
        self.assertGreater(summary["team_achieved"], 0)

    def test_filter_and_dimension_rollup(self):
        north = du.team_target_summary(region="north")
        self.assertEqual(north["record_count"], 200)
        self.assertEqual(sum(group["reps"] for group in du.region_breakdown().values()), 1_000)

    def test_large_results_are_paginated_and_capped(self):
        page = du.full_leaderboard(page=2, page_size=500)
        self.assertEqual(page["page_size"], 100)
        self.assertEqual(page["total"], 1_000)
        self.assertEqual(len(page["items"]), 100)

    def test_employee_code_lookup(self):
        result = du.individual_performance("SR-0001")
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["items"][0]["id"], 1)

    def test_bad_status_is_rejected(self):
        with self.assertRaises(ValueError):
            du.performers_by_status("unknown")


if __name__ == "__main__":
    unittest.main()
