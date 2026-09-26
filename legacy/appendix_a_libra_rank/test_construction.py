import random
import unittest
from crypto_core.modular_rank import rank, kernel_basis
from appendix_a_libra_rank.construction import build_libra_constraints, direct_transcript


class TestLibraConstruction(unittest.TestCase):
    def test_matrix_matches_direct_boolean_sums(self):
        rng = random.Random(42)
        for p, degree in ((3, 2), (101, 2), (101, 3)):
            for n in (1, 3, 5):
                coeffs = [rng.randrange(p) for _ in range(1+n*degree)]
                for policy in ("random", "zero_one"):
                    r = [rng.randrange(p if policy == "random" else 2) for _ in range(n)]
                    for k in range(n+1):
                        C = build_libra_constraints(n, k, r, p, degree)
                        observed = [sum(a*b for a, b in zip(row, coeffs)) % p for row in C]
                        self.assertEqual(observed, direct_transcript(coeffs, n, k, r, p, degree))

    def test_uniform_degree_terminal_saturates(self):
        for p in (3, 101):
            for n in (1, 3, 7):
                for k in range(n+1):
                    C = build_libra_constraints(n, k, [0, 1]*n, p)
                    self.assertEqual(rank(C, p), 1+2*k)
                    self.assertEqual(len(kernel_basis(C, p)), 2*(n-k))

    def test_kernel_remask_preserves_direct_transcript(self):
        n, k, p = 3, 2, 101
        r = [0, 1, 7]
        coeffs = list(range(7))
        C = build_libra_constraints(n, k, r, p)
        expected = direct_transcript(coeffs, n, k, r, p)
        for direction in kernel_basis(C, p):
            refreshed = [(x+11*y) % p for x, y in zip(coeffs, direction)]
            self.assertEqual(direct_transcript(refreshed, n, k, r, p), expected)

