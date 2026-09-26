"""
Run all four experiments end-to-end (V3).

Usage:
    python run_all.py              # full sweep (slow)
    python run_all.py --quick      # quick smoke (fast, for CI)

Outputs:
    unittest discovery -> foundation and experiment regression tests
    exp1_rank_saturation/results/    -> rank_table_multi_prime.csv + challenges.jsonl
    exp2_barrier/results/            -> barrier_table.csv
    exp3_communication/results/      -> communication_benchmark.csv + abort_restart.csv
    exp3_communication/plots/        -> 5 main + 4 sensitivity figures (PDF/PNG)
    appendix_a_libra_rank/results/   -> libra_rank_table.csv
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path


def run_step(label: str, cmd: list, env=None) -> int:
    print(f"\n{'='*70}\n  {label}\n{'='*70}", flush=True)
    print("  $ " + " ".join(cmd))
    here = Path(__file__).resolve().parent
    logs = here / "validation" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(cmd, env=env, cwd=here, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)
    (logs / (label.split()[0].rstrip('.') + '.log')).write_text(result.stdout)
    print(result.stdout)
    rc = result.returncode
    print(f"  -> exit code: {rc}")
    if rc:
        raise SystemExit(rc)
    return rc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true",
                    help="smaller sweeps for quick verification")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    py = sys.executable
    failures = []

    # 0) foundation and experiment regression tests
    rc = run_step("0a. all unit tests",
                  [py, "-m", "unittest", "discover", "-v"])
    if rc != 0:
        failures.append("crypto_core tests")

    # 1) Experiment 1: rank saturation
    cmd = [py, "exp1_rank_saturation/verify_rank.py", "--mode", "both"]
    if args.quick:
        cmd += ["--ns", "3", "4", "5", "--trials", "2"]
    rc = run_step("1. Experiment 1: rank saturation (main + stress)", cmd)
    if rc != 0:
        failures.append("exp1 main mode")

    # 2) Experiment 2: barrier validation
    cmd = [py, "exp2_barrier/barrier_validation.py"]
    if args.quick:
        cmd += ["--Ms", "3", "5", "7", "--trials", "2"]
    rc = run_step("2. Experiment 2: barrier validation", cmd)
    if rc != 0:
        failures.append("exp2 barrier")
    run_step("2b. one-more post-boundary exposure",
             [py, "exp2_barrier/one_more_exposure.py"])

    # 3) Experiment 3: communication benchmark
    cmd = [py, "exp3_communication/benchmark.py"]
    if args.quick:
        cmd += ["--Ms", "3", "5", "9", "--ns", "4", "8"]
    rc = run_step("3a. Experiment 3: communication benchmark", cmd)
    if rc != 0:
        failures.append("exp3 benchmark")

    # 3b) plots
    rc = run_step("3b. Experiment 3: plots",
                  [py, "exp3_communication/plot_results.py"])
    if rc != 0:
        failures.append("exp3 plots")

    # 4) Appendix A: Libra rank
    cmd = [py, "appendix_a_libra_rank/libra_rank_check.py"]
    if args.quick:
        cmd += ["--ns", "3", "5", "--trials", "2"]
    rc = run_step("4. Appendix A: Libra rank sanity", cmd)
    if rc != 0:
        failures.append("appendix A")

    run_step("5. output consistency and reproducibility manifest",
             [py, "verify_results.py"])

    print(f"\n{'='*70}\n  SUMMARY\n{'='*70}")
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("ALL STAGES PASSED")
    sys.exit(0)


if __name__ == "__main__":
    main()
