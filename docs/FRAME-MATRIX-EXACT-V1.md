# FRAME-MATRIX-V1 — exact metatagged pixels, finite frames and reversible play

Status: executable reference model / mathematical software verification. Date: 2026-11-21.

## Source lineage

This is a narrow executable continuation of the original 3d_vectorspace_expansion.md
and quantum_vector_space.py (2024 particle ID, 3D position, momentum, spin,
energy/interaction tags) and the later metatag_v2_behcs.py (2026 content-derived
state address, pair cosign and guarded transitions).

The original scheme distinguishes three ideas:
1. Stable entity: a named particle in a 3D cell world.
2. Changing metadata: location, momentum, energy, spin, L and correlation partners.
3. Frame identity: a frozen state whose next state is deterministically computed.

A state-derived SHA address changes as a particle moves. This implementation
therefore keeps both a stable uid and a state_sha256. Frame SHA256 identifies the
entire frozen state, not an individual particle.

## Finite mathematical specification

Let the pixel lattice be V = (Z/NZ)^3, N >= 3. Each particle is
(uid, xyz, v, energy, spin, L_tag, bond), where:

- xyz in V and v in {-1,0,+1}^3;
- energy is a nonnegative integer carried by this reference update;
- spin in {-1,0,+1};
- L_tag is an integer triple carried unchanged by this reference update;
- bond is empty or the reciprocal uid of a particle with opposite spin.

The pixel map is a second view of the same state:
PIXEL(n, xyz) = sorted stable uids occupying xyz at frame n.
Multiple particles can occupy the same cell. The ordering is canonical.

The deterministic update T does two operations:
A. Simultaneous move: xyz'_i = (xyz_i + v_i) modulo N in each axis.
B. For each destination pixel, sort co-occupants by stable uid and cyclically
   permute their velocity triples by one position. An isolated particle keeps v.
All other metatags remain attached to their stable uid.

This convention uses L-infinity movement <= 1 cell/frame; the chosen metric is
a simulation convention, and the periodic wrap from N-1 to 0 is a one-step
adjacency. It is not a measurement of light speed or tunneling.

### Exact conservation and inversion

Because B only permutes the velocity multiset within each destination cell,
the summed ternary momentum tuple is unchanged. Entity count, summed energy,
summed L_tag and summed spin are unchanged. Reciprocal bonds stay reciprocal.

T is bijective on the validated finite state set. Given the output state,
first invert each destination-cell velocity permutation, then subtract each
restored velocity modulo N. This recovers the entire preceding particle state.
For a complete hash-chain frame, rewind additionally needs the previous
frame's parent commitment from the frozen chain.

Frame bytes are canonical ASCII HBP lines, and frame_hash =
SHA256(canonical frame bytes). Playback validates the parent digest and exact
recomputed next frame, then independently applies the inverse. Hashing verifies
identity; hashing alone does not establish physics, and a digest alone cannot
recover discarded input data.

## Frozen predictions and adversarial acceptance

The frozen prediction file is docs/FRAME-MATRIX-V1-PREDICTION.hbp,
committed at 3daddc2644cf1c15b31b304ff595bdc73caa7135 before the
executable tests were authored at 90b90a27d9c4997319af9ba403745f3200dd965e.

A three-particle fixture predicts:
- n=0: 3 particles, energy 12, momentum (0,1,0), L_tag (0,1,0), spin 0.
- n=1: P1/P2 meet at (2,2,2) and exchange velocities; P3 at (4,0,4).
- n=2: P1 at (1,2,2), P2 at (3,2,2).

The test suite covers canonical byte re-encoding, freeze/play SHA identity,
forward/inverse equality, 729 pair velocity assignments, three-particle
collisions, toroidal adjacency, and deliberate wrong-bond, spin, energy,
velocity, duplicate-ID, altered-frame and altered-hash cases.

## Run it

    python3 -B -m unittest discover -s tests -p test_frame_matrix_exact.py -v
    python3 -B frame_matrix_exact.py > FRAME-MATRIX-RECEIPT.hbp
    sha256sum FRAME-MATRIX-RECEIPT.hbp

No GPU, Node, NumPy, subprocess launch or floating-point arithmetic is needed
for this reference evaluator.

## Relationship to finite Yang-Mills work

The exact-integer conservation checks, adversarial controls, HBP receipts,
canonical frame addresses and replays can serve as engineering patterns for
future finite-lattice simulations. The 3x4 S3 original Wilson theorem, the
continuous SU(2) physical transfer, spectral reconstruction and continuum mass
gap retain their separate mathematical definitions and certificate gates.

The model tested here is a software cell automaton. Physical quantum
entanglement, real particle dynamics and a Yang-Mills spectral gap require
separate experimental and mathematical validation.

## Next acceptance gates

- Prove a relation between any proposed lattice operator and this exact T,
  rather than identifying them by label.
- Introduce explicit collision/interaction energy and physically motivated
  local observables, then retest conservation and reversibility.
- Add a Rust 1.81 production implementation with an independently written
  integer-only reference comparison and a stable frozen receipt.
- Compare multi-resolution particle and pixel projections with exact
  decode/encode invariants; test any proposed quantum interpretation
  independently.
