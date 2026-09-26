"""Independent Libra Section 4.1 Construction 1 mask constraints.

Source: https://www.cs.yale.edu/homes/cpap/published/libra-crypto19.pdf
g = a0 + sum_i sum_{m=1}^d a[i,m] X_i^m; dimension 1+n*d.
C_k includes the Boolean-sum claim and round evaluations at 0,...,d.
Prediction derived from the chain constraint: rank(C_k)=1+d*k,
residual dimension d*(n-k), including terminal saturation at k=n.
Only the algebraic mask map is tested; commitments and full GKR are out of scope.
"""
from itertools import product


def mask_value(coefficients, point, degree, p):
    return (coefficients[0] + sum(
        coefficients[1 + i*degree + m-1] * pow(x, m, p)
        for i, x in enumerate(point) for m in range(1, degree+1))) % p


def build_libra_constraints(n, k, challenges, p, degree=2):
    if n < 1 or not 0 <= k <= n or len(challenges) < k:
        raise ValueError("invalid round parameters")
    if p == 2 or degree < 1 or degree >= p:
        raise ValueError("need odd p and 1 <= degree < p for distinct evaluations")
    # Build the linear functional directly on the monomial basis.
    # No LXYY matrix or special terminal degree is used.
    claim = [pow(2, n, p)] + [pow(2, n-1, p)] * (n*degree)
    rows = [claim]
    for j in range(k):
        for x in range(degree+1):
            weight = pow(2, n-j-1, p)
            row = [weight]
            for i in range(n):
                for m in range(1, degree+1):
                    if i < j:
                        entry = weight * pow(challenges[i], m, p)
                    elif i == j:
                        entry = weight * pow(x, m, p)
                    else:
                        entry = pow(2, n-j-2, p)
                    row.append(entry % p)
            rows.append(row)
    return rows


def direct_transcript(coefficients, n, k, challenges, p, degree=2):
    """Independent exhaustive Boolean-sum oracle, used in tests only."""
    values = [sum(mask_value(coefficients, point, degree, p)
                  for point in product((0, 1), repeat=n)) % p]
    for j in range(k):
        for x in range(degree+1):
            values.append(sum(mask_value(
                coefficients, list(challenges[:j]) + [x] + list(tail), degree, p)
                for tail in product((0, 1), repeat=n-j-1)) % p)
    return values

