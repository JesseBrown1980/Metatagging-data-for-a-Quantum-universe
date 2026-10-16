# Asolaria Meta Tagging → Q-PRISM → Constellation → GitRAM

**Scope:** source-bound software computation, not an optical photon-memory measurement or quantum hardware experiment. Preserves the 2024 metatag → 2026 Asolaria lineage.

## Original components reused by contract

- This repository's original metatag/particle addressing, versioned per-particle memory and interaction gate (metatag_v2_behcs.py).
- [Asolaria Universe Simulator combined laws](https://github.com/JesseBrown1980/ASOLARIA-UNIVERSE-SIMULATOR-with-gravity-light-time-space-color-rime-winding-drills/blob/main/books/COMBINED-BOOK-OF-LAWS.md): freeze/source, ternary R³, honest controls, HRM/MTP/Fischer and lighthouse return.
- [Q-PRISM cube absorption](https://github.com/JesseBrown1980/Q-PRISM-human-organoid-neural-stream-as-a-high-dimensional-control/blob/acer/qprism-muscle-sim-2026-07-01/qprism/cube_absorb.py): byte-exact 256 ↔ 1024 bit-packing, Host8 FNV1a64 IDs, Brown-Hilbert 1024-ary selectors. **This adapter implements integer-only representation functions; it does not invoke the separate Talbot–Lau optical apparatus model.**
- [The Colour QR](https://github.com/JesseBrown1980/the-colour-qr/blob/main/README.md): three separately indexed and independently decoded standard QR symbols in red/green/blue planes. The container-generated companion artifact carries the exact source receipt. Seven rainbow velocity-display classes are *not measured seven-band light spectra*.
- [GitRAM doctrine](https://github.com/JesseBrown1980/GitRAM/blob/main/docs/GITRAM-DOCTRINE.md): one unit per isolated cell, independent checkpoint artifacts, all-nine fan-in and no partial seal.
- [Rotating lighthouse Rust 1.81 source](https://github.com/JesseBrown1980/asolaria-rotating-lighthouse-2026-10-09/blob/main/kernel/lighthouse.rs): order-3 ternary digital rotation and five-station hose. The Rust kernel is a separate upstream artifact. **This branch contains a Python data/transport adapter, not a newly compiled Rust lighthouse binary**; Rust 1.81 Clippy gate remains pending.

## Frozen real astronomical input

CDS J/A+A/700/A11/spec.dat (Suárez Mascareño et al., A&A 700 A11, 2025). Exactly 722 measured Proxima Centauri RV records with date, uncertainty and telescope instrument index.

- Source SHA256: 027cff5c10b541608b727abada2af531037223edec3bb9112fcbb45fc333e474.
- Each of 9 GitRAM cells stores a compressed, byte-exact consecutive fraction of this published source. The nine *actual time-sorted observation windows* in the local report are a **separate** grouping.
- The 3×3×3 Merkle leaves within each cell are digital address slots and may be empty; they are not simulated physical particles.

## Local invocation — Python stdlib only

    curl -fL 'https://cdsarc.cds.unistra.fr/ftp/J/A+A/700/A11/spec.dat' -o spec.dat
    echo '027cff5c10b541608b727abada2af531037223edec3bb9112fcbb45fc333e474  spec.dat' | sha256sum -c -
    python3 integrations/constellation_gitram.py --source spec.dat --out output

GitRAM cells individually, then exact fan-in:

    for cell in 0 1 2 3 4 5 6 7 8; do
        python3 integrations/constellation_gitram.py --source spec.dat --out checkpoints --cell "$cell"
    done
    python3 integrations/constellation_gitram.py --source spec.dat --out result --fanin --cells-dir checkpoints

The public PR workflow schedules nine separate standard GitHub-hosted Ubuntu cells, uploads one HBP checkpoint per cell, requires all nine at fan-in, and verifies source SHA-256, source byte parity, 256↔1024 Q-PRISM exactness and ternary R³. Only actual concluded GitHub checks certify the remote run; the local pass is not a substitute.

## Local container baseline — 2026-10-16

| Check | Outcome |
|---|---|
| Published RV rows | 722 / 722, exact SHA |
| Independent GitRAM-style cell processes | 9 / 9 PASS |
| Total digitally addressed leaves | 243 |
| Byte-exact recovered source | PASS |
| Q-PRISM bit-packing 256↔1024 | PASS |
| Three ternary rotations and inverse | PASS |
| Missing, replayed, tampered cells | HELD, HELD, HELD |
| Separate local pytest suite | 7 / 7 PASS |
| Local three-channel Colour QR receipt | 1067 / 1067 bytes decoded, matching SHA |
| Omega | d11121b8143ad25f3e00972a9c28e89b4923b5a8f817477a0aaed56e6b6e9c66 |

## Scientific and release boundaries

Software checks on a powered CPU are real physical computations, but do not independently establish historical photon storage, optical instrument custody, quantum advantage, AI awareness, new astronomical objects or a seven-band physical spectrometer. This implementation uses measured radial velocities and integer software colour classes. Q-PRISM optical apparatus verification, full Rust 1.81/Clippy compilation and original calibrated optical observations are distinct gates.

**Draft PR only. No auto-merge, paid execution, physics-claim promotion, credentials or hardware actuation.** Missing source, wrong SHA, duplicate/missing checkpoint, failed inverse or unexpected Omega must fail closed.
