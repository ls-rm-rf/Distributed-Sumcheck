"""
Full-vs-Kernel mask comparison (V3 §6.7, fixed subplot per advisor sign-off).

Compares two refresh schemes:
    - FULL  : refresh the whole mask coordinate space (3n+3 fixed)
    - KERNEL: refresh only the kernel-restricted mask (3(n-k)+2 at round k)

Default boundary policy K_refresh = {1, ..., n-1}  (V3 §6.8 sign-off).

We provide TWO totalization variants:
    full_total(n)         : (n - 1) * (3n + 3)         (constant per round * |K|)
    kernel_total(n, K)    : sum over k in K of d_k_kernel(n, k)

Used by benchmark.py to populate boundary_policy column and to plot
the fixed Full-vs-Kernel subplot.
"""

from typing import Iterable
from exp3_communication.state_size import d_k_full, d_k_kernel


def default_K_refresh(n: int):
    """V3 sign-off default refresh-round set: {1, ..., n-1}."""
    return list(range(1, n))


def refresh_boundaries(n: int, policy: str):
    if policy == "fold_after":
        return default_K_refresh(n)
    if policy == "fold_before":
        return list(range(n - 1))
    raise ValueError(f"unknown boundary policy: {policy}")


def full_per_round(n: int) -> int:
    """Constant per-round full mask coordinate dim."""
    return d_k_full(n)


def full_total(n: int, K_refresh: Iterable[int] = None) -> int:
    if K_refresh is None:
        K_refresh = default_K_refresh(n)
    return sum(d_k_full(n) for _ in K_refresh)


def kernel_per_round(n: int, k: int) -> int:
    return d_k_kernel(n, k)


def kernel_total(n: int, K_refresh: Iterable[int] = None) -> int:
    if K_refresh is None:
        K_refresh = default_K_refresh(n)
    return sum(d_k_kernel(n, k) for k in K_refresh)


def full_vs_kernel_ratio(n: int, K_refresh: Iterable[int] = None) -> float:
    """full_total / kernel_total -- pure ratio for plotting."""
    K_refresh = list(K_refresh) if K_refresh is not None else default_K_refresh(n)
    if not K_refresh:
        return 1.0
    kt = kernel_total(n, K_refresh)
    if kt == 0:
        return float("inf")
    return full_total(n, K_refresh) / kt
