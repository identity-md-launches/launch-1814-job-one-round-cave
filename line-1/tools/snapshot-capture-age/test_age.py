import hashlib
import io
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

A = runpy.run_path(str(Path(__file__).with_name('age.py')))
SOURCE = 'line-1/tools/snapshot-integer/live-zto.json'
RAW = Path(SOURCE).read_bytes()
PIN = 'd620b767ccc4b4ea42e7660af9fc15aeb481a808888d43675c300820f3e6b51f'
CAPTURE = '2026-10-15T04:02:16.159255Z'


class AgeTests(unittest.TestCase):
    def review(self, reference=CAPTURE, maximum=0, raw=RAW, expected=PIN):
        return A['review'](raw, expected, reference, maximum)

    def changed(self, edit):
        value = json.loads(RAW)
        edit(value)
        return json.dumps(value).encode()

    def test_real_zto_zero_age(self):
        result = self.review()
        self.assertTrue(result['accepted'])
        self.assertEqual(result['age_microseconds'], '0')
        self.assertEqual(result['request']['params'][0]['to'], A['B']['ZTO'])

    def test_exact_limit(self):
        result = self.review('2026-10-15T05:02:16.159255Z', 3600)
        self.assertTrue(result['accepted'])
        self.assertEqual(result['age_microseconds'], '3600000000')

    def test_one_microsecond_over(self):
        result = self.review('2026-10-15T05:02:16.159256Z', 3600)
        self.assertFalse(result['accepted'])
        self.assertEqual(result['status'], 'capture_too_old')

    def test_one_microsecond_future(self):
        result = self.review('2026-10-15T04:02:16.159254Z', 3600)
        self.assertFalse(result['accepted'])
        self.assertEqual(result['age_microseconds'], '-1')
        self.assertEqual(result['status'], 'future_capture')

    def test_whole_seconds_and_z_equivalence(self):
        self.assertEqual(A['timestamp']('2026-10-15T00:00:00Z'),
                         A['timestamp']('2026-10-15T00:00:00+00:00'))

    def test_bad_times(self):
        for value in (None, 1, '', '2026-10-15', '2026-10-15 00:00:00Z',
                      '2026-10-15T00:00:00', '2026-10-15T00:00:00-00:00',
                      '2026-10-15T00:00:00+01:00', '2026-10-15T00:00:00.1234567Z',
                      '2026-02-29T00:00:00Z', '2026-10-15T00:00:60Z'):
            with self.subTest(value=value), self.assertRaises((ValueError, TypeError)):
                A['timestamp'](value)

    def test_bad_limits(self):
        for value in (-1, True, 1.0, '10', 315537897600):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.review(maximum=value)

    def test_pin_format(self):
        for value in ('', PIN.upper(), PIN[:-1], None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.review(expected=value)

    def test_metadata_replacement_detected(self):
        raw = self.changed(lambda v: v.update(captured_at_utc='2026-10-15T05:00:00Z'))
        with self.assertRaisesRegex(ValueError, 'retained'):
            self.review(raw=raw)

    def test_pinned_bad_timestamp_refuses(self):
        raw = self.changed(lambda v: v.update(captured_at_utc='yesterday'))
        with self.assertRaises(ValueError):
            self.review(raw=raw, expected=hashlib.sha256(raw).hexdigest())

    def test_pinned_bad_response_still_refuses(self):
        raw = self.changed(lambda v: v['response'].update(result='0x01'))
        with self.assertRaisesRegex(A['B']['SnapshotError'], 'checksum'):
            self.review(raw=raw, expected=hashlib.sha256(raw).hexdigest())

    def test_duplicate_json_key(self):
        raw = RAW.replace(b'"content_type":', b'"content_type":"x", "content_type":')
        with self.assertRaisesRegex(A['B']['SnapshotError'], 'duplicate'):
            self.review(raw=raw, expected=hashlib.sha256(raw).hexdigest())

    def test_single_read_and_unchanged_shared_verifier(self):
        safe = A['B']['SAFE_FILES']
        reader = safe['read_bytes']
        with patch.dict(safe, read_bytes=unittest.mock.Mock(return_value=RAW)):
            self.assertTrue(A['verify'](SOURCE, PIN, CAPTURE, 0)['accepted'])
            safe['read_bytes'].assert_called_once_with(SOURCE, A['MAX_BYTES'])
        self.assertIs(safe['read_bytes'], reader)
        self.assertEqual(Path(SOURCE).read_bytes(), RAW)

    def test_policy_validated_before_io(self):
        with patch.dict(A['B']['SAFE_FILES'], read_bytes=unittest.mock.Mock(side_effect=AssertionError)):
            with self.assertRaises(ValueError):
                A['verify'](SOURCE, PIN, CAPTURE, -1)
            with self.assertRaises(ValueError):
                A['verify'](SOURCE, 'bad', CAPTURE, 0)

    def test_path_boundary(self):
        for path in ('/etc/passwd', '../x', '.git/config', 'line-1//x'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                A['verify'](path, PIN, CAPTURE, 0)

    def test_input_and_output_bounds(self):
        with self.assertRaises(ValueError):
            self.review(raw=b'x' * (A['MAX_BYTES'] + 1))
        with self.assertRaises(ValueError):
            A['render']({'x': 'a' * 100000})

    def test_cli_exit_codes_and_no_network(self):
        base = [SOURCE, '--expected-sha256', PIN, '--max-age-seconds', '3600', '--reference']
        with patch('socket.socket', side_effect=AssertionError('network forbidden')):
            for reference, code in (('2026-10-15T05:02:16.159255Z', 0),
                                    ('2026-10-15T05:02:16.159256Z', 1), ('invalid', 2)):
                with self.subTest(code=code), patch('sys.stdout', new_callable=io.StringIO) as out, \
                        patch('sys.stderr', new_callable=io.StringIO):
                    self.assertEqual(A['main'](base + [reference]), code)
                    if code < 2:
                        self.assertEqual(json.loads(out.getvalue())['accepted'], code == 0)
                    else:
                        self.assertEqual(out.getvalue(), '')


if __name__ == '__main__':
    unittest.main()
