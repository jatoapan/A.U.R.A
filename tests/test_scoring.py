import unittest

import pandas as pd

from src.app.scoring import compute_hybrid_score


class TestScoring(unittest.TestCase):
    def test_hybrid_score_range(self):
        s = compute_hybrid_score(
            pd.Series([35]),
            pd.Series([0.8]),
            pd.Series([0.5]),
        )
        self.assertGreaterEqual(int(s.iloc[0]), 0)
        self.assertLessEqual(int(s.iloc[0]), 100)


if __name__ == "__main__":
    unittest.main()
