"""Unit tests for crypto_core.field_arithmetic."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import unittest
from crypto_core import field_arithmetic as F
from crypto_core.primes import PRIME_TINY, PRIME_MERSENNE_61, PRIME_RANDOM_61


class TestFieldArithmetic(unittest.TestCase):

    def test_basic_ops(self):
        for p in (PRIME_TINY, 7, 11, PRIME_MERSENNE_61, PRIME_RANDOM_61):
            self.assertEqual(F.add(p - 1, 1, p), 0)
            self.assertEqual(F.sub(0, 1, p), p - 1)
            self.assertEqual(F.mul(2, 3, p), 6 % p)
            self.assertEqual(F.neg(5, p), (-5) % p)

    def test_inverse(self):
        for p in (PRIME_TINY, 7, 11, PRIME_MERSENNE_61):
            for a in [1, 2, p - 1, p // 2]:
                if a == 0:
                    continue
                self.assertEqual(F.mul(a, F.inv(a, p), p), 1)
        with self.assertRaises(ZeroDivisionError):
            F.inv(0, 7)

    def test_pow_mod(self):
        self.assertEqual(F.pow_mod(2, 10, 1000003), pow(2, 10, 1000003))
        self.assertEqual(F.pow_mod(3, 0, 7), 1)

    def test_vec_ops(self):
        u = [1, 2, 3]
        v = [4, 5, 6]
        self.assertEqual(F.vec_add(u, v, 7), [5, 0, 2])
        self.assertEqual(F.vec_sub(u, v, 7), [4, 4, 4])
        self.assertEqual(F.vec_dot(u, v, 100), 32)
        self.assertEqual(F.vec_scale(2, u, 7), [2, 4, 6])

    def test_mat_mul(self):
        A = [[1, 2], [3, 4]]
        B = [[5, 6], [7, 8]]
        # AB = [[19, 22], [43, 50]]
        self.assertEqual(F.mat_mul(A, B, 100), [[19, 22], [43, 50]])
        self.assertEqual(F.mat_mul(A, B, 10), [[9, 2], [3, 0]])


if __name__ == "__main__":
    unittest.main()
