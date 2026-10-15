# Settlement window review

An offline decision for workers deciding whether retained Ethereum transactions
landed within chosen block ranges. Gathering 17 joins Line 2's explicit JSON
contracts and diagnostic pointers to Line 3's pinned settlement-window replay.
Python standard library only; copy this entire folder to another workspace.
No line folders, installed packages or network access are needed.

From the repository root:

```sh
python3 -B shared/window-settlement/review.py shared/window-settlement/plan.json --sha256 be5ee9b0eefa06067695aac1caaaa5b1dabb8a505d3025f3a9ed447e4c525cb5
```

Tried: exit 0, `accepted: true`, `settlement_window_match`. Two retained real
ZTO transactions passed settlement and inclusion windows at block heights
26190898 and 26194715. The first has a single-block inclusive window; the second
has the illustrative interval 26194710–26194720. `example-match.json` is the
actual result. No new transaction observation was made for this integration.

The exact full-plan hash is checked before parsing. Line 2 validates structure
and produces JSON Pointer diagnostics before evidence opens. Line 3 checks
window membership, uniqueness and bound ordering, then replays every transaction
against its own exact evidence pin and settlement policy. Only a completely
accepted batch may enter the inclusive window comparison. Unknown fields,
including a caller-supplied acceptance flag, refuse. Window order and batch
storage order do not impose a transaction sequence; use the separate ordered
settlement tool when ordering is required.

Changing the second window's end to 26194714 refuses with exit 1 and
`window_review_required`, although settlement still passes. Supplying a string
for its start refuses with `structural_review_required` and diagnostic pointer
`/windows/1/notBeforeBlock`, before evidence replay. Actual reports are
`example-window-rejection.json` and `example-structure-rejection.json`.
The tests deliberately compute new pins for altered test plans to exercise
later gates; the production command never updates or approves a plan pin.

```sh
python3 -B shared/window-settlement/test_review.py
```

All 14 tests pass here and in a detached workspace containing only this folder.
They cover retained ZTO replay, inclusive boundaries, early/late rejection,
storage ordering, pin-before-parse, structural/semantic-before-evidence gates,
duplicate aliases, missing/mismatching evidence, unmet settlement policy,
untrusted acceptance flags, strict JSON, bounds, unsafe paths, offline execution
and input immutability. The tests patch transport to raise on use.

For your own plan, supply independently chosen windows and settlement policies,
and retain the exact complete plan hash separately. Bundled expectations are a
demonstration, not independent approval. Windows are unsigned 64-bit inclusive
block heights, one per batch transaction; batches contain 2–32 transactions.
Input plans are at most 90,000 bytes. Evidence uses bounded visible workspace
relative regular files and refuses symlinks/parent traversal. Duplicate JSON
keys and nonfinite values refuse. The complete ASCII report, including its
newline, must fit 100,000 bytes. Exit 0 is acceptance, 1 is checked mismatch,
and 2 is invalid/missing evidence, input or processing failure. Require both
exit 0 and `accepted: true`; never promote a partial report.

`provenance.json` lists ordinary, byte-identical vendored Line 2/3 sources and
real evidence with SHA-256. No submodules or remote runtime dependencies.
Historical provider assertions establish no consensus, trie inclusion,
inter-block ancestry, wall-clock deadline, current freshness, payment amount,
ownership, authorization or persistent accounting. A sufficient-confirmations
refusal may surface as `input_error` because the inherited strict replayer
detects unused reads after early refusal; it cannot yield acceptance. Replacing
the plan and expected pin together defeats the pin's trust boundary. Nothing
is signed, sent, paid or deployed. ZTO supplies the real examples; no new coin
or hook is needed.
