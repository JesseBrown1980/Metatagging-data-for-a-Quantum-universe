# Frame–Operator–Gauge V1 — exact mathematical acceptance

Date: 2026-11-21. Status: mathematical software verification, with physical interpretation deferred.

## Source and projections

This continues the original 2024 3D particle-metatag architecture and the 2026 exact frame_matrix work. The frame stores stable particle identities and changing position, momentum, energy, spin, and correlation tags. The pixel view stores which stable particle IDs occupy each cell. Reconstructing an entire frame requires both its canonical metatag table and pixel table, checked against the complete frame SHA-256 commitment. A pixel table alone is insufficient.

## 729-state reversible frame operator

For one particle, let position x belong to the periodic three-dimensional grid (Z/3Z)^3 and ternary velocity v belong to {-1,0,+1}^3. The frame step is T(x,v) = (x+v mod 3,v).

There are 729 states. Each of the 27 zero-velocity states is fixed. For each of the other 26 velocities, the 27 positions divide into nine length-three cycles, yielding 234 three-cycles. Thus the characteristic polynomial is

    det(z I - T) = (z-1)^27 * (z^3-1)^234

and traces are Tr(T)=27, Tr(T^2)=27, Tr(T^3)=729. Every eigenvalue has modulus 1. On any length-three orbit, the vector (1,-1,0) has real quadratic form -1 under T. Consequently, this reversible software frame step is not a positive self-adjoint Osterwalder-Seiler physical transfer operator. Tensoring it directly with a positive gauge transfer does not automatically repair that boundary.

## Exact Z2 gauge square

A single oriented square has four links in Z2={-1,+1} and four vertex gauge transformations. All 16 link assignments fall into two gauge orbits of eight assignments each, classified by the Wilson-loop product W=U01*U12*U23*U30.

In raw-link coordinates the 8-scaled gauge projector P8 has value 1 for two link assignments in the same orbit and 0 otherwise. P8^2 = 8*P8. Every one of the 16 vertex gauge transformations preserves W.

For a positive illustrative quotient transfer, choose the two-state matrix

    K = [[3,1],[1,3]]

with flux basis (-1,+1). Lift it to 16 raw assignments as T_raw(U,V) = K[W(U),W(V)] / 8. The scaled raw matrix T8=8*T_raw satisfies P8*T8 = T8*P8 = 8*T8. The physical quotient eigenvalues are 4 and 2. Fourteen non-gauge-invariant raw directions have zero eigenvalue.

With R=K/4, the constant normalized vacuum and diagonal Wilson W give connected moments

    C_n = <vacuum, W R^n W vacuum> = 1/2^n.

Therefore C0=1, C1=1/2, C2=1/4, C4=1/16. At n=2 and q=1/4, the exact spectral-window polynomial certifies low-energy Wilson spectral weight at least 1/5; the true weight in this two-state example is 1.

This K is a chosen mathematical example, rather than the Wilson transfer of the original 4D continuous SU2 theory. Its positive fixed-size spectrum is not the Clay mass-gap certificate.

## Frozen predictions and reproducibility

Prediction commit 47e70e0f52273b108e44321bb7e4b8a074fc20fd preceded the executable operator implementation and test files. Tests compare pixel and tag reconstructions, independent cycle enumeration, exact positive-kernel identities, exhaustive gauge transformations, exact moments and spectral windows, and tampered metadata.

Commands:

    python3 -B -m unittest discover -s tests -p test_frame_operator_gauge_exact.py -v
    python3 -B frame_operator_gauge_exact.py

## Next mathematical gates

1. Derive a gauge transfer from a stated lattice action or Hamiltonian, including normalization, rather than choosing K.
2. Extend the gauge-algebra and spectral checks to the original continuous SU2 Wilson transfer and a physical Gauss-law projector, with certified character tails.
3. Calculate physically normalized Wilson moments and apply spectral-window inequalities.
4. Seek a separate physical-size and volume-uniform full-spectrum bound on the weak-coupling continuum trajectory.

The exact finite S3 Wilson certificates and 4D continuous-SU2 obligations remain separately scoped.
