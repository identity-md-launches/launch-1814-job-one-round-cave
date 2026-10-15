"""Check field inclusion paths against independent hashing and refusal gates."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import witness_path as tool
from keccak_check import keccak256

HERE = Path(__file__).resolve().parent
ZTO = '0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774'
MAIL = '0xbe609aee343fb3c4b28e1df9e632fca64fcfaede20f02e86244efddf30957bd2'
EDGE = '0xbf1f9acedd3f9924aafba0d1b362a4bb33ab5c7fa4855b930ed2ededc2ce9ba6'


def load(name):
    return json.loads((HERE/name).read_bytes())


class PathTests(unittest.TestCase):
    def setUp(self):
        self.source = load('zto-payment.json')
        self.trace = load('zto-trace.json')

    def review(self, path='/message/token', expected=ZTO):
        return tool.review(self.source, self.trace, expected, path)

    def check_chain(self, result):
        self.assertTrue(result['accepted'])
        self.assertTrue(result['pathExplained'])
        word = result['selectedNode']['word']
        for step in result['steps']:
            self.assertEqual(step['childWord'], word)
            preimage = bytes.fromhex(step['parentPreimage'][2:])
            at = step['offsetBytes']
            self.assertEqual(preimage[at:at+32].hex(), word[2:])
            word = '0x' + keccak256(preimage).hex()
            self.assertEqual(word, step['parentWord'])
        self.assertEqual(word, result['digest'])

    def test_real_zto_address_offsets(self):
        result = self.review()
        self.check_chain(result)
        self.assertEqual([s['offsetBytes'] for s in result['steps']], [64, 34])
        self.assertEqual(result['selectedNode']['normalizedValue'],
                         '0xd782bdea4ef02a0bd391eb9089470c8080f0a68e')

    def test_exact_large_amount(self):
        result = self.review('/message/minimumRaw')
        self.check_chain(result)
        self.assertEqual(result['selectedNode']['normalizedValue'], '166357571280020680094504')

    def test_domain_goes_into_envelope_at_two(self):
        result = self.review('/domain/chainId')
        self.check_chain(result)
        self.assertEqual(result['steps'][-1]['offsetBytes'], 2)

    def test_roots(self):
        for path in ('/domain', '/message'):
            with self.subTest(path=path):
                result = self.review(path)
                self.check_chain(result)
                self.assertEqual(len(result['steps']), 1)

    def test_all_zto_paths(self):
        for node in self.trace['nodes']:
            self.check_chain(self.review(node['path']))

    def test_dynamic_string_and_nested_struct(self):
        source, trace = load('ether-mail.json'), load('ether-mail-trace.json')
        for path in ('/message/contents', '/message/from/wallet', '/message/from'):
            result = tool.review(source, trace, MAIL, path)
            self.check_chain(result)
        self.assertEqual(len(result['steps']), 2)

    def test_every_recursive_and_array_node(self):
        source, trace = load('edge-data.json'), load('edge-trace.json')
        for node in trace['nodes']:
            with self.subTest(path=node['path']):
                self.check_chain(tool.review(source, trace, EDGE, node['path']))

    def test_invalid_path(self):
        for path in ('', '/', '/message/missing', '/message/token/0', '/message/~1token',
                     '/message/Token', '/domain/chainId/', '$digest', None):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.review(path)

    def test_digest_mismatch_explains_nothing(self):
        result = self.review(expected=MAIL)
        self.assertFalse(result['accepted'])
        self.assertFalse(result['pathExplained'])
        self.assertEqual(result['steps'], [])
        self.assertNotIn('selectedNode', result)

    def test_unselected_source_substitution_blocks_explanation(self):
        self.source['message']['token'] = '0xd34a99bc0f67ae1bbd63c660e6d0b0dd03e263b7'
        result = self.review('/domain/chainId')
        self.assertFalse(result['accepted'])
        self.assertEqual(result['steps'], [])
        self.assertEqual(result['differences'][0]['path'], '/message/token')

    def test_unselected_witness_tampering_blocks_explanation(self):
        self.trace['nodes'][0]['word'] = '0x' + 'ff'*32
        with self.assertRaises(ValueError):
            self.review('/message/token')

    def test_offset_tampering(self):
        self.trace['nodes'][-1]['fields'][0]['offsetBytes'] += 32
        with self.assertRaises(ValueError):
            self.review()

    def test_duplicate_node(self):
        self.trace['nodes'].insert(0, copy.deepcopy(self.trace['nodes'][0]))
        with self.assertRaises(ValueError):
            self.review()

    def test_source_tree_cycle_fails(self):
        self.source['message']['cycle'] = self.source
        with self.assertRaises(ValueError):
            self.review()

    def test_input_immutability(self):
        before = copy.deepcopy((self.source, self.trace))
        self.review()
        self.assertEqual((self.source, self.trace), before)

    def test_output_bound(self):
        result = self.review()
        with patch.object(tool.binder.witness, 'MAX_BYTES', 10):
            with self.assertRaises(ValueError):
                tool.render(result)

    def test_cli_exits_and_ascii_output(self):
        cmd = [sys.executable, '-B', str(HERE/'witness_path.py'), str(HERE/'zto-payment.json'),
               str(HERE/'zto-trace.json'), '--path', '/message/token', '--expect']
        for expected, code in ((ZTO, 0), (MAIL, 1), ('0x12', 2)):
            run = subprocess.run(cmd+[expected], capture_output=True, timeout=20)
            self.assertEqual(run.returncode, code, run.stderr)
            if code == 2:
                self.assertEqual(run.stdout, b'')
            else:
                self.assertEqual(json.loads(run.stdout.decode('ascii'))['accepted'], code == 0)

    def test_cli_refuses_unsafe_path(self):
        run = subprocess.run([sys.executable, '-B', str(HERE/'witness_path.py'), '../outside.json',
                              str(HERE/'zto-trace.json'), '--path', '/message/token', '--expect', ZTO],
                             capture_output=True, timeout=20)
        self.assertEqual(run.returncode, 2)
        self.assertEqual(run.stdout, b'')


if __name__ == '__main__':
    unittest.main()
