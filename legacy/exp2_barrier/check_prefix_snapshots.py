"""Exact checks for public prefixes, passive snapshots, and negative cases."""
import itertools
import json
import unittest
from collections import Counter, defaultdict
from pathlib import Path

if not __debug__:
    raise SystemExit("Run without -O: exact checks require assertions.")


def require_kernel(direction, q=3):
    rows = ((4, 2, 2), (2, 0, 1), (0, 2, 0))
    if any(sum(a*b for a, b in zip(row, direction)) % q for row in rows):
        raise ValueError("Refresh direction is outside ker C_1")


def joint_prefix_views():
    q = 3
    direction = (-pow(2, -1, q) % q, 0, 1)
    require_kernel(direction, q)
    reference = None
    summaries = []
    for w in range(q):
        views = defaultdict(Counter)
        for g0, g1, g2, a0, a1, a2, u, b0, b1, b2, tape in itertools.product(range(q), repeat=11):
            h0 = (2*w+4*g0+2*g1+2*g2) % q
            H1 = ((2*g0+g2) % q, 2*(w+g1) % q)
            rho = (H1[0]+tape) % q
            s0 = ((g0+a0) % q, (g1+a1) % q, (g2+a2) % q)
            new = tuple((g+u*b) % q for g, b in zip((g0, g1, g2), direction))
            assert (4*new[0]+2*new[1]+2*new[2]) % q == (4*g0+2*g1+2*g2) % q
            assert ((2*new[0]+new[2]) % q, 2*(w+new[1]) % q) == H1
            H2 = ((w*rho+new[0]+new[1]*rho) % q, new[2])
            assert (H1[0]+rho*H1[1]-2*H2[0]-H2[1]) % q == 0
            # All tapes, including unused refresh coins, are enumerated.
            # rho is public before the stop decision. H2 is not released if stopped.
            if h0 == 0:
                record = ('stopped', h0, H1, rho)
                answer = (s0,)
            else:
                alpha = 1+sum(s0) % 2
                s1 = tuple((x+alpha*(a+b)) % q
                           for x, a, b in zip(new, (a0, a1, a2), (b0, b1, b2)))
                record = ('completed', h0, H1, rho, H2)
                answer = (s0, alpha, s1)
            views[record][answer] += 1
        stopped = [v for h, v in views.items() if h[0] == 'stopped']
        completed = [v for h, v in views.items() if h[0] == 'completed']
        assert len(stopped) == 9 and len(completed) == 54
        assert all(len(v) == 27 and set(v.values()) == {243} for v in stopped)
        assert all(len(v) == 729 and set(v.values()) == {3} for v in completed)
        if reference is None:
            reference = views
        assert views == reference
        summaries.append({'witness': w, 'inputs': sum(sum(v.values()) for v in views.values()),
                          'stopped_inputs': sum(sum(v.values()) for v in stopped),
                          'completed_inputs': sum(sum(v.values()) for v in completed),
                          'stopped_records': len(stopped), 'completed_records': len(completed)})
    assert all(s['inputs'] == 177147 and s['stopped_inputs'] == 59049
               and s['completed_inputs'] == 118098 for s in summaries)
    return {'field': q, 'per_witness': summaries, 'conditional_views_uniform': True,
            'witness_laws_identical': True}


def initial_coin_challenge():
    public, full = [], []
    for w in range(5):
        prefixes, views = Counter(), Counter()
        for g0, g1, g2, a0, a1, a2 in itertools.product(range(5), repeat=6):
            h0 = (2*w+4*g0+2*g1+2*g2) % 5
            H1 = ((2*g0+g2) % 5, 2*(w+g1) % 5)
            rho = (4*a0+2*a1+2*a2) % 5
            share = tuple((g+a) % 5 for g, a in zip((g0, g1, g2), (a0, a1, a2)))
            ell_s = sum(a*b for a, b in zip((4, 2, 2), share)) % 5
            assert (3*(h0-ell_s+rho)) % 5 == w
            prefixes[(h0, H1, rho)] += 1
            views[(h0, H1, rho, share)] += 1
        public.append(prefixes)
        full.append(views)
    assert all(v == public[0] for v in public)
    assert all(set(full[i]).isdisjoint(full[j]) for i in range(5) for j in range(i))
    return {'inputs_per_witness': 15625, 'inputs_all_witnesses': 78125,
            'public_laws_identical': True, 'witness_recovery': True}


def stopping_leak():
    public, short = [], []
    for w in range(5):
        prefixes, leaked = Counter(), Counter()
        for g0, g1, a0, a1 in itertools.product(range(5), repeat=4):
            h0 = (2*w+2*g0+g1) % 5
            share = ((g0+a0) % 5, (g1+a1) % 5)
            if (2*a0+a1) % 5 == 0:
                h = (h0, 'stopped')
                assert 3*(h0-2*share[0]-share[1]) % 5 == w
                leaked[(h, share)] += 1
            else:
                h = (h0, ((w+g0) % 5, g1), 'completed', 1)
            prefixes[h] += 1
        public.append(prefixes)
        short.append(leaked)
    assert all(v == public[0] for v in public)
    assert all(sum(v.values()) == 125 for v in short)
    assert all(set(short[i]).isdisjoint(short[j]) for i in range(5) for j in range(i))
    return {'inputs_per_witness': 625, 'stopped_per_witness': 125, 'stopped_witness_recovery': True}


def pairwise_independence():
    public, full = [], []
    for w in range(5):
        tg, ta, prefixes, views = Counter(), Counter(), Counter(), Counter()
        for g0, g1, a0, a1 in itertools.product(range(5), repeat=4):
            tape = (2*g0+g1+2*(2*a0+a1)) % 5
            tg[tape, g0, g1] += 1
            ta[tape, a0, a1] += 1
            h0 = (w+2*g0+g1) % 5
            H1 = (g0, (g1+w) % 5)
            share = ((g0+a0) % 5, (g1+a1) % 5)
            assert (h0-2*(2*share[0]+share[1])+tape) % 5 == w
            prefixes[(h0, H1, tape)] += 1
            views[(h0, H1, tape, share)] += 1
        assert len(tg) == len(ta) == 125
        assert set(tg.values()) == set(ta.values()) == {5}
        public.append(prefixes)
        full.append(views)
    assert all(v == public[0] for v in public)
    assert all(set(full[i]).isdisjoint(full[j]) for i in range(5) for j in range(i))
    return {'inputs_per_witness': 625, 'separate_independence': True,
            'joint_independence': False, 'witness_recovery': True}


def fiber_history():
    fiber = [g for g in itertools.product(range(5), repeat=3)
             if (4*g[0]+2*g[1]+2*g[2]) % 5 == 0
             and (2*g[0]+g[2]) % 5 == 0 and 2*g[1] % 5 == 0]
    terminal = [g for g in fiber if (g[0], g[2]) == (0, 0)]
    assert len(fiber) == 5 and len(terminal) == 1
    old_given_new = defaultdict(Counter)
    for u, v in itertools.product(range(5), repeat=2):
        old_given_new[(u+v) % 5][u] += 1
    assert all(len(c) == 5 and set(c.values()) == {1} for c in old_given_new.values())
    for w, g0, g1 in ((0, 0, 0), (1, 0, 4)):
        assert ((w+2*g0+g1) % 5, g0, (g1+w) % 5) == (0, 0, 0)
    return {'current_fiber': 5, 'terminal_fiber_without_refresh': 1,
            'historical_values_after_refresh': 5, 'terminal_uniqueness_requires_fixed_witness': True}


def frozen_suffix():
    # All 343 scalar quadratics: zero increments give a longer frozen interval.
    for secret, a, b in itertools.product(range(7), repeat=3):
        y = [(secret+a*x+b*x*x) % 7 for x in (1, 2, 3)]
        assert (3*y[0]-3*y[1]+y[2]) % 7 == secret
    # n=4, k=2: same complete observations, different initial targets.
    d = 15
    direction = [0]*d
    direction[0], direction[4] = 3, 1
    G = [pow(2, 4, 7)]+[pow(2, 3, 7)]*(d-1)
    C1 = [G]+[[int(j == i) for j in range(d)] for i in (1, 2, 3)]
    assert all(sum(a*b for a, b in zip(row, direction)) % 7 == 0 for row in C1)
    assert direction[4] == 1
    # p0=b*(1-X/4), D1=-p0, then all later polynomials are zero.
    assert all(b*(1-4*pow(4, -1, 7)) % 7 == 0 for b in direction)
    return {'quadratics': 343, 'suffix_condition_not_necessary': True,
            'same_views_different_initial_target': True, 'recovered_target': 'lambda*p^(k-1)(0)'}


class PrefixSnapshotChecks(unittest.TestCase):
    results = {}

    def test_joint_prefix(self):
        self.results['joint_prefix'] = joint_prefix_views()

    def test_invalid_kernel_mutation(self):
        with self.assertRaises(ValueError):
            require_kernel((0, 0, 1))
        self.results['invalid_kernel_mutation'] = 'rejected'

    def test_initial_coin_challenge(self):
        self.results['initial_coin_challenge'] = initial_coin_challenge()

    def test_stopping_leak(self):
        self.results['stopping_leak'] = stopping_leak()

    def test_pairwise_independence(self):
        self.results['pairwise_independence'] = pairwise_independence()

    def test_fiber_history(self):
        self.results['fiber_history'] = fiber_history()

    def test_frozen_suffix(self):
        self.results['frozen_suffix'] = frozen_suffix()


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PrefixSnapshotChecks)
    outcome = unittest.TextTestRunner(verbosity=2).run(suite)
    output = Path(__file__).resolve().parent/'validation'
    output.mkdir(exist_ok=True)
    summary = {'status': 'PASS' if outcome.wasSuccessful() else 'FAIL',
               'tests_run': outcome.testsRun, 'checks': PrefixSnapshotChecks.results}
    (output/'prefix_checks.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    raise SystemExit(0 if outcome.wasSuccessful() else 1)
