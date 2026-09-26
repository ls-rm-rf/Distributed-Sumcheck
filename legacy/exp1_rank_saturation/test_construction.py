"""
Sanity test for exp1_rank_saturation.construction:

Verifies the C_k matrix matches paper §4.5 Example (n=3) row-by-row,
and that Lemma 4.4 (rank = 1+3k, 3n+3 at terminal) holds across all
three primes including PRIME_TINY at challenge values in {0, 1}.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from crypto_core import modular_rank as MR
from crypto_core.primes import PRIMES, PRIME_TINY, PRIME_MERSENNE_61, PRIME_RANDOM_61
from exp1_rank_saturation.construction import (
    build_C_k, expected_rank, gamma_dim, index_g0, index_g,
)


class TestExp1Construction(unittest.TestCase):

    def test_gamma_indices_n3(self):
        # n=3: dim is 12; layout [g0, g11..g13, g21..g23, g31..g35]
        self.assertEqual(gamma_dim(3), 12)
        self.assertEqual(index_g0(), 0)
        # g_{1,1..3} -> indices 1, 2, 3
        self.assertEqual(index_g(1, 1, 3), 1)
        self.assertEqual(index_g(1, 3, 3), 3)
        # g_{2,1..3} -> indices 4, 5, 6
        self.assertEqual(index_g(2, 1, 3), 4)
        self.assertEqual(index_g(2, 3, 3), 6)
        # g_{3,1..5} -> indices 7..11
        self.assertEqual(index_g(3, 1, 3), 7)
        self.assertEqual(index_g(3, 5, 3), 11)

    def test_paper_example_n3_initial_row_G(self):
        """
        Paper §4.5: G = 8 g_0 + 4 (S_1 + S_2 + S_3),
        where S_i = P_i(1):
          S_1 = g_{1,1} + g_{1,2} + g_{1,3}
          S_2 = g_{2,1} + g_{2,2} + g_{2,3}
          S_3 = g_{3,1} + g_{3,2} + g_{3,3} + g_{3,4} + g_{3,5}
        """
        p = 1_000_003
        C = build_C_k(n=3, k=0, challenges=[], p=p)
        self.assertEqual(len(C), 1)
        row = C[0]
        self.assertEqual(row[index_g0()], 8)
        for m in (1, 2, 3):
            self.assertEqual(row[index_g(1, m, 3)], 4)
            self.assertEqual(row[index_g(2, m, 3)], 4)
        for m in (1, 2, 3, 4, 5):
            self.assertEqual(row[index_g(3, m, 3)], 4)

    def test_paper_example_n3_H1_rows(self):
        """
        Paper §4.5: H_1(X) = 4 g_0 + 4 P_1(X) + 2 S_2 + 2 S_3
            c_0  : 4 on g_0; 2 on g_{2,m} (m=1..3); 2 on g_{3,m} (m=1..5)
            c_1  : 4 on g_{1,1}
            c_2  : 4 on g_{1,2}
            c_3  : 4 on g_{1,3}
        """
        p = 1_000_003
        C = build_C_k(n=3, k=1, challenges=[7], p=p)
        # 1 (G) + 4 (H_1) = 5 rows
        self.assertEqual(len(C), 5)
        c0 = C[1]
        self.assertEqual(c0[index_g0()], 4)
        for m in (1, 2, 3):
            self.assertEqual(c0[index_g(1, m, 3)], 0)  # H_1 const has no g_{1,*}
            self.assertEqual(c0[index_g(2, m, 3)], 2)
        for m in (1, 2, 3, 4, 5):
            self.assertEqual(c0[index_g(3, m, 3)], 2)
        # nonconstant rows
        c1, c2, c3 = C[2], C[3], C[4]
        for row, m_target in zip((c1, c2, c3), (1, 2, 3)):
            for idx, val in enumerate(row):
                if idx == index_g(1, m_target, 3):
                    self.assertEqual(val, 4)
                else:
                    self.assertEqual(val, 0,
                        f"H_1 c_{m_target} should only touch g_{{1,{m_target}}}")

    def test_paper_example_n3_H2_const_row_uses_r1(self):
        """
        Paper §4.5: H_2(X) = 2 g_0 + 2 P_1(r_1) + 2 P_2(X) + S_3
        c_0 of H_2: 2 g_0 + 2*r_1*g_{1,1} + 2*r_1^2*g_{1,2} + 2*r_1^3*g_{1,3}
                    + 1*g_{3,m} for m=1..5
        """
        p = 1_000_003
        r1 = 7
        C = build_C_k(n=3, k=2, challenges=[r1, 11], p=p)
        # rows: G, H_1's 4, H_2's 4 -> 9 rows
        self.assertEqual(len(C), 9)
        c0_H2 = C[5]  # row 5 = H_2's first
        self.assertEqual(c0_H2[index_g0()], 2)
        self.assertEqual(c0_H2[index_g(1, 1, 3)], (2 * r1) % p)
        self.assertEqual(c0_H2[index_g(1, 2, 3)], (2 * r1 * r1) % p)
        self.assertEqual(c0_H2[index_g(1, 3, 3)], (2 * r1 * r1 * r1) % p)
        # g_{2,*} should be 0 (H_2 has 2 P_2(X) which only contributes to nonconst rows)
        for m in (1, 2, 3):
            self.assertEqual(c0_H2[index_g(2, m, 3)], 0)
        # g_{3,*} should be 1 (S_3 = sum_{m=1..5} g_{3,m})
        for m in (1, 2, 3, 4, 5):
            self.assertEqual(c0_H2[index_g(3, m, 3)], 1)

    def test_lemma_44_rank_pattern_n3(self):
        """Paper §4.5: ranks are [1, 4, 7, 12] for n=3, k=0..3."""
        p = PRIME_MERSENNE_61
        challenges = [123, 456, 789]
        for k in range(4):
            C = build_C_k(n=3, k=k, challenges=challenges[:k], p=p)
            self.assertEqual(MR.rank(C, p), expected_rank(k, 3),
                             f"rank mismatch at n=3, k={k}")

    def test_lemma_44_holds_at_degenerate_challenges(self):
        """
        Paper construction: rank = 1+3k for ANY r in F_p, including 0 and 1.
        This is the key feature distinguishing it from a Vandermonde
        placeholder. Test ALL primes including PRIME_TINY (p=3).
        """
        for prime_label, p in PRIMES:
            for n in (2, 3, 4, 5):
                for challenges in [[0]*n, [1]*n, [0, 1, 0, 1, 0][:n]]:
                    for k in range(n + 1):
                        C = build_C_k(n=n, k=k, challenges=challenges[:k], p=p)
                        observed = MR.rank(C, p)
                        expected = expected_rank(k, n)
                        self.assertEqual(observed, expected,
                            f"FAIL prime={prime_label} n={n} k={k} "
                            f"challenges={challenges[:k]}: "
                            f"rank={observed} != expected={expected}")

    def test_dimensions_independent_of_k(self):
        """gamma_dim(n) is always 3n+3 -- does not change between ordinary and terminal."""
        for n in (1, 3, 5, 8):
            self.assertEqual(gamma_dim(n), 3 * n + 3)
            for k in range(n + 1):
                challenges = [11, 22, 33, 44, 55, 66, 77, 88][:k]
                C = build_C_k(n=n, k=k, challenges=challenges, p=PRIME_MERSENNE_61)
                # all rows have width 3n+3
                for row in C:
                    self.assertEqual(len(row), 3 * n + 3)

    def test_row_count(self):
        """Row count: 1 (k=0); 1+4k (1<=k<=n-1); 4n+3 (k=n)."""
        for n in (2, 3, 5, 8):
            for k in range(n + 1):
                challenges = list(range(2, 2 + k))  # avoid {0,1}
                C = build_C_k(n=n, k=k, challenges=challenges, p=PRIME_MERSENNE_61)
                if k == 0:
                    expected = 1
                elif k <= n - 1:
                    expected = 1 + 4 * k
                else:  # k == n
                    expected = 4 * n + 3
                self.assertEqual(len(C), expected,
                    f"row count mismatch at n={n}, k={k}: got {len(C)}, expected {expected}")


if __name__ == "__main__":
    unittest.main()
