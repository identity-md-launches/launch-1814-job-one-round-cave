#!/usr/bin/env python3
"""Apply an explicit time policy to a pinned saved RPC capture, offline."""
import argparse
from datetime import datetime, timezone
import hashlib
import hmac
import json
from pathlib import Path
import re
import runpy
import sys
import types

B = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                       'bounded-rpc-snapshot' / 'snapshot.py'))
MAX_BYTES = B['MAX_RESPONSE'] + B['MAX_REQUEST']
STAMP = re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}'
                   r'(?:\.[0-9]{1,6})?(?:Z|\+00:00)\Z')
PIN = re.compile(r'[0-9a-f]{64}\Z')


def timestamp(value):
    if type(value) is not str or not STAMP.fullmatch(value):
        raise ValueError('time must be UTC YYYY-MM-DDTHH:MM:SS[.ffffff]Z or +00:00')
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def policy(reference, max_age_seconds):
    reference_time = timestamp(reference)
    if type(max_age_seconds) is not int or not 0 <= max_age_seconds <= 315537897599:
        raise ValueError('max age must be a nonnegative whole second count within datetime range')
    return reference_time


def pin(value):
    if type(value) is not str or not PIN.fullmatch(value):
        raise ValueError('expected SHA-256 must be 64 lowercase hex digits')
    return value


def review(raw, expected_sha256, reference, max_age_seconds):
    """Pure byte review. No clock lookup, transport or filesystem access."""
    reference_time = policy(reference, max_age_seconds)
    pin(expected_sha256)
    if type(raw) is not bytes or len(raw) > MAX_BYTES:
        raise ValueError('snapshot bytes exceed bounded snapshot limit')
    digest = hashlib.sha256(raw).hexdigest()
    if not hmac.compare_digest(digest, expected_sha256):
        raise ValueError('snapshot differs from retained exact-byte SHA-256')

    # Reuse the full ancestor verifier on exactly the bytes just pinned. A local
    # function with isolated globals changes only its file reader, avoiding a
    # second filesystem read and avoiding mutation of the shared verifier.
    verifier = B['verify_snapshot']
    globals_copy = dict(verifier.__globals__)
    globals_copy['SAFE_FILES'] = {'read_bytes': lambda path, limit: raw}
    check = types.FunctionType(verifier.__code__, globals_copy)
    snapshot = check('memory')
    captured = timestamp(snapshot['captured_at_utc'])
    delta = reference_time - captured
    age_us = (delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds
    accepted = 0 <= age_us <= max_age_seconds * 1000000
    status = ('future_capture' if age_us < 0 else
              'within_capture_age_policy' if accepted else 'capture_too_old')
    return {
        'schema': 'line1-snapshot-capture-age-v1',
        'accepted': accepted, 'status': status,
        'file_sha256': digest, 'file_bytes': len(raw),
        'captured_at_utc': captured.isoformat(),
        'reference_at_utc': reference_time.astimezone(timezone.utc).isoformat(),
        'age_microseconds': str(age_us), 'max_age_seconds': max_age_seconds,
        'request': snapshot['request'],
        'response_sha256': snapshot['response_sha256'],
        'meaning': 'Pinned capture metadata meets an explicit age policy only. '
                   'Neither timestamp nor reference clock is authenticated; '
                   'this proves no block age, chain freshness, state, or intended request.'}


def verify(path, expected_sha256, reference, max_age_seconds):
    policy(reference, max_age_seconds)
    pin(expected_sha256)
    raw = B['SAFE_FILES']['read_bytes'](path, MAX_BYTES)
    return review(raw, expected_sha256, reference, max_age_seconds)


def render(result):
    raw = json.dumps(result, ensure_ascii=True, allow_nan=False, separators=(',', ':')) + '\n'
    if len(raw.encode('ascii')) > 100000:
        raise ValueError('complete age report exceeds 100000 bytes')
    return raw


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', help='relative visible workspace snapshot path')
    parser.add_argument('--expected-sha256', required=True, help='exact-byte pin retained separately')
    parser.add_argument('--reference', required=True, help='explicit UTC reference time')
    parser.add_argument('--max-age-seconds', required=True, type=int)
    args = parser.parse_args(argv)
    try:
        result = verify(args.snapshot, args.expected_sha256, args.reference, args.max_age_seconds)
        sys.stdout.write(render(result))
        return 0 if result['accepted'] else 1
    except (ValueError, B['SnapshotError'], OSError, RecursionError, TypeError,
            OverflowError) as exc:
        print('snapshot-capture-age: ' + str(exc)[:1000], file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
