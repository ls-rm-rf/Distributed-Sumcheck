"""
PRSS (Pseudo-Random Secret Sharing) refresh communication (V3 §6.6 sign-off).

V3 fixes THREE PROFILES with different online communication costs:

    | profile      | c_online       | meaning                              |
    |--------------|----------------|--------------------------------------|
    | prss_local   | 0              | offline-only; no online round-trips  |
    | prss_commit  | 1              | one-round commit phase per refresh   |
    | prss_dispute | ceil(log2(M))  | dispute-resolution rounds            |

Per-party communication for a given profile c_online:

    prss_per_party(M, D_k, c_online) = D_k + c_online * (M - 1)

Notes:
- D_k: bulk handoff of round-k state to new committee
- c_online * (M-1): one round of all-to-all online for c_online rounds
- Total = M * prss_per_party
"""

import math


PRSS_LOCAL_C_ONLINE = 0
PRSS_COMMIT_C_ONLINE = 1


def prss_dispute_c_online(M: int) -> int:
    """ceil(log2(M)), with M >= 2."""
    if M < 2:
        raise ValueError(f"need M >= 2; got {M}")
    return int(math.ceil(math.log2(M)))


def prss_per_party(M: int, D_k: int, c_online: int) -> int:
    if M < 2:
        raise ValueError(f"need M >= 2; got {M}")
    if c_online < 0:
        raise ValueError("c_online must be >= 0")
    return D_k + c_online * (M - 1)


def prss_total(M: int, D_k: int, c_online: int) -> int:
    return M * prss_per_party(M, D_k, c_online)


# convenience profiles ------------------------------------------------------

def prss_local(M: int, D_k: int):
    """profile=local, c_online=0; returns (per_party, total)."""
    pp = prss_per_party(M, D_k, PRSS_LOCAL_C_ONLINE)
    return pp, M * pp


def prss_commit(M: int, D_k: int):
    """profile=commit, c_online=1; returns (per_party, total)."""
    pp = prss_per_party(M, D_k, PRSS_COMMIT_C_ONLINE)
    return pp, M * pp


def prss_dispute(M: int, D_k: int):
    """profile=dispute, c_online=ceil(log2(M)); returns (per_party, total)."""
    co = prss_dispute_c_online(M)
    pp = prss_per_party(M, D_k, co)
    return pp, M * pp
