"""
Prime constants and registry for all experiments.

Conventions (from V3 §0):
- All experiments run over a prime field F_p.
- p = 2 is NOT supported (Lemma 4.4 needs odd characteristic).
- Three primes are used in sweeps:
    PRIME_TINY        = 3                          (extreme small-field stress)
    PRIME_MERSENNE_61 = 2^61 - 1                   (standard Mersenne prime)
    PRIME_RANDOM_61   = 2305843009213693967        (random 61-bit prime)
"""

PRIME_TINY = 3
PRIME_MERSENNE_61 = (1 << 61) - 1
PRIME_RANDOM_61 = 2305843009213693967


PRIMES = [
    ("PRIME_TINY", PRIME_TINY),
    ("PRIME_MERSENNE_61", PRIME_MERSENNE_61),
    ("PRIME_RANDOM_61", PRIME_RANDOM_61),
]


def is_probable_prime(n: int, k: int = 20) -> bool:
    """Miller-Rabin probabilistic primality (used only for sanity checks)."""
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n == p:
            return True
        if n % p == 0:
            return False
    import random
    d = n - 1
    r = 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for _ in range(k):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = (x * x) % n
            if x == n - 1:
                break
        else:
            return False
    return True


# Verify constants on import.
assert PRIME_TINY == 3
assert PRIME_MERSENNE_61 == 2305843009213693951
assert is_probable_prime(PRIME_MERSENNE_61)
assert is_probable_prime(PRIME_RANDOM_61)
