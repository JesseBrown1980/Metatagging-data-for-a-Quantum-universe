"""Exact, finite frame-by-frame pixel/metatag reference model (stdlib only).

This is a deterministic software experiment. 'Bond' is a reciprocal metadata
link, not a demonstration of physical quantum entanglement. Velocity is ternary
and cell distance is in the L-infinity grid metric. Integers are exact.
"""
from dataclasses import dataclass, replace
from hashlib import sha256
import re


_UID = re.compile(r"[A-Za-z0-9_-]+")
_HEX = re.compile(r"[0-9a-f]{64}")


def need(ok, label):
    if not ok:
        raise ValueError(label)


@dataclass(frozen=True)
class Particle:
    uid: str                    # Stable identity across frames
    xyz: tuple                  # Integer location in finite cubic pixel grid
    v: tuple                    # Ternary momentum/motion tag, -1/0/+1 per axis
    energy: int                 # Conserved integer metadata in this reference rule
    spin: int                   # -1/0/+1 metadata
    L: tuple                    # Conserved intrinsic angular tag (not orbital r x p)
    bond: str = ""              # Reciprocal stable-id metadata pair

    def record(self):
        fields = (
            "PARTICLE", "uid=" + self.uid,
            "xyz=" + triple(self.xyz), "v=" + triple(self.v),
            "energy=" + str(self.energy), "spin=" + str(self.spin),
            "L=" + triple(self.L), "bond=" + (self.bond or "_"), "json=0",
        )
        return "|".join(fields)

    def state_sha256(self):
        return sha256((self.record() + "\n").encode("ascii")).hexdigest()


@dataclass(frozen=True)
class Frame:
    n: int
    side: int
    parent: str
    particles: tuple

    def bytes(self):
        validate(self)
        head = "FRAME|n=" + str(self.n) + "|side=" + str(self.side)
        head += "|parent=" + self.parent + "|json=0\n"
        return (head + "".join(p.record() + "\n" for p in self.particles)).encode("ascii")

    def digest(self):
        return sha256(self.bytes()).hexdigest()


def triple(values):
    return ",".join(str(x) for x in values)


def validate(frame):
    need(type(frame.n) is int and frame.n >= 0, "invalid_frame_number")
    need(type(frame.side) is int and frame.side >= 3, "invalid_grid_side")
    need(
        (frame.n == 0 and frame.parent == "GENESIS")
        or (frame.n > 0 and bool(_HEX.fullmatch(frame.parent))),
        "invalid_parent_hash",
    )
    need(isinstance(frame.particles, tuple), "particles_must_be_tuple")
    ids = [p.uid for p in frame.particles]
    need(ids == sorted(ids) and len(ids) == len(set(ids)), "duplicate_or_unsorted_ids")
    by_id = {}
    for p in frame.particles:
        need(isinstance(p, Particle), "invalid_particle_type")
        need(isinstance(p.uid, str) and bool(_UID.fullmatch(p.uid)), "invalid_uid")
        need(isinstance(p.xyz, tuple) and len(p.xyz) == 3, "invalid_position")
        need(all(type(x) is int and 0 <= x < frame.side for x in p.xyz), "outside_grid")
        need(isinstance(p.v, tuple) and len(p.v) == 3, "invalid_velocity")
        need(all(type(x) is int and x in (-1, 0, 1) for x in p.v), "velocity_not_ternary")
        need(type(p.energy) is int and p.energy >= 0, "invalid_energy")
        need(type(p.spin) is int and p.spin in (-1, 0, 1), "invalid_spin")
        need(isinstance(p.L, tuple) and len(p.L) == 3, "invalid_L")
        need(all(type(x) is int for x in p.L), "invalid_L_tag")
        need(p.bond == "" or (bool(_UID.fullmatch(p.bond)) and p.bond != p.uid),
             "invalid_bond")
        by_id[p.uid] = p
    for p in frame.particles:
        if p.bond:
            need(p.bond in by_id and by_id[p.bond].bond == p.uid,
                 "bond_not_reciprocal")
            need(p.spin + by_id[p.bond].spin == 0, "bond_spin_mismatch")


def genesis(side, particles):
    return Frame(0, side, "GENESIS", tuple(sorted(particles, key=lambda p: p.uid)))


def occupied(frame):
    validate(frame)
    cells = {}
    for p in frame.particles:
        cells.setdefault(p.xyz, []).append(p.uid)
    return {key: tuple(sorted(value)) for key, value in sorted(cells.items())}


def totals(frame):
    validate(frame)
    ps = frame.particles
    return (
        len(ps), sum(p.energy for p in ps),
        tuple(sum(p.v[a] for p in ps) for a in range(3)),
        tuple(sum(p.L[a] for p in ps) for a in range(3)),
        sum(p.spin for p in ps),
    )


def _permute_at_cells(particles, inverse=False):
    groups = {}
    for p in particles:
        groups.setdefault(p.xyz, []).append(p)
    velocities = {}
    for group in groups.values():
        group.sort(key=lambda p: p.uid)
        k = len(group)
        for i, p in enumerate(group):
            donor = group[(i + 1) % k] if inverse else group[(i - 1) % k]
            velocities[p.uid] = donor.v
    return [replace(p, v=velocities[p.uid]) for p in particles]


def step(frame):
    """Simultaneous toroidal position update; local velocity permutation on collision."""
    validate(frame)
    moved = [replace(p, xyz=tuple((p.xyz[a] + p.v[a]) % frame.side
                                   for a in range(3))) for p in frame.particles]
    collided = _permute_at_cells(moved)
    out = Frame(frame.n + 1, frame.side, frame.digest(), tuple(collided))
    validate(out)
    need(totals(frame) == totals(out), "conservation_failure")
    return out


def rewind(frame, previous_parent):
    """Exact inverse requires the prior frame's parent commitment from the ledger."""
    validate(frame)
    need(frame.n > 0, "cannot_rewind_genesis")
    uncollided = _permute_at_cells(list(frame.particles), inverse=True)
    prior = [replace(p, xyz=tuple((p.xyz[a] - p.v[a]) % frame.side
                                  for a in range(3))) for p in uncollided]
    out = Frame(frame.n - 1, frame.side, previous_parent, tuple(prior))
    validate(out)
    need(out.digest() == frame.parent, "rewind_parent_hash_mismatch")
    return out


def _parse_fields(line, tag, keys):
    chunks = line.split("|")
    need(chunks[0] == tag and chunks[-1] == "json=0", "wrong_record_kind")
    need(len(chunks) == len(keys) + 2, "wrong_field_count")
    fields = {}
    for chunk, key in zip(chunks[1:-1], keys):
        prefix = key + "="
        need(chunk.startswith(prefix), "wrong_field_order")
        fields[key] = chunk[len(prefix):]
    return fields


def _parse_triple(value):
    parts = value.split(",")
    need(len(parts) == 3, "triple_arity")
    return tuple(int(x) for x in parts)


def parse_frame(raw):
    """Canonical decoder: rejects altered ordering, leading zeros and extra fields."""
    need(type(raw) is bytes, "bytes_required")
    text = raw.decode("ascii")
    need(text.endswith("\n"), "missing_line_terminator")
    lines = text.rstrip("\n").split("\n")
    need(len(lines) >= 1, "missing_frame")
    header = _parse_fields(lines[0], "FRAME", ("n", "side", "parent"))
    particles = []
    for line in lines[1:]:
        x = _parse_fields(line, "PARTICLE",
                          ("uid", "xyz", "v", "energy", "spin", "L", "bond"))
        particles.append(Particle(
            x["uid"], _parse_triple(x["xyz"]), _parse_triple(x["v"]),
            int(x["energy"]), int(x["spin"]), _parse_triple(x["L"]),
            "" if x["bond"] == "_" else x["bond"],
        ))
    f = Frame(int(header["n"]), int(header["side"]),
              header["parent"], tuple(particles))
    need(f.bytes() == raw, "noncanonical_encoding")
    return f


def chain(genesis_frame, steps):
    need(type(steps) is int and 0 <= steps <= 100000, "invalid_steps")
    frames = [genesis_frame]
    for _ in range(steps):
        frames.append(step(frames[-1]))
    return tuple(frames)


def verify_replay(frames):
    need(len(frames) > 0 and frames[0].n == 0, "missing_genesis")
    for before, after in zip(frames, frames[1:]):
        need(step(before).bytes() == after.bytes(), "frame_replay_mismatch")
        need(rewind(after, before.parent).bytes() == before.bytes(),
             "inverse_replay_mismatch")
    return True


def hbp_receipt(frames):
    verify_replay(frames)
    rows = []
    for frame in frames:
        count, energy, momentum, intrinsic_L, spin = totals(frame)
        rows.append("FRAMECHECK|n=" + str(frame.n) + "|sha256=" + frame.digest()
                    + "|particles=" + str(count) + "|energy=" + str(energy)
                    + "|momentum=" + triple(momentum)
                    + "|L_tag=" + triple(intrinsic_L)
                    + "|spin=" + str(spin) + "|json=0")
        for xyz, ids in occupied(frame).items():
            rows.append("PIXEL|n=" + str(frame.n) + "|xyz=" + triple(xyz)
                        + "|uids=" + ",".join(ids) + "|json=0")
        for p in frame.particles:
            rows.append("METATAG|n=" + str(frame.n) + "|uid=" + p.uid
                        + "|state_sha256=" + p.state_sha256() + "|json=0")
    rows.append("FRAME_MATRIX_VERDICT|exact_replay=PASS|inverse=PASS"
                "|stable_identity=PASS|momentum_tag=CONSERVED"
                "|energy_tag=CONSERVED|L_tag=CONSERVED"
                "|physical_quantum_claim=NOT_TESTED|json=0")
    return ("\n".join(rows) + "\n").encode("ascii")


def fixture():
    # P1/P2 land at the same pixel in frame 1, exchange momenta, then separate.
    return genesis(5, (
        Particle("P1", (1, 2, 2), (1, 0, 0), 3, 1, (2, 0, 0), "P2"),
        Particle("P2", (3, 2, 2), (-1, 0, 0), 4, -1, (-2, 0, 0), "P1"),
        Particle("P3", (4, 4, 4), (0, 1, 0), 5, 0, (0, 1, 0)),
    ))


if __name__ == "__main__":
    frames = chain(fixture(), 6)
    print(hbp_receipt(frames).decode("ascii"), end="")
