# Settlement inside an explicit block window

`window.py` checks whether each transaction in a pinned Ethereum settlement
batch was included between an independently chosen first and last block,
inclusive. It uses Python 3's standard library and the unchanged Line 3
`settlement-batch` and `pinned-position` pieces. Nothing is signed or sent.

From the repository root, one command shows it working offline:

```sh
python3 -B line-3/tools/settlement-window/window.py --demo
```

Tried locally: exit 0 with `settlement_window_match`. Two retained real ZTO
transaction observations passed. One landed exactly on its chosen lower and
upper boundary, block **26190898**; the other landed at **26194715** within
the illustrative inclusive interval **26194710–26194720**. Changing the
second interval to end at 26194714 or begin at 26194716 returns exit 1,
`window_review_required`, while the underlying settlement batch still passes.
Eight focused tests passed. `demo-result.json` contains the actual demo report.
No new live-chain observation was made.

For a separately reviewed plan, run:

```sh
python3 -B line-3/tools/settlement-window/window.py --plan path/to/plan.json --sha256 YOUR_INDEPENDENTLY_RETAINED_FULL_PLAN_SHA256
```

The plan has exactly `version` (integer 1), `batch` (a settlement-batch
version-1 manifest), and `windows` (one entry per batch transaction). Each
window has exactly `transactionHash`, `notBeforeBlock`, and `notAfterBlock`.
Bounds are inclusive integers from 0 through 2^64−1, with first no greater
than last. Transactions must match the batch exactly once; windows may appear
in any order. See `demo-plan.json`. The SHA-256 is over **the exact whole plan
file**, including settlement policies, evidence pins and interval bounds.

The tool checks the outer pin before parsing. It validates all windows and the
whole batch before opening any evidence. Every batch item must pass its own
evidence pin, canonicality, success, confirmation and finality policy before
window checks can accept. Inherited same-height block-hash conflicts also
reject the batch. File reads are bounded to 90 KB and restricted to visible,
workspace-relative regular files without symlinks; strict JSON rejects duplicate
keys and nonfinite values. Output is bounded to 100 KB.

Exit 0 means all checks pass. Exit 1 means pin, settlement or window review is
required. Exit 2 means invalid input or unavailable/invalid evidence. The
bundled plan hash illustrates retention; it is not independent approval.

This reports historical provider assertions. It does not prove Ethereum
consensus, trie inclusion or inter-block ancestry. A block-height window is
not a wall-clock deadline, contract timelock, payment amount, authorization,
freshness assertion or persistent ledger. The caller chooses and retains the
right policy and full-plan hash independently. No network or dependency
installation is needed for the demo or CLI.

Tests: `python3 -B -m unittest discover -s line-3/tools/settlement-window -p 'test_*.py' -v`.
