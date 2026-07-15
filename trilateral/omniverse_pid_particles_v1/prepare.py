"""Build and verify the Asolaria Floor-1 trilateral cold-preparation packet.

The packet binds the metatagging origin, the existing v3 PRs, the pinned CDC
source, and the measured 34-body LIRIS cube formation.  It prepares typed
scan/training/GNN/reverse-gain/Omega routes but never fires them.
"""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .model import (
    CatalogEvent,
    EdgeProposal,
    GeometryFamily,
    NativeGlyphLanguageWitness,
    NodeDescriptor,
    NestedUniverseAddress,
    OmegaBinding,
    OmegaCoordinate,
    PIDDagNode,
    Path3Projection,
    Response,
    RouteSelector,
    StorageClass,
    SELF_IMPROVING_FUNCTION_FAMILIES,
    cube_edges,
    cube_face_cycles,
    digest,
    engine_promotion_gate,
    hypercube_counts,
    omega_hierarchy,
    paired_learning_edges,
    reversible_digital_projection,
    sphere_projection_window,
    sphere_refinement,
    supervisor_collision_table,
    tetra_edges,
    tetra_face_cycles,
    verify_cycle_double_cover,
    verify_pid_dag,
)


SCHEMA = "ASOLARIA-SIMULATED-UNIVERSE-FLOOR1-TRILATERAL-PREP-V1"
TARGET_REPO = "JesseBrown1980/Metatagging-data-for-a-Quantum-universe"
TARGET_BASE = "c19c74325d6b075da8aed624c81f46e79cefb739"
TARGET_TREE = "91e00a3982426babfbebb9543416e196de9a50fe"
PR3_HEAD = "83368e40ac67c513c5c873feeff903df10935db4"
PR4_HEAD = "93dcf9ef71163554b16ed147903a87a2491647bf"
CDC_REPO = "openai/cdc-lean"
CDC_COMMIT = "577e9d9ea326d520f80672ee69b830bf1d513df5"
CDC_TREE = "54828f5060c272946b2e1a81e94e8e795fdd29d2"
CDC_GROUP_SHA = "1c632bc526ca991584b6854cf6e12ffaa633055b3db47968214f3753d223931f"
CDC_GROUP_HBI_SHA = "8f3f43e658961999d7491bb832e31a1296fe44430a29a6edf4a11a1659e5c7a3"
CDC_CONTRACT_SHA = "0085b73a7bb0b009385446eb371809e50f5b9a8d96615de867a006ac59b223c2"
CDC_FORMATION_RESULT_SHA = "8f4f4be4a83fb2a385e7c0b5b6cecf9fd07f8ec3e358a3c68242f78eccfe84c3"
CDC_FORMATION_ROOT = "851c2ec0649c746659fdac38fab83dbe2bb5496e0beb080affeca0178d401fdb"
CDC_BODY_WITNESS_SOURCE_ROOT = "e8dcae7cc8555bd257b2ec3e77d7f8e07512a2b57cd69f7789636c0a3acd422e"
OMEGA_BODY_LEAF = "c96b29ed0d01c93e64d7b9883e9ab89ad2fc3a09118577dc20c3b188d1456012"
APEX_BODY_LEAVES = (
    "ebd460da71715255d05e8e79baf56502422bef6d6592e7809f4f516220cc4d15",
    "cffc7eb2396879fe835755c0a0c77cdafb2c65d2375c79823d6ef75bb7831552",
    "2879a3747369fe6e46990e5d8161428a6e695ade4b5ac5ce19bd174ef4b638c3",
    "c739520e6e8eeb45ca835e3cdbca45b84a6bf828d0c2aac1675c6ab41b02e083",
    "d1808ffdb864c806b4cd784179e4d2647ebe6a32b7c13047caf6bed210ed419d",
    "e040dc0c17d3d525b02b37ff40941854d25bd0c28c4dc67672dc343bf7ed63c1",
)
APEX_FACES = ("+R", "-R", "+N", "-N", "+Q", "-Q")

HBP_NAME = "ASOLARIA-FLOOR1-TRILATERAL-PREPARATION-20260715.hbp"
HBI_NAME = "ASOLARIA-FLOOR1-TRILATERAL-PREPARATION-20260715.hbi"
HEX_NAME = HBP_NAME + ".hex"
SUMS_NAME = "SHA256SUMS"


class PreparationError(RuntimeError):
    pass


def sha256_bytes(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe(value: object) -> str:
    if isinstance(value, bool):
        value = int(value)
    text = str(value)
    if any(mark in text for mark in ("|", "\r", "\n")):
        raise PreparationError(f"reserved HBP character in {text!r}")
    return text


def row(tag: str, **fields: object) -> str:
    return "|".join([tag, *(f"{key}={_safe(value)}" for key, value in fields.items()), "json=0"])


def parse_fields(line: str) -> tuple[str, dict[str, str]]:
    parts = line.split("|")
    fields: dict[str, str] = {}
    for item in parts[1:]:
        if "=" not in item:
            raise PreparationError(f"malformed HBP field: {line[:120]}")
        key, value = item.split("=", 1)
        if key in fields:
            raise PreparationError(f"duplicate HBP field {key}")
        fields[key] = value
    if fields.get("json") != "0":
        raise PreparationError("every hot-path row must end in json=0")
    return parts[0], fields


def atomic_write(path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    temporary.write_bytes(body)
    os.replace(temporary, path)


def write_lf(path: Path, lines: Iterable[str]) -> None:
    body = ("\n".join(lines) + "\n").encode("utf-8")
    if b"\r" in body:
        raise PreparationError(f"CR forbidden in {path}")
    atomic_write(path, body)


def write_sidecar(path: Path) -> Path:
    sidecar = path.with_name(path.name + ".sha256")
    write_lf(sidecar, [f"{sha256_file(path)}  {path.name}"])
    return sidecar


def selector(language: str, face: str, temporal_slice: str) -> RouteSelector:
    seed = hashlib.sha256(f"{language}|{face}|{temporal_slice}".encode()).digest()
    axes = tuple(((seed[index % len(seed)] << 2) + index) % 1024 for index in range(60))
    return RouteSelector(
        axes_60d=axes,
        glyph_family="BEHCS-1024",
        glyph_levels=("BEHCS-256", "BEHCS-1024", "HYPERBEHCS-60D+"),
        language=language,
        executor="CUBE_PID_ENGINE_CANDIDATE",
        pipe="HOOKWALL_GNN_REVERSE_GAIN_OMEGA",
        operation="ASOLARIA_FLOOR1_TRAIN",
        room=f"OMEGA-HOTEL-{face}",
        proof_tier="MEASURED_LIRIS_LOCAL",
        runtime_mode="E0_COLD_PREPARATION",
        colony="ASOLARIA",
        seat="LIRIS",
        temporal_slice=temporal_slice,
    )


def build_nodes() -> tuple[tuple[NodeDescriptor, ...], NodeDescriptor, OmegaBinding]:
    apex: list[NodeDescriptor] = []
    for index, (face, content_sha) in enumerate(zip(APEX_FACES, APEX_BODY_LEAVES)):
        apex.append(
            NodeDescriptor(
                geometry=GeometryFamily.CUBIC_6_APEX,
                address=(index,),
                generation=1,
                content_sha256=content_sha,
                parent_pid="PID-CDCLEAN-CUBIC-FLOOR1",
                owner_reference="APEX-HUMAN-JESSE",
                selector=selector("HYPERBEHCS", face, "CDC-FLOOR1-SETTLED-EPOCH-10"),
                storage=StorageClass.GITRAM_STUB,
                logical_tick_us=index,
                feedback_delay_us=1,
                body_kind="TRAINED_APEX_OMNIBIT",
            )
        )
    omega = NodeDescriptor(
        geometry=GeometryFamily.CUBIC_6_APEX,
        address=(6,),
        generation=2,
        content_sha256=OMEGA_BODY_LEAF,
        parent_pid="PID-CDCLEAN-SIX-OF-SIX-APEX",
        owner_reference="APEX-HUMAN-JESSE",
        selector=selector("OMNISHANNON", "OMEGA", "CDC-FLOOR1-SETTLED-EPOCH-10"),
        storage=StorageClass.GITRAM_STUB,
        logical_tick_us=10,
        feedback_delay_us=1,
        body_kind="TRAINED_OMEGA_OMNIBIT",
    )
    binding = OmegaBinding(tuple(item.pid for item in apex), omega.pid, settled_epoch=10)
    return tuple(apex), omega, binding


def verify_cdc_group_receipt(path: Path) -> tuple[NativeGlyphLanguageWitness, ...]:
    if not path.is_file():
        raise PreparationError(f"CDC group receipt missing: {path}")
    if sha256_file(path) != CDC_GROUP_SHA:
        raise PreparationError("CDC group receipt SHA-256 mismatch")
    body = path.read_bytes()
    if b"\r" in body:
        raise PreparationError("CDC group receipt must be LF-only")
    lines = body.decode("utf-8").splitlines()
    parsed = [parse_fields(line) for line in lines]
    headers = [fields for tag, fields in parsed if tag == "PAISGROUPHDR"]
    footers = [fields for tag, fields in parsed if tag == "PAISGROUPFTR"]
    formations = [fields for tag, fields in parsed if tag == "FORMATIONREF"]
    base_refs = [fields for tag, fields in parsed if tag == "BASEBODYREF"]
    if len(headers) != 1 or len(footers) != 1 or len(formations) != 1:
        raise PreparationError("CDC group receipt cardinality mismatch")
    header, footer, formation = headers[0], footers[0], formations[0]
    expected = {
        "trained_bodies": "34",
        "cells_total": "27200",
        "representation": "CUBIC_C2^3",
        "contract_sha256": CDC_CONTRACT_SHA,
        "tree": CDC_TREE,
    }
    if any(header.get(key) != value for key, value in expected.items()):
        raise PreparationError("CDC group header invariant mismatch")
    if footer.get("trained_bodies") != "34_of_34" or footer.get("status") != "PASS":
        raise PreparationError("CDC group footer invariant mismatch")
    if formation.get("result_sha256") != CDC_FORMATION_RESULT_SHA:
        raise PreparationError("CDC formation result mismatch")
    if formation.get("formation_root_sha256") != CDC_FORMATION_ROOT:
        raise PreparationError("CDC formation root mismatch")
    if len(base_refs) != 27:
        raise PreparationError("CDC group must expose exactly 27 ordered base-body references")
    source_items: list[tuple[str, int, str, str]] = []
    for ordinal, item in enumerate(base_refs, 1):
        if (
            item.get("ord") != str(ordinal)
            or item.get("restore") != "1"
            or not item.get("body_leaf_sha256")
            or not item.get("receipt_sha256")
        ):
            raise PreparationError(f"CDC base-body witness mismatch at ordinal {ordinal}")
        source_items.append(
            (
                "BASE",
                ordinal,
                item["body_leaf_sha256"],
                item["receipt_sha256"],
            )
        )
    source_items.extend(
        ("APEX", ordinal, leaf, CDC_FORMATION_RESULT_SHA)
        for ordinal, leaf in enumerate(APEX_BODY_LEAVES, 1)
    )
    source_items.append(("OMEGA", 1, OMEGA_BODY_LEAF, CDC_FORMATION_RESULT_SHA))
    source_root = digest("CDC_BODY_WITNESS_SOURCE_SET_V1", tuple(source_items))
    if source_root != CDC_BODY_WITNESS_SOURCE_ROOT:
        raise PreparationError("CDC 34-body native-language witness source set changed")
    witnesses = tuple(
        NativeGlyphLanguageWitness(
            body_kind=kind,
            body_ordinal=ordinal,
            body_leaf_sha256=body_leaf,
            body_receipt_sha256=body_receipt,
            formation_receipt_sha256=CDC_GROUP_SHA,
            evidence_class="OPERATOR_OBSERVED",
            owning_catalog_import="PENDING_CURRENT_34_CATALOG_CITATION",
        )
        for kind, ordinal, body_leaf, body_receipt in source_items
    )
    if len({item.body_pid for item in witnesses}) != 34 or len(
        {item.native_language_pid for item in witnesses}
    ) != 34:
        raise PreparationError("CDC native-language witness identities are not 34 distinct objects")
    return witnesses


def build_rows(
    language_witnesses: Sequence[NativeGlyphLanguageWitness],
) -> list[str]:
    here = Path(__file__).resolve().parent
    apex, omega, binding = build_nodes()
    cube_cover = verify_cycle_double_cover(cube_edges(), cube_face_cycles())
    tetra_cover = verify_cycle_double_cover(tetra_edges(), tetra_face_cycles())
    sphere = sphere_refinement(4)
    hierarchy = omega_hierarchy(4)
    q3 = hypercube_counts(3)
    q6 = hypercube_counts(6)
    sphere_window = sphere_projection_window(4, 0, 16)
    owner_reference = "APEX-HUMAN-JESSE"
    null_origin = PIDDagNode(
        kind="NULL_ORIGIN_SEED",
        content_sha256=sha256_bytes(b""),
        owner_reference=owner_reference,
        geometry="DIGITAL_EMPTY_SEED",
        floor=1,
        generation=0,
        source_state_receipt_sha256=sha256_bytes(b"JESSE_DANIEL_BROWN_OPERATOR_DESIGN_2026-07-15"),
        metadata_sha256=sha256_bytes(b"EXPLICIT_EMPTY_BYTES_NOT_UNNAMED_MAGIC_ROOT"),
        status="OPERATOR_DESIGN_DIGITAL_SEED",
    )
    omega_namespace_root = PIDDagNode(
        kind="OMEGA_NAMESPACE_ROOT",
        content_sha256=sha256_bytes(f"{TARGET_REPO}@{TARGET_BASE}".encode("utf-8")),
        owner_reference=owner_reference,
        geometry="OMEGA_NAMESPACE",
        floor=1,
        generation=1,
        parent_pids=(null_origin.pid,),
        parent_identity_sha256s=(null_origin.identity_sha256,),
        source_state_receipt_sha256=sha256_bytes(TARGET_TREE.encode("ascii")),
        metadata_sha256=sha256_bytes(b"OMEGA_NAMESPACE_ROOT_V1"),
    )
    omega_pi = OmegaCoordinate(
        GeometryFamily.SPHERE_PI_LIMIT,
        1,
        parent_omega_pid=omega_namespace_root.pid,
        parent_identity_sha256=omega_namespace_root.identity_sha256,
        source_state_receipt_sha256=sha256_bytes(b"OMEGA_PI_L4_R0_DESIGN_SOURCE"),
        owner_reference=owner_reference,
        slot_address="PI/F1/L4/R0",
        slot_version=1,
        refinement_level=4,
        projected_cell=0,
    )
    omega_12 = OmegaCoordinate(
        GeometryFamily.TETRA_12_DIRECTED,
        1,
        parent_omega_pid=omega_pi.pid,
        parent_identity_sha256=omega_pi.identity_sha256,
        source_state_receipt_sha256=omega_pi.source_state_receipt_sha256,
        owner_reference=owner_reference,
        slot_address="TETRA12/F1/OMEGA",
        slot_version=1,
    )
    omega_6_floor3 = OmegaCoordinate(
        GeometryFamily.CUBIC_6_APEX,
        3,
        parent_omega_pid=omega_12.pid,
        parent_identity_sha256=omega_12.identity_sha256,
        source_state_receipt_sha256=omega_12.source_state_receipt_sha256,
        owner_reference=owner_reference,
        slot_address="Q3/OMEGA6/F3",
        slot_version=1,
    )
    omega_6_floor2 = OmegaCoordinate(
        GeometryFamily.CUBIC_6_APEX,
        2,
        parent_omega_pid=omega_6_floor3.pid,
        parent_identity_sha256=omega_6_floor3.identity_sha256,
        source_state_receipt_sha256=omega_6_floor3.source_state_receipt_sha256,
        owner_reference=owner_reference,
        slot_address="Q3/OMEGA6/F2",
        slot_version=1,
    )
    omega_6_floor1 = OmegaCoordinate(
        GeometryFamily.CUBIC_6_APEX,
        1,
        parent_omega_pid=omega_6_floor2.pid,
        parent_identity_sha256=omega_6_floor2.identity_sha256,
        source_state_receipt_sha256=CDC_GROUP_SHA,
        owner_reference=owner_reference,
        slot_address="Q3/OMEGA6/F1",
        slot_version=1,
    )
    omega_coordinates = (
        omega_6_floor1,
        omega_6_floor2,
        omega_6_floor3,
        omega_12,
        omega_pi,
    )
    if len(language_witnesses) != 34:
        raise PreparationError("native-language witness population must be exactly 34 bodies")
    witness_source_items = tuple(
        (
            item.body_kind,
            item.body_ordinal,
            item.body_leaf_sha256,
            item.body_receipt_sha256,
        )
        for item in language_witnesses
    )
    witness_source_root = digest(
        "CDC_BODY_WITNESS_SOURCE_SET_V1", witness_source_items
    )
    if witness_source_root != CDC_BODY_WITNESS_SOURCE_ROOT:
        raise PreparationError("native-language witness source root changed before row emission")
    witness_identity_root = digest(
        "NATIVE_GLYPH_LANGUAGE_WITNESS_SET_V1",
        tuple(item.identity_sha256 for item in language_witnesses),
    )
    rows = [
        row(
            "FLOOR1PREPHDR",
            schema=SCHEMA,
            authority="OPERATOR_REQUEST_JESSE_DANIEL_BROWN_2026-07-15",
            seat="LIRIS",
            scope="FULL_ASOLARIA_NEURAL_NETWORK_MATRIX_FABRIC_FLOOR1",
            hot_path="HBP_HBI_SHA_HEX",
            mode="COLD_TRILATERAL_PREPARATION",
            process_launch=0,
            fabric_write=0,
            usb_write=0,
            github_write=0,
        ),
        row(
            "SYSTEMFRAME",
            metatag_repo_role="FOUNDATION_GRID_AND_PARTICLE_ADDRESS_ONTOLOGY",
            asolaria_role="NEURAL_NETWORK_MATRIX_AND_FABRIC",
            cube_role="TRAINED_REVERSIBLE_PID_ENGINE_CANDIDATE",
            class_="OPERATOR_CANON",
        ),
        row(
            "DOCTRINEPIN",
            file="TRILATERAL-PHYSICS-AND-COMPUTATION-EVIDENCE-2026-07-11.md",
            base_commit=TARGET_BASE,
            no_deflate=1,
            no_inflate=1,
        ),
        row(
            "AUTHORITYREF",
            layer="HUMAN_APEX",
            ordinal="NA",
            name="APEX-HUMAN-JESSE",
            reference_kind="ROLE_REFERENCE",
            human_reference="HUMAN-1",
            content_pid="NONE",
            identity_status="ROLE_REFERENCE_NOT_AUTOMATICALLY_A_PID",
            quintet_member=0,
            can_sign=0,
            can_parent=0,
            claims_final_apex=0,
            authority_effect="REFERENCE_ONLY_NO_FIRE",
        ),
        row(
            "AUTHORITYREF",
            layer="SPECIAL_OPERATOR",
            ordinal="00",
            name="SPECIAL-OP-JESSE",
            reference_kind="SEAT_REFERENCE",
            content_pid="NONE",
            identity_status="NAMED_SEAT_REFERENCE",
            quintet_member=0,
            can_sign=0,
            can_parent=0,
            claims_final_apex=0,
            authority_effect="REFERENCE_ONLY_NO_FIRE",
        ),
        row(
            "AUTHORITYREF",
            layer="OPERATOR",
            ordinal="01",
            name="OP-JESSE",
            reference_kind="SEAT_REFERENCE",
            content_pid="NONE",
            identity_status="NAMED_SEAT_REFERENCE",
            quintet_member=1,
            can_sign=0,
            can_parent=0,
            claims_final_apex=0,
            authority_effect="REFERENCE_ONLY_NO_FIRE",
        ),
        row(
            "AUTHORITYREF",
            layer="OPERATOR",
            ordinal="02",
            name="OP-RAYSSA",
            reference_kind="SEAT_REFERENCE",
            content_pid="NONE",
            identity_status="NAMED_SEAT_REFERENCE",
            quintet_member=1,
            can_sign=0,
            can_parent=0,
            claims_final_apex=0,
            authority_effect="REFERENCE_ONLY_NO_FIRE",
        ),
        row(
            "AUTHORITYREF",
            layer="OPERATOR",
            ordinal="03",
            name="OP-FELIPE",
            reference_kind="SEAT_REFERENCE",
            content_pid="NONE",
            identity_status="NAMED_SEAT_REFERENCE",
            quintet_member=1,
            can_sign=0,
            can_parent=0,
            claims_final_apex=0,
            authority_effect="REFERENCE_ONLY_NO_FIRE",
        ),
        row(
            "AUTHORITYREF",
            layer="OPERATOR",
            ordinal="04",
            name="OP-DAN",
            reference_kind="SEAT_REFERENCE",
            content_pid="NONE",
            identity_status="NAMED_SEAT_REFERENCE",
            quintet_member=1,
            can_sign=0,
            can_parent=0,
            claims_final_apex=0,
            authority_effect="REFERENCE_ONLY_NO_FIRE",
        ),
        row(
            "AUTHORITYREF",
            layer="OPERATOR",
            ordinal="05",
            name="OP-AMY",
            reference_kind="SEAT_REFERENCE",
            content_pid="NONE",
            identity_status="NAMED_SEAT_REFERENCE",
            quintet_member=1,
            can_sign=0,
            can_parent=0,
            claims_final_apex=0,
            authority_effect="REFERENCE_ONLY_NO_FIRE",
        ),
        row(
            "AUTHORITYREF",
            layer="SELF_REFLECT",
            ordinal="NA",
            name="AUTO_SELF_REFLECT_LEVELS",
            reference_kind="ROLE_REFERENCE",
            content_pid="NONE",
            identity_status="UNRESOLVED_OWNING_PID_REQUIRED",
            quintet_member=0,
            can_sign=0,
            can_parent=0,
            claims_final_apex=0,
            authority_effect="REFERENCE_ONLY_NO_FIRE",
        ),
        row(
            "AUTHORITYREF",
            layer="FINAL_APEX_AUTHORITY",
            ordinal="NA",
            name="JESSE",
            reference_kind="ROLE_REFERENCE",
            content_pid="NONE",
            identity_status="UNRESOLVED_OWNING_AUTHORITY_RECEIPT_REQUIRED",
            quintet_member=0,
            can_sign=0,
            can_parent=0,
            claims_final_apex=0,
            authority_effect="REFERENCE_ONLY_NO_FIRE",
        ),
        row(
            "AUTHORITYSET",
            name="OP_QUINTET",
            members="OP-JESSE,OP-RAYSSA,OP-FELIPE,OP-DAN,OP-AMY",
            member_count=5,
            separate_member_references=5,
            composite_content_pid="NONE",
            collapsed_into_operator_ownership=0,
            authority_effect="REFERENCE_ONLY_NO_FIRE",
        ),
        row(
            "AUTHORITYGATE",
            reference_rows=9,
            distinct_labels=9,
            content_pids=0,
            shared_content_pid_collisions=0,
            role_strings_as_content_pids=0,
            unresolved_signers=0,
            unresolved_parents=0,
            self_reflect_claims_final_apex=0,
            quintet_seats="5_OF_5",
            quintet_collapsed_into_operator_ownership=0,
            status="PASS",
            authority_effect="REFERENCE_VALIDATION_ONLY_NO_FIRE",
        ),
        row("SOURCEPIN", role="TARGET_BASE", repo=TARGET_REPO, commit=TARGET_BASE, tree=TARGET_TREE, evidence="MEASURED_GITHUB"),
        row("SOURCEPIN", role="C2_CUBED_ORBIT_OMEGA_PR3", repo=TARGET_REPO, commit=PR3_HEAD, state="OPEN_DRAFT", evidence="MEASURED_GITHUB"),
        row("SOURCEPIN", role="LIRIS_OMEGA_REVERSIBILITY_PR4", repo=TARGET_REPO, commit=PR4_HEAD, state="OPEN_DRAFT", evidence="MEASURED_GITHUB"),
        row("SOURCEPIN", role="CDC_SOURCE", repo=CDC_REPO, commit=CDC_COMMIT, tree=CDC_TREE, theorem="SOURCE_CARRIED", liris_kernel_check="NOT_RUN"),
        row(
            "LOCALCUBEEVIDENCE",
            group_result_sha256=CDC_GROUP_SHA,
            group_hbi_sha256=CDC_GROUP_HBI_SHA,
            contract_sha256=CDC_CONTRACT_SHA,
            formation_result_sha256=CDC_FORMATION_RESULT_SHA,
            formation_root_sha256=CDC_FORMATION_ROOT,
            bodies=34,
            cells=27200,
            scoped_models=2720,
            byte_observations=288932800,
            final_model_local_relations=8369168,
            external_gnn_calls=0,
            external_gnn_edges=0,
            evidence="MEASURED_LIRIS_LOCAL",
        ),
        row(
            "CAPABILITYEVIDENCE",
            capability="DESCENDANT_CUBES_DERIVED_CORRECT_UNSEEN_INFORMATION",
            result_status="EXISTING_OPERATOR_OBSERVED_RESULT",
            evidence="OPERATOR_OBSERVED_CLAUDE_REPORTED",
            observed_date="2026-07-14",
            owning_receipt_import="PENDING_ACER_OR_CLAUDE_HBP_HBI_SHA",
            repeat_experiment_required=0,
            independent_liris_receipt_audit="COMPLETE_EXACT_SEMANTIC_QA_RECEIPT_NOT_LOCATED",
            closest_liris_receipt_sha256="cce058b6f0812d5bfede3f6a94d17c9e3d3fbc7a923666167418c9eef80a6c15",
            closest_liris_scope="HELDOUT_COMPRESSION_NOT_SEMANTIC_QA",
            folded_into_34_body_training_count=0,
            no_downgrade_from_missing_liris_copy=1,
        ),
        row(
            "CAPABILITYEVIDENCE",
            capability="MULTIPLE_AND_IMPROVING_TYPES_OF_SELF_IMPROVING_FUNCTIONS",
            result_status="EXISTING_OPERATOR_OBSERVED_RESULT",
            evidence="OPERATOR_OBSERVED",
            function_families="LANGUAGE_GENESIS,LEARNER,GENERATOR,EVALUATOR,SELECTOR_PROMOTION,REVERSE_GAIN,REPLAY_ROLLBACK,OMEGA_SYNTHESIS,TRANSLATION_ALIGNMENT,PID_LINEAGE",
            ecosystem_order="LANGUAGE_CREATION,LEARNING,GENERATION,EVALUATION,SELECTION,REVERSE_GAIN_CORRECTION,REPLAY_ROLLBACK,OMEGA_SYNTHESIS,CROSS_LANGUAGE_ALIGNMENT,PID_LINEAGE",
            improvement_criterion="EVAL_HELDOUT_CHILD_MINUS_EVAL_HELDOUT_PARENT_GT_0",
            pre_child_commitments="HELDOUT_SET_SHA256,EVALUATOR_SHA256",
            heldout_set_unchanged="REQUIRED",
            leakage_audit="REQUIRED",
            evaluator_version="REQUIRED",
            parent_child_pids="REQUIRED",
            stochastic_evaluation_receipt="SEEDS,REPEATED_TRIALS,CONFIDENCE_BOUNDS",
            noise_gate="DELTA_EXCEEDS_MEASUREMENT_NOISE",
            parent_lineage_required=1,
            reverse_replay_required=1,
            rollback_state="REQUIRED",
            owning_receipt_import="PENDING_EXACT_IMPROVEMENT_LINEAGE_RECEIPTS",
            repeat_experiment_required=0,
            independent_liris_receipt_audit="SCOPED_MECHANISM_RECEIPTS_LOCATED_NOT_FULL_ECOSYSTEM",
            recurrence_receipt_sha256="22136de15bbeab9f38c60bec88ce5f3a4a866dfe76c7b630e2f9a13a569e9a5d",
            recurrence_scope="49_OF_49_SPECIALIZATION_IMPROVED_DISJOINT_HOLDOUT_DEGRADED_8.16559_PERCENT",
            folded_into_34_body_training_count=0,
            no_downgrade_from_missing_liris_copy=1,
        ),
        row(
            "CAPABILITYEVIDENCE",
            capability="PER_CUBE_CREATED_GLYPH_LANGUAGE_NOT_ENGLISH_NATIVE",
            result_status="EXISTING_OPERATOR_OBSERVED_RESULT",
            evidence="OPERATOR_OBSERVED",
            scope="OPERATOR_REPORTED_CUBE_POPULATION",
            per_cube_language=1,
            native_representation="CREATED_GLYPHS",
            native_catalog_binding="PER_CUBE_PID_BOUND",
            native_catalog_contents="GLYPH_VOCABULARY,RELATIONAL_MEANINGS,LEARNED_STATE,QUESTIONS,ERRORS,IDEAS,MESSAGES",
            english_role="OPERATOR_FACING_TRANSLATION_LAYER",
            distinct_viewpoint_preserved=1,
            translation_receipts="FORWARD_AND_REVERSE",
            typed_adapter_erases_native_language=0,
            language_generation_revision_pid_trace=1,
            omega_cross_language_role="COMMUNICATION_AND_AGGREGATION",
            emergent_symbolic_communication="CONDITIONAL_ON_UNFAMILIAR_COMPOSITION_AND_REVERSIBLE_TRANSLATION_RECEIPT",
            custom_encoding_only="NOT_ASSUMED",
            symbol_substitution_only="REJECT",
            novel_compositional_glyph_messages="REQUIRED",
            reversible_native_omega_translation="REQUIRED",
            cross_cube_meaning_preservation="REQUIRED",
            native_language_retained_after_alignment="REQUIRED",
            measured_github_receipt="HYPER-BECHS--the-third-set_PR28_FIRST-FLOOR-RESULT.hbp",
            measured_github_hbp_sha256="e6776b192ca432988e82ed3ae71f30983254c60a6deb6e5252e45933c03564bd",
            measured_github_hbi_sha256="adfdae1cf46979ad869cd67f6c8abf1ded956099a4e9d035e7e77adf7bf50650",
            measured_github_cube_languages="27_DISTINCT_OF_27",
            measured_github_learned_catalog_relations=356,
            measured_github_training_decisions=810,
            measured_github_restore="27_OF_27",
            measured_github_production_gnn_calls=0,
            measured_github_scope="PRIOR_GLYPH_HYPERSTACK_NOT_CURRENT_34_CDC_BODIES",
            owning_receipt_import="PENDING_CURRENT_34_CATALOG_CITATION",
            repeat_experiment_required=0,
            independent_liris_receipt_audit="PRIOR_27_LANGUAGE_RECEIPT_VERIFIED_CURRENT_34_PENDING",
            folded_into_34_body_training_count=0,
            no_downgrade_from_missing_liris_copy=1,
        ),
        *(
            row(
                "NATIVEGLYPHWITNESS",
                ordinal=ordinal,
                body_kind=item.body_kind,
                body_ordinal=item.body_ordinal,
                body_pid=item.body_pid,
                native_language_pid=item.native_language_pid,
                witness_pid=item.pid,
                identity_sha256=item.identity_sha256,
                body_leaf_sha256=item.body_leaf_sha256,
                body_receipt_sha256=item.body_receipt_sha256,
                formation_receipt_sha256=item.formation_receipt_sha256,
                evidence=item.evidence_class,
                owning_catalog_import=item.owning_catalog_import,
                native_catalog_sha256=item.native_catalog_sha256 or "NONE",
                semantic_evaluation="NOT_IMPORTED",
                claim_boundary="WITNESS_IDENTITY_NOT_FIVE_GATE_SEMANTIC_PROOF",
            )
            for ordinal, item in enumerate(language_witnesses, 1)
        ),
        row(
            "NATIVEGLYPHGATE",
            witness_objects="34_OF_34",
            base_bodies="27_OF_27",
            apex_bodies="6_OF_6",
            omega_bodies="1_OF_1",
            distinct_body_pids=34,
            distinct_native_language_pids=34,
            source_set_sha256=witness_source_root,
            witness_set_sha256=witness_identity_root,
            measured_catalog_imports=0,
            pending_catalog_imports=34,
            semantic_evaluations="0_OF_34",
            operator_observed_population="34_OF_34",
            measured_github_prior_population="27_DISTINCT_LANGUAGES_356_RELATIONS",
            status="OPERATOR_OBSERVED_WITNESSES_PENDING_OWNING_CATALOG_BYTES",
        ),
        row(
            "IMPROVEMENTAUDITSCHEMA",
            schema="ASOLARIA_IMPROVEMENT_CLAIM_V1",
            function_families=",".join(SELF_IMPROVING_FUNCTION_FAMILIES),
            precommit_fields="PARENT_PID,HELDOUT_SET_SHA256,EVALUATOR_SHA256,EVALUATOR_VERSION,COMMITTED_TICK_US",
            ordering="PRECOMMIT_TICK_LT_CHILD_CREATED_TICK_LE_CHILD_EVALUATED_TICK",
            evaluation_fields="SUBJECT_PID,SCORE_PPM,TRIAL_SCORES_PPM,SEEDS,CONFIDENCE_LOW_PPM,CONFIDENCE_HIGH_PPM,EVALUATED_TICK_US",
            fixed_inputs="PARENT_AND_CHILD_MATCH_PRECOMMITTED_HELDOUT_EVALUATOR_VERSION",
            stochastic_gate="REPEATED_TRIALS_UNIQUE_SEED_PER_TRIAL_EQUAL_TRIAL_COUNTS",
            acceptance="DELTA_GT_0_AND_DELTA_GT_NOISE_AND_CHILD_CI_LOW_GT_PARENT_CI_HIGH",
            evidence_gates="LEAKAGE_AUDIT,LINEAGE_RECEIPT,REVERSE_REPLAY,ROLLBACK_STATE",
            materialized_precommits=0,
            materialized_claims=0,
            historical_import="PENDING_EXACT_OWNING_RECEIPTS",
            status="DESIGN_SCHEMA_READY_NO_IMPROVEMENT_CLAIM_IMPORTED",
        ),
        row(
            "GLYPHLANGUAGEAUDITSCHEMA",
            schema="ASOLARIA_GLYPH_LANGUAGE_EVALUATION_V1",
            independent_tests="BEYOND_SYMBOL_SUBSTITUTION,NOVEL_COMPOSITION,REVERSIBLE_NATIVE_OMEGA,CROSS_CUBE_MEANING,NATIVE_LANGUAGE_RETAINED",
            required_receipts="TRAINING_CORPUS,ABSENCE_AUDIT,FORWARD_TRANSLATION,REVERSE_TRANSLATION,CROSS_CUBE_ALIGNMENT",
            materialized_evaluations=0,
            witness_objects=34,
            historical_catalog_import="PENDING_EXACT_OWNING_RECEIPTS",
            status="DESIGN_SCHEMA_READY_NO_SEMANTIC_EVALUATION_IMPORTED",
        ),
        row(
            "FLOORTRANSITION",
            completed="CDC_CUBIC_FLOOR1_34_OF_34",
            next="ASOLARIA_SELF_SCAN_AND_CUBE_FLOOR1",
            automatic_authority_transfer=0,
            status="PREPARED",
        ),
        row(
            "GEOMETRY",
            family="CUBIC_6_APEX",
            graph="Q3",
            signed_apex_directions=6,
            is_q6=0,
            vertices=8,
            undirected_edges=12,
            directed_edges=24,
            face_cycles=6,
            cdc_counted_memberships=cube_cover["cycle_memberships"],
            cdc_fixture=cube_cover["status"],
        ),
        row(
            "DIMENSIONBOUNDARY",
            six_apex_geometry="SIX_SIGNED_FACE_DIRECTIONS_AROUND_Q3",
            q3_vertices=q3["vertices"],
            q3_undirected_edges=q3["undirected_edges"],
            q6_vertices=q6["vertices"],
            q6_undirected_edges=q6["undirected_edges"],
            conflated=0,
        ),
        row(
            "GEOMETRY",
            family="TETRA_12_DIRECTED",
            vertices=4,
            undirected_edges=6,
            directed_edges=12,
            triangular_faces=4,
            cdc_counted_memberships=tetra_cover["cycle_memberships"],
            cdc_fixture=tetra_cover["status"],
            training="HELD_NEW_GEOMETRY_COHORT",
        ),
        row(
            "GEOMETRY",
            family="SPHERE_PI_LIMIT",
            refinement_level=sphere["level"],
            vertices=sphere["vertices"],
            edges=sphere["edges"],
            directed_edges=sphere["directed_edges"],
            triangular_faces=sphere["triangular_faces"],
            euler=sphere["euler_characteristic"],
            pi_role=sphere["pi_role"],
            continuum_convergence="PROOF_REQUIRED",
        ),
        row(
            "SPHEREWINDOW",
            refinement_level=4,
            start=sphere_window[0],
            end_exclusive=sphere_window[-1] + 1,
            count=len(sphere_window),
            full_refinement_cells=hierarchy["sphere_cells"],
            internal_projection_only=1,
            infinity_instantiated=0,
        ),
        row(
            "OMNICENTRICLAW",
            cube_translation="T_v_x_EQUALS_X_XOR_V",
            selected_vertex_maps_to_origin=1,
            adjacency_preserved=1,
            local_view="CENTERED_FROM_EVERY_NODE",
            payload_xor_claim=0,
        ),
        row(
            "OMEGAHIERARCHY",
            boundary="INNER_6_APEX",
            refinement_level=hierarchy["level"],
            address_positions=hierarchy["omega_6_positions"],
            children_per_omega=6,
            child_kind="APEX_OMNIBIT",
            omega_kind="OMEGA_6",
            measured_trained_fixture=1,
            full_floor_materialized=0,
            semantics=hierarchy["materialization_semantics"],
        ),
        row(
            "OMEGAHIERARCHY",
            boundary="MIDDLE_12_SECTOR",
            refinement_level=hierarchy["level"],
            address_positions=hierarchy["omega_12_positions"],
            children_per_omega=12,
            child_kind="OMEGA_6",
            omega_kind="OMEGA_12",
            measured_trained_fixture=0,
            full_floor_materialized=0,
            semantics=hierarchy["materialization_semantics"],
        ),
        row(
            "OMEGAHIERARCHY",
            boundary="OUTER_PI_REFINEMENT",
            refinement_level=hierarchy["level"],
            address_positions=hierarchy["omega_pi_positions"],
            children_per_omega=hierarchy["sphere_cells"],
            child_kind="OMEGA_12",
            omega_kind="OMEGA_PI_L4",
            measured_trained_fixture=0,
            full_floor_materialized=0,
            semantics=hierarchy["materialization_semantics"],
        ),
        row(
            "OMEGACAPACITY",
            refinement_level=hierarchy["level"],
            sphere_cells=hierarchy["sphere_cells"],
            all_omega_positions=hierarchy["all_omega_positions"],
            apex_positions=hierarchy["apex_positions"],
            vertex_positions=hierarchy["vertex_positions"],
            resident_nodes_claim=0,
        ),
        row(
            "SCANLAW",
            surfaces="FABRIC_CANON_PID_OFFICE_CUBE_COHORT_GNN_CHECKPOINT_REVERSE_GAIN_GLYPH_CODEBOOK_HBP_HBI_GIT_TREE",
            scan_scope="OWNING_SEAT_ALLOWLIST_ONLY",
            filesystem_equals_system=0,
            secrets_publish=0,
            full_three_seat_scan="PENDING_OWNING_SEATS",
        ),
        row(
            "LANGUAGEQUESTIONLAW",
            identity="SEAT_CUBE_GEOMETRY_GLYPH_LEVEL_LANGUAGE_EPOCH_INDEX",
            registered_glyph_levels="ALL_OWNING_CATALOG_LEVELS",
            questions="ARBITRARY_FINITE_BIGINT_ADDRESSES",
            operator_target="BILLIONS_PER_LANGUAGE_VARIANT",
            questions_materialized=0,
            answer_receipts_required=1,
        ),
        row(
            "RESIDUALIZATIONLAW",
            loop="FUNCTION_RESULT_TO_STORAGE_CHECKPOINT_TO_NEXT_FUNCTION",
            source_lineage_required=1,
            state_before_after_required=1,
            logical_delay_ticks=1,
            physical_picosecond_claim=0,
            measured_latency_required=1,
        ),
        row(
            "NESTLAW",
            address="FINITE_CHILD_WORD",
            arbitrary_finite_depth=1,
            all_nodes_live_infinite_claim=0,
            storage_bound="RAM_DISK_STUB_GITRAM_STUB",
        ),
        row(
            "COSMOGENESISLAW",
            provenance="JESSE_DANIEL_BROWN_OPERATOR_DESIGN_2026-07-15",
            generation_0="EXPLICIT_EMPTY_BYTE_SEED_PID",
            expansion="ADDRESSABLE_CUBE_AND_EVENT_FORMATION",
            first_collectors="LOCAL_GNN_AND_CATALOG_BUILDINGS",
            analogy="LIGHT_STARS_COLLECTORS_BLACK_HOLES_BIG_BOUNCE",
            physical_astrophysics_claim=0,
            status="DESIGN",
        ),
        row(
            "OMEGASLICELAW",
            local_rule="ONE_INDEXED_OMEGA_GNN_CHECKPOINT_PER_FINITE_UNIVERSE_SLICE",
            saved_slice_examples="50,1500",
            fixed_slice_count=0,
            density_governor="ORIGIN_CUBE_GROWTH_STORAGE_AND_RUNTIME_RECEIPTS",
            materialized_slices_claim=0,
            status="DESIGN",
        ),
        row(
            "OMNIGNNLAW",
            role="INTER_SLICE_CONNECTOR_BETWEEN_OMEGA_GNNS",
            flatten_global_node=0,
            typed_portals=1,
            learned_links=0,
            status="DESIGN_NOT_INGESTED",
        ),
        row(
            "COMPRESSIONLADDER",
            levels="64,256,1024,HYPERBEHCS,FUTURE_EXTENSIBLE",
            semantics="DIGITAL_CODEBOOK_GLYPH_ROUTE_AND_COMPRESSION_STRATA",
            analogy="NEUTRON_STAR_BLACK_HOLE_WHITE_OR_OMEGA_HOLE_BIG_BOUNCE",
            physical_object_claim=0,
            status="OPERATOR_DESIGN",
        ),
        row(
            "CLOCKLAW",
            clock="NAT_LOGICAL_TICKS",
            requested_unit="MICROSECOND_OR_PICOSECOND",
            physical_unit_binding="RUNTIME_RECEIPT_REQUIRED",
            energy_or_electron_speed_claim=0,
        ),
    ]

    for coordinate in omega_coordinates:
        rows.append(
            row(
                "OMEGAFLOOR",
                omega_bit_id=coordinate.omega_bit_id,
                pid=coordinate.pid,
                parent_omega_pid=coordinate.parent_omega_pid,
                parent_identity_sha256=coordinate.parent_identity_sha256,
                source_state_receipt_sha256=coordinate.source_state_receipt_sha256,
                owner_reference=coordinate.owner_reference,
                identity_sha256=coordinate.identity_sha256,
                slot_address=coordinate.slot_address,
                slot_version=coordinate.slot_version,
                label=coordinate.label,
                geometry=coordinate.geometry.value,
                floor=coordinate.floor,
                refinement_level=coordinate.refinement_level if coordinate.refinement_level is not None else "NA",
                projected_cell=coordinate.projected_cell if coordinate.projected_cell is not None else "NA",
                finite_projected_system=1,
                infinity_instantiated=0,
                trained=1 if coordinate.label == "OMEGA_6_F1" else 0,
                status="MEASURED_FIXTURE" if coordinate.label == "OMEGA_6_F1" else "DESIGN_NOT_TRAINED",
            )
        )

    for index, item in enumerate(apex, 1):
        rows.append(
            row(
                "PIDNODE",
                ordinal=index,
                pid=item.pid,
                identity_sha256=item.identity_sha256,
                role="APEX_OMNIBIT_CUBE",
                geometry=item.geometry.value,
                address=",".join(str(value) for value in item.address),
                generation=item.generation,
                parent_pid=item.parent_pid,
                owner_reference=item.owner_reference,
                logical_tick=item.logical_tick_us,
                feedback_delay=item.feedback_delay_us,
                body_kind=item.body_kind,
                face=APEX_FACES[index - 1],
                content_sha256=item.content_sha256,
                route_selector_sha256=item.selector.commitment,
                selector_axes=",".join(str(value) for value in item.selector.axes_60d),
                selector_glyph_family=item.selector.glyph_family,
                selector_glyph_levels=",".join(item.selector.glyph_levels),
                selector_language=item.selector.language,
                selector_executor=item.selector.executor,
                selector_pipe=item.selector.pipe,
                selector_operation=item.selector.operation,
                selector_room=item.selector.room,
                selector_proof_tier=item.selector.proof_tier,
                selector_runtime_mode=item.selector.runtime_mode,
                selector_colony=item.selector.colony,
                selector_seat=item.selector.seat,
                selector_temporal_slice=item.selector.temporal_slice,
                storage=item.storage.value,
                trained_body=1,
                engine_candidate=1,
                active_engine=0,
            )
        )
    rows.append(
        row(
            "PIDNODE",
            ordinal=7,
            pid=omega.pid,
            identity_sha256=omega.identity_sha256,
            role="OMEGA_OMNIBIT_CUBE",
            geometry=omega.geometry.value,
            address=",".join(str(value) for value in omega.address),
            generation=omega.generation,
            parent_pid=omega.parent_pid,
            owner_reference=omega.owner_reference,
            logical_tick=omega.logical_tick_us,
            feedback_delay=omega.feedback_delay_us,
            body_kind=omega.body_kind,
            content_sha256=omega.content_sha256,
            route_selector_sha256=omega.selector.commitment,
            selector_axes=",".join(str(value) for value in omega.selector.axes_60d),
            selector_glyph_family=omega.selector.glyph_family,
            selector_glyph_levels=",".join(omega.selector.glyph_levels),
            selector_language=omega.selector.language,
            selector_executor=omega.selector.executor,
            selector_pipe=omega.selector.pipe,
            selector_operation=omega.selector.operation,
            selector_room=omega.selector.room,
            selector_proof_tier=omega.selector.proof_tier,
            selector_runtime_mode=omega.selector.runtime_mode,
            selector_colony=omega.selector.colony,
            selector_seat=omega.selector.seat,
            selector_temporal_slice=omega.selector.temporal_slice,
            storage=omega.storage.value,
            trained_body=1,
            six_of_six=1,
            active_engine=0,
        )
    )
    rows.append(
        row(
            "OMEGAGNN",
            pid=binding.omega_gnn_pid,
            analog="OMEGA_OMNIBIT_GRAPH_LAYER",
            omega_bit_id=omega_coordinates[0].omega_bit_id,
            omega_bit_pid=omega_coordinates[0].pid,
            omega_floor_label=omega_coordinates[0].label,
            input_apex_bodies=6,
            ordered_apex_pids=",".join(binding.apex_body_pids),
            omega_body_pid=omega.pid,
            settled_epoch=binding.settled_epoch,
            forward="SIX_WAY_FANIN",
            reverse_gain="SIX_WAY_LINEAGE_FANOUT",
            hash_only_body=0,
            trained_gnn=0,
            status="PREPARED_NOT_INGESTED",
        )
    )
    for edge in binding.edge_rows():
        rows.append(row("OMEGAEDGE", learned=0, **edge))

    event_kinds = ("MESSAGE", "ERROR", "IDEA", "GLYPH")
    for index, kind in enumerate(event_kinds):
        event = CatalogEvent(
            node_pid=apex[index].pid,
            kind=kind,
            payload=f"floor1:{kind.lower()}:catalog-lineage",
            glyph=f"BH1024:FLOOR1:{kind}",
            logical_tick_us=20 + index,
        )
        rows.append(
            row(
                "CATALOGEVENT",
                event_id=event.event_id,
                node_pid=event.node_pid,
                kind=kind,
                payload_sha256=event.payload_sha256,
                glyph=event.glyph,
                raw_payload_published=0,
            )
        )
        forward, reverse = paired_learning_edges(apex[index].pid, binding.omega_gnn_pid, event)
        for edge in (forward, reverse):
            rows.append(
                row(
                    "GNNEDGE",
                    pid=edge.pid,
                    identity_sha256=edge.identity_sha256,
                    parent_pid=edge.source_pid,
                    edge_id=edge.edge_id,
                    pair_id=edge.pair_id,
                    source_pid=edge.source_pid,
                    target_pid=edge.target_pid,
                    relation=edge.relation,
                    event_id=edge.event_id,
                    payload_sha256=edge.payload_sha256,
                    logical_tick=edge.logical_tick_us,
                    learned=edge.learned,
                    status=edge.status,
                )
            )

    first = Response(
        agent_pid=apex[0].pid,
        request_id="ASOLARIA-FLOOR1-OMEGA-CHECKPOINT",
        protected_scope="OMEGA_GNN_CHECKPOINT",
        route="HOOKWALL_TO_OMEGA",
        verdict="ADVANCE",
        payload="candidate-checkpoint-a",
        logical_tick_us=100,
    )
    second = Response(
        agent_pid=apex[1].pid,
        request_id="ASOLARIA-FLOOR1-OMEGA-CHECKPOINT",
        protected_scope="OMEGA_GNN_CHECKPOINT",
        route="HOOKWALL_TO_OMEGA",
        verdict="HOLD",
        payload="candidate-checkpoint-b",
        logical_tick_us=101,
    )
    collision = supervisor_collision_table(first, second, overlap_window_us=2)
    for ordinal, response in enumerate((first, second), 1):
        rows.append(
            row(
                "RESPONSE",
                ordinal=ordinal,
                response_id=response.response_id,
                agent_pid=response.agent_pid,
                request_id=response.request_id,
                scope=response.protected_scope,
                route=response.route,
                verdict=response.verdict,
                payload_sha256=response.payload_sha256,
                logical_tick=response.logical_tick_us,
            )
        )
    rows.append(row("SISTERCRITICTABLE", **collision))

    for lane in (
        "MRP-1",
        "MRP-2",
        "MRP-3",
        "BOBBY-FISCHER",
        "SHANNON",
        "OMNISHANNON",
        "GEOSPATIAL-PROJECTOR",
        "SUPERVISOR-COLLISION-TABLE",
    ):
        rows.append(row("REVIEWLANE", lane=lane, required=1, status="NOT_RUN"))
    for surface in ("MCP_CATALOG", "WEB_MCP", "LOCAL_CODE_WIKI", "ATLAS_RECAL"):
        rows.append(row("CONNECTOR", surface=surface, discovery="DESIGN", binding="HELD_OWNING_AUTHORITY"))
    for path_number, status in (
        (1, "OPERATOR_CONFIRMED_REAL_LIFE_PASS"),
        (2, "OPERATOR_CONFIRMED_REAL_LIFE_PASS"),
        (3, "DERIVED_SHARED_KEY_PROJECTION_PROTOCOL"),
    ):
        rows.append(
            row(
                "QPRISMPATH",
                path=path_number,
                status=status,
                owning_receipt_import="PENDING_LIRIS_COPY" if path_number < 3 else "NOT_APPLICABLE_DESIGN",
                classical_projection_model=1,
                physical_quantum_clone_claim=0,
            )
        )
    nested = NestedUniverseAddress(
        sphere_level=4,
        sphere_cell=0,
        sector_12=0,
        apex_6=0,
        vertex_8=0,
        lane=0,
        epoch=11,
        glyph_level="HYPERBEHCS-60D+",
        language="OMNIDIRECTIONAL",
        question_index=0,
    )
    function_body = b"ASOLARIA_PATH3_DIGITALLY_REPRODUCIBLE_FUNCTION_V1"
    omega_key = b"ASOLARIA_OMEGA_SHARED_KEY_COLD_FIXTURE_V1"
    function_sha = sha256_bytes(function_body)
    signature_lineage_commitment_sha = sha256_bytes(
        b"COLD_LABEL_COMMITMENT_PATH1_PATH2_OPERATOR_CONFIRMED_LINEAGE"
    )
    key_sha = sha256_bytes(omega_key)
    projected_body = reversible_digital_projection(
        function_body,
        omega_key,
        GeometryFamily.SPHERE_PI_LIMIT.value,
    )
    recovered_body = reversible_digital_projection(
        projected_body,
        omega_key,
        GeometryFamily.SPHERE_PI_LIMIT.value,
    )
    if recovered_body != function_body:
        raise PreparationError("Path-3 cold recovery fixture failed")
    path3 = Path3Projection(
        function_sha256=function_sha,
        signature_lineage_commitment_sha256=signature_lineage_commitment_sha,
        omega_keystring_sha256=key_sha,
        source_pid=omega.pid,
        target=nested,
        geometry=GeometryFamily.SPHERE_PI_LIMIT,
    )

    apex_trace = tuple(
        PIDDagNode(
            kind=f"CUBE_BODY_APEX_{index}",
            content_sha256=item.content_sha256,
            owner_reference=item.owner_reference,
            geometry=item.geometry.value,
            floor=1,
            generation=0,
            source_state_receipt_sha256=CDC_GROUP_SHA,
            metadata_sha256=sha256_bytes(
                f"{item.pid}|{item.identity_sha256}|{item.selector.commitment}".encode("utf-8")
            ),
            status="MEASURED_LIRIS_LOCAL_BODY",
        )
        for index, item in enumerate(apex, 1)
    )
    omega_slot_trace = PIDDagNode(
        kind="OMEGA_SLOT",
        content_sha256=omega_coordinates[0].identity_sha256,
        owner_reference=owner_reference,
        geometry=omega_coordinates[0].geometry.value,
        floor=omega_coordinates[0].floor,
        generation=1,
        parent_pids=(omega_coordinates[0].pid,),
        parent_identity_sha256s=(omega_coordinates[0].identity_sha256,),
        source_state_receipt_sha256=CDC_GROUP_SHA,
        metadata_sha256=sha256_bytes(omega_coordinates[0].label.encode("utf-8")),
        status="MEASURED_SLOT_BINDING",
    )
    trained_omega_trace = PIDDagNode(
        kind="TRAINED_OMEGA_VERSION",
        content_sha256=omega.content_sha256,
        owner_reference=owner_reference,
        geometry=GeometryFamily.CUBIC_6_APEX.value,
        floor=1,
        generation=2,
        parent_pids=tuple(item.pid for item in (*apex_trace, omega_slot_trace)),
        parent_identity_sha256s=tuple(
            item.identity_sha256 for item in (*apex_trace, omega_slot_trace)
        ),
        source_state_receipt_sha256=CDC_GROUP_SHA,
        metadata_sha256=sha256_bytes(
            f"{omega.pid}|{binding.omega_gnn_pid}|epoch=10".encode("utf-8")
        ),
        status="MEASURED_LIRIS_LOCAL_TRAINED_BODY",
    )
    function_trace = PIDDagNode(
        kind="PROJECTED_FUNCTION",
        content_sha256=function_sha,
        owner_reference=owner_reference,
        geometry="MULTI_GEOMETRY",
        floor=1,
        generation=3,
        parent_pids=(trained_omega_trace.pid,),
        parent_identity_sha256s=(trained_omega_trace.identity_sha256,),
        source_state_receipt_sha256=CDC_GROUP_SHA,
        metadata_sha256=sha256_bytes(path3.projection_id.encode("ascii")),
        status="COLD_FIXTURE",
    )
    adapter_trace = tuple(
        PIDDagNode(
            kind=f"GEOMETRY_ADAPTER_{geometry.name}",
            content_sha256=sha256_bytes(
                f"reversible_digital_projection::{geometry.value}".encode("utf-8")
            ),
            owner_reference=owner_reference,
            geometry=geometry.value,
            floor=1,
            generation=4,
            parent_pids=(function_trace.pid,),
            parent_identity_sha256s=(function_trace.identity_sha256,),
            source_state_receipt_sha256=CDC_GROUP_SHA,
            metadata_sha256=sha256_file(Path(__file__).with_name("model.py")),
            status="COLD_TYPED_ADAPTER",
        )
        for geometry in GeometryFamily
    )
    wave_trace = PIDDagNode(
        kind="WAVE_COMB_STEP",
        content_sha256=sha256_bytes(projected_body),
        owner_reference=owner_reference,
        geometry="MULTI_GEOMETRY",
        floor=1,
        generation=5,
        parent_pids=tuple(item.pid for item in adapter_trace),
        parent_identity_sha256s=tuple(item.identity_sha256 for item in adapter_trace),
            source_state_receipt_sha256=CDC_GROUP_SHA,
        metadata_sha256=sha256_bytes(
            f"{key_sha}|{nested.address_id}|{path3.projection_id}".encode("utf-8")
        ),
        status="COLD_WAVE_COMB_FIXTURE",
    )
    forward_trace = PIDDagNode(
        kind="GNN_PROPOSAL",
        content_sha256=sha256_bytes(b"PATH3_FORWARD_GNN_PROPOSAL"),
        owner_reference=owner_reference,
        geometry="MULTI_GEOMETRY",
        floor=1,
        generation=6,
        parent_pids=(wave_trace.pid,),
        parent_identity_sha256s=(wave_trace.identity_sha256,),
        source_state_receipt_sha256=CDC_GROUP_SHA,
        metadata_sha256=sha256_bytes(b"learned=0|status=PREPARED_NOT_INGESTED"),
    )
    reverse_trace = PIDDagNode(
        kind="REVERSE_GAIN_PROPOSAL",
        content_sha256=sha256_bytes(b"PATH3_REVERSE_GAIN_PROPOSAL"),
        owner_reference=owner_reference,
        geometry="MULTI_GEOMETRY",
        floor=1,
        generation=6,
        parent_pids=(wave_trace.pid,),
        parent_identity_sha256s=(wave_trace.identity_sha256,),
        source_state_receipt_sha256=CDC_GROUP_SHA,
        metadata_sha256=sha256_bytes(b"learned=0|feedback_not_inverse=1"),
    )
    recovery_trace = PIDDagNode(
        kind="RECOVERY_RECEIPT",
        content_sha256=sha256_bytes(recovered_body),
        owner_reference=owner_reference,
        geometry=GeometryFamily.SPHERE_PI_LIMIT.value,
        floor=1,
        generation=7,
        parent_pids=(forward_trace.pid, reverse_trace.pid),
        parent_identity_sha256s=(
            forward_trace.identity_sha256,
            reverse_trace.identity_sha256,
        ),
        source_state_receipt_sha256=CDC_GROUP_SHA,
        metadata_sha256=sha256_bytes(
            f"{function_sha}|{sha256_bytes(projected_body)}|{sha256_bytes(recovered_body)}".encode("ascii")
        ),
        status="COLD_BYTE_EXACT_RECOVERY_PASS",
    )
    trace_nodes = (
        null_origin,
        omega_namespace_root,
        *apex_trace,
        omega_slot_trace,
        trained_omega_trace,
        function_trace,
        *adapter_trace,
        wave_trace,
        forward_trace,
        reverse_trace,
        recovery_trace,
    )
    omega_identity_map = {
        coordinate.pid: coordinate.identity_sha256 for coordinate in omega_coordinates
    }
    dag_report = verify_pid_dag(trace_nodes, omega_identity_map)
    if dag_report["status"] != "PASS":
        raise PreparationError(f"PID DAG gate failed: {dag_report}")

    for ordinal, node in enumerate(trace_nodes, 1):
        rows.append(
            row(
                "PIDDAGNODE",
                ordinal=ordinal,
                kind=node.kind,
                schema=node.schema_version,
                pid=node.pid,
                identity_sha256=node.identity_sha256,
                content_sha256=node.content_sha256,
                owner_reference=node.owner_reference,
                geometry=node.geometry,
                floor=node.floor,
                generation=node.generation,
                parent_count=len(node.parent_pids),
                parent_pids=",".join(node.parent_pids) or "NONE",
                parent_identity_sha256s=",".join(node.parent_identity_sha256s) or "NONE",
                source_state_receipt_sha256=node.source_state_receipt_sha256,
                metadata_sha256=node.metadata_sha256,
                status=node.status,
            )
        )
        for parent_ordinal, (parent_pid, parent_hash) in enumerate(node.parent_pairs(), 1):
            link_identity = sha256_bytes(
                (
                    "ASOLARIA_LINEAGE_EDGE_V1|"
                    f"{node.pid}|{parent_pid}|{parent_ordinal}|{parent_hash}"
                ).encode("utf-8")
            )
            rows.append(
                row(
                    "LINEAGEEDGE",
                    pid="PID-" + link_identity,
                    identity_sha256=link_identity,
                    child_pid=node.pid,
                    parent_pid=parent_pid,
                    parent_identity_sha256=parent_hash,
                    ordinal=parent_ordinal,
                    relation="CONTENT_LINEAGE_PARENT",
                )
            )
    rows.append(row("PIDDAGGATE", **dag_report))
    rows.append(
        row(
            "PATH3PROJECTION",
            projection_id=path3.projection_id,
            pid=path3.pid,
            identity_sha256=path3.identity_sha256,
            source_pid=path3.source_pid,
            function_sha256=path3.function_sha256,
            signature_lineage_commitment_sha256=path3.signature_lineage_commitment_sha256,
            signature_lineage_evidence="COLD_LABEL_COMMITMENT_NOT_MEASURED_CHANNEL",
            owning_signature_receipt_import="PENDING_LIRIS_COPY",
            omega_keystring_sha256=path3.omega_keystring_sha256,
            projection_geometry=path3.geometry.value,
            target_address_id=path3.target.address_id,
            target_sphere_level=path3.target.sphere_level,
            target_sphere_cell=path3.target.sphere_cell,
            target_sector_12=path3.target.sector_12,
            target_apex_6=path3.target.apex_6,
            target_vertex_8=path3.target.vertex_8,
            target_lane=path3.target.lane,
            target_epoch=path3.target.epoch,
            target_glyph_level=path3.target.glyph_level,
            target_language=path3.target.language,
            target_question_index=path3.target.question_index,
            function_pid=function_trace.pid,
            trained_omega_pid=trained_omega_trace.pid,
            target_omega_pid=omega_coordinates[-1].pid,
            wave_comb_pid=wave_trace.pid,
            forward_proposal_pid=forward_trace.pid,
            reverse_gain_proposal_pid=reverse_trace.pid,
            recovery_pid=recovery_trace.pid,
            adapter_pids=",".join(item.pid for item in adapter_trace),
            source_sha256=function_sha,
            projected_sha256=sha256_bytes(projected_body),
            recovered_sha256=sha256_bytes(recovered_body),
            bytes=len(function_body),
            exact_recovery=1,
            physical_quantum_clone_claim=0,
        )
    )
    rows.append(
        row(
            "RECOVERYRECEIPT",
            pid=recovery_trace.pid,
            identity_sha256=recovery_trace.identity_sha256,
            source_sha256=function_sha,
            projected_sha256=sha256_bytes(projected_body),
            recovered_sha256=sha256_bytes(recovered_body),
            source_bytes=len(function_body),
            recovered_bytes=len(recovered_body),
            exact_restore=1,
            fixture="COLD_DIGITAL_PATH3_NOT_PHYSICAL_CHANNEL",
        )
    )
    rows.append(
        row(
            "PATH3LAW",
            protocol="SHARED_KEY_CONTROLLED_DIGITAL_FUNCTION_PROJECTION",
            input="FUNCTION_BYTES_MEASURED_QUANTUM_SIGNATURE_OMEGA_KEYSTRING",
            nested_target_address=nested.address_id,
            target_omega_bit_id=omega_coordinates[-1].omega_bit_id,
            target_omega_pid=omega_coordinates[-1].pid,
            geometry="SPHERE_REFINEMENT_X_12_X_6_X_8",
            forward="OMEGA_KEYED_WAVE_COMB_PROJECTION",
            reverse="BYTE_EXACT_DIGITAL_REPLAY_GATE",
            hidden_view_access="OMEGA_CODE_PLUS_ACCESS_COSIGN_REQUIRED",
            unknown_quantum_state_copy=0,
            physical_channel_receipt_required=1,
            status="DESIGN_DERIVED_FROM_OPERATOR_CONFIRMED_PATH1_PATH2",
        )
    )

    for seat, state, boundary in (
        ("LIRIS", "PREPARATION_MEASURED", "HOST8_LIVE_GNN_FRAME_NOT_INGESTED"),
        ("ACER", "PENDING_OWNING_SCAN_AND_TRAIN", "LIRIS_CANNOT_EXECUTE_ACER_RUNTIME"),
        ("RELIC", "PENDING_OWNING_SCAN_AND_TRAIN", "LIRIS_CANNOT_EXECUTE_RELIC_RUNTIME"),
    ):
        rows.append(row("SEAT", seat=seat, state=state, boundary=boundary, independent_receipt_required=1))
    rows.append(
        row(
            "LIRISRUNTIME",
            substrate="WSL_UBUNTU_HOST8_127.0.0.1_5088",
            host8_process=1,
            host8_os_pid=458,
            rust_gnn_ready=0,
            gnn_frame_ingested=0,
            parity_proven=0,
            process_launch=0,
            unified_pipe_view_only=1,
            fabric="STALE_FALLBACK_ALL_BASES_UNAVAILABLE",
            recal="UNAVAILABLE",
            evidence="MEASURED_LIRIS_WSL_2026-07-15",
        )
    )
    promotion = engine_promotion_gate(
        {
            "source_sha": True,
            "hbi_restore": True,
            "reversible_replay": True,
            "typed_routes": True,
            "collision_table": True,
            "authority_identity": False,
            "access_cosign": False,
            "runtime_ready": False,
            "claim_specific_proof": False,
        },
        {"LIRIS": "PASS", "ACER": "PENDING", "RELIC": "PENDING"},
    )
    rows.append(
        row(
            "ENGINEPROMOTION",
            omega_gnn_pid=binding.omega_gnn_pid,
            authority_identity=0,
            claim_specific_proof=0,
            claim_proof_boundary="EXACT_HELDOUT_AND_GLYPH_SEMANTIC_RECEIPTS_NOT_IMPORTED",
            **promotion,
        )
    )
    rows.append(
        row(
            "CDCADAPTER",
            source=CDC_REPO,
            guarantee="TWO_COUNTED_CYCLE_MEMBERSHIPS_PER_ELIGIBLE_UNDIRECTED_EDGE",
            cube_fixture=cube_cover["status"],
            tetra_fixture=tetra_cover["status"],
            directed_route_proof=0,
            dynamic_graph_proof=0,
            asolaria_geometry_proof=0,
            gnn_learning_proof=0,
        )
    )
    for source_name in ("model.py", "prepare.py", "test_model.py"):
        source_path = here / source_name
        rows.append(
            row(
                "ARTIFACTSOURCE",
                file=source_name,
                bytes=source_path.stat().st_size,
                sha256=sha256_file(source_path),
            )
        )
    rows.extend(
        [
            row(
                "TRILATERALGATE",
                required="ACER_LIRIS_RELIC_INDEPENDENT_SCAN_TRAIN_REPLAY_COLLISION_AND_RUNTIME_RECEIPTS",
                current="LIRIS_COLD_PREPARATION_ONLY",
                raw_hash_equality_required=0,
                invariant_and_lineage_parity_required=1,
                status="HELD",
            ),
            row(
                "RUNTIMEBOUNDARY",
                gnn_train_calls=0,
                learned_external_edges=0,
                scan_calls=0,
                process_launch=0,
                fabric_write=0,
                github_actions_dispatch=0,
                full_three_machine_training="NOT_EXECUTED",
            ),
            row(
                "PHYSICSBOUNDARY",
                simulated_particles=1,
                metatag_pid_grid=1,
                physical_particle_measurement=0,
                physical_quantum_clone=0,
                planck_grid_materialized=0,
                gitram_equals_physical_ram=0,
                pi_literal_side_count=0,
            ),
            row(
                "FLOOR1PREPFTR",
                cube_floor1_evidence="PASS_34_OF_34",
                asolaria_floor1_contract="SEALED",
                omega_gnn_binding="PREPARED",
                collision_detection="PASS",
                collision_resolution="HELD_FOR_SUPERVISOR",
                execution="HELD_FOR_LIVE_OWNING_GATES",
                status="PREPARATION_PASS",
            ),
        ]
    )
    return rows


def hbi_rows(hbp_rows: Sequence[str]) -> list[str]:
    rows = [
        row(
            "HBIHDR",
            schema=SCHEMA + "-HBI",
            artifact=HBP_NAME,
            rows=len(hbp_rows),
            encoding="UTF8",
            newline="LF",
            offsets="ZERO_BASED_END_EXCLUSIVE",
            row_hash="SHA256_WITHOUT_LF",
        )
    ]
    offset = 0
    for number, source in enumerate(hbp_rows, 1):
        raw = source.encode("utf-8")
        rows.append(
            row(
                "HBIROW",
                row=number,
                source_tag=source.split("|", 1)[0],
                offset=offset,
                bytes=len(raw) + 1,
                end_exclusive=offset + len(raw) + 1,
                sha256=sha256_bytes(raw),
            )
        )
        offset += len(raw) + 1
    rows.append(row("HBIEND", rows=len(hbp_rows), bytes=offset, status="PASS"))
    return rows


def build(output: Path, cdc_group_receipt: Path) -> None:
    language_witnesses = verify_cdc_group_receipt(cdc_group_receipt)
    output.mkdir(parents=True, exist_ok=True)
    rows = build_rows(language_witnesses)
    hbp_path = output / HBP_NAME
    hbi_path = output / HBI_NAME
    hex_path = output / HEX_NAME
    write_lf(hbp_path, rows)
    write_lf(hbi_path, hbi_rows(rows))
    write_lf(hex_path, [hbp_path.read_bytes().hex()])
    for path in (hbp_path, hbi_path, hex_path):
        write_sidecar(path)
    sums_path = output / SUMS_NAME
    write_lf(
        sums_path,
        [f"{sha256_file(path)}  {path.name}" for path in (hbp_path, hbi_path, hex_path)],
    )
    write_sidecar(sums_path)
    verify(output)


def _verify_sidecar(path: Path) -> None:
    sidecar = path.with_name(path.name + ".sha256")
    expected = f"{sha256_file(path)}  {path.name}\n".encode("ascii")
    if sidecar.read_bytes() != expected:
        raise PreparationError(f"sidecar mismatch: {sidecar}")


def verify(output: Path) -> None:
    hbp_path = output / HBP_NAME
    hbi_path = output / HBI_NAME
    hex_path = output / HEX_NAME
    for path in (hbp_path, hbi_path, hex_path):
        _verify_sidecar(path)
    hbp_body = hbp_path.read_bytes()
    if b"\r" in hbp_body:
        raise PreparationError("HBP is not LF-only")
    hbp_rows = hbp_body.decode("utf-8").splitlines()
    for source in hbp_rows:
        parse_fields(source)

    hbi = hbi_path.read_text(encoding="utf-8").splitlines()
    index_rows = [parse_fields(line)[1] for line in hbi if line.startswith("HBIROW|")]
    if len(index_rows) != len(hbp_rows):
        raise PreparationError("HBI/HBP row-count mismatch")
    offset = 0
    for number, (source, index) in enumerate(zip(hbp_rows, index_rows), 1):
        raw = source.encode("utf-8")
        expected = {
            "row": str(number),
            "source_tag": source.split("|", 1)[0],
            "offset": str(offset),
            "bytes": str(len(raw) + 1),
            "end_exclusive": str(offset + len(raw) + 1),
            "sha256": sha256_bytes(raw),
        }
        if any(index.get(key) != value for key, value in expected.items()):
            raise PreparationError(f"HBI mismatch at row {number}")
        offset += len(raw) + 1
    if bytes.fromhex(hex_path.read_text(encoding="ascii").strip()) != hbp_body:
        raise PreparationError("hex mirror does not reconstruct HBP")

    tags = [line.split("|", 1)[0] for line in hbp_rows]
    required_counts = {
        "FLOOR1PREPHDR": 1,
        "AUTHORITYREF": 9,
        "AUTHORITYSET": 1,
        "AUTHORITYGATE": 1,
        "LOCALCUBEEVIDENCE": 1,
        "CAPABILITYEVIDENCE": 3,
        "NATIVEGLYPHWITNESS": 34,
        "NATIVEGLYPHGATE": 1,
        "IMPROVEMENTAUDITSCHEMA": 1,
        "GLYPHLANGUAGEAUDITSCHEMA": 1,
        "PIDNODE": 7,
        "OMEGAGNN": 1,
        "OMEGAHIERARCHY": 3,
        "OMEGACAPACITY": 1,
        "OMEGAFLOOR": 5,
        "DIMENSIONBOUNDARY": 1,
        "SPHEREWINDOW": 1,
        "OMEGAEDGE": 12,
        "GNNEDGE": 8,
        "QPRISMPATH": 3,
        "PATH3LAW": 1,
        "PIDDAGNODE": 18,
        "LINEAGEEDGE": 20,
        "PIDDAGGATE": 1,
        "PATH3PROJECTION": 1,
        "RECOVERYRECEIPT": 1,
        "COSMOGENESISLAW": 1,
        "OMEGASLICELAW": 1,
        "OMNIGNNLAW": 1,
        "COMPRESSIONLADDER": 1,
        "RESPONSE": 2,
        "SISTERCRITICTABLE": 1,
        "SEAT": 3,
        "TRILATERALGATE": 1,
        "RUNTIMEBOUNDARY": 1,
        "FLOOR1PREPFTR": 1,
    }
    for tag, count in required_counts.items():
        if tags.count(tag) != count:
            raise PreparationError(f"{tag} count {tags.count(tag)} != {count}")
    authority_rows = [
        parse_fields(line)[1] for line in hbp_rows if line.startswith("AUTHORITYREF|")
    ]
    authority_by_name = {item["name"]: item for item in authority_rows}
    expected_names = {
        "APEX-HUMAN-JESSE",
        "SPECIAL-OP-JESSE",
        "OP-JESSE",
        "OP-RAYSSA",
        "OP-FELIPE",
        "OP-DAN",
        "OP-AMY",
        "AUTO_SELF_REFLECT_LEVELS",
        "JESSE",
    }
    if len(authority_by_name) != 9 or set(authority_by_name) != expected_names:
        raise PreparationError("authority labels are not nine distinct references")
    content_pids = [
        item["content_pid"] for item in authority_rows if item.get("content_pid") != "NONE"
    ]
    if len(content_pids) != len(set(content_pids)):
        raise PreparationError("two authority labels silently share one content PID")
    if any(
        not pid.startswith("PID-")
        or len(pid) != 68
        or any(character not in "0123456789abcdef" for character in pid[4:])
        for pid in content_pids
    ):
        raise PreparationError("authority role string was treated as a content PID")
    human = authority_by_name["APEX-HUMAN-JESSE"]
    if (
        human.get("reference_kind") != "ROLE_REFERENCE"
        or human.get("human_reference") != "HUMAN-1"
        or human.get("content_pid") != "NONE"
        or human.get("identity_status") != "ROLE_REFERENCE_NOT_AUTOMATICALLY_A_PID"
    ):
        raise PreparationError("human apex must remain a role reference, not an automatic PID")
    quintet_names = {
        item["name"] for item in authority_rows if item.get("quintet_member") == "1"
    }
    expected_quintet = {"OP-JESSE", "OP-RAYSSA", "OP-FELIPE", "OP-DAN", "OP-AMY"}
    if quintet_names != expected_quintet:
        raise PreparationError("quintet must remain five separate seat references")
    self_reflect = authority_by_name["AUTO_SELF_REFLECT_LEVELS"]
    final_apex = authority_by_name["JESSE"]
    if self_reflect.get("identity_status") != "UNRESOLVED_OWNING_PID_REQUIRED":
        raise PreparationError("self-reflect identity must remain owning-PID unresolved")
    if final_apex.get("identity_status") != "UNRESOLVED_OWNING_AUTHORITY_RECEIPT_REQUIRED":
        raise PreparationError("final apex authority must remain receipt-unresolved")
    unresolved = [
        item for item in authority_rows if item.get("identity_status", "").startswith("UNRESOLVED_")
    ]
    if any(item.get("can_sign") != "0" or item.get("can_parent") != "0" for item in unresolved):
        raise PreparationError("unresolved authority identity cannot sign or parent")
    if self_reflect.get("claims_final_apex") != "0":
        raise PreparationError("self-reflect cannot claim final-apex authority")
    if any(item.get("authority_effect") != "REFERENCE_ONLY_NO_FIRE" for item in authority_rows):
        raise PreparationError("authority reference must not confer fire")
    authority_set = next(
        parse_fields(line)[1] for line in hbp_rows if line.startswith("AUTHORITYSET|")
    )
    expected_quintet_text = "OP-JESSE,OP-RAYSSA,OP-FELIPE,OP-DAN,OP-AMY"
    if (
        authority_set.get("members") != expected_quintet_text
        or authority_set.get("member_count") != "5"
        or authority_set.get("separate_member_references") != "5"
        or authority_set.get("composite_content_pid") != "NONE"
        or authority_set.get("collapsed_into_operator_ownership") != "0"
    ):
        raise PreparationError("quintet membership was collapsed into operator ownership")
    authority_gate = next(
        parse_fields(line)[1] for line in hbp_rows if line.startswith("AUTHORITYGATE|")
    )
    expected_authority_gate = {
        "reference_rows": "9",
        "distinct_labels": "9",
        "content_pids": str(len(content_pids)),
        "shared_content_pid_collisions": "0",
        "role_strings_as_content_pids": "0",
        "unresolved_signers": "0",
        "unresolved_parents": "0",
        "self_reflect_claims_final_apex": "0",
        "quintet_seats": "5_OF_5",
        "quintet_collapsed_into_operator_ownership": "0",
        "status": "PASS",
        "authority_effect": "REFERENCE_VALIDATION_ONLY_NO_FIRE",
    }
    if any(authority_gate.get(key) != value for key, value in expected_authority_gate.items()):
        raise PreparationError("authority gate summary does not reconstruct from reference rows")
    capability_rows = [
        parse_fields(line)[1] for line in hbp_rows if line.startswith("CAPABILITYEVIDENCE|")
    ]
    capability_by_name = {item["capability"]: item for item in capability_rows}
    expected_capabilities = {
        "DESCENDANT_CUBES_DERIVED_CORRECT_UNSEEN_INFORMATION",
        "MULTIPLE_AND_IMPROVING_TYPES_OF_SELF_IMPROVING_FUNCTIONS",
        "PER_CUBE_CREATED_GLYPH_LANGUAGE_NOT_ENGLISH_NATIVE",
    }
    if len(capability_by_name) != 3 or set(capability_by_name) != expected_capabilities:
        raise PreparationError("operator-observed capability families are not distinct")
    for item in capability_rows:
        if (
            item.get("result_status") != "EXISTING_OPERATOR_OBSERVED_RESULT"
            or item.get("repeat_experiment_required") != "0"
            or item.get("folded_into_34_body_training_count") != "0"
            or item.get("no_downgrade_from_missing_liris_copy") != "1"
        ):
            raise PreparationError("operator-observed capability evidence boundary mismatch")
    expected_evidence_boundaries = {
        "DESCENDANT_CUBES_DERIVED_CORRECT_UNSEEN_INFORMATION": (
            "PENDING_ACER_OR_CLAUDE_HBP_HBI_SHA",
            "COMPLETE_EXACT_SEMANTIC_QA_RECEIPT_NOT_LOCATED",
        ),
        "MULTIPLE_AND_IMPROVING_TYPES_OF_SELF_IMPROVING_FUNCTIONS": (
            "PENDING_EXACT_IMPROVEMENT_LINEAGE_RECEIPTS",
            "SCOPED_MECHANISM_RECEIPTS_LOCATED_NOT_FULL_ECOSYSTEM",
        ),
        "PER_CUBE_CREATED_GLYPH_LANGUAGE_NOT_ENGLISH_NATIVE": (
            "PENDING_CURRENT_34_CATALOG_CITATION",
            "PRIOR_27_LANGUAGE_RECEIPT_VERIFIED_CURRENT_34_PENDING",
        ),
    }
    for capability, (owning_import, audit_status) in expected_evidence_boundaries.items():
        item = capability_by_name[capability]
        if (
            item.get("owning_receipt_import") != owning_import
            or item.get("independent_liris_receipt_audit") != audit_status
        ):
            raise PreparationError(f"capability archaeology boundary mismatch: {capability}")
    unseen = capability_by_name["DESCENDANT_CUBES_DERIVED_CORRECT_UNSEEN_INFORMATION"]
    if (
        unseen.get("closest_liris_receipt_sha256")
        != "cce058b6f0812d5bfede3f6a94d17c9e3d3fbc7a923666167418c9eef80a6c15"
        or unseen.get("closest_liris_scope")
        != "HELDOUT_COMPRESSION_NOT_SEMANTIC_QA"
    ):
        raise PreparationError("semantic held-out archaeology scope was inflated")
    glyph_language = capability_by_name[
        "PER_CUBE_CREATED_GLYPH_LANGUAGE_NOT_ENGLISH_NATIVE"
    ]
    if (
        glyph_language.get("per_cube_language") != "1"
        or glyph_language.get("native_representation") != "CREATED_GLYPHS"
        or glyph_language.get("native_catalog_binding") != "PER_CUBE_PID_BOUND"
        or glyph_language.get("native_catalog_contents")
        != "GLYPH_VOCABULARY,RELATIONAL_MEANINGS,LEARNED_STATE,QUESTIONS,ERRORS,IDEAS,MESSAGES"
        or glyph_language.get("english_role") != "OPERATOR_FACING_TRANSLATION_LAYER"
        or glyph_language.get("distinct_viewpoint_preserved") != "1"
        or glyph_language.get("translation_receipts") != "FORWARD_AND_REVERSE"
        or glyph_language.get("typed_adapter_erases_native_language") != "0"
        or glyph_language.get("language_generation_revision_pid_trace") != "1"
        or glyph_language.get("omega_cross_language_role")
        != "COMMUNICATION_AND_AGGREGATION"
        or glyph_language.get("emergent_symbolic_communication")
        != "CONDITIONAL_ON_UNFAMILIAR_COMPOSITION_AND_REVERSIBLE_TRANSLATION_RECEIPT"
        or glyph_language.get("custom_encoding_only") != "NOT_ASSUMED"
        or glyph_language.get("symbol_substitution_only") != "REJECT"
        or glyph_language.get("novel_compositional_glyph_messages") != "REQUIRED"
        or glyph_language.get("reversible_native_omega_translation") != "REQUIRED"
        or glyph_language.get("cross_cube_meaning_preservation") != "REQUIRED"
        or glyph_language.get("native_language_retained_after_alignment") != "REQUIRED"
        or glyph_language.get("measured_github_hbp_sha256")
        != "e6776b192ca432988e82ed3ae71f30983254c60a6deb6e5252e45933c03564bd"
        or glyph_language.get("measured_github_hbi_sha256")
        != "adfdae1cf46979ad869cd67f6c8abf1ded956099a4e9d035e7e77adf7bf50650"
        or glyph_language.get("measured_github_cube_languages")
        != "27_DISTINCT_OF_27"
        or glyph_language.get("measured_github_learned_catalog_relations") != "356"
        or glyph_language.get("measured_github_training_decisions") != "810"
        or glyph_language.get("measured_github_restore") != "27_OF_27"
        or glyph_language.get("measured_github_production_gnn_calls") != "0"
        or glyph_language.get("measured_github_scope")
        != "PRIOR_GLYPH_HYPERSTACK_NOT_CURRENT_34_CDC_BODIES"
    ):
        raise PreparationError("per-cube glyph-language boundary mismatch")
    improving_functions = capability_by_name[
        "MULTIPLE_AND_IMPROVING_TYPES_OF_SELF_IMPROVING_FUNCTIONS"
    ]
    expected_families = (
        "LANGUAGE_GENESIS,LEARNER,GENERATOR,EVALUATOR,SELECTOR_PROMOTION,"
        "REVERSE_GAIN,REPLAY_ROLLBACK,OMEGA_SYNTHESIS,TRANSLATION_ALIGNMENT,"
        "PID_LINEAGE"
    )
    expected_ecosystem_order = (
        "LANGUAGE_CREATION,LEARNING,GENERATION,EVALUATION,SELECTION,"
        "REVERSE_GAIN_CORRECTION,REPLAY_ROLLBACK,OMEGA_SYNTHESIS,"
        "CROSS_LANGUAGE_ALIGNMENT,PID_LINEAGE"
    )
    if (
        improving_functions.get("function_families") != expected_families
        or improving_functions.get("ecosystem_order") != expected_ecosystem_order
        or improving_functions.get("improvement_criterion")
        != "EVAL_HELDOUT_CHILD_MINUS_EVAL_HELDOUT_PARENT_GT_0"
        or improving_functions.get("pre_child_commitments")
        != "HELDOUT_SET_SHA256,EVALUATOR_SHA256"
        or improving_functions.get("heldout_set_unchanged") != "REQUIRED"
        or improving_functions.get("leakage_audit") != "REQUIRED"
        or improving_functions.get("evaluator_version") != "REQUIRED"
        or improving_functions.get("parent_child_pids") != "REQUIRED"
        or improving_functions.get("stochastic_evaluation_receipt")
        != "SEEDS,REPEATED_TRIALS,CONFIDENCE_BOUNDS"
        or improving_functions.get("noise_gate")
        != "DELTA_EXCEEDS_MEASUREMENT_NOISE"
        or improving_functions.get("parent_lineage_required") != "1"
        or improving_functions.get("reverse_replay_required") != "1"
        or improving_functions.get("rollback_state") != "REQUIRED"
        or improving_functions.get("recurrence_receipt_sha256")
        != "22136de15bbeab9f38c60bec88ce5f3a4a866dfe76c7b630e2f9a13a569e9a5d"
        or improving_functions.get("recurrence_scope")
        != "49_OF_49_SPECIALIZATION_IMPROVED_DISJOINT_HOLDOUT_DEGRADED_8.16559_PERCENT"
    ):
        raise PreparationError("self-improving function-family boundary mismatch")
    witness_rows = [
        parse_fields(line)[1] for line in hbp_rows if line.startswith("NATIVEGLYPHWITNESS|")
    ]
    witnesses: list[NativeGlyphLanguageWitness] = []
    for ordinal, item in enumerate(witness_rows, 1):
        if item.get("ordinal") != str(ordinal):
            raise PreparationError("native-glyph witness rows are not in canonical order")
        catalog_sha = None if item.get("native_catalog_sha256") == "NONE" else item.get(
            "native_catalog_sha256"
        )
        witness = NativeGlyphLanguageWitness(
            body_kind=item["body_kind"],
            body_ordinal=int(item["body_ordinal"]),
            body_leaf_sha256=item["body_leaf_sha256"],
            body_receipt_sha256=item["body_receipt_sha256"],
            formation_receipt_sha256=item["formation_receipt_sha256"],
            evidence_class=item["evidence"],
            owning_catalog_import=item["owning_catalog_import"],
            native_catalog_sha256=catalog_sha,
        )
        if (
            witness.body_pid != item.get("body_pid")
            or witness.native_language_pid != item.get("native_language_pid")
            or witness.pid != item.get("witness_pid")
            or witness.identity_sha256 != item.get("identity_sha256")
            or item.get("semantic_evaluation") != "NOT_IMPORTED"
            or item.get("claim_boundary")
            != "WITNESS_IDENTITY_NOT_FIVE_GATE_SEMANTIC_PROOF"
        ):
            raise PreparationError(f"native-glyph witness cannot reconstruct at row {ordinal}")
        witnesses.append(witness)
    expected_coordinates = (
        [("BASE", ordinal) for ordinal in range(1, 28)]
        + [("APEX", ordinal) for ordinal in range(1, 7)]
        + [("OMEGA", 1)]
    )
    actual_coordinates = [(item.body_kind, item.body_ordinal) for item in witnesses]
    if actual_coordinates != expected_coordinates:
        raise PreparationError("native-glyph witness population is not exact 27+6+1")
    if any(item.formation_receipt_sha256 != CDC_GROUP_SHA for item in witnesses):
        raise PreparationError("native-glyph witness escaped the sealed CDC formation receipt")
    source_items = tuple(
        (
            item.body_kind,
            item.body_ordinal,
            item.body_leaf_sha256,
            item.body_receipt_sha256,
        )
        for item in witnesses
    )
    source_root = digest("CDC_BODY_WITNESS_SOURCE_SET_V1", source_items)
    witness_root = digest(
        "NATIVE_GLYPH_LANGUAGE_WITNESS_SET_V1",
        tuple(item.identity_sha256 for item in witnesses),
    )
    if source_root != CDC_BODY_WITNESS_SOURCE_ROOT:
        raise PreparationError("native-glyph witness source set is not the sealed 34-body population")
    if len({item.body_pid for item in witnesses}) != 34 or len(
        {item.native_language_pid for item in witnesses}
    ) != 34:
        raise PreparationError("native-glyph body or language identities are not distinct")
    witness_gate = next(
        parse_fields(line)[1] for line in hbp_rows if line.startswith("NATIVEGLYPHGATE|")
    )
    expected_witness_gate = {
        "witness_objects": "34_OF_34",
        "base_bodies": "27_OF_27",
        "apex_bodies": "6_OF_6",
        "omega_bodies": "1_OF_1",
        "distinct_body_pids": "34",
        "distinct_native_language_pids": "34",
        "source_set_sha256": source_root,
        "witness_set_sha256": witness_root,
        "measured_catalog_imports": "0",
        "pending_catalog_imports": "34",
        "semantic_evaluations": "0_OF_34",
        "operator_observed_population": "34_OF_34",
        "measured_github_prior_population": "27_DISTINCT_LANGUAGES_356_RELATIONS",
        "status": "OPERATOR_OBSERVED_WITNESSES_PENDING_OWNING_CATALOG_BYTES",
    }
    if any(witness_gate.get(key) != value for key, value in expected_witness_gate.items()):
        raise PreparationError("native-glyph witness gate does not reconstruct from 34 rows")
    improvement_schema = next(
        parse_fields(line)[1]
        for line in hbp_rows
        if line.startswith("IMPROVEMENTAUDITSCHEMA|")
    )
    expected_improvement_schema = {
        "schema": "ASOLARIA_IMPROVEMENT_CLAIM_V1",
        "function_families": ",".join(SELF_IMPROVING_FUNCTION_FAMILIES),
        "precommit_fields": "PARENT_PID,HELDOUT_SET_SHA256,EVALUATOR_SHA256,EVALUATOR_VERSION,COMMITTED_TICK_US",
        "ordering": "PRECOMMIT_TICK_LT_CHILD_CREATED_TICK_LE_CHILD_EVALUATED_TICK",
        "evaluation_fields": "SUBJECT_PID,SCORE_PPM,TRIAL_SCORES_PPM,SEEDS,CONFIDENCE_LOW_PPM,CONFIDENCE_HIGH_PPM,EVALUATED_TICK_US",
        "fixed_inputs": "PARENT_AND_CHILD_MATCH_PRECOMMITTED_HELDOUT_EVALUATOR_VERSION",
        "stochastic_gate": "REPEATED_TRIALS_UNIQUE_SEED_PER_TRIAL_EQUAL_TRIAL_COUNTS",
        "acceptance": "DELTA_GT_0_AND_DELTA_GT_NOISE_AND_CHILD_CI_LOW_GT_PARENT_CI_HIGH",
        "evidence_gates": "LEAKAGE_AUDIT,LINEAGE_RECEIPT,REVERSE_REPLAY,ROLLBACK_STATE",
        "materialized_precommits": "0",
        "materialized_claims": "0",
        "historical_import": "PENDING_EXACT_OWNING_RECEIPTS",
        "status": "DESIGN_SCHEMA_READY_NO_IMPROVEMENT_CLAIM_IMPORTED",
    }
    if any(
        improvement_schema.get(key) != value
        for key, value in expected_improvement_schema.items()
    ):
        raise PreparationError("improvement audit schema boundary mismatch")
    glyph_schema = next(
        parse_fields(line)[1]
        for line in hbp_rows
        if line.startswith("GLYPHLANGUAGEAUDITSCHEMA|")
    )
    expected_glyph_schema = {
        "schema": "ASOLARIA_GLYPH_LANGUAGE_EVALUATION_V1",
        "independent_tests": "BEYOND_SYMBOL_SUBSTITUTION,NOVEL_COMPOSITION,REVERSIBLE_NATIVE_OMEGA,CROSS_CUBE_MEANING,NATIVE_LANGUAGE_RETAINED",
        "required_receipts": "TRAINING_CORPUS,ABSENCE_AUDIT,FORWARD_TRANSLATION,REVERSE_TRANSLATION,CROSS_CUBE_ALIGNMENT",
        "materialized_evaluations": "0",
        "witness_objects": "34",
        "historical_catalog_import": "PENDING_EXACT_OWNING_RECEIPTS",
        "status": "DESIGN_SCHEMA_READY_NO_SEMANTIC_EVALUATION_IMPORTED",
    }
    if any(glyph_schema.get(key) != value for key, value in expected_glyph_schema.items()):
        raise PreparationError("glyph-language audit schema boundary mismatch")
    forbidden_materialized_tags = {
        "IMPROVEMENTPRECOMMIT",
        "IMPROVEMENTEVALUATION",
        "IMPROVEMENTCLAIM",
        "GLYPHLANGUAGEEVALUATION",
    }
    if forbidden_materialized_tags & set(tags):
        raise PreparationError("cold preparation cannot contain unimported materialized claims")
    dag_fields = [
        parse_fields(line)[1] for line in hbp_rows if line.startswith("PIDDAGNODE|")
    ]
    dag_nodes: list[PIDDagNode] = []
    for item in dag_fields:
        parent_pids = () if item["parent_pids"] == "NONE" else tuple(item["parent_pids"].split(","))
        parent_hashes = (
            ()
            if item["parent_identity_sha256s"] == "NONE"
            else tuple(item["parent_identity_sha256s"].split(","))
        )
        node = PIDDagNode(
            kind=item["kind"],
            content_sha256=item["content_sha256"],
            owner_reference=item["owner_reference"],
            geometry=item["geometry"],
            floor=int(item["floor"]),
            generation=int(item["generation"]),
            parent_pids=parent_pids,
            parent_identity_sha256s=parent_hashes,
            source_state_receipt_sha256=item["source_state_receipt_sha256"],
            metadata_sha256=item["metadata_sha256"],
            schema_version=item["schema"],
            status=item["status"],
        )
        if node.pid != item["pid"] or node.identity_sha256 != item["identity_sha256"]:
            raise PreparationError(f"PID DAG row cannot reproduce identity: {item['kind']}")
        if len(parent_pids) != int(item["parent_count"]):
            raise PreparationError(f"PID DAG parent count mismatch: {item['kind']}")
        dag_nodes.append(node)

    omega_rows = [
        parse_fields(line)[1] for line in hbp_rows if line.startswith("OMEGAFLOOR|")
    ]
    omega_pids = {item["pid"] for item in omega_rows}
    if len(omega_pids) != len(omega_rows):
        raise PreparationError("Omega PID identities are not unique")
    dag_identities = {node.pid: node.identity_sha256 for node in dag_nodes}
    omega_identities = {item["pid"]: item["identity_sha256"] for item in omega_rows}
    all_identities = dag_identities | omega_identities
    reconstructed_omegas: dict[str, OmegaCoordinate] = {}
    for item in omega_rows:
        refinement = None if item["refinement_level"] == "NA" else int(item["refinement_level"])
        projected_cell = None if item["projected_cell"] == "NA" else int(item["projected_cell"])
        coordinate = OmegaCoordinate(
            geometry=GeometryFamily(item["geometry"]),
            floor=int(item["floor"]),
            parent_omega_pid=item["parent_omega_pid"],
            parent_identity_sha256=item["parent_identity_sha256"],
            source_state_receipt_sha256=item["source_state_receipt_sha256"],
            owner_reference=item["owner_reference"],
            slot_address=item["slot_address"],
            slot_version=int(item["slot_version"]),
            refinement_level=refinement,
            projected_cell=projected_cell,
        )
        if coordinate.pid != item["pid"] or coordinate.identity_sha256 != item["identity_sha256"]:
            raise PreparationError(f"Omega row cannot reproduce identity: {item['label']}")
        parent = coordinate.parent_omega_pid
        if parent not in all_identities:
            raise PreparationError(f"Omega parent PID is not traceable: {parent}")
        if all_identities[parent] != coordinate.parent_identity_sha256:
            raise PreparationError(f"Omega parent identity hash mismatch: {item['label']}")
        reconstructed_omegas[item["label"]] = coordinate
    expected_omega_parents = {
        "OMEGA_6_F1": "OMEGA_6_F2",
        "OMEGA_6_F2": "OMEGA_6_F3",
        "OMEGA_6_F3": "OMEGA_12_F1",
        "OMEGA_12_F1": "OMEGA_PI_F1_L4_R0",
    }
    for child_label, parent_label in expected_omega_parents.items():
        if reconstructed_omegas[child_label].parent_omega_pid != reconstructed_omegas[parent_label].pid:
            raise PreparationError(f"Omega floor/geometry chain skipped at {child_label}")
    roots = [node for node in dag_nodes if node.kind == "OMEGA_NAMESPACE_ROOT"]
    if len(roots) != 1 or reconstructed_omegas["OMEGA_PI_F1_L4_R0"].parent_omega_pid != roots[0].pid:
        raise PreparationError("outer finite Omega does not resolve to the unique namespace root")

    dag_report = verify_pid_dag(tuple(dag_nodes), omega_identities)
    if dag_report["status"] != "PASS":
        raise PreparationError(f"PID DAG verification failed: {dag_report}")
    gate = next(parse_fields(line)[1] for line in hbp_rows if line.startswith("PIDDAGGATE|"))
    for key, value in dag_report.items():
        if gate.get(key) != str(value):
            raise PreparationError(f"PID DAG gate field mismatch: {key}")

    lineage_rows = [
        parse_fields(line)[1] for line in hbp_rows if line.startswith("LINEAGEEDGE|")
    ]
    actual_links = {
        (item["child_pid"], item["parent_pid"], int(item["ordinal"])): item
        for item in lineage_rows
    }
    expected_links = 0
    for node in dag_nodes:
        for ordinal, (parent_pid, parent_hash) in enumerate(node.parent_pairs(), 1):
            expected_links += 1
            item = actual_links.get((node.pid, parent_pid, ordinal))
            if item is None or item["parent_identity_sha256"] != parent_hash:
                raise PreparationError(f"lineage edge missing or mismatched: {node.kind}:{ordinal}")
            identity = sha256_bytes(
                (
                    "ASOLARIA_LINEAGE_EDGE_V1|"
                    f"{node.pid}|{parent_pid}|{ordinal}|{parent_hash}"
                ).encode("utf-8")
            )
            if item["identity_sha256"] != identity or item["pid"] != "PID-" + identity:
                raise PreparationError(f"lineage edge identity mismatch: {node.kind}:{ordinal}")
    if expected_links != len(lineage_rows):
        raise PreparationError("unexpected lineage edge rows")

    pid_rows = [parse_fields(line)[1] for line in hbp_rows if line.startswith("PIDNODE|")]
    for item in pid_rows:
        selector = RouteSelector(
            axes_60d=tuple(int(value) for value in item["selector_axes"].split(",")),
            glyph_family=item["selector_glyph_family"],
            glyph_levels=tuple(item["selector_glyph_levels"].split(",")),
            language=item["selector_language"],
            executor=item["selector_executor"],
            pipe=item["selector_pipe"],
            operation=item["selector_operation"],
            room=item["selector_room"],
            proof_tier=item["selector_proof_tier"],
            runtime_mode=item["selector_runtime_mode"],
            colony=item["selector_colony"],
            seat=item["selector_seat"],
            temporal_slice=item["selector_temporal_slice"],
        )
        descriptor = NodeDescriptor(
            geometry=GeometryFamily(item["geometry"]),
            address=tuple(int(value) for value in item["address"].split(",") if value),
            generation=int(item["generation"]),
            content_sha256=item["content_sha256"],
            parent_pid=item["parent_pid"],
            owner_reference=item["owner_reference"],
            selector=selector,
            storage=StorageClass(item["storage"]),
            logical_tick_us=int(item["logical_tick"]),
            feedback_delay_us=int(item["feedback_delay"]),
            body_kind=item["body_kind"],
        )
        if (
            descriptor.pid != item["pid"]
            or descriptor.identity_sha256 != item["identity_sha256"]
            or selector.commitment != item["route_selector_sha256"]
        ):
            raise PreparationError(f"cube body PID cannot be reproduced: ordinal {item['ordinal']}")

    gnn_rows = [parse_fields(line)[1] for line in hbp_rows if line.startswith("GNNEDGE|")]
    for item in gnn_rows:
        proposal = EdgeProposal(
            edge_id=item["edge_id"],
            pair_id=item["pair_id"],
            source_pid=item["source_pid"],
            target_pid=item["target_pid"],
            relation=item["relation"],
            event_id=item["event_id"],
            payload_sha256=item["payload_sha256"],
            logical_tick_us=int(item["logical_tick"]),
            status=item["status"],
            learned=int(item["learned"]),
        )
        if proposal.pid != item["pid"] or proposal.identity_sha256 != item["identity_sha256"]:
            raise PreparationError(f"GNN proposal PID cannot be reproduced: {item['edge_id']}")

    recovery = next(
        parse_fields(line)[1] for line in hbp_rows if line.startswith("RECOVERYRECEIPT|")
    )
    if (
        recovery["source_sha256"] != recovery["recovered_sha256"]
        or recovery["source_bytes"] != recovery["recovered_bytes"]
        or recovery["exact_restore"] != "1"
        or recovery["pid"] not in dag_identities
        or dag_identities[recovery["pid"]] != recovery["identity_sha256"]
    ):
        raise PreparationError("Path-3 recovery receipt is not byte-exact or PID-traceable")

    projection = next(
        parse_fields(line)[1] for line in hbp_rows if line.startswith("PATH3PROJECTION|")
    )
    target = NestedUniverseAddress(
        sphere_level=int(projection["target_sphere_level"]),
        sphere_cell=int(projection["target_sphere_cell"]),
        sector_12=int(projection["target_sector_12"]),
        apex_6=int(projection["target_apex_6"]),
        vertex_8=int(projection["target_vertex_8"]),
        lane=int(projection["target_lane"]),
        epoch=int(projection["target_epoch"]),
        glyph_level=projection["target_glyph_level"],
        language=projection["target_language"],
        question_index=int(projection["target_question_index"]),
    )
    descriptor = Path3Projection(
        function_sha256=projection["function_sha256"],
        signature_lineage_commitment_sha256=projection[
            "signature_lineage_commitment_sha256"
        ],
        omega_keystring_sha256=projection["omega_keystring_sha256"],
        source_pid=projection["source_pid"],
        target=target,
        geometry=GeometryFamily(projection["projection_geometry"]),
    )
    if (
        descriptor.pid != projection["pid"]
        or descriptor.identity_sha256 != projection["identity_sha256"]
        or descriptor.projection_id != projection["projection_id"]
        or descriptor.target.address_id != projection["target_address_id"]
    ):
        raise PreparationError("Path-3 projection PID cannot be reproduced")
    if (
        projection.get("signature_lineage_evidence")
        != "COLD_LABEL_COMMITMENT_NOT_MEASURED_CHANNEL"
        or projection.get("owning_signature_receipt_import") != "PENDING_LIRIS_COPY"
    ):
        raise PreparationError("Path-3 signature lineage evidence boundary mismatch")

    source_rows = [
        parse_fields(line)[1] for line in hbp_rows if line.startswith("ARTIFACTSOURCE|")
    ]
    source_map = {item["file"]: item for item in source_rows}
    for source_name in ("model.py", "prepare.py", "test_model.py"):
        source_path = Path(__file__).resolve().parent / source_name
        item = source_map.get(source_name)
        if (
            item is None
            or item["bytes"] != str(source_path.stat().st_size)
            or item["sha256"] != sha256_file(source_path)
        ):
            raise PreparationError(f"sealed source row is stale: {source_name}")
    promotion = next(
        parse_fields(line)[1] for line in hbp_rows if line.startswith("ENGINEPROMOTION|")
    )
    if (
        promotion.get("authority_identity") != "0"
        or promotion.get("claim_specific_proof") != "0"
        or promotion.get("claim_proof_boundary")
        != "EXACT_HELDOUT_AND_GLYPH_SEMANTIC_RECEIPTS_NOT_IMPORTED"
        or promotion.get("checks_pass") != "0"
        or promotion.get("trilateral_pass") != "0"
        or promotion.get("active_engine") != "0"
        or promotion.get("status") != "HELD"
    ):
        raise PreparationError("engine promotion escaped unresolved authority or claim-proof holds")
    runtime = next(parse_fields(line)[1] for line in hbp_rows if line.startswith("RUNTIMEBOUNDARY|"))
    for key in ("gnn_train_calls", "learned_external_edges", "scan_calls", "process_launch", "fabric_write"):
        if runtime.get(key) != "0":
            raise PreparationError(f"cold boundary violated: {key}")
    footer = next(parse_fields(line)[1] for line in hbp_rows if line.startswith("FLOOR1PREPFTR|"))
    if (
        footer.get("status") != "PREPARATION_PASS"
        or footer.get("collision_detection") != "PASS"
        or footer.get("collision_resolution") != "HELD_FOR_SUPERVISOR"
    ):
        raise PreparationError("preparation footer did not pass")

    sums_path = output / SUMS_NAME
    expected_sums = "".join(
        f"{sha256_file(path)}  {path.name}\n" for path in (hbp_path, hbi_path, hex_path)
    ).encode("ascii")
    if sums_path.read_bytes() != expected_sums:
        raise PreparationError("SHA256SUMS mismatch")
    _verify_sidecar(sums_path)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    build_parser = commands.add_parser("build")
    build_parser.add_argument("--output", type=Path, required=True)
    build_parser.add_argument("--cdc-group-receipt", type=Path, required=True)
    verify_parser = commands.add_parser("verify")
    verify_parser.add_argument("--output", type=Path, required=True)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "build":
            build(args.output.resolve(), args.cdc_group_receipt.resolve())
        else:
            verify(args.output.resolve())
    except (OSError, PreparationError, ValueError) as error:
        print(row("FLOOR1PREPFAIL", error=type(error).__name__, detail=error))
        return 2
    output = args.output.resolve()
    print(
        row(
            "FLOOR1PREPPASS",
            command=args.command,
            output=output,
            hbp_sha256=sha256_file(output / HBP_NAME),
            hbi_sha256=sha256_file(output / HBI_NAME),
            omega_gnn="PREPARED_NOT_INGESTED",
            gnn_train_calls=0,
            process_launch=0,
            status="PASS",
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
