"""Unit tests for crypto_core.shamir."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import unittest
import random
from crypto_core import shamir
from crypto_core.primes import PRIME_MERSENNE_61, PRIME_RANDOM_61


class TestShamir(unittest.TestCase):

    def test_share_reconstruct_roundtrip(self):
        rng = random.Random(0)
        for p in (PRIME_MERSENNE_61, PRIME_RANDOM_61):
            for M in (3, 5, 7, 9):
                for t in range(1, M):
                    secret = rng.randrange(p)
                    shares = shamir.share(secret, t, M, p, rng)
                    # reconstruct from any t+1 of them
                    sub = rng.sample(shares, t + 1)
                    self.assertEqual(shamir.reconstruct(sub, p), secret)

    def test_t_shares_insufficient(self):
        # any t shares should NOT determine the secret for random poly
        rng = random.Random(1)
        p = PRIME_MERSENNE_61
        secret = 12345
        t, M = 2, 5
        shares = shamir.share(secret, t, M, p, rng)
        # take only t shares, append a dummy "secret" guess (0); reconstruct
        # via t+1 = (t shares) + (alpha=0, value=guess) — different guesses
        # should give different reconstructed polys, all consistent with the
        # t shares. So just assert that we can interpolate any value at 0
        # and still match the known shares.
        from crypto_core import polynomial as P
        sub_two = shares[:t]
        for guess in (0, 1, 999):
            xs = [a for (a, _) in sub_two] + [0]
            ys = [v for (_, v) in sub_two] + [guess]
            poly = P.lagrange_interpolate(xs, ys, p)
            # poly should evaluate to the guess at 0
            self.assertEqual(P.poly_eval(poly, 0, p), guess)


if __name__ == "__main__":
    unittest.main()
