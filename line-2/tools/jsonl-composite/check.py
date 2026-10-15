#!/usr/bin/env python3
"""Check JSON Lines structure and uniqueness of one explicit composite scalar key."""
import argparse
import json
from pathlib import Path
import sys
import types

def bounded_module():
    # Bootstrap only the fixed, trusted sibling; user inputs use its no-follow reader.
    source = Path(__file__).absolute().parent.parent / 'bounded-contract' / 'check.py'
    relative = source.relative_to(Path.cwd()).as_posix()
    if any(not p or p.startswith('.') for p in relative.split('/')):
        raise ValueError('run inside the workspace containing the sibling tools')
    # Open each component without following links, including the trusted bootstrap.
    import os
    import stat
    directory = os.open('.', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    leaf = None
    try:
        parts = relative.split('/')
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=directory)
            os.close(directory)
            directory = child
        leaf = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                       dir_fd=directory)
        if not stat.S_ISREG(os.fstat(leaf).st_mode):
            raise ValueError('trusted sibling must be a regular file')
        chunks, remaining = [], 1_000_001
        while remaining:
            chunk = os.read(leaf, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        code = b''.join(chunks)
        if len(code) > 1_000_000:
            raise ValueError('trusted sibling exceeds byte limit')
    finally:
        if leaf is not None:
            os.close(leaf)
        os.close(directory)
    module = types.ModuleType('repair_bounded_contract')
    module.__file__ = str(source)
    exec(compile(code, str(source), 'exec'), module.__dict__)
    return module


def dependencies():
    reader = bounded_module()
    path = Path(__file__).absolute().parent.parent / 'jsonl-unique' / 'check.py'
    unique = types.ModuleType('composite_unique_helpers')
    unique.__file__ = str(path)
    exec(compile(reader.read_bytes(path.relative_to(Path.cwd()).as_posix()), str(path), 'exec'), unique.__dict__)
    _, framing, source, engine, rules = unique.dependencies()
    return reader, unique, framing, source, engine, rules


def inspect(reader, unique, framing, source, engine, rules, contract_name,
            document_name, pointers, contract_sha256=None, document_sha256=None):
    # Validate selection before opening either user input. Order is significant.
    unique.pointers_checked(pointers)
    if len(pointers) < 2:
        raise ValueError('a composite key needs 2 to 16 distinct JSON Pointers')
    captured = {}
    class Capture:
        def read_bytes(self, name):
            if name not in captured:
                captured[name] = reader.read_bytes(name)
            return captured[name]
    structural = framing.inspect(Capture(), source, engine, rules, contract_name,
                                 document_name, contract_sha256, document_sha256)
    text = captured[document_name].decode('utf-8')
    bodies = text.split('\n')
    if text.endswith('\n'):
        bodies.pop()
    seen, errors, malformed, ineligible = {}, [], [], []
    char_start = checked = 0
    for row, body in zip(structural['rows'], bodies):
        line = row['line']
        if row['status'] == 'malformed':
            malformed.append(line)
        else:
            document = source.Source(body.encode('utf-8'), document_name)
            components, locations, failures = [], [], []
            for pointer in pointers:
                anchor = pointer
                while anchor not in document.values:
                    anchor = anchor.rsplit('/', 1)[0]
                location = document.location(anchor)
                framing.shift_location(location, line, row['byte_start'], char_start)
                component = {'pointer': pointer, 'document_source': location}
                try:
                    value = unique.resolve(document.value, pointer)
                except KeyError:
                    failures.append(dict(component, kind='missing_value', anchor_pointer=anchor))
                    continue
                try:
                    start, end = document.values[pointer]
                    key = unique.scalar_key(value, body[start:end])
                except ValueError as exc:
                    failures.append(dict(component,
                        kind='non_scalar' if isinstance(value, (dict, list)) else 'unsupported_number',
                        message=str(exc)))
                    continue
                components.append(key)
                locations.append(component)
            if failures:
                ineligible.append(line)
                errors.extend(dict(error, line=line) for error in failures)
            else:
                # Tuple-of-typed-scalars: no concatenation, separators or coercion.
                key = tuple(components)
                occurrence = {'line': line, 'components': locations}
                checked += 1
                if key in seen:
                    errors.append(dict(occurrence, kind='duplicate_key', first=seen[key]))
                else:
                    seen[key] = occurrence
        char_start += len(body) + 1
    key_valid = not (errors or malformed)
    valid = structural['valid'] and key_valid
    return {'valid': valid, 'complete': True,
            'status': 'valid' if valid else 'rejected', 'structural': structural,
            'composite_uniqueness': {'pointers': list(pointers), 'valid': key_valid,
                'checked_rows': checked, 'distinct_keys': len(seen),
                'skipped_malformed_lines': malformed, 'ineligible_lines': ineligible,
                'error_count': len(errors), 'errors': errors,
                'equality': 'ordered tuple of exact decimal numbers or typed strings, booleans and null; all components must match'}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('contract')
    parser.add_argument('document')
    parser.add_argument('--key', nargs='+', required=True, help='2 to 16 JSON Pointers forming one key')
    parser.add_argument('--contract-sha256')
    parser.add_argument('--document-sha256')
    args = parser.parse_args(argv)
    try:
        deps = dependencies()
        result = inspect(*deps, args.contract, args.document, args.key,
                         args.contract_sha256, args.document_sha256)
        output = deps[2].encode(result)
        sys.stdout.write(output)
        return 2 if result['structural']['summary']['malformed'] else (0 if result['valid'] else 1)
    except (ValueError, OSError, RecursionError, KeyError, IndexError) as exc:
        sys.stderr.write(json.dumps({'valid': False, 'complete': False,
                                     'error': str(exc)[:1000]}, ensure_ascii=True)+'\n')
        return 2


if __name__ == '__main__':
    sys.exit(main())
