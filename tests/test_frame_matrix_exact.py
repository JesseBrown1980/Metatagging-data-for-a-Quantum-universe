"""Independent acceptance tests for exact particle-to-pixel frame model."""
import itertools
import unittest
from dataclasses import replace

from frame_matrix_exact import (
    Frame, Particle, chain, fixture, genesis, hbp_receipt, occupied,
    parse_frame, rewind, step, totals, validate, verify_replay,
)


class FrameMatrixTests(unittest.TestCase):
    def test_frozen_genesis_predictions(self):
        f = fixture()
        self.assertEqual(totals(f), (3, 12, (0, 1, 0), (0, 1, 0), 0))
        g = step(f)
        self.assertEqual(occupied(g)[(2, 2, 2)], ("P1", "P2"))
        self.assertEqual(occupied(g)[(4, 0, 4)], ("P3",))
        d = {p.uid: p for p in g.particles}
        self.assertEqual(d["P1"].v, (-1, 0, 0))
        self.assertEqual(d["P2"].v, (1, 0, 0))
        h = step(g)
        d2 = {p.uid: p for p in h.particles}
        self.assertEqual(d2["P1"].xyz, (1, 2, 2))
        self.assertEqual(d2["P2"].xyz, (3, 2, 2))

    def test_exact_forward_backward_and_canonical_decode(self):
        frames = chain(fixture(), 30)
        self.assertTrue(verify_replay(frames))
        for before, after in zip(frames, frames[1:]):
            self.assertEqual(rewind(after, before.parent), before)
            self.assertEqual(parse_frame(after.bytes()), after)
            self.assertEqual(totals(before), totals(after))

    def test_stable_identity_and_changed_state_address(self):
        a, b = chain(fixture(), 1)
        self.assertEqual([p.uid for p in a.particles],
                         [p.uid for p in b.particles])
        hashes_a = {p.uid: p.state_sha256() for p in a.particles}
        hashes_b = {p.uid: p.state_sha256() for p in b.particles}
        self.assertNotEqual(hashes_a["P1"], hashes_b["P1"])
        self.assertNotEqual(a.digest(), b.digest())
        self.assertEqual(b.parent, a.digest())

    def test_deterministic_byte_identity(self):
        frames_a = chain(fixture(), 6)
        frames_b = chain(fixture(), 6)
        self.assertEqual(hbp_receipt(frames_a), hbp_receipt(frames_b))
        self.assertTrue(hbp_receipt(frames_a).endswith(
            b"|physical_quantum_claim=NOT_TESTED|json=0\n"))
        self.assertIn(b"PIXEL|n=1|xyz=2,2,2|uids=P1,P2|json=0",
                      hbp_receipt(frames_a))

    def test_three_particle_collision_is_permutation(self):
        f = genesis(5, (
            Particle("A", (0, 1, 1), (1, 0, 0), 2, 0, (0, 0, 1)),
            Particle("B", (2, 1, 1), (-1, 0, 0), 2, 0, (0, 0, 1)),
            Particle("C", (1, 0, 1), (0, 1, 0), 2, 0, (0, 0, 1)),
        ))
        after = step(f)
        d = {p.uid: p.v for p in after.particles}
        self.assertEqual(d, {"A": (0, 1, 0), "B": (1, 0, 0),
                             "C": (-1, 0, 0)})
        self.assertEqual(rewind(after, "GENESIS"), f)

    def test_periodic_wrapping_one_step(self):
        f = genesis(5, (Particle("A", (4, 0, 0), (1, 0, 0), 0, 0, (0, 0, 0)),))
        after = step(f)
        self.assertEqual(after.particles[0].xyz, (0, 0, 0))
        self.assertEqual(rewind(after, "GENESIS"), f)

    def test_exhaustive_ternary_two_particle_inverse(self):
        velocities = tuple(itertools.product((-1, 0, 1), repeat=3))
        for u in velocities:
            for v in velocities:
                f = genesis(5, (
                    Particle("A", (1, 1, 1), u, 2, 0, (0, 1, 0)),
                    Particle("B", (3, 3, 3), v, 3, 0, (0, 0, 1)),
                ))
                next_frame = step(f)
                self.assertEqual(totals(f), totals(next_frame))
                self.assertEqual(rewind(next_frame, "GENESIS"), f)

    def test_bad_bond_rejected(self):
        f = genesis(5, (
            Particle("A", (0, 0, 0), (0, 0, 0), 2, 1, (0, 0, 0), "B"),
            Particle("B", (1, 0, 0), (0, 0, 0), 2, -1, (0, 0, 0)),
        ))
        with self.assertRaisesRegex(ValueError, "bond_not_reciprocal"):
            validate(f)

    def test_bad_spin_relation_rejected(self):
        f = genesis(5, (
            Particle("A", (0, 0, 0), (0, 0, 0), 2, 1, (0, 0, 0), "B"),
            Particle("B", (1, 0, 0), (0, 0, 0), 2, 1, (0, 0, 0), "A"),
        ))
        with self.assertRaisesRegex(ValueError, "bond_spin_mismatch"):
            validate(f)

    def test_duplicate_stable_identity_rejected(self):
        p = Particle("A", (0, 0, 0), (0, 0, 0), 1, 0, (0, 0, 0))
        f = genesis(5, (p, p))
        with self.assertRaisesRegex(ValueError, "duplicate_or_unsorted_ids"):
            validate(f)

    def test_bad_ternary_velocity_rejected(self):
        p = Particle("A", (0, 0, 0), (2, 0, 0), 1, 0, (0, 0, 0))
        with self.assertRaisesRegex(ValueError, "velocity_not_ternary"):
            validate(genesis(5, (p,)))

    def test_negative_energy_rejected(self):
        p = Particle("A", (0, 0, 0), (0, 0, 0), -1, 0, (0, 0, 0))
        with self.assertRaisesRegex(ValueError, "invalid_energy"):
            validate(genesis(5, (p,)))

    def test_tampered_frame_rejected(self):
        before = fixture()
        after = step(before)
        bad_p = replace(after.particles[0], energy=after.particles[0].energy + 1)
        bad = replace(after, particles=(bad_p,) + after.particles[1:])
        with self.assertRaisesRegex(ValueError, "frame_replay_mismatch"):
            verify_replay((before, bad))
        with self.assertRaisesRegex(ValueError, "rewind_parent_hash_mismatch"):
            rewind(bad, before.parent)

    def test_noncanonical_bytes_rejected(self):
        data = fixture().bytes()
        with self.assertRaisesRegex(ValueError, "noncanonical_encoding"):
            parse_frame(data.replace(b"n=0", b"n=00", 1))
        lines = data.decode("ascii").splitlines()
        reordered = (lines[0] + "\n" + "\n".join(reversed(lines[1:])) + "\n").encode()
        with self.assertRaises(ValueError):
            parse_frame(reordered)
        with self.assertRaises(ValueError):
            parse_frame(data + b"\n")

    def test_invalid_parent_commit_rejected(self):
        after = step(fixture())
        with self.assertRaisesRegex(ValueError, "invalid_parent_hash"):
            validate(replace(after, parent="not_a_sha"))


if __name__ == "__main__":
    unittest.main()
