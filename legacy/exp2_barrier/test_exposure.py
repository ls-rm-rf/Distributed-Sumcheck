import unittest
from exp2_barrier.one_more_exposure import evaluate


class TestOneMoreExposure(unittest.TestCase):
    def test_overlap_alone_does_not_recover_secret(self):
        self.assertEqual(evaluate(3, 3, 101, False), (0, 0))

    def test_one_new_post_share_recovers_at_full_overlap(self):
        self.assertEqual(evaluate(3, 3, 101, True), (1, 0))

    def test_partial_overlap_retains_transition_dimension(self):
        for c in (0, 1, 2):
            self.assertEqual(evaluate(3, c, 101, True), (0, 3-c))

