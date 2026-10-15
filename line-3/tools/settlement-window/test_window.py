import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location('window_test', HERE / 'window.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


class WindowTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((HERE / 'demo-plan.json').read_text())

    def check(self, plan=None):
        raw = json.dumps(self.plan if plan is None else plan).encode()
        return w.review_bytes(raw, hashlib.sha256(raw).hexdigest())

    def test_retained_real_zto_evidence_and_inclusive_edges(self):
        result = self.check()
        self.assertTrue(result['accepted'])
        self.assertTrue(result['windowChecked'])
        self.assertEqual([r['inclusionBlock'] for r in result['comparisons']],
                         [26190898, 26194715])
        self.plan['windows'][1]['notBeforeBlock'] = 26194715
        self.plan['windows'][1]['notAfterBlock'] = 26194715
        self.assertTrue(self.check()['accepted'])

    def test_too_early_or_too_late_rejects_after_settlement(self):
        for start, end in ((26194716, 26194720), (26194710, 26194714)):
            with self.subTest(start=start, end=end):
                plan = copy.deepcopy(self.plan)
                plan['windows'][1].update(notBeforeBlock=start, notAfterBlock=end)
                result = self.check(plan)
                self.assertFalse(result['accepted'])
                self.assertEqual(result['state'], 'window_review_required')
                self.assertTrue(result['batch']['accepted'])

    def test_wrong_pin_does_not_parse_or_read_evidence(self):
        raw = b'not even json'
        with patch.object(w.b.k.p.s, 'strict_json', side_effect=AssertionError('parsed')):
            with patch.object(w.b.k, 'review_file', side_effect=AssertionError('read')):
                result = w.review_bytes(raw, '0'*64)
        self.assertEqual(result['state'], 'plan_pin_mismatch')
        self.assertFalse(result['evidenceChecked'])

    def test_plan_validation_precedes_evidence(self):
        bad = []
        for value in (True, 1.5, -1, 2**64, '26194710'):
            p = copy.deepcopy(self.plan)
            p['windows'][1]['notBeforeBlock'] = value
            bad.append(p)
        for mutate in ('overlap', 'duplicate', 'missing', 'extra', 'unknown'):
            p = copy.deepcopy(self.plan)
            if mutate == 'overlap':
                p['windows'][1].update(notBeforeBlock=26194720, notAfterBlock=26194710)
            elif mutate == 'duplicate':
                p['windows'][1]['transactionHash'] = p['windows'][0]['transactionHash']
            elif mutate == 'missing':
                p['windows'].pop()
            elif mutate == 'extra':
                p['windows'].append(copy.deepcopy(p['windows'][0]))
            else:
                p['windows'][0]['memo'] = 'unreviewed'
            bad.append(p)
        with patch.object(w.b.k, 'review_file', side_effect=AssertionError('read')):
            for p in bad:
                with self.subTest(plan=p), self.assertRaises(w.Error):
                    self.check(p)

    def test_case_alias_and_window_order_do_not_change_meaning(self):
        self.plan['windows'].reverse()
        self.plan['windows'][0]['transactionHash'] = (
            '0x' + self.plan['windows'][0]['transactionHash'][2:].upper())
        self.assertTrue(self.check()['accepted'])

    def test_failed_settlement_cannot_be_overridden_by_window(self):
        self.plan['batch']['items'][0]['policy']['minimumConfirmations'] = 1000000
        result = self.check()
        self.assertFalse(result['accepted'])
        self.assertFalse(result['windowChecked'])
        self.assertEqual(result['state'], 'input_error')

    def test_ambiguous_or_oversized_json(self):
        for raw in (b'{"version":1,"version":1}', b'{"x":NaN}', b'\xff', b' ' * 90001):
            with self.subTest(raw=raw[:30]), self.assertRaises(w.Error):
                w.review_bytes(raw, hashlib.sha256(raw).hexdigest())

    def test_cli_demo_and_bad_override(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(w.main(['--demo']), 0)
        self.assertEqual(json.loads(out.getvalue())['state'], 'settlement_window_match')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(w.main(['--demo', '--sha256', '0'*64]), 2)
            self.assertEqual(w.main(['--plan', 'missing.json']), 2)


if __name__ == '__main__':
    unittest.main()
