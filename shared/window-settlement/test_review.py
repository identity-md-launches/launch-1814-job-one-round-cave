"""Exercise retained real ZTO evidence, fail-closed gates and portability."""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('window_gate_test', HERE / 'review.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.raw = (HERE / 'plan.json').read_bytes()
        self.pin = (HERE / 'plan.sha256').read_text().strip()
        self.plan = json.loads(self.raw)

    def review(self, plan=None):
        raw = (json.dumps(self.plan if plan is None else plan) + '\n').encode()
        return g.review(raw, hashlib.sha256(raw).hexdigest())

    def test_real_zto_evidence(self):
        r = g.review(self.raw, self.pin)
        self.assertTrue(r['accepted'])
        self.assertTrue(r['structure']['valid'])
        self.assertEqual(r['state'], 'settlement_window_match')
        self.assertEqual([x['inclusionBlock'] for x in r['windowReview']['comparisons']],
                         [26190898, 26194715])

    def test_inclusive_edges(self):
        self.plan['windows'][1].update(notBeforeBlock=26194715, notAfterBlock=26194715)
        self.assertTrue(self.review()['accepted'])

    def test_early_and_late_reject_after_settlement(self):
        for start, end in ((26194716, 26194720), (26194710, 26194714)):
            with self.subTest(start=start):
                p = copy.deepcopy(self.plan)
                p['windows'][1].update(notBeforeBlock=start, notAfterBlock=end)
                r = self.review(p)
                self.assertFalse(r['accepted'])
                self.assertTrue(r['windowChecked'])
                self.assertTrue(r['windowReview']['batch']['accepted'])
                self.assertEqual(r['state'], 'window_review_required')

    def test_window_order_is_not_transaction_order(self):
        self.plan['windows'].reverse()
        self.plan['batch']['items'].reverse()
        self.assertTrue(self.review()['accepted'])

    def test_pin_checked_before_parsing(self):
        with patch.object(g.window.b.k.p.s, 'strict_json', side_effect=AssertionError('parsed')):
            r = g.review(b'not JSON', self.pin)
        self.assertFalse(r['evidenceChecked'])
        self.assertNotIn('structure', r)

    def test_structural_diagnostics_before_evidence(self):
        for value in ('26194710', True, -1, 2**64):
            with self.subTest(value=value):
                p = copy.deepcopy(self.plan)
                p['windows'][1]['notBeforeBlock'] = value
                with patch.object(g.window, 'review_bytes', side_effect=AssertionError('replayed')):
                    r = self.review(p)
                self.assertEqual(r['state'], 'structural_review_required')
                self.assertEqual(r['structure']['diagnostics'][0]['path'],
                                 '/windows/1/notBeforeBlock')

    def test_semantic_errors_before_evidence(self):
        for error in ('reversed', 'duplicate', 'missing', 'unmatched'):
            p = copy.deepcopy(self.plan)
            if error == 'reversed':
                p['windows'][1].update(notBeforeBlock=26194720, notAfterBlock=26194710)
            elif error == 'duplicate':
                p['windows'][1]['transactionHash'] = '0x' + p['windows'][0]['transactionHash'][2:].upper()
            elif error == 'missing':
                p['windows'].pop()
            else:
                p['windows'][1]['transactionHash'] = '0x' + 'a' * 64
            with self.subTest(error=error), patch.object(
                    g.window.b, 'review', side_effect=AssertionError('evidence opened')):
                if error == 'missing':
                    self.assertEqual(self.review(p)['state'], 'structural_review_required')
                else:
                    with self.assertRaises(g.window.Error):
                        self.review(p)

    def test_evidence_pin_failure_never_accepts(self):
        self.plan['batch']['items'][1]['sha256'] = self.plan['batch']['items'][0]['sha256']
        r = self.review()
        self.assertFalse(r['accepted'])
        self.assertFalse(r['windowChecked'])

    def test_unmet_settlement_policy_cannot_be_overridden(self):
        self.plan['batch']['items'][0]['policy']['minimumConfirmations'] = 1000000
        r = self.review()
        self.assertFalse(r['accepted'])
        self.assertFalse(r['windowChecked'])

    def test_missing_evidence_no_partial_acceptance(self):
        self.plan['batch']['items'][1]['evidence'] = 'missing-window-evidence.json'
        r = self.review()
        self.assertFalse(r['accepted'])
        self.assertEqual(r['state'], 'input_error')

    def test_incoming_acceptance_flag_refuses(self):
        self.plan['accepted'] = True
        r = self.review()
        self.assertEqual(r['state'], 'structural_review_required')
        self.assertEqual(r['structure']['diagnostics'][0]['path'], '/accepted')

    def test_strict_json_and_bounds(self):
        for raw in (b'{"version":1,"version":1}', b'{"version":NaN}', b'\xff', b' ' * 90001):
            with self.subTest(raw=raw[:30]), self.assertRaises((ValueError, g.window.Error)):
                g.review(raw, hashlib.sha256(raw).hexdigest())
        with self.assertRaises(ValueError):
            g.review(bytearray(self.raw), self.pin)
        with self.assertRaises(ValueError):
            g.render({'message': 'x' * 100000})

    def test_invalid_pin_before_io_and_unsafe_paths(self):
        with patch.object(g.window.b.k, 'load_bytes', side_effect=AssertionError('opened')):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(g.main(['irrelevant', '--sha256', 'invalid']), 2)
        for path in ('/outside', '../outside', '.hidden', 'a//b', 'a/./b'):
            with self.subTest(path=path), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(g.main([path, '--sha256', self.pin]), 2)

    def test_cli_offline_and_immutable(self):
        files = [HERE / 'plan.json', HERE / 'plan.sha256'] + [
            Path(i['evidence']) for i in self.plan['batch']['items']]
        before = [p.read_bytes() for p in files]
        with patch.object(g.window.b.k.p.s.RPC, 'call', side_effect=AssertionError('network')):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(g.main([str((HERE / 'plan.json').relative_to(Path.cwd())),
                                         '--sha256', self.pin]), 0)
        self.assertTrue(json.loads(out.getvalue())['accepted'])
        self.assertLessEqual(len(out.getvalue().encode()), 100000)
        self.assertEqual(before, [p.read_bytes() for p in files])


if __name__ == '__main__':
    unittest.main(verbosity=2)
