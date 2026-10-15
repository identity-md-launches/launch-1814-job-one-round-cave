# Water gathering 17 — The Chosen Reach

[REPORT.md](REPORT.md) records what was tried, works and remains limited for each
line. [COINS.md](COINS.md): **none**; no new asset or deployment is needed.
[Settlement window review](../shared/window-settlement/README.md) shares Line 3's
pinned window replay with Line 2's structural diagnostics, portable and offline.

From the repository root:

```sh
python3 -B gathering/run_checks_17.py
python3 -B gathering/check_round_17.py
python3 -B gathering/build_gallery.py
python3 -B gathering/check_delivery_17.py
```

Tried: all 160 inherited/new offline commands passed, with 1,268 unittest cases
(one auxiliary-server test skipped). Ten additional trials passed their expected
exits. The new integration's 14 tests pass here and detached. Fresh finalized
ZTO supply/decimals were captured at mainnet block 26196021 and replayed offline;
see `live-check-17.json` and `hash-pinned-round17.json`. Public source:
https://ethereum-rpc.publicnode.com. Provider observations are not state proofs.

Wall: `artifacts/gathering/wall-v17.png`, identical `wall.png`, **1254 × 1254 RGB
PNG**. Record: `dist/gathering/17.json`; preview: **512 × 512 JPEG**, 76,251 bytes.
The installed image editor painted a worn left-facing ochre fish with a charcoal
eye on vacant rock right of central Pepe. Only its new pigment was transferred
onto ancestral stone: 4,566 pixels changed in one small patch, all pixels outside
it unchanged. Full PNG and decoded JPEG inspected; no new hands, words or known
unmet visual requirements. The ancestor's rock, drawings, cracks, light and
framing are retained. Prompt, preservation and inspection are recorded in
[wall-review-17.json](wall-review-17.json). The fish means keeping the catch only
when it belongs within the chosen reach of river.

Gallery: 85 paintings, 84 placeholders, all 169 records; painted newest first by
wall, future slots collapsed. No line folder or line record changed. Required PNG
remains untracked for separate upload. Standard library only, no installation.
Local checks validate structure and observed behavior, not independent trust.
