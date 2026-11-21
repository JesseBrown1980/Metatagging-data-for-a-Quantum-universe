"""Independent exact source, operator, gauge and adversarial acceptance checks."""
import unittest

from frame_matrix_exact import chain, fixture
from frame_operator_gauge_exact import (
    connected_wilson_moment, cycle_summary, exact_receipt,
    frame_operator_negative_witness, gauge_matrix_acceptance,
    gauge_orbits, gauge_transfer_scaled8, links, matmul,
    permutation_operator, physical_gauge_projection_scaled8,
    project_frame, restore_frame, single_next, site_gauges,
    spectral_window_lower, trace_power, transform_links, wilson,
)


class FrameOperatorGaugeTests(unittest.TestCase):
    def test_frame_pixel_lossless_every_frame(self):
        for f in chain(fixture(), 27):
            view = project_frame(f)
            restored = restore_frame(view)
            self.assertEqual(restored, f)
            self.assertEqual(restored.bytes(), f.bytes())
            self.assertEqual(restored.digest(), view[3])
            self.assertEqual(len(view[5]), len(f.particles))

    def test_pixel_omission_rejected(self):
        v = project_frame(fixture())
        bad = v[:4] + (v[4][1:],) + (v[5],)
        with self.assertRaisesRegex(ValueError, "pixel_projection_mismatch"):
            restore_frame(bad)

    def test_pixel_relabel_rejected(self):
        v = project_frame(fixture())
        cells = list(v[4])
        xyz, ids = cells[0]
        cells[0] = (xyz, ("FORGED",))
        with self.assertRaisesRegex(ValueError, "pixel_projection_mismatch"):
            restore_frame(v[:4] + (tuple(cells), v[5]))

    def test_tampered_metatag_rejected_by_digest(self):
        v = project_frame(fixture())
        tags = list(v[5])
        tags[0] = tags[0].replace("energy=3", "energy=9")
        with self.assertRaisesRegex(ValueError, "frame_commitment_mismatch"):
            restore_frame(v[:5] + (tuple(tags),))

    def test_orphan_metatag_rejected(self):
        v = project_frame(fixture())
        with self.assertRaisesRegex(ValueError, "pixel_projection_mismatch"):
            restore_frame(v[:5] + (v[5][:-1],))

    def test_exact_729_state_operator_and_charpoly(self):
        states, perm = permutation_operator(3)
        self.assertEqual(len(states), 729)
        self.assertEqual(len(set(perm)), 729)
        self.assertEqual(cycle_summary(3), ((1, 27), (3, 234)))
        self.assertEqual(sum(k * m for k, m in cycle_summary(3)), 729)
        # Characteristic polynomial of a permutation with 27 fixed points,
        # and 234 three-cycles: (x-1)^27 (x^3-1)^234.
        self.assertEqual(sum(m for _, m in cycle_summary(3)), 261)
        self.assertEqual((trace_power(cycle_summary(3), 1),
                          trace_power(cycle_summary(3), 2),
                          trace_power(cycle_summary(3), 3)),
                         (27, 27, 729))

    def test_independent_direct_frame_next(self):
        states, perm = permutation_operator(3)
        for i, (xyz, v) in enumerate(states):
            expected = tuple((xyz[a] + v[a]) % 3 for a in range(3))
            self.assertEqual(states[perm[i]], (expected, v))
            self.assertEqual(single_next((xyz, v), 3), (expected, v))
            # Every ternary velocity returns after three side-3 steps.
            self.assertEqual(perm[perm[perm[i]]], i)

    def test_side_five_cycle_prediction_independent(self):
        cycles = cycle_summary(5)
        self.assertEqual(cycles, ((1, 125), (5, 650)))
        self.assertEqual(trace_power(cycles, 1), 125)
        self.assertEqual(trace_power(cycles, 5), 3375)

    def test_frame_unitary_not_positive(self):
        self.assertEqual(frame_operator_negative_witness(), -1)
        # Three-cycle matrix is not symmetric: position 0 maps to 1, not 0.
        states, perm = permutation_operator(3)
        i = states.index(((0, 0, 0), (1, 0, 0)))
        j = states.index(((1, 0, 0), (1, 0, 0)))
        self.assertEqual(perm[i], j)
        self.assertNotEqual(perm[j], i)

    def test_z2_gauge_orbits_and_wilson(self):
        self.assertEqual(gauge_matrix_acceptance(),
                         (16, 16, 2, (8, 8), (4, 2)))
        seen = set()
        for orbit in gauge_orbits():
            self.assertEqual(len(orbit), 8)
            self.assertEqual(len({wilson(u) for u in orbit}), 1)
            seen.update(orbit)
        self.assertEqual(seen, set(links()))
        for u in links():
            for g in site_gauges():
                self.assertEqual(wilson(transform_links(u, g)), wilson(u))
        self.assertEqual(wilson((1, 1, 1, 1)), 1)
        self.assertEqual(wilson((-1, 1, 1, 1)), -1)

    def test_projector_and_quotient_kernel_integer(self):
        p = physical_gauge_projection_scaled8()
        t = gauge_transfer_scaled8()
        self.assertEqual(matmul(p, p),
                         tuple(tuple(8 * v for v in row) for row in p))
        self.assertEqual(matmul(p, t),
                         tuple(tuple(8 * v for v in row) for row in t))
        self.assertEqual(matmul(t, p),
                         tuple(tuple(8 * v for v in row) for row in t))
        self.assertEqual([sum(row) for row in p], [8] * 16)
        self.assertEqual([sum(row) for row in t], [32] * 16)
        # T_raw=T8/8, row sum 4, vacuum eigenvalue 4.
        # Its physical complement has eigenvalue 2; 14 null gauge modes.

    def test_raw_kernel_gauge_covariance(self):
        states = links()
        index = {u: i for i, u in enumerate(states)}
        t = gauge_transfer_scaled8()
        for u in states:
            for v in states:
                a = t[index[u]][index[v]]
                for g in site_gauges():
                    self.assertEqual(t[index[transform_links(u, g)]][index[v]], a)
                    self.assertEqual(t[index[u]][index[transform_links(v, g)]], a)

    def test_exact_wilson_moments(self):
        self.assertEqual(connected_wilson_moment(0), (1, 1))
        self.assertEqual(connected_wilson_moment(1), (1, 2))
        self.assertEqual(connected_wilson_moment(2), (1, 4))
        self.assertEqual(connected_wilson_moment(4), (1, 16))
        for n in range(15):
            a, b = connected_wilson_moment(n)
            self.assertEqual((a, b), (1, 2 ** n))
            self.assertGreater(a, 0)

    def test_spectral_window_and_falsifier(self):
        self.assertEqual(spectral_window_lower(1, 4, 2), (1, 5))
        self.assertEqual(spectral_window_lower(3, 4, 2), (0, 1))
        # The lower window bound is less than the true unit spectral weight.
        self.assertLess(1, 5)
        with self.assertRaisesRegex(ValueError, "invalid_window"):
            spectral_window_lower(1, 1, 2)

    def test_bad_gauge_and_state_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_Wilson_links"):
            wilson((2, 1, 1, 1))
        with self.assertRaisesRegex(ValueError, "not_Z2"):
            transform_links((1, 1, 1, 1), (1, 1, 2, 1))
        with self.assertRaisesRegex(ValueError, "bad_link_or_gauge_length"):
            transform_links((1, 1, 1), (1, 1, 1, 1))

    def test_bad_exponents_rejected(self):
        with self.assertRaisesRegex(ValueError, "bad_exponent"):
            trace_power(cycle_summary(3), -1)
        with self.assertRaisesRegex(ValueError, "invalid_moment_order"):
            connected_wilson_moment(-1)

    def test_receipt_and_claim_boundary(self):
        receipt = exact_receipt()
        self.assertIn("cycles_length3=234|trace1=27|trace2=27|trace3=729",
                      receipt)
        self.assertIn("P8_squared=8P8|Wilson_gauge_invariant=PASS", receipt)
        self.assertIn("C0=1|C1=1/2|C2=1/4|C4=1/16", receipt)
        self.assertIn("original_SU2_Wilson=NOT_TESTED|continuum_mass_gap=OPEN",
                      receipt)
        self.assertEqual(receipt, exact_receipt())


if __name__ == "__main__":
    unittest.main()
