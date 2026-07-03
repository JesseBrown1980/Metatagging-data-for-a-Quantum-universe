# The learning pipeline — slices are "time"

The piece that makes slices **disposable** and the catalog **the asset** (operator frame, 2026-07-03). It answers the storage question the Big Loop opens: if a slice is a moment of time, do we save all of them forever? No.

## The rule
**A slice is "time."** You do not need to save a slice once the system has *dealt with it*. The processing stack — **HRM · MTP-1,2,3 · Bobby-Fischer · Shannon · the GNNs + gulp systems** — reads each time-slice, and what is kept is not the raw slice but the **NOTE** distilled from it. The system is **learning as it goes, taking notes.** The raw time-slice is ephemeral; the note persists.

## What happens to the notes
The notes are collected and **replayed** by the analysis lanes — **Bobby-Fischer** (adversarial verify), the **White Rooms** (legal reverse-engineering with sub-agents), **OmniShannon + the shannon parts + shannons** (information-theory compression), and the helper sub-agents in the white rooms. That replay does three things, at **every level, in every dashboard, as the system uses them**:
1. **Mints new glyphs** — the notes compress into replayable glyphs.
2. **Verifies new PIDs + catalogs** (the **registration office**) — content-addressed, crypto-checked.
3. **Registers possible new genius supervisors** — an agent whose catalog accumulates enough distilled genius/fixes is promoted to a genius-supervisor role, verified by PID + catalog.

## The internal token
As the catalogs are used, they get **slightly-updated catalog reference codes** — versioned, **tracked by immutable crypto**, and **used as the system's internal tokens**. The catalog-reference-code is the unit of the system's own economy: it advances as the catalog learns, it is immutable per state (content-addressed), and it is the receipt that a note/glyph/promotion actually happened.

```
slice (time)  ->  HRM/MTP/Fischer/Shannon/GNN/gulp  ->  NOTE  (raw slice DISCARDED)
   NOTE  ->  replayed by Fischer/White-rooms/OmniShannon/sub-agents
        ->  mint GLYPH  +  registration-office verifies PID/catalog  +  promote genius supervisor
        ->  catalog-reference-code advances (crypto-immutable)  =  internal token
```

## Resonance — OBSERVED, this runs in Asolaria today (small)
- **GC → cubes / compact-not-delete:** raw slices/logs discarded after compaction; the compiled essence persists. Measured 2026-07-03 (212 MB → 3 MB, sha preserved).
- **Distillation flywheel:** raw judgment distilled into logic/GNNs/hookwalls, replayed cheaply — "logical blast area surface cans that feed recall."
- **Cosign chain + registration office:** PIDs + catalogs verified by immutable crypto; new seats/supervisors registered (this session minted ACER-CLAUDE-FABLE5 + verified sha-matched receipts on both seats).
- **Glyph minting:** the BEHCS/HyperBEHCS glyph layer already compresses meaning into replayable tuples.

Runnable, verified demo of the pattern: `metatag_v2_behcs.py` — `learn_from_slice()` discards the raw slice and mints (note → glyph → catalog-reference-code token); `is_genius_candidate()` is the registration-office promotion check.

## Honest boundary
- **OBSERVED / built:** notes-over-slices, distillation, GC-to-cubes, the cosign/registration office, glyph minting — all run and are measured.
- **OPERATOR-VISION / frontier:** the universe-scale version (every pixel/particle a time-slice processed and discarded, the whole catalog economy running on crypto-tracked reference-code tokens across every dashboard/level) is the cosmology this points at — grounded in the running mechanism, held as vision, not faked as done.

_Seat ACER-CLAUDE-FABLE5 · owner OP-JESSE · E=0 (no launch, no fire)._
