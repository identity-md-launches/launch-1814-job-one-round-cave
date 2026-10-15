#!/usr/bin/env python3
"""Explain a source-bound EIP-712 field's verified byte path to the digest."""
import argparse
import json
import sys

import source_witness as binder


def review(source, trace, expected, path):
    # Apply the CLI's tree bounds to direct Python callers as well.
    binder.witness.validate_tree(source)
    binder.witness.require(type(path) is str and len(path) <= 8192,
                           'path must be a bounded string')
    result = binder.review(source, trace, expected)
    result['selectedPath'] = path
    result['pathExplained'] = False
    result['steps'] = []
    result['scope'] = ('Full witness and source checked before path extraction; '
                       'byte inclusion is not authorization or a standalone proof.')
    if not result['accepted']:
        return result
    nodes = {node['path']: node for node in trace['nodes']}
    binder.witness.require(path in nodes, 'selected path is not a witness node')
    # Build links from verified metadata rather than interpreting pointer prefixes.
    parents = {}
    for parent in trace['nodes']:
        for link in parent.get('fields', parent.get('elements', [])):
            parents[link['path']] = (parent, link['offsetBytes'])
    current = nodes[path]
    result['selectedNode'] = current.copy()
    while current['path'] in parents:
        parent, offset = parents[current['path']]
        result['steps'].append({
            'childPath': current['path'], 'childWord': current['word'],
            'parentPath': parent['path'], 'parentKind': parent['kind'],
            'offsetBytes': offset, 'lengthBytes': 32,
            'parentPreimage': parent['preimage'], 'parentWord': parent['word'],
            'operation': 'keccak256(parentPreimage)',
        })
        current = parent
    envelope = trace['envelope']
    offset = 2 if current['path'] == '/domain' else 34
    result['steps'].append({
        'childPath': current['path'], 'childWord': current['word'],
        'parentPath': '$digest', 'parentKind': 'EIP-712 envelope',
        'offsetBytes': offset, 'lengthBytes': 32,
        'parentPreimage': envelope['preimage'], 'parentWord': trace['digest'],
        'operation': 'keccak256(parentPreimage)',
    })
    result['pathExplained'] = True
    return result


def render(result):
    output = json.dumps(result, ensure_ascii=True, indent=2) + '\n'
    binder.witness.require(len(output.encode('ascii')) <= binder.witness.MAX_BYTES,
                           'complete report exceeds 1048576 bytes')
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('trace')
    parser.add_argument('--expect', required=True, help='separately retained digest')
    parser.add_argument('--path', required=True, help='exact /domain or /message node path')
    args = parser.parse_args(argv)
    try:
        binder.witness.unhex(args.expect, 32)
        result = review(binder.witness.read_workspace(args.source),
                        binder.witness.read_workspace(args.trace), args.expect, args.path)
        output = render(result)
        sys.stdout.write(output)
        return 0 if result['accepted'] else 1
    except (ValueError, OSError, RecursionError, KeyError, TypeError) as exc:
        print('witness-path: ' + json.dumps(str(exc), ensure_ascii=True), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
