# Snapshot capture age

An offline, standard-library Python tool for a worker deciding whether a saved
Ethereum RPC capture meets a chosen age limit. It checks the full inherited
snapshot format and response checksum, requires a separately retained SHA-256
over **all file bytes**, and compares `captured_at_utc` to an explicit UTC
reference. No network, system clock, wallet, environment lookup or write occurs.

Run from the repository root:

```sh
python3 -B line-1/tools/snapshot-capture-age/age.py line-1/tools/snapshot-integer/live-zto.json --expected-sha256 d620b767ccc4b4ea42e7660af9fc15aeb481a808888d43675c300820f3e6b51f --reference 2026-10-15T05:02:16.159255Z --max-age-seconds 3600
```

Tried here: the retained real ZTO `totalSupply()` capture is exactly
3,600,000,000 microseconds old at that reference. The command returns exit 0,
`accepted: true`, `within_capture_age_policy`. Its actual report is
`example.json`. Moving the reference forward one microsecond returns exit 1,
`capture_too_old`; that actual report is `example-rejection.json`. No fresh chain
read was made. All 17 focused tests passed:

```sh
python3 -B line-1/tools/snapshot-capture-age/test_age.py
```

For a new snapshot, retain its exact-byte SHA-256 separately when you capture it,
then choose your reference time and maximum age independently. Do not calculate
a pin from a candidate you already distrust. This command's reference is a fixed
historical example, not the current time or a recommendation for a policy.

The age interval is inclusive: `0 <= age <= maximum`. A future capture fails,
even by one microsecond; there is no implicit clock-skew allowance. Time accepts
only `YYYY-MM-DDTHH:MM:SS[.ffffff]Z` or the equivalent `+00:00` UTC suffix,
with valid calendar fields and at most six fractional digits. Leap seconds,
non-UTC offsets and naive timestamps refuse. The maximum is a nonnegative whole
second count, capped at 315537897599. Age is an exact signed decimal string of
microseconds, avoiding rounding. Exit 0 means this policy passed, 1 means a valid
snapshot failed the age policy, and 2 means invalid input or evidence. Errors
emit no partial JSON. Reports are bounded to 100,000 bytes.

The tool uses the existing descriptor-relative no-follow reader once, refuses
hidden/parent/absolute/symlink paths, pins those bytes, and runs an isolated
in-memory copy of the existing snapshot verifier over those same bytes. It
does not change the ancestor verifier or reread a replaceable file. Imports
remain repository-relative; keep this folder with `bounded-rpc-snapshot/` and
`safe-snapshot-files/` under `line-1/tools/`.

The pin detects replacement only relative to the trusted retained hash. Neither
the capture timestamp nor reference clock is authenticated. Someone replacing
the evidence **and** the expected pin can invent a recent timestamp. The saved
response checksum alone does not cover capture metadata. A recent capture can
contain an old block, cached response or fabricated data; this is no block-age,
Ethereum state, provider authenticity, intended-request or chain-freshness check.
For intent comparison use the separate `snapshot-request-match` tool. This piece
supports the existing single-response bounded format, not the other bundle
formats. No coin, payment or deployed contract is needed; the real example uses
ZTO first.
