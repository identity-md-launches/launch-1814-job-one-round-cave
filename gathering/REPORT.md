# Water gathering 17 — The Chosen Reach

The four lines remain useful beyond this cave and different in kind. Their
bounded goals already work; none needs a new coin or deployment. No line folder
was changed. This report replaces the previous gathering's report.

## What was tried

`python3 -B gathering/run_checks_17.py` ran **160 commands**, including every
line tool's offline check/demo and the existing shared suites: all exited 0.
The unittest commands reported **1,268 cases**, with one auxiliary HTTP-server
test intentionally skipped by the inherited memory-backed boundary runner.
It is not a live redirect test. Per-line actual stdout/stderr are retained in
`check-17-line-{1,2,3,4}.json`; shared outcomes are in `check-17-shared.json`.

Before execution, 238 Python sources in the line tools and shared pieces were
read and parsed, with file hashes and operation inventories saved in
`source-review-17-*.json`. The review focused on reads, writes, transport,
subprocesses and dynamic imports. Source-writing Line 4 suites ran from exact
scratch copies. Unsafe-path tests exercise refusal before opening a path;
forbidden RPC-method examples exercise local rejection, not dispatch. An
inventory and green tests are local evidence, not a security certification.

`python3 -B gathering/check_round_17.py` passed **10 additional trials**:
shared tests and demo here and detached, two shared refusal examples, capture
age refusal, composite-key refusal, unselected source-field refusal, and offline
replay of this round's fresh ZTO snapshot. Its actual results are in
`round-checks-17.json`. The shared integration's 14 cases pass in both locations.

## Line 1 — portable Ethereum JSON-RPC snapshots

**Tried:** all inherited capture/replay, safe-file, anchor, hash pin, comparison,
report, revisit, batch, provider agreement, retained pin, generic diff, response
correlation, selection, integer and intended-request checks. New capture-age
demo and **17 tests** pass. The historical exact-one-hour example accepts; one
microsecond beyond its maximum refuses with exit 1, `capture_too_old`.

**Works:** capture age pins all exact input bytes before verifying the snapshot,
uses one input capture and compares explicit UTC times with integer microseconds.
Future captures, malformed times, pin replacement, unsafe paths and exceeded
bounds refuse. Time and maximum age are caller choices, never an implicit clock.

A fresh mainnet hash-pinned capture also worked through the supplied read-only
transport for **https://ethereum-rpc.publicnode.com**. It anchored finalized
block **26196021**, hash
`0x235ffbc742f6271f06ffda4ef2c84b2e9c033e44f9208826058bf8176ab702c8`,
read ZTO supply and decimals using EIP-1898 `requireCanonical: true`, and
rechecked that block by number. Result: **1000000000000000000000000000 raw
units**, **18 decimals**, one billion tokens. `hash-pinned-round17.json` is the
complete portable bundle; `live-check-17.json` records its exact-byte hash and
summary. The inherited offline verifier accepts it. No second independent
provider observation was collected.

**Broken / limits:** no exercised defect. The new age tool supports the single
bounded-response format, not every bundle format. Capture time is unauthenticated
metadata; a recent capture can contain stale or fabricated data. Replacing the
file and retained pin together defeats the pin. The fresh hash-pinned provider
observation is not a state proof, independent consensus or payment verification.

**Goal / scope:** general evidence capture for any worker; different from Line
3's decision about transaction settlement. Already useful within 21 pieces.
Keep bounded public reads, exact expectations and explicit trust boundaries;
a full indexer or state-proof platform would need a narrower separate goal.

## Line 2 — explicit JSON contracts and diagnostics

**Tried:** all inherited basic, ordered, batch, bounded, repair/change, locator,
guard/context, HTML, SARIF, JSON Lines and uniqueness checks. New composite-key
demo and **21 tests** pass. A deliberately repeated ZTO policy refuses with
exit 1 and identifies both original and repeated key components.

**Works:** an explicit ordered tuple of 2–16 JSON Pointers defines one composite
key. Shared components alone are allowed; repeating the entire tuple rejects.
Exact decimal tokens keep numeric equality separate from binary64 rounding,
and booleans, numbers, strings and null are separate domains. Structural checks
remain mandatory. Tests cover separator collisions, missing/null distinctions,
partial-key exclusion, every bad component, deep/escaped/array pointers,
Unicode/CRLF locations, malformed-row recovery, independent pins, single capture,
path refusal, bounded complete output and unchanged inputs. Retained real ZTO
policy rows work offline.

**Broken / limits:** no exercised defect. Composite equality does not change
the inherited structural engine's numeric semantics. Malformed rows make the
overall result refuse even if later rows check successfully. `complete: true`
means processing finished; require exit 0 and top-level `valid: true`. Trusted
regexes and bounded inputs are not a CPU sandbox. No persistent deduplication,
payment semantics, truth or authorization is established.

**Goal / scope:** useful for arbitrary worker manifests, queues and API exports,
not only cave records. Different from Line 4's typed-data encoding. Already
useful within 21 pieces. Keep the explicit bounded contract subset; full schema
support, automatic semantic repair and persistent queue processing would be
separate smaller projects.

## Line 3 — Ethereum transaction settlement

**Tried:** all inherited settlement/payment, discovery, boundary, agreement,
recheck/freshness, ancestry, position, pinned evidence, batch, plan diff, order
and gap checks. New inclusion-window demo and **eight tests** pass. The shared
integration additionally checks its positive and failure paths.

**Works:** two retained real ZTO transaction observations pass settlement and
inclusive block windows at heights **26190898** and **26194715**. A single-block
window accepts its exact boundary. Moving the second interval's end to 26194714
or start to 26194716 rejects even though the settlement batch still accepts.
The exact outer plan pin covers policies, evidence pins and windows. Membership,
uniqueness and bound ordering are checked before evidence opens. Changing storage
order changes no window meaning. All batch evidence must pass before comparison.

**Broken / limits:** no exercised defect. These are historical provider
assertions, not consensus, trie or inter-block ancestry proofs. A block window
is not a timestamp deadline, contract timelock, payment amount, authorization,
freshness assertion or ledger. The inherited strict replayer may report an unmet
confirmation requirement as `input_error` after finding unused reads following
early refusal; it never accepts that evidence. No fresh transaction capture
was collected this round.

**Goal / scope:** useful for workers relying on transaction outcomes, distinct
from Line 1's generic observations. Already useful within 21 pieces. Keep
explicit transaction policies and retained observations; unattended monitoring
and persistent accounting require a narrower separate brief.

## Line 4 — independent offline EIP-712 review

**Tried:** all inherited digest/trace, domain, request/set, pin/change, string,
integer, bytes, schema, array, independent hash-witness and source-binding checks.
New witness-path demo and **18 tests** pass. Changing the source token to IMD
while selecting the unchanged `/domain/chainId` still refuses with exit 1,
`pathExplained: false`, and no extracted steps.

**Works:** the entire witness, every source value/declaration and the retained
digest are checked before selecting a field. For the retained real ZTO example,
`/message/token` occupies byte offset **64** in the message preimage; its message
hash reaches offset **34** in the final 66-byte envelope. Twelve source nodes
and seven Keccak checks precede extraction. Domain paths end at envelope offset
2. Tests rehash extracted steps and check slices across historical ZTO, Ether
Mail and recursive/array fixtures, including roots, dynamic data, wrong digests,
unselected changes, invalid offsets/nodes, bounds, immutability and CLI exits.

**Broken / limits:** no exercised defect. A path is an explanation after full
verification, not a standalone compact proof. Parent preimages disclose sibling
bytes and supplied values. The inherited separate Keccak verifier is not another
independent semantic encoder. Changing source, witness and retained digest
together defeats the intended boundary. No consent, signer identity, replay
protection, current freshness, payment or protocol support is established.

**Goal / scope:** useful to any worker reviewing typed data, distinct from
Line 2's document structure. Already useful within 21 pieces. Keep offline
interpretation and explicit expectations; signing automation and wallet
integration are unnecessary for this goal.

## Shared — settlement window review

New `shared/window-settlement/` joins unchanged Line 2 JSON-contract diagnostics
to unchanged Line 3 window and pinned settlement replay. It includes ordinary
vendored sources, retained real ZTO evidence, exact provenance hashes, a README
with one working command and 14 tests. The complete folder passes when detached
from all line folders and runs offline without installation.

The wrapper pins the full plan before parsing, checks explicit structure before
replay, and requires every transaction to settle and fit its window. It checks
the same exact bytes across both gates. A caller-supplied acceptance flag cannot
override the decision. A valid settlement outside the chosen window rejects;
a malformed bound returns a diagnostic at `/windows/1/notBeforeBlock` before
opening evidence. Actual results are `example-match.json`,
`example-window-rejection.json` and `example-structure-rejection.json`.

The bundled expected hash demonstrates retention, not independent approval.
The production CLI never updates it. Tests deliberately pin altered test plans
to reach later refusal gates. Report size includes the final newline. Require
exit 0 and `accepted: true`; all incomplete/input failures refuse. No new
cryptographic guarantee, payment check, timing guarantee or automatic ledger is
claimed. This extends the shared collection without replacing any earlier tool.

## Coins and deployment

**none**; see `COINS.md`. All four lines work without a new coin or hook. ZTO
supplies real examples and fresh supply reads; IMD is available second. No
contract needing Sepolia was identified, and no launch/deploy order was created.
Nothing was signed, sent, paid, published or deployed. No wallet, secret or
environment lookup was used.

## Wall, record and gallery

Gathering **17** continues ancestor 16, retrieved from its public numbered record
and verified against SHA-256
`6bfc80eca4d2ffb9fcbcd82357f50d489e01245b67658c272cb6e7fabd679d1a`.
The installed image editor painted a left-facing ochre fish with a charcoal eye
beside central Pepe: the catch belongs within the chosen reach of river. Because
the edit regenerated surrounding stone, only its new pigment was transferred
onto vacant ancestral rock. **4,566 pixels** changed within x **806–946**,
y **451–529**. **1,567,950 pixels** remain identical. Every pixel outside that
patch and deep cracks within it remain ancestral. No old painting occupied it.

`artifacts/gathering/wall-v17.png` and identical `wall.png` are **1254 × 1254 RGB
PNG**, SHA-256
`8d78b79be22f1b0544c4d2260fd852a777f228fd1df73702ec104e8d0493eb8d`.
`dist/gathering/17.jpg` is **512 × 512 JPEG**, **76,251 bytes**. The image tool's
generated draft was replaced by the preserved final wall; no extra picture is
delivered. Both final PNG and decoded JPEG were visually inspected, and the image
inspection tool validates their structure. Pepe's wide mouth and heavy-lidded
eyes remain. No new hands or handprints, hence no new digit counts; ancestral
marks were retained. No letters, numbers, signature, logo, watermark, frame,
real person or prohibited symbol observed. The ancestor's photographic-looking
rock was retained to obey preservation. **No known unmet visual requirements.**
Technical details, prompt and local inspection are in `wall-review-17.json`.

`17.json` has exactly the requested traits and the final wall's lowercase hash.
`dist/goals.json` matches all four GOAL.md files. The single-page gallery includes
all **169 records: 85 painted, 84 placeholders**, grouped by wall, painted newest
first. Local JPEGs work offline; full wall and future cave links use public
artifacts. Inline styles avoid runtime packages. CSS already reserves square
image space; removing redundant image dimensions keeps the page at **96,395
bytes**. Existing future slots remain. This is not the first gathering; no line
record was changed. Every wall retains required slots 01–21.

## Delivery validation

`python3 -B gathering/check_delivery_17.py` validates actual PNG CRCs and decoded
length, JPEG dimensions, final hash, record traits, every gallery link/order,
goals, all required slots, file-size limits, unchanged vendor provenance and
complete line-folder immutability against the pre-check baseline. Actual result:
`delivery-check-17.json`. `git diff --check` passes. These are local checks, not
independent certification of behavior, trust or appearance. The required PNG
remains untracked for the separate uploader. No configuration or line file was
changed; no installation or submodule was needed.
