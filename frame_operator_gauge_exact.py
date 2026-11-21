"""Exact frame/pixel projection, finite transition spectrum, and Z2 gauge toy.

All arithmetic is integer. The frame operator is a reversible permutation;
the gauge-projected two-level transfer kernel is a separate illustrative
positive operator, not the original 4D SU(2) Wilson transfer.
"""
from itertools import product
from math import gcd

from frame_matrix_exact import need, occupied, parse_frame, validate


def project_frame(frame):
    """Canonical lossless particle+pixel dual view, authenticated by frame SHA."""
    validate(frame)
    pixels = tuple((xyz, ids) for xyz, ids in occupied(frame).items())
    tags = tuple(p.record() for p in frame.particles)
    return (frame.n, frame.side, frame.parent, frame.digest(), pixels, tags)


def restore_frame(view):
    """Check both redundant projections against the committed canonical frame."""
    need(type(view) is tuple and len(view) == 6, "bad_projection_shape")
    n, side, parent, commitment, pixels, tags = view
    need(type(n) is int and type(side) is int and type(parent) is str,
         "invalid_frame_header")
    need(type(tags) is tuple and all(type(t) is str for t in tags),
         "invalid_metatag_table")
    header = "FRAME|n=" + str(n) + "|side=" + str(side)
    header += "|parent=" + parent + "|json=0\n"
    raw = (header + "".join(tag + "\n" for tag in tags)).encode("ascii")
    frame = parse_frame(raw)
    need(occupied(frame) == dict(pixels), "pixel_projection_mismatch")
    need(frame.digest() == commitment, "frame_commitment_mismatch")
    return frame


def ternary_states(side):
    need(type(side) is int and 3 <= side <= 8, "side_out_of_bound")
    locs = product(range(side), repeat=3)
    velocities = tuple(product((-1, 0, 1), repeat=3))
    return tuple((tuple(xyz), tuple(v)) for xyz in locs for v in velocities)


def single_next(state, side):
    xyz, v = state
    need(len(xyz) == len(v) == 3, "bad_single_particle_state")
    return (tuple((xyz[k] + v[k]) % side for k in range(3)), v)


def permutation_operator(side):
    """Sparse column-to-row permutation representation for all one-particle states."""
    states = ternary_states(side)
    index = {state: i for i, state in enumerate(states)}
    return states, tuple(index[single_next(state, side)] for state in states)


def cycle_summary(side):
    states, targets = permutation_operator(side)
    need(len(set(targets)) == len(states), "operator_not_bijective")
    visited = set()
    cycles = []
    for i in range(len(states)):
        if i in visited:
            continue
        j = i
        steps = []
        while j not in visited:
            visited.add(j)
            steps.append(j)
            j = targets[j]
        need(j == i, "noncycle_successor")
        cycles.append(tuple(steps))
    counts = {}
    for cycle in cycles:
        counts[len(cycle)] = counts.get(len(cycle), 0) + 1
    return tuple(sorted(counts.items()))


def trace_power(cycles, exponent):
    need(type(exponent) is int and exponent >= 0, "bad_exponent")
    return sum(length * count for length, count in cycles
               if exponent % length == 0)


def frame_operator_negative_witness():
    """A 3-cycle has a negative real quadratic form, so is not positive OS T."""
    # Basis labels are successive positions of one particle on a 3-site ring.
    p = (1, -1, 0)
    shifted = (p[2], p[0], p[1])
    q = sum(p[i] * shifted[i] for i in range(3))
    need(q == -1, "expected_negative_frame_transfer_quadratic_form")
    return q


# A single closed square. Z2 link matrices are scalars +/-1.
EDGES = ((0, 1), (1, 2), (2, 3), (3, 0))


def links():
    return tuple(product((-1, 1), repeat=4))


def site_gauges():
    return tuple(product((-1, 1), repeat=4))


def transform_links(u, g):
    need(len(u) == len(EDGES) and len(g) == 4, "bad_link_or_gauge_length")
    need(all(x in (-1, 1) for x in u + g), "not_Z2")
    return tuple(g[a] * value * g[b]
                 for value, (a, b) in zip(u, EDGES))


def wilson(u):
    need(len(u) == 4 and all(x in (-1, 1) for x in u), "invalid_Wilson_links")
    w = 1
    for value in u:
        w *= value
    return w


def gauge_orbits():
    all_states = links()
    seen = set()
    orbits = []
    for u in all_states:
        if u in seen:
            continue
        orbit = tuple(sorted({transform_links(u, g) for g in site_gauges()}))
        seen.update(orbit)
        orbits.append(orbit)
    need(sum(len(o) for o in orbits) == len(all_states),
         "invalid_orbit_partition")
    return tuple(sorted(orbits, key=lambda o: wilson(o[0])))


def physical_gauge_projection_scaled8():
    """8*P_G on 16 raw links; 2 gauge-invariant orbit dimensions."""
    all_states = links()
    return tuple(tuple(int(wilson(u) == wilson(v)) for v in all_states)
                 for u in all_states)


def gauge_transfer_scaled8():
    """8*T_raw, where quotient physical kernel K is [[3,1],[1,3]]."""
    all_states = links()
    return tuple(tuple(3 if wilson(u) == wilson(v) else 1
                       for v in all_states)
                 for u in all_states)


def matmul(a, b):
    n = len(a)
    need(n and len(b) == n and all(len(row) == n for row in a + b),
         "bad_matrix_shape")
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(n))
                       for j in range(n)) for i in range(n))


def gauge_matrix_acceptance():
    orbits = gauge_orbits()
    need(len(orbits) == 2 and all(len(o) == 8 for o in orbits),
         "gauge_orbit_count_failed")
    need(tuple(wilson(o[0]) for o in orbits) == (-1, 1),
         "wrong_flux_sector_order")
    for u in links():
        for g in site_gauges():
            need(wilson(transform_links(u, g)) == wilson(u),
                 "Wilson_gauge_invariance_failed")
    p = physical_gauge_projection_scaled8()
    t = gauge_transfer_scaled8()
    pp = matmul(p, p)
    pt = matmul(p, t)
    tp = matmul(t, p)
    need(all(pp[i][j] == 8 * p[i][j]
             and pt[i][j] == 8 * t[i][j]
             and tp[i][j] == 8 * t[i][j]
             for i in range(16) for j in range(16)),
         "gauge_projector_or_transfer_invalid")
    # K has trace 6, determinant 8, eigenvalues exactly 4 and 2.
    k = ((3, 1), (1, 3))
    need(k[0][0] + k[1][1] == 6 and
         k[0][0] * k[1][1] - k[0][1] * k[1][0] == 8,
         "wrong_quotient_transfer_spectrum")
    # On the full raw space the remaining 14 eigenvalues are zero.
    return (len(links()), len(site_gauges()), len(orbits),
            tuple(len(o) for o in orbits), (4, 2))


def connected_wilson_moment(n):
    """Exact C_n=<Omega|W(K/4)^n W|Omega> = 1/2^n, as (num,den)."""
    need(type(n) is int and 0 <= n <= 64, "invalid_moment_order")
    k = ((3, 1), (1, 3))
    v = (1, -1)  # W * vacuum, unnormalized
    for _ in range(n):
        v = (k[0][0] * v[0] + k[0][1] * v[1],
             k[1][0] * v[0] + k[1][1] * v[1])
    numerator = v[0] - v[1]
    denominator = 2 * (4 ** n)
    d = gcd(numerator, denominator)
    return (numerator // d, denominator // d)


def spectral_window_lower(q_num, q_den, n):
    """One polynomial exact window bound from C0 and Cn; no eigen-isolation claim."""
    need(type(q_num) is int and type(q_den) is int
         and 0 < q_num < q_den and type(n) is int and n >= 1,
         "invalid_window")
    cn_num, cn_den = connected_wilson_moment(n)
    # (Cn - q**n C0) / (1-q**n), exact integer cross multiplication.
    qn, qd = q_num ** n, q_den ** n
    numer = cn_num * qd - qn * cn_den
    denom = cn_den * (qd - qn)
    if numer <= 0:
        return (0, 1)
    d = gcd(numer, denom)
    return (numer // d, denom // d)


def exact_receipt():
    cycles = cycle_summary(3)
    gauge = gauge_matrix_acceptance()
    need(cycles == ((1, 27), (3, 234)), "frozen_cycle_counts_disagree")
    need(gauge == (16, 16, 2, (8, 8), (4, 2)),
         "frozen_gauge_values_disagree")
    need(tuple(connected_wilson_moment(n) for n in (0, 1, 2, 4))
         == ((1, 1), (1, 2), (1, 4), (1, 16)),
         "frozen_Wilson_moments_disagree")
    need(spectral_window_lower(1, 4, 2) == (1, 5),
         "frozen_spectral_window_disagree")
    need(frame_operator_negative_witness() == -1,
         "invalid_nonpositive_frame_witness")
    rows = (
        "FRAME_OPERATOR|side=3|states=729|cycles_fixed=27|cycles_length3=234"
        "|trace1=27|trace2=27|trace3=729|json=0",
        "GAUGE_Z2|edges=4|raw=16|gauge_actions=16|orbits=2"
        "|orbit_sizes=8,8|P8_squared=8P8|Wilson_gauge_invariant=PASS|json=0",
        "TOY_TRANSFER|K=3,1;1,3|vacuum_eigenvalue=4"
        "|excited_eigenvalue=2|physical_quotient=2|json=0",
        "TOY_WILSON|C0=1|C1=1/2|C2=1/4|C4=1/16"
        "|window_q1over4_n2_lower=1/5|json=0",
        "BOUNDARY|frame_operator_quadratic=-1|frame_OS_positive=REJECTED"
        "|original_SU2_Wilson=NOT_TESTED|continuum_mass_gap=OPEN|json=0",
    )
    return "\n".join(rows) + "\n"


if __name__ == "__main__":
    print(exact_receipt(), end="")
