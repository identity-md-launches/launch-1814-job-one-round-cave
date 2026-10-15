#!/usr/bin/env python3
"""Bind a verified EIP-712 hash witness to its complete source typed data."""
import argparse
import json
import re
import sys

import hash_witness as witness

HEX_INTEGER = re.compile(r'0[xX][0-9a-fA-F]+\Z')
DEC_INTEGER = re.compile(r'-?(?:0|[1-9][0-9]*)\Z')
SAFE_JSON_INTEGER = (1 << 53) - 1


def need(ok, problem):
    if not ok:
        raise ValueError(problem)


def schema(source):
    """Validate every declaration, then derive canonical reachable encodings."""
    need(type(source) is dict and set(source) == {'types', 'primaryType', 'domain', 'message'},
         'source must have exactly types, primaryType, domain and message')
    types = source['types']
    primary = source['primaryType']
    need(type(types) is dict and 2 <= len(types) <= 64 and
         type(primary) is str and primary in types and primary != 'EIP712Domain' and
         'EIP712Domain' in types, 'invalid source type roots')
    count = 0
    for name, fields in types.items():
        need(type(name) is str and re.fullmatch(witness.IDENT, name) is not None and
             not witness.atomic_type(name) and name not in ('uint', 'int') and
             re.fullmatch(r'(?:u?int|bytes)[0-9]+', name) is None,
             'invalid or reserved struct name')
        need(type(fields) is list, 'struct fields must be a list')
        count += len(fields)
        need(count <= 256, 'too many declared fields')
        names = set()
        for field in fields:
            need(type(field) is dict and set(field) == {'name', 'type'}, 'invalid field object')
            label, kind = field['name'], field['type']
            need(type(label) is str and re.fullmatch(witness.IDENT, label) is not None and
                 label not in names and type(kind) is str and witness.TYPE.fullmatch(kind) is not None,
                 'invalid or duplicate field')
            names.add(label)
            base = witness.base(kind)
            need(witness.atomic_type(base) or base in types, 'unknown field type')

    def declaration(name):
        return name + '(' + ','.join(f["type"] + ' ' + f["name"] for f in types[name]) + ')'

    encodings = {}

    def encoding_for(root):
        if root not in encodings:
            pending, visited = [root], set()
            while pending:
                name = pending.pop()
                if name in visited:
                    continue
                visited.add(name)
                for field in types[name]:
                    child = witness.base(field['type'])
                    if child in types:
                        pending.append(child)
            encodings[root] = declaration(root) + ''.join(
                declaration(name) for name in sorted(visited - {root}))
        return encodings[root]

    reached = set()
    for root in ('EIP712Domain', primary):
        encoding_for(root)
        reached.update(witness.declarations(encodings[root], root))
    need(reached == set(types), 'source has declarations absent from both roots')
    return types, primary, encoding_for


def source_integer(value):
    if type(value) is int:
        need(abs(value) <= SAFE_JSON_INTEGER,
             'unsafe JSON numeric literal; use a decimal or 0x string')
        return value
    need(type(value) is str and len(value) <= 80 and
         (DEC_INTEGER.fullmatch(value) or HEX_INTEGER.fullmatch(value)),
         'integer must be a canonical decimal or 0x string')
    return int(value, 16 if value[:2].lower() == '0x' else 10)


def check_source(source, trace):
    types, primary, encoding_for = schema(source)
    nodes = {n['path']: n for n in trace['nodes']}
    differences = []
    inspected = set()

    def difference(path, reason):
        if len(differences) < 100:
            differences.append({'path': path, 'reason': reason})

    if trace['primaryType'] != primary:
        difference('/primaryType', 'type differs')

    def visit(kind, value, path, depth):
        need(depth <= 48, 'source value nesting limit exceeded')
        node = nodes.get(path)
        if node is None:
            difference(path, 'node missing from witness')
        else:
            inspected.add(path)
            if node['type'] != kind:
                difference(path, 'declared type differs')
        array = witness.ARRAY.fullmatch(kind)
        if array:
            need(type(value) is list and len(value) <= witness.MAX_NODES,
                 path + ': expected bounded array')
            if array[2]:
                need(len(value) == int(array[2]), path + ': fixed array length differs')
            if node is not None and node['kind'] == 'array' and len(node['elements']) != len(value):
                difference(path, 'array length differs')
            for i, item in enumerate(value):
                visit(array[1], item, path + '/' + str(i), depth + 1)
            return
        if kind in types:
            need(type(value) is dict and set(value) == {f['name'] for f in types[kind]},
                 path + ': source struct fields differ')
            expected_encoding = encoding_for(kind)
            if node is not None and node['kind'] == 'struct' and node['typeEncoding'] != expected_encoding:
                difference(path, 'type encoding differs')
            for field in types[kind]:
                visit(field['type'], value[field['name']], path + '/' + field['name'], depth + 1)
            return
        if kind in ('string', 'bytes'):
            raw = value.encode('utf-8') if kind == 'string' and type(value) is str else None
            if kind == 'bytes':
                raw = witness.unhex(value)
            need(raw is not None, path + ': string value required')
            if node is not None and node['kind'] == 'dynamic' and witness.unhex(node['preimage']) != raw:
                difference(path, 'dynamic bytes differ')
            return
        if witness.INTEGER.fullmatch(kind):
            normalized = str(source_integer(value))
        elif kind == 'bool':
            normalized = value
        elif kind == 'address' or witness.FIXED.fullmatch(kind):
            normalized = value
        else:
            raise ValueError(path + ': unsupported atomic type')
        word = witness.atomic_word(kind, normalized)
        if node is not None and witness.unhex(node['word'], 32) != word:
            difference(path, 'atomic encoded word differs')

    visit('EIP712Domain', source['domain'], '/domain', 0)
    visit(primary, source['message'], '/message', 0)
    for path in sorted(set(nodes) - inspected):
        difference(path, 'witness node absent from source')
    return {'sourceTypedDataChecked': True, 'sourceMatchesWitness': not differences,
            'sourceNodesChecked': len(inspected), 'differences': differences,
            'differenceLimit': 100}


def review(source, trace, expected):
    witness_result = witness.verify(trace, expected)
    source_result = check_source(source, trace)
    return {**witness_result, **source_result,
            'accepted': witness_result['matchesExpected'] and source_result['sourceMatchesWitness'],
            'scope': 'Witness bytes, source typed data and separately supplied digest agree; no signing authorization proven.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', help='source EIP-712 typed-data JSON under cwd')
    parser.add_argument('trace', help='complete version-1 witness JSON under cwd')
    parser.add_argument('--expect', required=True, help='independently retained 32-byte digest')
    args = parser.parse_args(argv)
    try:
        witness.unhex(args.expect, 32)
        source = witness.read_workspace(args.source)
        trace = witness.read_workspace(args.trace)
        result = review(source, trace, args.expect)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0 if result['accepted'] else 1
    except (ValueError, OSError, RecursionError, KeyError, TypeError) as exc:
        print('source-witness: ' + json.dumps(str(exc), ensure_ascii=True), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
