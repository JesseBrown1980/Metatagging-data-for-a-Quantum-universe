"""Formal, non-firing substrate for Asolaria Floor-1 cube/PID training.

This module models content-addressed nodes, three geometry families, paired GNN
and reverse-gain proposals, an Omega-GNN/Omega-omnibit junction, logical-time
feedback, and supervisor-visible collision comparison.  It performs no network,
process, device, GitHub, or fabric action.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from itertools import combinations
from typing import Iterable, Mapping, Sequence


def _field_bytes(value: object) -> bytes:
    if isinstance(value, Enum):
        encoded = _field_bytes(value.value)
        name = value.__class__.__qualname__.encode("utf-8")
        return b"E" + len(name).to_bytes(8, "big") + name + encoded
    if value is None:
        return b"N"
    if isinstance(value, bool):
        return b"Z1" if value else b"Z0"
    if isinstance(value, int):
        return b"I" + str(value).encode("ascii")
    if isinstance(value, bytes):
        return b"B" + len(value).to_bytes(8, "big") + value
    if isinstance(value, str):
        encoded = value.encode("utf-8")
        return b"S" + len(encoded).to_bytes(8, "big") + encoded
    if isinstance(value, tuple):
        body = bytearray(b"T" + len(value).to_bytes(8, "big"))
        for item in value:
            encoded = _field_bytes(item)
            body.extend(len(encoded).to_bytes(8, "big"))
            body.extend(encoded)
        return bytes(body)
    if isinstance(value, list):
        body = bytearray(b"L" + len(value).to_bytes(8, "big"))
        for item in value:
            encoded = _field_bytes(item)
            body.extend(len(encoded).to_bytes(8, "big"))
            body.extend(encoded)
        return bytes(body)
    raise TypeError(f"unsupported identity field type: {type(value).__qualname__}")


def digest(*values: object) -> str:
    """Length-prefix fields so content identities cannot be delimiter-ambiguous."""

    body = bytearray(b"ASOLARIA-FLOOR1-PID-V1\0")
    for value in values:
        encoded = _field_bytes(value)
        body.extend(len(encoded).to_bytes(8, "big"))
        body.extend(encoded)
    return sha256(body).hexdigest()


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value.lower())


def _is_content_pid(value: str) -> bool:
    return (
        value.startswith("PID-")
        and len(value) == 68
        and all(character in "0123456789abcdef" for character in value[4:].lower())
    )


class GeometryFamily(str, Enum):
    CUBIC_6_APEX = "CUBIC_6_APEX_C2^3"
    TETRA_12_DIRECTED = "TETRA_12_DIRECTED"
    SPHERE_PI_LIMIT = "SPHERE_TRIANGLE_REFINEMENT_PI_LIMIT"


class StorageClass(str, Enum):
    RAM = "RAM"
    DISK_STUB = "DISK_STUB"
    GITRAM_STUB = "GITRAM_STUB"


SELF_IMPROVING_FUNCTION_FAMILIES = (
    "LANGUAGE_GENESIS",
    "LEARNER",
    "GENERATOR",
    "EVALUATOR",
    "SELECTOR_PROMOTION",
    "REVERSE_GAIN",
    "REPLAY_ROLLBACK",
    "OMEGA_SYNTHESIS",
    "TRANSLATION_ALIGNMENT",
    "PID_LINEAGE",
)


@dataclass(frozen=True)
class RouteSelector:
    """High-dimensional route identity; intentionally not a three-field tuple."""

    axes_60d: tuple[int, ...]
    glyph_family: str
    glyph_levels: tuple[str, ...]
    language: str
    executor: str
    pipe: str
    operation: str
    room: str
    proof_tier: str
    runtime_mode: str
    colony: str
    seat: str
    temporal_slice: str

    def __post_init__(self) -> None:
        if len(self.axes_60d) < 60:
            raise ValueError("a Floor-1 selector must preserve at least 60 D axes")
        if any(axis < 0 or axis >= 1024 for axis in self.axes_60d):
            raise ValueError("BEHCS-1024 axes must be in 0..1023")

    @property
    def commitment(self) -> str:
        return digest(
            "ROUTE_SELECTOR",
            self.axes_60d,
            self.glyph_family,
            self.glyph_levels,
            self.language,
            self.executor,
            self.pipe,
            self.operation,
            self.room,
            self.proof_tier,
            self.runtime_mode,
            self.colony,
            self.seat,
            self.temporal_slice,
        )


@dataclass(frozen=True)
class NodeDescriptor:
    geometry: GeometryFamily
    address: tuple[int, ...]
    generation: int
    content_sha256: str
    parent_pid: str
    owner_reference: str
    selector: RouteSelector
    storage: StorageClass
    logical_tick_us: int
    feedback_delay_us: int
    body_kind: str = "CUBE_PID"

    def __post_init__(self) -> None:
        if self.generation < 0 or self.logical_tick_us < 0:
            raise ValueError("generation and logical tick must be nonnegative")
        if self.feedback_delay_us <= 0:
            raise ValueError("feedback delay must be positive")
        if not _is_sha256(self.content_sha256):
            raise ValueError("content_sha256 must be a full SHA-256 digest")

    @property
    def identity_sha256(self) -> str:
        return digest(
            "NODE",
            self.geometry,
            self.address,
            self.generation,
            self.content_sha256,
            self.parent_pid,
            self.owner_reference,
            self.selector.commitment,
            self.storage,
            self.logical_tick_us,
            self.feedback_delay_us,
            self.body_kind,
        )

    @property
    def pid(self) -> str:
        return "PID-" + self.identity_sha256


@dataclass(frozen=True)
class CatalogEvent:
    node_pid: str
    kind: str
    payload: str
    glyph: str
    logical_tick_us: int

    def __post_init__(self) -> None:
        if self.kind not in {"MESSAGE", "ERROR", "IDEA", "GLYPH", "QUESTION", "ANSWER"}:
            raise ValueError("unsupported catalog event kind")

    @property
    def payload_sha256(self) -> str:
        return sha256(self.payload.encode("utf-8")).hexdigest()

    @property
    def event_id(self) -> str:
        return "EVT-" + digest(
            self.node_pid,
            self.kind,
            self.payload_sha256,
            self.glyph,
            self.logical_tick_us,
        )[:32]


@dataclass(frozen=True)
class EdgeProposal:
    edge_id: str
    pair_id: str
    source_pid: str
    target_pid: str
    relation: str
    event_id: str
    payload_sha256: str
    logical_tick_us: int
    status: str = "PREPARED_NOT_INGESTED"
    learned: int = 0

    def __post_init__(self) -> None:
        route = {
            "FORWARD_GNN_SCORE_EVENT": "FORWARD_GNN",
            "REVERSE_GAIN_OUTCOME_FEEDBACK": "REVERSE_GAIN",
        }.get(self.relation)
        if route is None:
            raise ValueError("unsupported GNN proposal relation")
        expected = "EDGE-" + digest(
            self.pair_id,
            route,
            self.source_pid,
            self.target_pid,
        )[:32]
        if self.edge_id != expected:
            raise ValueError("GNN proposal edge_id does not match semantic fields")
        if not _is_sha256(self.payload_sha256):
            raise ValueError("GNN proposal payload requires full SHA-256")

    @property
    def identity_sha256(self) -> str:
        return digest(
            "EDGE_PROPOSAL",
            self.edge_id,
            self.pair_id,
            self.source_pid,
            self.target_pid,
            self.relation,
            self.event_id,
            self.payload_sha256,
            self.logical_tick_us,
            self.status,
            self.learned,
        )

    @property
    def pid(self) -> str:
        return "PID-" + self.identity_sha256


def paired_learning_edges(
    parent_pid: str,
    child_pid: str,
    event: CatalogEvent,
) -> tuple[EdgeProposal, EdgeProposal]:
    """Emit paired proposals; reverse gain is feedback, not an asserted inverse."""

    pair_id = "PAIR-" + digest(parent_pid, child_pid, event.event_id)[:32]
    forward = EdgeProposal(
        edge_id="EDGE-" + digest(pair_id, "FORWARD_GNN", parent_pid, child_pid)[:32],
        pair_id=pair_id,
        source_pid=parent_pid,
        target_pid=child_pid,
        relation="FORWARD_GNN_SCORE_EVENT",
        event_id=event.event_id,
        payload_sha256=event.payload_sha256,
        logical_tick_us=event.logical_tick_us,
    )
    reverse = EdgeProposal(
        edge_id="EDGE-" + digest(pair_id, "REVERSE_GAIN", child_pid, parent_pid)[:32],
        pair_id=pair_id,
        source_pid=child_pid,
        target_pid=parent_pid,
        relation="REVERSE_GAIN_OUTCOME_FEEDBACK",
        event_id=event.event_id,
        payload_sha256=event.payload_sha256,
        logical_tick_us=event.logical_tick_us + 1,
    )
    return forward, reverse


@dataclass(frozen=True)
class Response:
    agent_pid: str
    request_id: str
    protected_scope: str
    route: str
    verdict: str
    payload: str
    logical_tick_us: int

    @property
    def payload_sha256(self) -> str:
        return sha256(self.payload.encode("utf-8")).hexdigest()

    @property
    def response_id(self) -> str:
        return "RSP-" + digest(
            self.agent_pid,
            self.request_id,
            self.protected_scope,
            self.route,
            self.verdict,
            self.payload_sha256,
            self.logical_tick_us,
        )[:32]


def supervisor_collision_table(
    first: Response,
    second: Response,
    overlap_window_us: int,
) -> dict[str, object]:
    """Compare exactly two signed results; all-pairs scans are a separate gate."""

    if overlap_window_us < 0:
        raise ValueError("overlap window cannot be negative")
    same_request = first.request_id == second.request_id
    same_scope = first.protected_scope == second.protected_scope
    same_route = first.route == second.route
    overlap = abs(first.logical_tick_us - second.logical_tick_us) <= overlap_window_us
    incompatible = (
        first.verdict != second.verdict
        or first.payload_sha256 != second.payload_sha256
    )
    collision = same_request and same_scope and same_route and overlap and incompatible
    if collision:
        classification = "COLLISION_REVIEW"
    elif same_request and not incompatible:
        classification = "CONSENSUS"
    elif same_request:
        classification = "DIVERGENCE_REVIEW"
    else:
        classification = "SEPARATE_REQUESTS"
    ordered_ids = tuple(sorted((first.response_id, second.response_id)))
    return {
        "join_id": "JOIN-" + digest(ordered_ids, overlap_window_us)[:32],
        "response_ids": ordered_ids,
        "collision": int(collision),
        "classification": classification,
        "supervisor_visible": 1,
        "action": "HELD_FOR_SUPERVISOR" if collision else "OBSERVE",
        "complete_scope": "EXACTLY_TWO_RESPONSES",
    }


def _edge(left: int, right: int) -> tuple[int, int]:
    if left == right:
        raise ValueError("self-edge is not allowed")
    return tuple(sorted((left, right)))


def cube_edges() -> set[tuple[int, int]]:
    return {
        _edge(vertex, vertex ^ (1 << axis))
        for vertex in range(8)
        for axis in range(3)
    }


def cube_face_cycles() -> tuple[tuple[int, ...], ...]:
    faces: list[tuple[int, ...]] = []
    for fixed_axis in range(3):
        other = [axis for axis in range(3) if axis != fixed_axis]
        for fixed_bit in (0, 1):
            start = fixed_bit << fixed_axis
            faces.append(
                (
                    start,
                    start ^ (1 << other[0]),
                    start ^ (1 << other[0]) ^ (1 << other[1]),
                    start ^ (1 << other[1]),
                )
            )
    return tuple(faces)


def cube_recenter(origin: int, vertex: int) -> int:
    if origin not in range(8) or vertex not in range(8):
        raise ValueError("cube vertices are 0..7")
    return origin ^ vertex


def tetra_edges() -> set[tuple[int, int]]:
    return {_edge(left, right) for left, right in combinations(range(4), 2)}


def tetra_face_cycles() -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(face) for face in combinations(range(4), 3))


def tetra_recenter(origin: int, vertex: int) -> int:
    """A K4 automorphism swapping the chosen origin with vertex zero."""

    if origin not in range(4) or vertex not in range(4):
        raise ValueError("tetra vertices are 0..3")
    if origin == 0:
        return vertex
    if vertex == origin:
        return 0
    if vertex == 0:
        return origin
    return vertex


def verify_cycle_double_cover(
    graph_edges: Iterable[tuple[int, int]],
    cycles: Iterable[Sequence[int]],
) -> dict[str, object]:
    """Verify two counted cycle memberships per undirected edge."""

    expected = {_edge(*edge) for edge in graph_edges}
    counts: Counter[tuple[int, int]] = Counter()
    for cycle in cycles:
        if len(cycle) < 3:
            raise ValueError("a cycle requires at least three vertices")
        for index, left in enumerate(cycle):
            counts[_edge(left, cycle[(index + 1) % len(cycle)])] += 1
    foreign = set(counts) - expected
    exact = not foreign and set(counts) == expected and all(counts[edge] == 2 for edge in expected)
    return {
        "edges": len(expected),
        "cycle_memberships": sum(counts.values()),
        "foreign_edges": len(foreign),
        "each_edge_exactly_twice": int(exact),
        "status": "PASS" if exact else "FAIL",
    }


def sphere_refinement(level: int) -> dict[str, int | str]:
    """Combinatorics of an icosphere refinement; pi is not a side count."""

    if level < 0:
        raise ValueError("refinement level must be nonnegative")
    scale = 4**level
    faces = 20 * scale
    edges = 30 * scale
    vertices = 10 * scale + 2
    return {
        "level": level,
        "vertices": vertices,
        "edges": edges,
        "directed_edges": edges * 2,
        "triangular_faces": faces,
        "euler_characteristic": vertices - edges + faces,
        "face_edge_incidence": faces * 3,
        "double_edge_incidence": edges * 2,
        "pi_role": "ANGLE_AND_MEASURE_CONTINUUM_LIMIT",
    }


def hypercube_counts(dimension: int) -> dict[str, int]:
    if dimension < 1:
        raise ValueError("hypercube dimension must be positive")
    vertices = 2**dimension
    edges = dimension * 2 ** (dimension - 1)
    return {
        "dimension": dimension,
        "vertices": vertices,
        "undirected_edges": edges,
        "directed_edges": edges * 2,
    }


def sphere_projection_window(level: int, start: int, count: int) -> tuple[int, ...]:
    """Return one finite internal window; the continuum limit is not indexed."""

    cells = int(sphere_refinement(level)["triangular_faces"])
    if start < 0 or count < 1 or start + count > cells:
        raise ValueError("sphere projection window is outside the finite refinement")
    return tuple(range(start, start + count))


def omega_hierarchy(level: int) -> dict[str, int | str]:
    """Finite Omega-intersection counts for one nested refinement floor.

    These are address positions, not a claim that every position is resident or
    trained. Each six-apex cell has an inner Omega, twelve inner Omegas feed a
    sector/spherical-cell Omega, and the finite sphere floor feeds one outer
    Omega. Increasing the level gives an arbitrarily fine finite hierarchy.
    """

    sphere_cells = int(sphere_refinement(level)["triangular_faces"])
    omega_6_positions = sphere_cells * 12
    omega_12_positions = sphere_cells
    omega_pi_positions = 1
    apex_positions = omega_6_positions * 6
    vertex_positions = apex_positions * 8
    return {
        "level": level,
        "sphere_cells": sphere_cells,
        "omega_6_positions": omega_6_positions,
        "omega_12_positions": omega_12_positions,
        "omega_pi_positions": omega_pi_positions,
        "all_omega_positions": omega_6_positions + omega_12_positions + omega_pi_positions,
        "apex_positions": apex_positions,
        "vertex_positions": vertex_positions,
        "materialization_semantics": "FINITE_ADDRESS_CAPACITY_NOT_RESIDENT_COUNT",
    }


def brown_hilbert_child(
    prefix: Sequence[int],
    digit: int,
    radix: int = 1024,
) -> tuple[int, ...]:
    if radix < 2 or digit < 0 or digit >= radix:
        raise ValueError("address digit is outside its radix")
    if any(item < 0 or item >= radix for item in prefix):
        raise ValueError("prefix digit is outside its radix")
    return (*prefix, digit)


@dataclass(frozen=True)
class QuestionAddress:
    cube_pid: str
    geometry: GeometryFamily
    glyph_level: str
    language: str
    epoch: int
    index: int

    @property
    def question_id(self) -> str:
        return "Q-" + digest(
            self.cube_pid,
            self.geometry,
            self.glyph_level,
            self.language,
            self.epoch,
            self.index,
        )[:32]


@dataclass(frozen=True)
class ImprovementPrecommit:
    """Held-out/evaluator bytes committed before any child is generated."""

    parent_pid: str
    heldout_set_sha256: str
    evaluator_sha256: str
    evaluator_version: str
    committed_tick_us: int

    def __post_init__(self) -> None:
        if not _is_content_pid(self.parent_pid):
            raise ValueError("improvement parent must be a full content PID")
        if not _is_sha256(self.heldout_set_sha256) or not _is_sha256(
            self.evaluator_sha256
        ):
            raise ValueError("held-out set and evaluator must be SHA-256 committed")
        if not self.evaluator_version or self.committed_tick_us < 0:
            raise ValueError("evaluator version and nonnegative precommit tick are required")

    @property
    def identity_sha256(self) -> str:
        return digest(
            "IMPROVEMENT_PRECOMMIT_V1",
            self.parent_pid,
            self.heldout_set_sha256,
            self.evaluator_sha256,
            self.evaluator_version,
            self.committed_tick_us,
        )

    @property
    def pid(self) -> str:
        return "PID-" + self.identity_sha256


@dataclass(frozen=True)
class HeldoutEvaluation:
    """One deterministic or repeated stochastic evaluation on fixed bytes."""

    subject_pid: str
    heldout_set_sha256: str
    evaluator_sha256: str
    evaluator_version: str
    score_ppm: int
    trial_scores_ppm: tuple[int, ...]
    seeds: tuple[int, ...]
    confidence_low_ppm: int
    confidence_high_ppm: int
    evaluated_tick_us: int
    stochastic: bool

    def __post_init__(self) -> None:
        if not _is_content_pid(self.subject_pid):
            raise ValueError("evaluation subject must be a full content PID")
        if not _is_sha256(self.heldout_set_sha256) or not _is_sha256(
            self.evaluator_sha256
        ):
            raise ValueError("evaluation inputs must be SHA-256 committed")
        if not self.evaluator_version or self.evaluated_tick_us < 0:
            raise ValueError("evaluation version and nonnegative tick are required")
        values = (
            self.score_ppm,
            self.confidence_low_ppm,
            self.confidence_high_ppm,
            *self.trial_scores_ppm,
        )
        if not self.trial_scores_ppm or any(value < 0 or value > 1_000_000 for value in values):
            raise ValueError("evaluation scores must be populated PPM values")
        if self.score_ppm * len(self.trial_scores_ppm) != sum(self.trial_scores_ppm):
            raise ValueError("reported score must be the exact mean of trial scores")
        if not self.confidence_low_ppm <= self.score_ppm <= self.confidence_high_ppm:
            raise ValueError("confidence interval must contain the reported score")
        if self.stochastic:
            if len(self.trial_scores_ppm) < 2:
                raise ValueError("stochastic evaluation requires repeated trials")
            if len(self.seeds) != len(self.trial_scores_ppm):
                raise ValueError("every stochastic trial requires one recorded seed")
            if len(set(self.seeds)) != len(self.seeds) or any(seed < 0 for seed in self.seeds):
                raise ValueError("stochastic seeds must be unique and nonnegative")
        elif (
            len(self.trial_scores_ppm) != 1
            or self.seeds
            or self.confidence_low_ppm != self.score_ppm
            or self.confidence_high_ppm != self.score_ppm
        ):
            raise ValueError("deterministic evaluation has one exact seedless trial")

    @property
    def identity_sha256(self) -> str:
        return digest(
            "HELDOUT_EVALUATION_V1",
            self.subject_pid,
            self.heldout_set_sha256,
            self.evaluator_sha256,
            self.evaluator_version,
            self.score_ppm,
            self.trial_scores_ppm,
            self.seeds,
            self.confidence_low_ppm,
            self.confidence_high_ppm,
            self.evaluated_tick_us,
            self.stochastic,
        )

    @property
    def pid(self) -> str:
        return "PID-" + self.identity_sha256


@dataclass(frozen=True)
class ImprovementClaim:
    """Reconstructable parent/child improvement proof, never a training action."""

    function_family: str
    precommit: ImprovementPrecommit
    parent_evaluation: HeldoutEvaluation
    child_evaluation: HeldoutEvaluation
    child_created_tick_us: int
    noise_floor_ppm: int
    leakage_audit_sha256: str
    lineage_receipt_sha256: str
    reverse_replay_receipt_sha256: str
    rollback_state_sha256: str
    leakage_audit_pass: bool
    reverse_replay_pass: bool

    def __post_init__(self) -> None:
        if self.function_family not in SELF_IMPROVING_FUNCTION_FAMILIES:
            raise ValueError("unknown self-improving function family")
        for value in (
            self.leakage_audit_sha256,
            self.lineage_receipt_sha256,
            self.reverse_replay_receipt_sha256,
            self.rollback_state_sha256,
        ):
            if not _is_sha256(value):
                raise ValueError("improvement proof receipts must be SHA-256 committed")
        if self.child_created_tick_us <= self.precommit.committed_tick_us:
            raise ValueError("held-out set and evaluator must be committed before child creation")
        if self.noise_floor_ppm < 0:
            raise ValueError("measurement-noise floor cannot be negative")
        parent = self.parent_evaluation
        child = self.child_evaluation
        if self.precommit.parent_pid != parent.subject_pid or parent.subject_pid == child.subject_pid:
            raise ValueError("claim must bind distinct parent and child content PIDs")
        expected_inputs = (
            self.precommit.heldout_set_sha256,
            self.precommit.evaluator_sha256,
            self.precommit.evaluator_version,
        )
        for evaluation in (parent, child):
            if (
                evaluation.heldout_set_sha256,
                evaluation.evaluator_sha256,
                evaluation.evaluator_version,
            ) != expected_inputs:
                raise ValueError("parent and child must use the precommitted held-out/evaluator bytes")
        if parent.evaluated_tick_us < self.precommit.committed_tick_us:
            raise ValueError("parent evaluation predates the evidence precommit")
        if child.evaluated_tick_us < self.child_created_tick_us:
            raise ValueError("child evaluation predates child creation")
        if parent.stochastic != child.stochastic:
            raise ValueError("parent and child evaluation modes differ")
        if parent.stochastic and len(parent.trial_scores_ppm) != len(child.trial_scores_ppm):
            raise ValueError("stochastic parent and child require equal repeated-trial counts")
        if not self.leakage_audit_pass or not self.reverse_replay_pass:
            raise ValueError("leakage audit and reverse replay must both pass")
        if self.delta_ppm <= 0 or self.delta_ppm <= self.noise_floor_ppm:
            raise ValueError("held-out improvement must be positive and exceed measurement noise")
        if child.confidence_low_ppm <= parent.confidence_high_ppm:
            raise ValueError("child confidence bound must clear the parent confidence bound")

    @property
    def parent_pid(self) -> str:
        return self.parent_evaluation.subject_pid

    @property
    def child_pid(self) -> str:
        return self.child_evaluation.subject_pid

    @property
    def delta_ppm(self) -> int:
        return self.child_evaluation.score_ppm - self.parent_evaluation.score_ppm

    @property
    def identity_sha256(self) -> str:
        return digest(
            "IMPROVEMENT_CLAIM_V1",
            self.function_family,
            self.precommit.identity_sha256,
            self.parent_evaluation.identity_sha256,
            self.child_evaluation.identity_sha256,
            self.child_created_tick_us,
            self.noise_floor_ppm,
            self.leakage_audit_sha256,
            self.lineage_receipt_sha256,
            self.reverse_replay_receipt_sha256,
            self.rollback_state_sha256,
            self.leakage_audit_pass,
            self.reverse_replay_pass,
        )

    @property
    def pid(self) -> str:
        return "PID-" + self.identity_sha256


@dataclass(frozen=True)
class NativeGlyphLanguageWitness:
    """Per-body language witness; catalog bytes may remain an explicit import boundary."""

    body_kind: str
    body_ordinal: int
    body_leaf_sha256: str
    body_receipt_sha256: str
    formation_receipt_sha256: str
    evidence_class: str
    owning_catalog_import: str
    native_catalog_sha256: str | None = None

    def __post_init__(self) -> None:
        if self.body_kind not in {"BASE", "APEX", "OMEGA"} or self.body_ordinal < 1:
            raise ValueError("native-language witness requires a typed positive body coordinate")
        for value in (
            self.body_leaf_sha256,
            self.body_receipt_sha256,
            self.formation_receipt_sha256,
        ):
            if not _is_sha256(value):
                raise ValueError("native-language witness source must be SHA-256 committed")
        if self.native_catalog_sha256 is not None and not _is_sha256(
            self.native_catalog_sha256
        ):
            raise ValueError("native catalog must be absent or SHA-256 committed")
        if self.evidence_class == "OPERATOR_OBSERVED":
            if self.native_catalog_sha256 is not None or not self.owning_catalog_import.startswith(
                "PENDING_"
            ):
                raise ValueError("operator-observed witness cannot invent absent catalog bytes")
        elif self.evidence_class == "MEASURED_CATALOG_IMPORTED":
            if self.native_catalog_sha256 is None or self.owning_catalog_import.startswith(
                "PENDING_"
            ):
                raise ValueError("measured witness requires imported catalog bytes")
        else:
            raise ValueError("unsupported native-language evidence class")

    @property
    def body_pid(self) -> str:
        return "PID-" + digest(
            "CDC_TRAINED_BODY_CONTENT_V1",
            self.body_kind,
            self.body_ordinal,
            self.body_leaf_sha256,
            self.body_receipt_sha256,
            self.formation_receipt_sha256,
        )

    @property
    def native_language_pid(self) -> str:
        return "PID-" + digest(
            "CUBE_NATIVE_GLYPH_LANGUAGE_V1",
            self.body_pid,
            self.body_leaf_sha256,
            self.evidence_class,
            self.native_catalog_sha256,
            self.owning_catalog_import,
        )

    @property
    def identity_sha256(self) -> str:
        return digest(
            "NATIVE_GLYPH_LANGUAGE_WITNESS_V1",
            self.body_kind,
            self.body_ordinal,
            self.body_pid,
            self.native_language_pid,
            self.body_leaf_sha256,
            self.body_receipt_sha256,
            self.formation_receipt_sha256,
            self.evidence_class,
            self.owning_catalog_import,
            self.native_catalog_sha256,
        )

    @property
    def pid(self) -> str:
        return "PID-" + self.identity_sha256


@dataclass(frozen=True)
class GlyphLanguageEvaluation:
    """Five independent gates for a measured native-glyph improvement claim."""

    witness_pid: str
    cube_body_pid: str
    native_language_pid: str
    aligned_cube_body_pid: str
    training_corpus_sha256: str
    native_message_sha256: str
    omega_message_sha256: str
    recovered_native_message_sha256: str
    native_semantic_sha256: str
    aligned_semantic_sha256: str
    native_catalog_before_sha256: str
    native_catalog_after_sha256: str
    absence_audit_sha256: str
    forward_translation_receipt_sha256: str
    reverse_translation_receipt_sha256: str
    cross_cube_receipt_sha256: str
    grammar_rule_count: int
    compositional_operator_count: int
    novel_message_absent_from_training: bool
    symbol_substitution_only: bool

    def __post_init__(self) -> None:
        for value in (
            self.witness_pid,
            self.cube_body_pid,
            self.native_language_pid,
            self.aligned_cube_body_pid,
        ):
            if not _is_content_pid(value):
                raise ValueError("glyph-language evaluation identities must be content PIDs")
        for value in (
            self.training_corpus_sha256,
            self.native_message_sha256,
            self.omega_message_sha256,
            self.recovered_native_message_sha256,
            self.native_semantic_sha256,
            self.aligned_semantic_sha256,
            self.native_catalog_before_sha256,
            self.native_catalog_after_sha256,
            self.absence_audit_sha256,
            self.forward_translation_receipt_sha256,
            self.reverse_translation_receipt_sha256,
            self.cross_cube_receipt_sha256,
        ):
            if not _is_sha256(value):
                raise ValueError("glyph-language evidence must be SHA-256 committed")
        if self.symbol_substitution_only or self.grammar_rule_count < 2:
            raise ValueError("native language must demonstrate structure beyond symbol substitution")
        if self.compositional_operator_count < 1 or not self.novel_message_absent_from_training:
            raise ValueError("a novel compositional glyph message must pass an absence audit")
        if self.native_message_sha256 != self.recovered_native_message_sha256:
            raise ValueError("native-to-Omega translation must reverse exactly")
        if self.native_semantic_sha256 != self.aligned_semantic_sha256:
            raise ValueError("cross-cube alignment must preserve meaning")
        if self.native_catalog_before_sha256 != self.native_catalog_after_sha256:
            raise ValueError("alignment must retain the cube-native language")

    @property
    def identity_sha256(self) -> str:
        return digest(
            "GLYPH_LANGUAGE_EVALUATION_V1",
            self.witness_pid,
            self.cube_body_pid,
            self.native_language_pid,
            self.aligned_cube_body_pid,
            self.training_corpus_sha256,
            self.native_message_sha256,
            self.omega_message_sha256,
            self.recovered_native_message_sha256,
            self.native_semantic_sha256,
            self.aligned_semantic_sha256,
            self.native_catalog_before_sha256,
            self.native_catalog_after_sha256,
            self.absence_audit_sha256,
            self.forward_translation_receipt_sha256,
            self.reverse_translation_receipt_sha256,
            self.cross_cube_receipt_sha256,
            self.grammar_rule_count,
            self.compositional_operator_count,
            self.novel_message_absent_from_training,
            self.symbol_substitution_only,
        )

    @property
    def pid(self) -> str:
        return "PID-" + self.identity_sha256


@dataclass(frozen=True)
class NestedUniverseAddress:
    """One finite address in the sphere -> 12 -> 6 -> 8 hierarchy."""

    sphere_level: int
    sphere_cell: int
    sector_12: int
    apex_6: int
    vertex_8: int
    lane: int
    epoch: int
    glyph_level: str
    language: str
    question_index: int

    def __post_init__(self) -> None:
        cells = int(sphere_refinement(self.sphere_level)["triangular_faces"])
        if self.sphere_cell not in range(cells):
            raise ValueError("sphere cell is outside this finite refinement")
        if self.sector_12 not in range(12):
            raise ValueError("sector_12 must be in 0..11")
        if self.apex_6 not in range(6):
            raise ValueError("apex_6 must be in 0..5")
        if self.vertex_8 not in range(8):
            raise ValueError("vertex_8 must be in 0..7")
        if min(self.lane, self.epoch, self.question_index) < 0:
            raise ValueError("lane, epoch, and question index must be nonnegative")

    @property
    def address_id(self) -> str:
        return "ADDR-" + digest(
            "NESTED_UNIVERSE",
            self.sphere_level,
            self.sphere_cell,
            self.sector_12,
            self.apex_6,
            self.vertex_8,
            self.lane,
            self.epoch,
            self.glyph_level,
            self.language,
            self.question_index,
        )[:32]

    @property
    def geometric_capacity_at_level(self) -> int:
        cells = int(sphere_refinement(self.sphere_level)["triangular_faces"])
        return cells * 12 * 6 * 8


@dataclass(frozen=True)
class OmegaCoordinate:
    """A distinct Omega bit at one geometry, floor, and finite projection."""

    geometry: GeometryFamily
    floor: int
    parent_omega_pid: str
    parent_identity_sha256: str
    source_state_receipt_sha256: str
    owner_reference: str
    slot_address: str
    slot_version: int
    refinement_level: int | None = None
    projected_cell: int | None = None

    def __post_init__(self) -> None:
        if self.floor < 1:
            raise ValueError("Omega floor must be at least one")
        if not self.parent_omega_pid.startswith("PID-"):
            raise ValueError("parent Omega must be a PID")
        if not _is_sha256(self.parent_identity_sha256):
            raise ValueError("parent Omega identity must be a full SHA-256")
        if not _is_sha256(self.source_state_receipt_sha256):
            raise ValueError("source-state receipt must be a full SHA-256")
        if not self.owner_reference:
            raise ValueError("Omega owner reference cannot be empty")
        if not self.slot_address or self.slot_version < 1:
            raise ValueError("Omega slot address and positive version are required")
        if self.geometry is GeometryFamily.SPHERE_PI_LIMIT:
            if self.refinement_level is None or self.projected_cell is None:
                raise ValueError("sphere Omega requires a finite refinement and projected cell")
            cells = int(sphere_refinement(self.refinement_level)["triangular_faces"])
            if self.projected_cell not in range(cells):
                raise ValueError("sphere Omega projected cell is outside the finite refinement")
        elif self.refinement_level is not None or self.projected_cell is not None:
            raise ValueError("only a sphere Omega carries a refinement and projected cell")

    @property
    def omega_bit_id(self) -> str:
        return "OMEGA-" + digest(
            "INDEXED_OMEGA_BIT",
            self.geometry,
            self.floor,
            self.parent_omega_pid,
            self.parent_identity_sha256,
            self.source_state_receipt_sha256,
            self.owner_reference,
            self.slot_address,
            self.slot_version,
            self.refinement_level if self.refinement_level is not None else "NA",
            self.projected_cell if self.projected_cell is not None else "NA",
        )[:32]

    @property
    def pid(self) -> str:
        return "PID-" + digest(
            "OMEGA_PID",
            self.omega_bit_id,
            self.parent_omega_pid,
            self.owner_reference,
            self.slot_address,
            self.slot_version,
        )

    @property
    def lineage_sha256(self) -> str:
        return digest(
            "OMEGA_LINEAGE",
            self.pid,
            self.parent_omega_pid,
            self.parent_identity_sha256,
            self.source_state_receipt_sha256,
            self.owner_reference,
            self.slot_address,
            self.slot_version,
            self.geometry,
            self.floor,
            self.refinement_level if self.refinement_level is not None else "NA",
            self.projected_cell if self.projected_cell is not None else "NA",
        )

    @property
    def identity_sha256(self) -> str:
        return self.lineage_sha256

    @property
    def label(self) -> str:
        family = {
            GeometryFamily.CUBIC_6_APEX: "OMEGA_6",
            GeometryFamily.TETRA_12_DIRECTED: "OMEGA_12",
            GeometryFamily.SPHERE_PI_LIMIT: "OMEGA_PI",
        }[self.geometry]
        if self.geometry is GeometryFamily.SPHERE_PI_LIMIT:
            return f"{family}_F{self.floor}_L{self.refinement_level}_R{self.projected_cell}"
        return f"{family}_F{self.floor}"


def reversible_digital_projection(
    body: bytes,
    omega_keystring: bytes,
    view: str,
) -> bytes:
    """Self-inverse digital view transform; not a physical quantum-state clone."""

    if not omega_keystring:
        raise ValueError("Omega keystring cannot be empty")
    output = bytearray(len(body))
    at = 0
    counter = 0
    while at < len(body):
        view_bytes = view.encode("utf-8")
        stream = sha256(
            b"ASOLARIA-PATH3-DIGITAL-PROJECTION-V1\0"
            + len(omega_keystring).to_bytes(8, "big")
            + omega_keystring
            + len(view_bytes).to_bytes(8, "big")
            + view_bytes
            + counter.to_bytes(8, "big")
        ).digest()
        for byte in stream:
            if at >= len(body):
                break
            output[at] = body[at] ^ byte
            at += 1
        counter += 1
    return bytes(output)


@dataclass(frozen=True)
class Path3Projection:
    function_sha256: str
    signature_lineage_commitment_sha256: str
    omega_keystring_sha256: str
    source_pid: str
    target: NestedUniverseAddress
    geometry: GeometryFamily

    def __post_init__(self) -> None:
        for value in (
            self.function_sha256,
            self.signature_lineage_commitment_sha256,
            self.omega_keystring_sha256,
        ):
            if not _is_sha256(value):
                raise ValueError("Path-3 commitments must be full SHA-256 values")
        if not self.source_pid.startswith("PID-"):
            raise ValueError("Path-3 source must be PID-addressed")

    @property
    def identity_sha256(self) -> str:
        return digest(
            "PATH3_PROJECTION_V1",
            self.function_sha256,
            self.signature_lineage_commitment_sha256,
            self.omega_keystring_sha256,
            self.source_pid,
            self.target.address_id,
            self.geometry,
        )

    @property
    def pid(self) -> str:
        return "PID-" + self.identity_sha256

    @property
    def projection_id(self) -> str:
        return "PATH3-" + self.identity_sha256[:32]


@dataclass(frozen=True)
class PIDDagNode:
    """One content-addressed node in a reconstructable multi-parent PID DAG."""

    kind: str
    content_sha256: str
    owner_reference: str
    geometry: str
    floor: int
    generation: int
    parent_pids: tuple[str, ...] = ()
    parent_identity_sha256s: tuple[str, ...] = ()
    source_state_receipt_sha256: str = "0" * 64
    metadata_sha256: str = "0" * 64
    schema_version: str = "ASOLARIA_CONTENT_PID_DAG_V1"
    status: str = "PREPARED_NOT_EXECUTED"

    def __post_init__(self) -> None:
        if not self.kind or not self.owner_reference or not self.geometry or not self.schema_version:
            raise ValueError("PID DAG kind, owner, and geometry are required")
        if self.floor < 1 or self.generation < 0:
            raise ValueError("PID DAG floor must be positive and generation nonnegative")
        for value in (
            self.content_sha256,
            self.source_state_receipt_sha256,
            self.metadata_sha256,
        ):
            if not _is_sha256(value):
                raise ValueError("PID DAG digests must be full SHA-256 values")
        if len(self.parent_pids) != len(self.parent_identity_sha256s):
            raise ValueError("every parent PID requires exactly one identity hash")
        if len(set(self.parent_pids)) != len(self.parent_pids):
            raise ValueError("PID DAG parents must be unique")
        if any(not parent.startswith("PID-") for parent in self.parent_pids):
            raise ValueError("PID DAG parents must be PID-addressed")
        if any(not _is_sha256(value) for value in self.parent_identity_sha256s):
            raise ValueError("parent identities must be full SHA-256 values")
        if self.generation == 0 and self.parent_pids:
            raise ValueError("generation-zero PID DAG nodes cannot have parents")
        if self.generation > 0 and not self.parent_pids:
            raise ValueError("non-root PID DAG nodes require at least one parent")

    @property
    def identity_sha256(self) -> str:
        return digest(
            "PID_DAG_NODE_V1",
            self.kind,
            self.content_sha256,
            self.owner_reference,
            self.geometry,
            self.floor,
            self.generation,
            self.parent_pids,
            self.parent_identity_sha256s,
            self.source_state_receipt_sha256,
            self.metadata_sha256,
            self.schema_version,
            self.status,
        )

    @property
    def pid(self) -> str:
        return "PID-" + self.identity_sha256

    def parent_pairs(self) -> tuple[tuple[str, str], ...]:
        return tuple(zip(self.parent_pids, self.parent_identity_sha256s))


def verify_pid_dag(
    nodes: Sequence[PIDDagNode],
    external_identities: Mapping[str, str] | None = None,
) -> dict[str, int | str]:
    """Verify local parent resolution, hashes, generation ordering, and cycles."""

    if not nodes:
        raise ValueError("PID DAG cannot be empty")
    external = dict(external_identities or {})
    if any(not pid.startswith("PID-") or not _is_sha256(value) for pid, value in external.items()):
        raise ValueError("external PID identities must be full PID/SHA pairs")
    local: dict[str, PIDDagNode] = {}
    duplicate_pids = 0
    for node in nodes:
        if node.pid in local:
            duplicate_pids += 1
        local[node.pid] = node
    missing_parents = 0
    parent_hash_mismatches = 0
    generation_mismatches = 0
    parent_edges = 0
    for node in nodes:
        for parent_pid, parent_hash in node.parent_pairs():
            parent_edges += 1
            parent = local.get(parent_pid)
            if parent is None and parent_pid not in external:
                missing_parents += 1
                continue
            resolved_hash = parent.identity_sha256 if parent is not None else external[parent_pid]
            if resolved_hash != parent_hash:
                parent_hash_mismatches += 1
            if parent is not None and parent.generation >= node.generation:
                generation_mismatches += 1

    colors: dict[str, int] = {}
    cycle_edges = 0

    def visit(pid: str) -> None:
        nonlocal cycle_edges
        colors[pid] = 1
        for parent_pid in local[pid].parent_pids:
            if parent_pid not in local:
                continue
            if colors.get(parent_pid) == 1:
                cycle_edges += 1
            elif colors.get(parent_pid, 0) == 0:
                visit(parent_pid)
        colors[pid] = 2

    for pid in local:
        if colors.get(pid, 0) == 0:
            visit(pid)
    passed = not any(
        (
            duplicate_pids,
            missing_parents,
            parent_hash_mismatches,
            generation_mismatches,
            cycle_edges,
        )
    )
    return {
        "nodes": len(nodes),
        "roots": sum(node.generation == 0 for node in nodes),
        "parent_edges": parent_edges,
        "multi_parent_nodes": sum(len(node.parent_pids) > 1 for node in nodes),
        "external_parent_identities": len(external),
        "duplicate_pids": duplicate_pids,
        "missing_parents": missing_parents,
        "parent_hash_mismatches": parent_hash_mismatches,
        "generation_mismatches": generation_mismatches,
        "cycle_edges": cycle_edges,
        "reconstructable": int(passed),
        "status": "PASS" if passed else "FAIL",
    }


@dataclass(frozen=True)
class OmegaBinding:
    apex_body_pids: tuple[str, ...]
    omega_body_pid: str
    settled_epoch: int

    def __post_init__(self) -> None:
        if len(self.apex_body_pids) != 6 or len(set(self.apex_body_pids)) != 6:
            raise ValueError("Omega junction requires six distinct apex bodies")
        if self.settled_epoch < 0:
            raise ValueError("settled epoch must be nonnegative")

    @property
    def omega_gnn_pid(self) -> str:
        return "PID-" + digest(
            "OMEGA_GNN",
            self.apex_body_pids,
            self.omega_body_pid,
            self.settled_epoch,
        )

    def edge_rows(self) -> tuple[dict[str, object], ...]:
        rows: list[dict[str, object]] = []
        for apex in self.apex_body_pids:
            pair = "PAIR-" + digest("OMEGA", apex, self.omega_gnn_pid)[:32]
            rows.append(
                {
                    "pid": "PID-" + digest(
                        "OMEGA_EDGE",
                        pair,
                        apex,
                        self.omega_gnn_pid,
                        "OMEGA_FORWARD_FANIN",
                    ),
                    "identity_sha256": digest(
                        "OMEGA_EDGE",
                        pair,
                        apex,
                        self.omega_gnn_pid,
                        "OMEGA_FORWARD_FANIN",
                    ),
                    "parent_pid": apex,
                    "pair_id": pair,
                    "source_pid": apex,
                    "target_pid": self.omega_gnn_pid,
                    "relation": "OMEGA_FORWARD_FANIN",
                    "status": "PREPARED_NOT_INGESTED",
                }
            )
            rows.append(
                {
                    "pid": "PID-" + digest(
                        "OMEGA_EDGE",
                        pair,
                        self.omega_gnn_pid,
                        apex,
                        "OMEGA_REVERSE_GAIN_FANOUT",
                    ),
                    "identity_sha256": digest(
                        "OMEGA_EDGE",
                        pair,
                        self.omega_gnn_pid,
                        apex,
                        "OMEGA_REVERSE_GAIN_FANOUT",
                    ),
                    "parent_pid": self.omega_gnn_pid,
                    "pair_id": pair,
                    "source_pid": self.omega_gnn_pid,
                    "target_pid": apex,
                    "relation": "OMEGA_REVERSE_GAIN_FANOUT",
                    "status": "PREPARED_NOT_INGESTED",
                }
            )
        return tuple(rows)


def engine_promotion_gate(
    checks: Mapping[str, bool],
    seat_attestations: Mapping[str, str],
) -> dict[str, object]:
    required_checks = {
        "source_sha",
        "hbi_restore",
        "reversible_replay",
        "typed_routes",
        "collision_table",
        "authority_identity",
        "access_cosign",
        "runtime_ready",
        "claim_specific_proof",
    }
    checks_pass = required_checks <= checks.keys() and all(checks[name] for name in required_checks)
    seats_pass = all(seat_attestations.get(seat) == "PASS" for seat in ("ACER", "LIRIS", "RELIC"))
    active = checks_pass and seats_pass
    return {
        "checks_pass": int(checks_pass),
        "trilateral_pass": int(seats_pass),
        "active_engine": int(active),
        "status": "ACTIVE" if active else "HELD",
    }
