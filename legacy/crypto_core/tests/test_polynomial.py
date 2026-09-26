"""Unit tests for crypto_core.polynomial."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import unittest
import random
from crypto_core import polynomial as P
from crypto_core.primes import PRIME_MERSENNE_61


class TestPolynomial(unittest.TestCase):

    def test_eval_constant(self):
        self.assertEqual(P.poly_eval([5], 100, 7), 5)
        self.assertEqual(P.poly_eval([0, 1], 3, 100), 3)  # f(X)=X, f(3)=3

    def test_add_sub_mul(self):
        a = [1, 2, 3]   # 1+2X+3X²
        b = [4, 5]      # 4+5X
        # a+b = [5,7,3]
        self.assertEqual(P.poly_add(a, b, 100), [5, 7, 3])
        # a*b = (1+2X+3X²)(4+5X) = 4+13X+22X²+15X³
        self.assertEqual(P.poly_mul(a, b, 100), [4, 13, 22, 15])

    def test_lagrange_interpolate(self):
        # f(X) = 2 + 3X + X²;  values at 1,2,3 are 6, 12, 20
        p = PRIME_MERSENNE_61
        f = [2, 3, 1]
        pts = [1, 2, 3]
        vals = [P.poly_eval(f, x, p) for x in pts]
        rec = P.lagrange_interpolate(pts, vals, p)
        self.assertEqual(rec, f)

    def test_random_poly_roundtrip(self):
        rng = random.Random(42)
        p = PRIME_MERSENNE_61
        for _ in range(5):
            d = rng.randint(0, 6)
            f = P.random_poly_at_most(d, p, rng)
            xs = [rng.randrange(1, p) for _ in range(d + 1)]
            xs = list(dict.fromkeys(xs))[:d + 1]
            while len(xs) < d + 1:
                cand = rng.randrange(1, p)
                if cand not in xs:
                    xs.append(cand)
            ys = [P.poly_eval(f, x, p) for x in xs]
            rec = P.lagrange_interpolate(xs, ys, p)
            for x in xs:
                self.assertEqual(P.poly_eval(rec, x, p), P.poly_eval(f, x, p))


if __name__ == "__main__":
    unittest.main()
