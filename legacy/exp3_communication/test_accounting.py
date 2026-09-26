import unittest
from exp3_communication.benchmark import protocol_rows, summarize
from exp3_communication.state_size import d_k_mask
from exp3_communication.comparisons.abort_restart_estimate import prefix_cost


class TestCommunication(unittest.TestCase):
    def totals(self, M=3, n=3, policy="fold_after"):
        return summarize(list(protocol_rows(M, n, policy, "test", 101)))

    def row(self, scheme, scope="per_party", seed="none", **kw):
        return next(r for r in self.totals(**kw) if r["scheme"] == scheme
                    and r["accounting_scope"] == scope and r["seed_state_model"] == seed)

    def test_protocol_sum_uses_actual_boundaries(self):
        # n=3: tables 8+4, masks 8+5, two actual refreshes.
        self.assertEqual(self.row("naive")["comm_per_party"], 50)
        self.assertEqual(self.row("dpss_model")["comm_per_party"], 43)
        self.assertEqual(self.row("full_mask")["comm_per_party"], 48)
        self.assertEqual(self.row("kernel_mask")["comm_per_party"], 26)
        self.assertEqual(self.row("naive", policy="fold_before")["comm_per_party"], 86)

    def test_seed_refresh_is_charged_once_per_boundary(self):
        # Commit online 25+2*2=29; DPSS seed S=3 adds 2*(3+9)=24.
        r = self.row("prss_commit_seed_dpss", seed="M")
        self.assertEqual(r["online_comm_per_party"], 29)
        self.assertEqual(r["seed_refresh_per_party"], 24)
        self.assertEqual(r["comm_per_party"], 53)
        self.assertEqual(self.row("prss_commit_seed_naive", seed="M")["comm_per_party"], 41)

    def test_total_scope_scales_both_cost_and_baseline(self):
        pp, total = self.row("naive"), self.row("naive", scope="total")
        self.assertEqual(total["communication_value"], 3*pp["communication_value"])
        self.assertEqual(total["baseline_value"], 3*pp["baseline_value"])
        self.assertEqual(total["overhead_ratio"], pp["overhead_ratio"])

    def test_closed_form_full_sweep(self):
        for n in (2, 4, 8, 14):
            for M in (3, 9, 63):
                table = 2**(n+1)-4
                kernel = 3*n*(n-1)//2 + 2*(n-1)
                self.assertEqual(self.row("naive", n=n, M=M)["comm_per_party"],
                                 (table+kernel)*(M-1))
                self.assertEqual(self.row("dpss_model", n=n, M=M)["comm_per_party"],
                                 table+kernel+(n-1)*M*M)
                self.assertEqual(d_k_mask(n, n), 0)

    def test_abort_replay_uses_verification_units(self):
        self.assertEqual(prefix_cost(8, 3), 12)
        self.assertEqual(prefix_cost(8, 8), 38)

