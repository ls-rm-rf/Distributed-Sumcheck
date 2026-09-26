"""
Abort-restart estimate for refresh-fault recovery (V3 §6.9 closed form).

When a refresh attempt aborts at round k, two recovery strategies exist:

    - RestartCost(n, k)   : restart the whole protocol
                              -> cost = lxyy_verify_per_party(n)   (full re-verify)

    - PrefixCost(n, k)    : replay only rounds 1..k
                              -> cost = 4*k ordinary-round reconstruction units
                              (verification replay only, no refresh or setup)

V3 sign-off: this is a CSV-only auxiliary, no heavy implementation,
no plot.  Reported alongside the main benchmark for context.
"""

from exp3_communication.lxyy_baseline import lxyy_verify_per_party


def restart_cost(n: int, k: int = None) -> int:
    """Full re-verify cost regardless of abort round."""
    return lxyy_verify_per_party(n)


def prefix_cost(n: int, k: int) -> int:
    """Replay ordinary verification rounds; terminal completion costs 4n+6."""
    if not (0 <= k <= n):
        raise ValueError(f"need 0 <= k <= n; got k={k}, n={n}")
    return 4 * k if k < n else lxyy_verify_per_party(n)


def abort_restart_summary(n: int, K_refresh):
    """Return (k, restart, prefix, prefix/restart) tuples for all k in K_refresh."""
    rc = restart_cost(n)
    rows = []
    for k in K_refresh:
        pc = prefix_cost(n, k)
        ratio = (pc / rc) if rc > 0 else float("inf")
        rows.append((k, rc, pc, ratio))
    return rows
