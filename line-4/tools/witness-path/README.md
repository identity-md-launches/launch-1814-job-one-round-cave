# Offline EIP-712 witness path

Show exactly how one typed-data field reaches the final digest. This Python
standard-library tool first verifies the **complete witness**, binds every
source value and declaration to it, and checks a separately supplied digest.
Only after all gates pass does it extract the selected node and its enclosing
hash steps. Each step gives the child's 32-byte word, its byte offset in the
parent's complete preimage, and the parent's Keccak hash. Nested structs,
arrays, dynamic strings/bytes and either root are supported.

One command from the repository root:

```sh
python3 -B line-4/tools/witness-path/witness_path.py line-4/tools/witness-path/zto-payment.json line-4/tools/witness-path/zto-trace.json --path /message/token --expect 0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774
```

**Tried:** exit 0, `accepted: true`, `pathExplained: true`. The real ZTO address
`0xd782bdea4ef02a0bd391eb9089470c8080f0a68e` occupies bytes 64..95 of the
message preimage; the resulting message hash occupies bytes 34..65 of the
66-byte EIP-712 envelope. Twelve source nodes and seven hashes are verified
before those two steps are shown. `example-zto.json` retains the actual report.
For `/domain/chainId`, the final offset is 2. Offsets are zero-based and a
step's `lengthBytes` is always 32. `selectedNode` includes the full verified
preimage for dynamic/array/struct nodes so the starting hash is inspectable too.

The fixture is inherited historical evidence for an actual ZTO transfer,
transaction `0xc4ca304c305cae326cab066639ab2156412eee7f5f774b41a2a136369f817ef7`.
It is an evidence commitment with no token signing interface. No fresh chain
observation, receipt validation, ownership or authorization is established.
The saved expected digest illustrates execution; retain your own intended
source and digest independently. Replacing source, witness and expectation
together defeats that trust boundary.

`--path` must name an exact existing witness node under `/domain` or `/message`.
Array indices are canonical decimal indices. Missing fields, declaration-only
types, nonexistent elements of empty arrays and the virtual `$digest` are not
selectable nodes. The whole source and witness are checked even when reviewing
only one field: a changed unselected source field prevents all path output.
Exit 0 means all gates passed and the path was explained; exit 1 means source
or expected digest mismatch, with no extracted nodes/steps; exit 2 means invalid
input/path or exceeded bounds, with no stdout. The path is validated after the
verification gates, so a mismatching input returns 1 before path selection.

Copy this entire folder for offline use. No installation, network, wallet,
secret, environment lookup, signing or sending occurs. Unchanged dependencies
and fixtures from `source-witness/` are listed with SHA-256 in `provenance.json`.
The witness verifier's separate Keccak implementation is inherited; this tool
adds path extraction, not another independent cryptographic implementation.

Input files must be regular, nonhidden, no-follow files beneath cwd; absolute
paths beneath cwd also work. Parent traversal and symlinks fail closed. Each
input and complete ASCII JSON output is limited to 1 MiB. Inherited limits
include 2,048 witness nodes, 48 JSON levels, 100,000 JSON tree entries, 64 types,
256 declared fields and 1 MiB total hash-input work. Strict UTF-8 JSON rejects
duplicate keys, floats and nonfinite values. Unsafe JSON integer literals must
be represented by decimal or hexadecimal strings. Size bounds are not CPU-time
guarantees. Reports disclose supplied field values and sibling bytes.

This is an explanation of a fully checked witness, not a compact standalone
Merkle proof. Sibling words appear in parent preimages, and their source
meaning is established by the full original verification, not by the extracted
path alone. Matching bytes prove no consent, replay protection, contract
support, freshness, payment or settlement.

```sh
python3 -B -m unittest discover -s line-4/tools/witness-path -v
```

**Tried:** 18 tests pass. These independently rehash every extracted step and
check byte slices for all historical ZTO and recursive/array fixture nodes,
nested Ether Mail structs, dynamic strings, root/domain offsets, exact large
integers, wrong digests, unselected source/witness changes, changed offsets,
duplicate nodes, nonexistent paths, cycles, input immutability, report bounds,
unsafe CLI paths and exit codes. The folder also works detached from all other
line tools. Local checks are not independent certification.
