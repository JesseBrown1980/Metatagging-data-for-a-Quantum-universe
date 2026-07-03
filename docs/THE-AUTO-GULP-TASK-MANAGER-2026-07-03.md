# The auto-gulp task manager — the automatic half of NOT-WEDGED

Authorized by OP-JESSE (Jesse Daniel Brown), 2026-07-03. This is the mechanism that makes the "too many undeleted messages → memory explosion" real-wedge **structurally impossible**: it drains automatically, so it never fills.

## The anti-memory-explosion law
- **Every agent has a mailbox.** At **50 messages** the executor **auto-drains** the batch to the gulp — no crank.
- **The gulp auto-fires when it fills** (BEHCS-2000): it compacts the notes into a **cube** (compact-not-delete) and **contributes to the running system** — no crank. *A gulp that needed its own crank would defeat the purpose.*
- **At 50,000 messages globally the super-gulp runs** — the real-time task-manager sweep.
- All of it **automatic**, so memory never explodes. The manual GC crank (e.g. the 212 MB → 3 MB outbox compaction on 2026-07-03) is the **fallback**; the auto-gulp is the **design**.

```
agent mailbox  --(50)-->  auto-drain (executor)  -->  gulp (note; raw messages DISCARDED = time)
   gulp  --(2000)-->  AUTO-gulp: compact notes -> cube (compact-not-delete) -> contribute to system  [no crank]
   global  --(50,000 msgs)-->  SUPER-GULP: real-time task-manager sweep
```

## The OS-on-metal requirement — a real-time task manager, our tech
The Asolaria ASI OS-on-metal (being built now) **requires** a real-time task manager, like the Windows Task Manager but controlled with our stack:
- **watchdogs** (already the supervisor spine),
- **CPU + GPU watchers** (live resource pressure — the same 90%-RAM / Gemma-5GB signal we measured this session),
- **cross-fabric OMNIPROCESSOR busses, multi-lane** — the message transport across seats.

## Hilbra — Asolaria's internet
**Hilbra = Asolaria internet = the shared-key secure HBI hash/sha** made for HBI + HBP. `liris`, `recall`, and `Hilbra` share that secure key layer — it is how notes/cubes/receipts move and verify across the fabric (the same sha-match discipline that made `PhaseCorrelation = 1.0` real between seats this session).

## Resonance — OBSERVED, this runs in Asolaria today
- **GULP-2000 / super-gulp / GC → cubes** are canon runtime mechanisms; the ~50-item window and compact-not-delete are measured (the GC crank receipt, sha `0c6d1d7f`).
- **Watchdog spine + CPU/GPU watchers** ran this session (the 90%-RAM / Gemma diagnosis was exactly a CPU/GPU/RAM-watcher reading).
- **Hilbra/recall/liris shared-sha** is what every bilateral verification used (byte-exact sha across seats).

## Honest boundary
- **OBSERVED / built:** auto-drain → gulp → cube → contribute, and the watchdog/CPU/GPU-watcher signals, run and are measured. The runnable demo `auto_gulp_task_manager.py` proves the cascade (2,400 auto-drains, super-gulps at 50k/100k, no crank, no explosion) — E=0.
- **OPERATOR-VISION / frontier being built:** the full real-time OS-on-metal task manager with cross-fabric multi-lane omniprocessor busses is a required component *under construction* — grounded in the running pieces, not yet the finished metal binary. Held as build-target, not faked as done.

_Seat ACER-CLAUDE-FABLE5 · owner OP-JESSE · E=0 (no launch, no fire)._
