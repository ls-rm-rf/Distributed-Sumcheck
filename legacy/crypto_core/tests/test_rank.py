"""Unit tests for crypto_core.modular_rank."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import unittest
import random
from crypto_core import modular_rank as MR
from crypto_core import field_arithmetic as F
from crypto_core.primes import PRIME_TINY, PRIME_MERSENNE_61


class TestModularRank(unittest.TestCase):

    def test_rank_simple(self):
        # rank of identity = n
        for n in (1, 3, 5, 8):
            I = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
            self.assertEqual(MR.rank(I, 7), n)
            self.assertEqual(MR.rank(I, PRIME_MERSENNE_61), n)

    def test_rank_zero_matrix(self):
        Z = [[0, 0], [0, 0]]
        self.assertEqual(MR.rank(Z, 7), 0)

    def test_rank_dependent_rows(self):
        M = [[1, 2, 3], [2, 4, 6], [0, 0, 0]]
        self.assertEqual(MR.rank(M, 11), 1)
        self.assertEqual(MR.rank(M, PRIME_MERSENNE_61), 1)

    def test_rank_full(self):
        M = [[1, 2], [3, 4]]
        # det = 1*4 - 2*3 = -2
        self.assertEqual(MR.rank(M, 7), 2)  # -2 mod 7 = 5 ≠ 0
        # over F_2 det would be 0 but we don't test p=2

    def test_kernel_basis_correctness(self):
        # M maps (x,y,z) → (x+y+z, x-y); ker is 1-dim if rank=2 over 3 vars
        rng = random.Random(0)
        for p in (7, 11, PRIME_MERSENNE_61):
            for _ in range(10):
                rows = rng.randint(2, 4)
                cols = rng.randint(rows + 1, rows + 3)
                M = [[rng.randrange(p) for _ in range(cols)] for _ in range(rows)]
                B = MR.kernel_basis(M, p)
                # every basis vector should be in kernel
                for v in B:
                    Mv = F.mat_vec(M, v, p)
                    self.assertEqual(Mv, [0] * rows)
                # rank-nullity
                r = MR.rank(M, p)
                self.assertEqual(len(B), cols - r)

    def test_projected_nullity_secret_recoverable(self):
        # If e_0 is in rowspan(M), then projected_nullity(M, [0]) == 0.
        # Trivial example: M = [[1,0,0]], indices=[0]
        self.assertEqual(MR.projected_nullity([[1, 0, 0]], [0], 7), 0)
        # M = [[0,1,0]], project on [0]: kernel of M = span((1,0,0),(0,0,1));
        # restricted to row 0 = (1, 0); rank = 1
        self.assertEqual(MR.projected_nullity([[0, 1, 0]], [0], 7), 1)

    def test_residual_dim_known(self):
        # Constructed: M ∈ F^{2×4} = [[1,0,0,0],[0,1,0,0]]
        # ker M = span((0,0,1,0),(0,0,0,1))
        # project on indices [2,3] gives full rank 2
        M = [[1, 0, 0, 0], [0, 1, 0, 0]]
        self.assertEqual(MR.projected_nullity(M, [2, 3], 11), 2)
        # project on [0,1] gives rank 0 (kernel basis has 0 in those coords)
        self.assertEqual(MR.projected_nullity(M, [0, 1], 11), 0)


if __name__ == "__main__":
    unittest.main()
