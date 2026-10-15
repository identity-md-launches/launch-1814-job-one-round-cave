# Offline JSON Lines composite key checker

Validate a queue or API export against an explicit structural contract and reject
rows whose **whole selected key** repeats. Shared individual fields are allowed:
`(1,"a")`, `(1,"b")`, `(2,"a")` are distinct keys. A later `(1,"a")` rejects.
Diagnostics identify every component token in the repeated row and the first
matching row, without rewriting either input.

From the repository root, Python 3.10+ on POSIX, no installation or network:

```sh
python3 -B line-2/tools/jsonl-composite/check.py shared/payment-evidence/policy.contract.json line-2/tools/jsonl-contract/zto-policy.jsonl --key /token /tx
```

Tried locally: exit **0**, the saved historical ZTO payment policy satisfies both
structure and the `/token` plus `/tx` key rule. This is retained evidence, not a
fresh chain read or proof of payment. No coin, account, wallet or RPC is needed.
The actual report is `policy.result.json` beside this README.

To see repetition refuse:

```sh
python3 -B line-2/tools/jsonl-composite/check.py shared/payment-evidence/policy.contract.json line-2/tools/jsonl-unique/repeated-policy.jsonl --key /token /tx
```

Tried locally: exit **1**, both rows satisfy structure, but row 2 repeats row 1's
entire key. `repeated.result.json` records both tokens on both rows. The input is
an explicitly duplicated saved policy, not two observations or two payments.

## Explicit key and equality

`--key` accepts 2–16 distinct RFC 6901 JSON Pointers, each at most 1,024
characters. Their order is retained. `~0` and `~1` escape tildes and slashes.
Array indices must be canonical nonnegative integers. An empty pointer selects
the row root, although a container root cannot be a scalar component.

Each component must exist and be a scalar. Null is present and compares to null;
missing values refuse. Containers and unsupported numeric tokens refuse. Every
bad component is listed; deep missing paths report the nearest existing source
container with `anchor_pointer`, never a fabricated token for the missing value.
A row with any bad component never registers a partial key.

Equality uses an ordered tuple of typed scalars, never joined strings. Numbers
compare their exact original decimal tokens: `1`, `1.0`, `10e-1` agree and `-0`
agrees with zero. Binary64 rounding cannot merge distinct key numbers. Booleans,
numbers, strings and null remain separate domains. Strings compare decoded code
points without case folding or Unicode normalization. Numeric Decimal/hash
limits refuse explicitly. The inherited structural engine retains its original
int/float semantics; exact key comparison does not fix structural numeric limits.

All strictly parsed rows participate, including structurally invalid rows.
Malformed rows are skipped for key matching, reported explicitly and make the
whole result refuse; later rows are still checked. Third and later duplicates
always point to the first eligible occurrence. `checked_rows` counts complete
keys including duplicates, `distinct_keys` counts their first occurrences.
`ineligible_lines` identifies parsed rows with unusable components.

## Acceptance and boundaries

Require **top-level `valid: true` and exit 0**. The complete structural report is
under `structural`; key results are under `composite_uniqueness`. `complete: true`
means processing finished, not acceptance or coverage of malformed rows.

Inputs are explicit visible relative workspace regular files. Inherited
no-follow descriptor traversal refuses absolute, hidden, parent, symlink and
special-file paths. Each path is captured once, at most 1,000,000 bytes; contract
preparation precedes document capture. Optional `--contract-sha256` and
`--document-sha256` bind independently retained lowercase SHA-256 hashes before
parsing. Hashes do not authenticate an author.

At most 256 LF-delimited rows; CRLF and an optional final LF retain original
coordinates. Duplicate keys, nonfinite numbers, blanks and invalid JSON refuse.
Spans use one-based lines/Unicode code-point columns and zero-based whole-file
byte/character offsets with exclusive ends. Reports are ASCII-escaped JSON and
must fit 100,000 bytes including the final newline, or no stdout is emitted.

Exit 0: both checks pass. Exit 1: structural or key violations. Exit 2 with a
complete report: malformed rows. Exit 2 with empty stdout and JSON stderr:
input, pin, contract or output-limit failure. Only input reads and stdout/stderr
writes occur. No repair, persistence or transaction sending.

Keep sibling folders `jsonl-unique`, `jsonl-contract`, `source-locator`,
`rule-locator`, `bounded-contract`, and `json-contract` as ordinary files when
relocating this tool. Runtime is Python standard library only. Contracts use the
inherited deliberate subset, not full JSON Schema. Trusted regexes are required;
byte bounds are not a CPU sandbox. This checks one composite key within one
file, not persistent deduplication, referential integrity, payment semantics,
authenticity or authorization. For independent unique columns, use the unchanged
`jsonl-unique` ancestor instead.

## Checks performed

```sh
python3 -B line-2/tools/jsonl-composite/test_check.py
```

All **21 tests passed** locally: shared components, whole-key repeats, first
anchors, separator collisions, ordering, typed and exact decimal comparisons,
large-number rounding, null/missing, partial-key exclusion, all bad components,
deep/escaped/array/root pointers, Unicode/CRLF source slices, malformed recovery,
mandatory structure, unsupported numbers, selection limits, independent pins,
single capture, path and symlink refusal, complete-output failure, CLI exits,
input immutability, and saved real ZTO policy with network disabled. The unchanged
ancestor suites also passed: **19 uniqueness + 18 JSON Lines tests**. Local
checks are observations, not independent certification.
