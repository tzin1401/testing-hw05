import unittest

from summarize import bucket_index, is_main, percentile, soak_summary


class SummarizeTests(unittest.TestCase):
    def test_nearest_rank(self):
        self.assertEqual(percentile(list(range(1, 21))), 19)
        self.assertEqual(percentile([42]), 42)

    def test_bucket_edges_and_partial_minute(self):
        self.assertEqual(bucket_index(60999, 1000), 0)
        self.assertEqual(bucket_index(61000, 1000), 1)
        samples = [
            {'start': 1000, 'elapsed': 10, 'success': True, 'thread': 'a'},
            {'start': 61000, 'elapsed': 1000, 'success': False, 'thread': 'a'},
        ]
        minutes = soak_summary(samples)['minutes']
        self.assertEqual([m['sample_count'] for m in minutes], [1, 1])
        self.assertEqual(minutes[0]['window_seconds'], 60)
        self.assertEqual(minutes[1]['window_seconds'], 1)
        self.assertEqual(minutes[1]['rps'], 1)

    def test_negative_exclusion(self):
        self.assertFalse(is_main({'label': 'Negative login'}))
        self.assertTrue(is_main({'label': '01 Login'}))


if __name__ == '__main__':
    unittest.main()
