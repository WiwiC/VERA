import unittest
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.scoring_utils import compute_tiered_score

class TestScoringUtils(unittest.TestCase):

    def setUp(self):
        # Define a standard test configuration
        self.config = [
            {"max": 10, "tier": (0.0, 0.4), "label": "low"},
            {"max": 20, "tier": (0.4, 0.8), "label": "mid"},
            {"max": 30, "tier": (0.8, 1.0), "label": "optimal"},   # Parabolic trigger
            {"max": 40, "tier": (0.4, 0.8), "label": "high"},
            {"max": 999, "tier": (0.0, 0.4), "label": "very_high"}
        ]

    def test_linear_interpolation_low(self):
        # Range: 0-10, Tier: 0.0-0.4
        # Value 5 is midpoint -> Score should be 0.2
        score = compute_tiered_score(5, self.config)
        self.assertAlmostEqual(score, 0.2, places=2)

    def test_linear_interpolation_mid(self):
        # Range: 10-20, Tier: 0.4-0.8
        # Value 15 is midpoint -> Score should be 0.6
        score = compute_tiered_score(15, self.config)
        self.assertAlmostEqual(score, 0.6, places=2)

    def test_parabolic_optimal_peak(self):
        # Range: 20-30, Tier: 0.8-1.0
        # Value 25 is exact center -> Score should be 1.0
        score = compute_tiered_score(25, self.config)
        self.assertAlmostEqual(score, 1.0, places=2)

    def test_parabolic_optimal_edges(self):
        # Range: 20-30, Tier: 0.8-1.0
        # Value 20 (start) -> Score should be 0.8
        score_start = compute_tiered_score(20, self.config)
        self.assertAlmostEqual(score_start, 0.8, places=2)

        # Value 30 (end) -> Score should be 0.8
        score_end = compute_tiered_score(30, self.config)
        self.assertAlmostEqual(score_end, 0.8, places=2)

    def test_parabolic_optimal_intermediate(self):
        # Range: 20-30, Tier: 0.8-1.0
        # Value 22.5 (25% into range)
        # Parabola: y = 1.0 - k*(x - center)^2
        # It should be significantly higher than linear (0.85)
        score = compute_tiered_score(22.5, self.config)
        self.assertTrue(score > 0.85)
        self.assertTrue(score < 1.0)

    def test_boundary_exact_match(self):
        # Exact boundary 10 -> Should belong to the first bucket (inclusive max)
        # OR second bucket depending on implementation logic.
        # In our logic: "x <= bucket['max']" finds the first match.
        # So 10 matches the first bucket (max=10).
        # Score at max=10 for Tier 0.0-0.4 is 0.4.
        score = compute_tiered_score(10, self.config)
        self.assertAlmostEqual(score, 0.4, places=2)

    def test_out_of_bounds_high(self):
        # Value 1000 -> Last bucket (max=999)
        # Range: 40-999, Tier: 0.0-0.4 (inverted)
        # 1000 > 999, effectively clamped to max or treated as max
        score = compute_tiered_score(1000, self.config)
        # Should be close to 0.0 since it's at the extreme end
        self.assertTrue(0.0 <= score <= 0.1)

    def test_inverted_tier(self):
        # Test a bucket where score goes down as value goes up
        # Bucket 4: 40-999, Tier: 0.0-0.4
        # Value 40 (start) -> 0.4
        # Value 999 (end) -> 0.0
        score_start = compute_tiered_score(40.01, self.config) # Just inside
        self.assertAlmostEqual(score_start, 0.4, places=1)

        score_mid = compute_tiered_score(520, self.config) # Approx mid
        self.assertAlmostEqual(score_mid, 0.2, places=1)

if __name__ == '__main__':
    unittest.main()
