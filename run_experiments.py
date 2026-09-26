"""Reproduce the legacy sweeps and the current manuscript supplement."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    output = ROOT/'results'
    output.mkdir(exist_ok=True)
    stages = []
    # Write a non-success marker before checking inputs or executing any stage.
    summary = {'status': 'RUNNING', 'python': sys.version, 'stages': stages}
    summary_path = output/'summary.json'
    summary_path.write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    if not __debug__:
        raise SystemExit('Run without -O: mathematical checks require assertions.')

    def run(name, script, cwd):
        print(f'Running {name}...', flush=True)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
        process = subprocess.run([sys.executable, str(script)], cwd=cwd, env=env,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, encoding='utf-8', errors='replace')
        log = process.stdout.replace(sys.executable, 'python').replace(str(ROOT), '<repository>')
        (output/f'{name}.log').write_text(log, encoding='utf-8')
        stages.append({'name': name, 'exit_code': process.returncode, 'log': f'results/{name}.log'})
        if process.returncode:
            summary['status'] = 'FAIL'
            summary_path.write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
            print(log[-6000:])
            raise SystemExit(process.returncode)
        print(f'PASS {name}', flush=True)

    # Generate every required CSV, figure, and manifest from source first.
    run('legacy_full', ROOT/'legacy/run_all.py', ROOT/'legacy')
    regenerated = json.loads((ROOT/'legacy/validation/run_manifest.json').read_text(encoding='utf-8'))
    summary['legacy_csv_rows'] = regenerated['csv_rows']
    run('complete_resharing', ROOT/'supplement/verify_paper.py', ROOT)
    run('prefix_snapshots', ROOT/'supplement/check_prefix_snapshots.py', ROOT)
    run('figure_epochs', ROOT/'supplement/make_fig_epochs.py', ROOT)
    summary['status'] = 'PASS'
    summary_path.write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    print('All experiments passed. See results/summary.json.')


if __name__ == '__main__':
    main()
