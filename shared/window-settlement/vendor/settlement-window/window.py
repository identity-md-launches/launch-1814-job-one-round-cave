#!/usr/bin/env python3
"""Replay pinned settlement evidence and require inclusion in explicit block windows."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

_spec = importlib.util.spec_from_file_location(
    'window_batch', Path(__file__).resolve().parent.parent / 'settlement-batch' / 'batch.py')
b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b)
Error = b.Error
MAX_BLOCK = 2**64 - 1
LIMITATIONS = (
    'Historical provider assertions, not consensus, trie or inter-block ancestry proofs. '
    'Windows use inclusive Ethereum block heights, not timestamps, elapsed seconds or '
    'a contract-specific deadline. No current freshness, payment amount, authorization '
    'or persistent ledger follows. Retain the full plan hash independently; replacing '
    'both plan and expected hash defeats the pin.')


def validate(plan):
    """Validate all expectations before any evidence is opened."""
    if (not isinstance(plan, dict) or set(plan) != {'version', 'batch', 'windows'}
            or type(plan['version']) is not int or plan['version'] != 1):
        raise Error('exact version 1 window plan required')
    items = b.validate(plan['batch'])
    windows = plan['windows']
    if not isinstance(windows, list) or len(windows) != len(items):
        raise Error('one window per transaction required')
    by_tx = {}
    for entry in windows:
        if not isinstance(entry, dict) or set(entry) != {
                'transactionHash', 'notBeforeBlock', 'notAfterBlock'}:
            raise Error('exact window fields required')
        tx = b.k.p.s.hash32(entry['transactionHash'])
        start, end = entry['notBeforeBlock'], entry['notAfterBlock']
        if (type(start) is not int or type(end) is not int
                or not 0 <= start <= end <= MAX_BLOCK or tx in by_tx):
            raise Error('unique ordered unsigned block window required')
        by_tx[tx] = (start, end)
    if set(by_tx) != {item['policy']['transactionHash'] for item in items}:
        raise Error('windows must match batch transactions exactly')
    return by_tx


def review_bytes(raw, expected_sha256):
    expected = b.k.pin(expected_sha256)
    if type(raw) is not bytes or len(raw) > b.k.LIMIT:
        raise Error('bounded exact plan bytes required')
    actual = hashlib.sha256(raw).hexdigest()
    result = {'accepted': False, 'state': 'plan_pin_mismatch',
              'expectedPlanSha256': expected, 'actualPlanSha256': actual,
              'evidenceChecked': False, 'windowChecked': False,
              'limitations': LIMITATIONS}
    if actual != expected:
        return result
    plan = b.k.p.s.strict_json(raw)
    windows = validate(plan)
    batch = b.review(plan['batch'])
    result.update(evidenceChecked=True, batch=batch)
    if not batch['accepted']:
        result['state'] = ('input_error' if batch['state'] == 'input_error'
                           else 'settlement_review_required')
        return result
    comparisons = []
    for row in batch['items']:
        tx = row['transactionHash']
        first, last = windows[tx]
        height = row['block']['number']
        comparisons.append({'transactionHash': tx, 'inclusionBlock': height,
                            'notBeforeBlock': first, 'notAfterBlock': last,
                            'withinWindow': first <= height <= last})
    accepted = all(row['withinWindow'] for row in comparisons)
    result.update(accepted=accepted, windowChecked=True, comparisons=comparisons,
                  state='settlement_window_match' if accepted else 'window_review_required')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--demo', action='store_true')
    mode.add_argument('--plan', help='visible workspace-relative window plan')
    parser.add_argument('--sha256', help='independently retained full-plan SHA-256')
    args = parser.parse_args(argv)
    try:
        if args.demo:
            if args.sha256 is not None:
                raise Error('demo refuses overrides')
            folder = Path(__file__).resolve().parent.relative_to(Path.cwd())
            raw = b.k.load_bytes(folder / 'demo-plan.json')
            expected = b.k.load_bytes(folder / 'demo-plan.sha256').decode('ascii').strip()
        else:
            if args.sha256 is None:
                raise Error('independent full-plan hash required')
            expected = b.k.pin(args.sha256)
            raw = b.k.load_bytes(args.plan)
        result = review_bytes(raw, expected)
        if args.demo:
            result['demoNote'] = ('Two retained real ZTO transactions in illustrative '
                                  'inclusive block windows; no fresh chain observation.')
        encoded = json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False)
        if len(encoded.encode('ascii')) > 100000:
            raise Error('report exceeds 100 KB')
        print(encoded)
        return 0 if result['accepted'] else 2 if result['state'] == 'input_error' else 1
    except (Error, ValueError, TypeError, KeyError, OSError, RecursionError):
        print(json.dumps({'accepted': False, 'state': 'input_error',
                          'reason': 'Invalid bounded window plan, pin or evidence'}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
