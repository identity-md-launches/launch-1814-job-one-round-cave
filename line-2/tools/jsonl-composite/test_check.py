"""Offline tests of composite semantics, evidence spans and failure boundaries."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import socket
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('composite_check', Path(__file__).with_name('check.py'))
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)

class Reader:
    def __init__(self, files):
        self.files, self.reads = files, []
    def read_bytes(self, name):
        self.reads.append(name)
        return self.files[name]

class CompositeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.deps = check.dependencies()
        cls.reader, cls.unique, cls.framing, cls.source, cls.engine, cls.rules = cls.deps

    def review(self, data, pointers=None, contract=b'{"type":"object"}', **pins):
        self.capture = Reader({'c':contract,'d':data})
        return check.inspect(self.capture,*self.deps[1:],'c','d',
                             ['/a','/b'] if pointers is None else pointers,**pins)

    def key_report(self, report):
        return report['composite_uniqueness']

    def test_shared_components_are_allowed(self):
        r=self.review(b'{"a":1,"b":"x"}\n{"a":1,"b":"y"}\n{"a":2,"b":"x"}')
        self.assertTrue(r['valid'])
        self.assertEqual(self.key_report(r)['distinct_keys'],3)
        self.assertEqual(self.capture.reads,['c','d'])

    def test_all_components_match_and_anchor_first(self):
        r=self.review(b'{"a":1,"b":"x"}\n{"a":1,"b":"x"}\n{"a":1,"b":"x"}')
        errors=self.key_report(r)['errors']
        self.assertEqual([e['first']['line'] for e in errors],[1,1])
        self.assertEqual([e['line'] for e in errors],[2,3])
        self.assertEqual([c['pointer'] for c in errors[0]['components']],['/a','/b'])
        self.assertTrue(r['structural']['valid'])
        self.assertFalse(r['valid'])

    def test_tuple_not_separator_concatenation(self):
        r=self.review(b'{"a":"a|b","b":"c"}\n{"a":"a","b":"b|c"}\n{"a":"ab","b":"c"}\n{"a":"a","b":"bc"}')
        self.assertTrue(r['valid'])

    def test_component_order_matters(self):
        self.assertTrue(self.review(b'{"a":"x","b":"y"}\n{"a":"y","b":"x"}')['valid'])

    def test_exact_numeric_equivalence(self):
        r=self.review(b'{"a":1,"b":-0}\n{"a":10e-1,"b":0.0}\n{"a":true,"b":0}\n{"a":"1","b":0}')
        self.assertEqual([e['line'] for e in self.key_report(r)['errors']],[2])

    def test_binary64_rounding_does_not_merge(self):
        r=self.review(b'{"a":9007199254740992.0,"b":1}\n{"a":9007199254740993.0,"b":1}')
        self.assertTrue(r['valid'])

    def test_null_missing_and_no_partial_key_registration(self):
        r=self.review(b'{"a":null}\n{"a":null,"b":null}\n{"a":null,"b":null}')
        k=self.key_report(r)
        self.assertEqual(k['ineligible_lines'],[1])
        self.assertEqual(k['checked_rows'],2)
        self.assertEqual(k['errors'][1]['first']['line'],2)

    def test_all_bad_components_reported(self):
        r=self.review(b'{"a":[]}\n{"a":{},"b":[]}')
        self.assertEqual([e['kind'] for e in self.key_report(r)['errors']],
                         ['non_scalar','missing_value','non_scalar','non_scalar'])
        self.assertEqual(self.key_report(r)['checked_rows'],0)

    def test_missing_deep_anchor(self):
        r=self.review(b'{"a":{}}',['/a/b/c','/z'])
        self.assertEqual([e['anchor_pointer'] for e in self.key_report(r)['errors']],['/a',''])

    def test_escaped_pointer_and_array_indices(self):
        data=b'{"a/b~":[1],"b":2}\n{"a/b~":[1],"b":2}'
        r=self.review(data,['/a~1b~0/0','/b'])
        self.assertEqual(self.key_report(r)['errors'][0]['kind'],'duplicate_key')
        r=self.review(data,['/a~1b~0/01','/b'])
        self.assertEqual(self.key_report(r)['ineligible_lines'],[1,2])

    def test_root_pointer_supported(self):
        r=self.review(b'null\nnull',['','/missing'],b'{"type":"null"}')
        self.assertEqual([e['kind'] for e in self.key_report(r)['errors']],['missing_value']*2)

    def test_unicode_crlf_spans_for_all_components(self):
        data='{"a":"日","b":1}\r\n\t{"b":1.0,"a":"\\u65e5"}\r\n'.encode()
        r=self.review(data)
        e=self.key_report(r)['errors'][0]
        for occurrence,expected in ((e,[b'"\\u65e5"',b'1.0']), (e['first'],['"日"'.encode(),b'1'])):
            for comp,token in zip(occurrence['components'],expected):
                span=comp['document_source']['value']
                self.assertEqual(data[span['start']['byte_offset']:span['end']['byte_offset']],token)
                self.assertEqual(data.decode()[span['start']['char_offset']:span['end']['char_offset']].encode(),token)
                self.assertEqual(span['start']['line'],occurrence['line'])

    def test_malformed_rows_do_not_hide_later_duplicate(self):
        r=self.review(b'{"a":1,"b":2}\n{\n{"a":1,"b":2}')
        self.assertEqual(self.key_report(r)['skipped_malformed_lines'],[2])
        self.assertEqual(self.key_report(r)['errors'][0]['line'],3)
        self.assertFalse(self.key_report(r)['valid'])

    def test_structure_still_mandatory(self):
        r=self.review(b'{"a":1,"b":2}',contract=b'{"type":"object","properties":{"x":{"type":"string"}},"required":["x"]}')
        self.assertFalse(r['valid'])
        self.assertTrue(self.key_report(r)['valid'])

    def test_unsupported_exact_number_refuses(self):
        r=self.review(b'{"a":1e-99999999999999999999999999,"b":0}')
        self.assertEqual(self.key_report(r)['errors'][0]['kind'],'unsupported_number')
        self.assertFalse(r['valid'])

    def test_selection_limits_precede_user_reads(self):
        for pointers in ([],['/a'],['/a','/a'],['a','/b'],['/~2','/b'],['/'+ 'a'*1025,'/b'],['/'+str(i) for i in range(17)]):
            with self.subTest(pointers=pointers), self.assertRaises(ValueError):
                self.review(b'{}',pointers)
            self.assertEqual(self.capture.reads,[])

    def test_pins_before_parse_and_contract_before_document(self):
        data=b'{"a":1,"b":2}'
        self.assertTrue(self.review(data,document_sha256=hashlib.sha256(data).hexdigest())['valid'])
        for pin in ('wrong','0'*64):
            with self.assertRaises(ValueError):
                self.review(b'{',contract_sha256=pin)
            self.assertNotIn('d',self.capture.reads)
        with self.assertRaisesRegex(ValueError,'SHA-256 mismatch'):
            self.review(b'{',document_sha256=hashlib.sha256(data).hexdigest())

    def test_complete_output_failure(self):
        r=self.review(b'{"a":1,"b":2}')
        out,err=io.StringIO(),io.StringIO()
        with patch.object(check,'dependencies',return_value=self.deps), patch.object(check,'inspect',return_value=r), patch.object(self.framing,'MAX_OUTPUT_BYTES',100), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status=check.main(['c','d','--key','/a','/b'])
        self.assertEqual(status,2)
        self.assertEqual(out.getvalue(),'')
        self.assertFalse(json.loads(err.getvalue())['complete'])

    def test_cli_exit_codes_and_immutability(self):
        for data,code in ((b'{"a":1,"b":2}',0),(b'{"a":1,"b":2}\n{"a":1,"b":2}',1),(b'{\n{"a":1,"b":2}',2)):
            r=self.review(data)
            out,err=io.StringIO(),io.StringIO()
            with patch.object(check,'dependencies',return_value=self.deps),patch.object(check,'inspect',return_value=r),contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
                status=check.main(['c','d','--key','/a','/b'])
            self.assertEqual(status,code)
            self.assertEqual(json.loads(out.getvalue()),r)
            self.assertEqual(err.getvalue(),'')
            self.assertEqual(self.capture.files['d'],data)

    def test_saved_real_zto_policy_no_network(self):
        with patch.object(socket,'socket',side_effect=AssertionError('network forbidden')):
            r=check.inspect(*self.deps,'shared/payment-evidence/policy.contract.json',
                'line-2/tools/jsonl-contract/zto-policy.jsonl',['/token','/tx'])
        self.assertTrue(r['valid'])

    def test_file_boundary_and_symlink(self):
        for path in ('../outside','.hidden','/outside'):
            with self.assertRaises((ValueError,OSError)):
                check.inspect(*self.deps,'shared/payment-evidence/policy.contract.json',path,['/token','/tx'])
        root=Path('test/scratch/composite37')
        root.mkdir(parents=True,exist_ok=True)
        target=root/'target.jsonl'
        target.write_bytes(b'{"a":1,"b":2}')
        link=root/'link.jsonl'
        if not link.is_symlink():
            link.symlink_to('target.jsonl')
        with self.assertRaises(OSError):
            self.reader.read_bytes(str(link))

if __name__=='__main__':
    unittest.main(verbosity=2)
