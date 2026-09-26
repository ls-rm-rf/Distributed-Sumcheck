"""
DPSS-style refresh communication MODEL (V3 §6.5 sign-off).

NOTE ON NAMING (V3 sign-off):
   The module is named `*_model` deliberately. We do NOT claim a new DPSS
   implementation; this is the normalized accounting model the V3 spec
   requires for apples-to-apples comparison with naive / PRSS.

Per-party formula:
    dpss_per_party(M, D_k) = D_k + M*M

Justification: D_k field-element handoff to the new committee plus
M*M coordination overhead (broadcast / commitment / sync). Total scales
to M * dpss_per_party.
"""


def dpss_per_party(M: int, D_k: int) -> int:
    if M < 2:
        raise ValueError(f"need M >= 2; got {M}")
    return D_k + M * M


def dpss_total(M: int, D_k: int) -> int:
    return M * dpss_per_party(M, D_k)
