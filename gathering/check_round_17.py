#!/usr/bin/env python3
"""Exercise round 17's refusals and the detached shared settlement-window gate."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
BASE = 'shared/window-settlement/'


def main():
    assert Path.cwd() == ROOT
    scratch = ROOT / 'test/scratch/round17'
    scratch.mkdir(parents=True, exist_ok=True)
    detached = scratch / 'portable'
    shutil.copytree(ROOT / BASE, detached / BASE, dirs_exist_ok=True)
    pin = (ROOT / BASE / 'plan.sha256').read_text().strip()
    demo = [BASE + 'review.py', BASE + 'plan.json', '--sha256', pin]
    plan = json.loads((ROOT / BASE / 'plan.json').read_text())
    late = json.loads(json.dumps(plan))
    late['windows'][1]['notAfterBlock'] = 26194714
    malformed = json.loads(json.dumps(plan))
    malformed['windows'][1]['notBeforeBlock'] = '26194710'
    cases = [
        (ROOT, 0, [BASE + 'test_review.py'], None),
        (ROOT, 0, demo, BASE + 'example-match.json'),
        (detached, 0, [BASE + 'test_review.py'], None),
        (detached, 0, demo, None),
    ]
    for name, changed, output in (
            ('late', late, 'example-window-rejection.json'),
            ('structure', malformed, 'example-structure-rejection.json')):
        raw = (json.dumps(changed) + '\n').encode()
        path = scratch / (name + '.json')
        path.write_bytes(raw)
        cases.append((ROOT, 1, [BASE + 'review.py', str(path.relative_to(ROOT)),
                               '--sha256', hashlib.sha256(raw).hexdigest()], BASE + output))
    bad_source = json.loads((ROOT / 'line-4/tools/witness-path/zto-payment.json').read_text())
    bad_source['message']['token'] = '0xd34a99bc0f67ae1bbd63c660e6d0b0dd03e263b7'
    source_path = scratch / 'substitution.json'
    source_path.write_text(json.dumps(bad_source) + '\n')
    cases.extend([
        (ROOT, 1, ['line-1/tools/snapshot-capture-age/age.py',
                  'line-1/tools/snapshot-integer/live-zto.json', '--expected-sha256',
                  'd620b767ccc4b4ea42e7660af9fc15aeb481a808888d43675c300820f3e6b51f',
                  '--reference', '2026-10-15T05:02:16.159256Z', '--max-age-seconds', '3600'], None),
        (ROOT, 1, ['line-2/tools/jsonl-composite/check.py',
                  'shared/payment-evidence/policy.contract.json',
                  'line-2/tools/jsonl-unique/repeated-policy.jsonl', '--key', '/token', '/tx'], None),
        (ROOT, 1, ['line-4/tools/witness-path/witness_path.py',
                  str(source_path.relative_to(ROOT)), 'line-4/tools/witness-path/zto-trace.json',
                  '--path', '/domain/chainId', '--expect',
                  '0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774'], None),
        (ROOT, 0, ['line-1/tools/hash-pinned-zto/pinned.py', '--verify',
                  'gathering/hash-pinned-round17.json'], None),
    ])
    rows = []
    for cwd, expected, args, save in cases:
        done = subprocess.run([sys.executable, '-B', *args], cwd=cwd, capture_output=True,
                              text=True, timeout=45,
                              env={'PATH': '/usr/bin:/bin', 'PYTHONDONTWRITEBYTECODE': '1'})
        row = {'command': ['python3', '-B', *args], 'detached': cwd != ROOT,
               'expectedExit': expected, 'exitCode': done.returncode,
               'passed': done.returncode == expected,
               'stdout': done.stdout, 'stderr': done.stderr}
        rows.append(row)
        if save and row['passed']:
            assert len(done.stdout.encode()) <= 100000
            (ROOT / save).write_text(done.stdout)
        print('PASS' if row['passed'] else 'FAIL', args[0], done.returncode)
    output = json.dumps(rows, indent=2) + '\n'
    assert len(output.encode()) <= 100000
    (ROOT / 'gathering/round-checks-17.json').write_text(output)
    return 0 if all(r['passed'] for r in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
