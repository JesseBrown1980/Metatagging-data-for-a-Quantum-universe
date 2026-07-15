from __future__ import annotations

import ast
import inspect
import shutil
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from trilateral.omniverse_pid_particles_v1 import model
from trilateral.omniverse_pid_particles_v1 import prepare


def selector(language: str = "BEHCS") -> model.RouteSelector:
    return model.RouteSelector(
        axes_60d=tuple(range(60)),
        glyph_family="BEHCS-1024",
        glyph_levels=("BEHCS-256", "BEHCS-1024", "HYPERBEHCS-60D+"),
        language=language,
        executor="CUBE_PID_ENGINE_CANDIDATE",
        pipe="HOOKWALL_GNN_REVERSE_GAIN",
        operation="TRAIN_FLOOR1",
        room="OMEGA_HOTEL_FLOOR1",
        proof_tier="MEASURED_REPO",
        runtime_mode="E0_COLD_PREPARATION",
        colony="ASOLARIA",
        seat="LIRIS",
        temporal_slice="2026-07-15-EPOCH-0",
    )


def node(address: tuple[int, ...], language: str = "BEHCS") -> model.NodeDescriptor:
    return model.NodeDescriptor(
        geometry=model.GeometryFamily.CUBIC_6_APEX,
        address=address,
        generation=len(address),
        content_sha256="ab" * 32,
        parent_pid="PID-ROOT" if address else "NONE",
        owner_reference="APEX-HUMAN-JESSE",
        selector=selector(language),
        storage=model.StorageClass.GITRAM_STUB,
        logical_tick_us=len(address),
        feedback_delay_us=1,
    )


class GeometryTests(unittest.TestCase):
    def test_cube_is_omnicentric_and_preserves_distance(self) -> None:
        for origin in range(8):
            self.assertEqual(model.cube_recenter(origin, origin), 0)
            mapped = {model.cube_recenter(origin, vertex) for vertex in range(8)}
            self.assertEqual(mapped, set(range(8)))
            for left in range(8):
                for right in range(8):
                    before = (left ^ right).bit_count()
                    after = (
                        model.cube_recenter(origin, left)
                        ^ model.cube_recenter(origin, right)
                    ).bit_count()
                    self.assertEqual(before, after)

    def test_six_apex_directions_around_q3_are_not_q6(self) -> None:
        q3 = model.hypercube_counts(3)
        q6 = model.hypercube_counts(6)
        self.assertEqual((q3["vertices"], q3["undirected_edges"]), (8, 12))
        self.assertEqual((q6["vertices"], q6["undirected_edges"]), (64, 192))
        self.assertNotEqual(q3, q6)

    def test_cube_faces_are_a_double_cover(self) -> None:
        edges = model.cube_edges()
        self.assertEqual(len(edges), 12)
        self.assertEqual(len(model.cube_face_cycles()), 6)
        report = model.verify_cycle_double_cover(edges, model.cube_face_cycles())
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["cycle_memberships"], 24)

    def test_tetra_has_six_edges_twelve_directions_and_double_cover(self) -> None:
        edges = model.tetra_edges()
        self.assertEqual(len(edges), 6)
        self.assertEqual(len(edges) * 2, 12)
        self.assertEqual(len(model.tetra_face_cycles()), 4)
        report = model.verify_cycle_double_cover(edges, model.tetra_face_cycles())
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["cycle_memberships"], 12)
        for origin in range(4):
            self.assertEqual(model.tetra_recenter(origin, origin), 0)
            self.assertEqual(
                {model.tetra_recenter(origin, vertex) for vertex in range(4)},
                set(range(4)),
            )

    def test_sphere_refinement_is_a_limit_not_pi_literal_sides(self) -> None:
        for level in (0, 1, 4):
            report = model.sphere_refinement(level)
            self.assertEqual(report["euler_characteristic"], 2)
            self.assertEqual(report["face_edge_incidence"], report["double_edge_incidence"])
            self.assertEqual(report["triangular_faces"], 20 * (4**level))
            self.assertEqual(report["pi_role"], "ANGLE_AND_MEASURE_CONTINUUM_LIMIT")
        self.assertEqual(model.sphere_projection_window(4, 5104, 16), tuple(range(5104, 5120)))
        with self.assertRaises(ValueError):
            model.sphere_projection_window(4, 5119, 2)
        with self.assertRaises(ValueError):
            model.sphere_projection_window(4, 0, 0)

    def test_each_nested_boundary_has_its_own_omega_intersection(self) -> None:
        hierarchy = model.omega_hierarchy(4)
        self.assertEqual(hierarchy["sphere_cells"], 5120)
        self.assertEqual(hierarchy["omega_6_positions"], 5120 * 12)
        self.assertEqual(hierarchy["omega_12_positions"], 5120)
        self.assertEqual(hierarchy["omega_pi_positions"], 1)
        self.assertEqual(hierarchy["apex_positions"], 5120 * 12 * 6)
        self.assertEqual(hierarchy["vertex_positions"], 5120 * 12 * 6 * 8)
        self.assertEqual(
            hierarchy["materialization_semantics"],
            "FINITE_ADDRESS_CAPACITY_NOT_RESIDENT_COUNT",
        )

    def test_bad_double_cover_fails(self) -> None:
        report = model.verify_cycle_double_cover(model.tetra_edges(), ((0, 1, 2),))
        self.assertEqual(report["status"], "FAIL")


class IdentityAndRoutingTests(unittest.TestCase):
    def test_pid_binds_lineage_content_selector_storage_and_time(self) -> None:
        first = node((1,))
        second = node((2,))
        translated = node((1,), language="PORTUGUESE")
        self.assertTrue(first.pid.startswith("PID-"))
        self.assertNotEqual(first.pid, second.pid)
        self.assertNotEqual(first.pid, translated.pid)
        self.assertEqual(first.pid, node((1,)).pid)
        self.assertEqual(first.pid, "PID-" + first.identity_sha256)

    def test_identity_encoding_is_typed_and_boundary_safe(self) -> None:
        values = {
            model.digest(1),
            model.digest("1"),
            model.digest((1, 2)),
            model.digest([1, 2]),
            model.digest(("a,b", "c")),
            model.digest(("a", "b,c")),
        }
        self.assertEqual(len(values), 6)

    def test_selector_cannot_flatten_below_sixty_axes(self) -> None:
        values = selector().__dict__ | {"axes_60d": tuple(range(59))}
        with self.assertRaises(ValueError):
            model.RouteSelector(**values)

    def test_brown_hilbert_address_expands_without_enumeration(self) -> None:
        address: tuple[int, ...] = ()
        for digit in (7, 99, 1023, 0):
            address = model.brown_hilbert_child(address, digit)
        self.assertEqual(address, (7, 99, 1023, 0))
        with self.assertRaises(ValueError):
            model.brown_hilbert_child(address, 1024)

    def test_question_ids_separate_languages_and_indices(self) -> None:
        base = dict(
            cube_pid=node((1,)).pid,
            geometry=model.GeometryFamily.CUBIC_6_APEX,
            glyph_level="HYPERBEHCS-60D+",
            epoch=1,
            index=10**12,
        )
        english = model.QuestionAddress(language="EN", **base)
        portuguese = model.QuestionAddress(language="PT-BR", **base)
        self.assertNotEqual(english.question_id, portuguese.question_id)
        self.assertEqual(english.question_id, model.QuestionAddress(language="EN", **base).question_id)

    def test_nested_universe_address_has_finite_floor_and_unbounded_levels(self) -> None:
        address = model.NestedUniverseAddress(
            sphere_level=3,
            sphere_cell=1279,
            sector_12=11,
            apex_6=5,
            vertex_8=7,
            lane=9,
            epoch=10,
            glyph_level="HYPERBEHCS-60D+",
            language="PT-BR",
            question_index=10**18,
        )
        self.assertEqual(address.geometric_capacity_at_level, 1280 * 12 * 6 * 8)
        self.assertTrue(address.address_id.startswith("ADDR-"))

    def test_omega_bits_are_distinct_by_family_floor_and_finite_projection(self) -> None:
        owner = "APEX-HUMAN-JESSE"
        parent_hash = "44" * 32
        source_receipt = "55" * 32
        six_floors = [
            model.OmegaCoordinate(
                model.GeometryFamily.CUBIC_6_APEX,
                floor,
                parent_omega_pid=f"PID-PARENT-{floor}",
                parent_identity_sha256=parent_hash,
                source_state_receipt_sha256=source_receipt,
                owner_reference=owner,
                slot_address=f"Q3/OMEGA6/F{floor}",
                slot_version=1,
            )
            for floor in (1, 2, 3)
        ]
        twelve = model.OmegaCoordinate(
            model.GeometryFamily.TETRA_12_DIRECTED,
            1,
            parent_omega_pid="PID-OMEGA-PI",
            parent_identity_sha256=parent_hash,
            source_state_receipt_sha256=source_receipt,
            owner_reference=owner,
            slot_address="TETRA/OMEGA12/F1",
            slot_version=1,
        )
        pi_zero = model.OmegaCoordinate(
            model.GeometryFamily.SPHERE_PI_LIMIT,
            1,
            parent_omega_pid="PID-OMEGA-ROOT",
            parent_identity_sha256=parent_hash,
            source_state_receipt_sha256=source_receipt,
            owner_reference=owner,
            slot_address="PI/L4/R0",
            slot_version=1,
            refinement_level=4,
            projected_cell=0,
        )
        pi_one = model.OmegaCoordinate(
            model.GeometryFamily.SPHERE_PI_LIMIT,
            1,
            parent_omega_pid="PID-OMEGA-ROOT",
            parent_identity_sha256=parent_hash,
            source_state_receipt_sha256=source_receipt,
            owner_reference=owner,
            slot_address="PI/L4/R1",
            slot_version=1,
            refinement_level=4,
            projected_cell=1,
        )
        coordinates = [*six_floors, twelve, pi_zero, pi_one]
        self.assertEqual(len({item.omega_bit_id for item in coordinates}), len(coordinates))
        self.assertEqual(len({item.pid for item in coordinates}), len(coordinates))
        self.assertTrue(all(item.lineage_sha256 for item in coordinates))
        self.assertEqual([item.label for item in six_floors], ["OMEGA_6_F1", "OMEGA_6_F2", "OMEGA_6_F3"])
        self.assertEqual(pi_zero.label, "OMEGA_PI_F1_L4_R0")
        with self.assertRaises(ValueError):
            model.OmegaCoordinate(
                model.GeometryFamily.SPHERE_PI_LIMIT,
                1,
                parent_omega_pid="PID-OMEGA-ROOT",
                parent_identity_sha256=parent_hash,
                source_state_receipt_sha256=source_receipt,
                owner_reference=owner,
                slot_address="PI/MISSING",
                slot_version=1,
            )
        with self.assertRaises(ValueError):
            model.OmegaCoordinate(
                model.GeometryFamily.SPHERE_PI_LIMIT,
                1,
                parent_omega_pid="PID-OMEGA-ROOT",
                parent_identity_sha256=parent_hash,
                source_state_receipt_sha256=source_receipt,
                owner_reference=owner,
                slot_address="PI/L4/BAD",
                slot_version=1,
                refinement_level=4,
                projected_cell=5120,
            )
        with self.assertRaises(ValueError):
            model.OmegaCoordinate(
                model.GeometryFamily.CUBIC_6_APEX,
                1,
                parent_omega_pid="PID-PARENT",
                parent_identity_sha256=parent_hash,
                source_state_receipt_sha256=source_receipt,
                owner_reference=owner,
                slot_address="Q3/BAD",
                slot_version=1,
                refinement_level=4,
                projected_cell=0,
            )

    def test_multi_parent_pid_dag_reconstructs_full_path3_lineage(self) -> None:
        owner = "APEX-HUMAN-JESSE"

        def make(
            kind: str,
            generation: int,
            parents: tuple[model.PIDDagNode, ...] = (),
            geometry: str = "CUBIC_6_APEX_Q3",
        ) -> model.PIDDagNode:
            return model.PIDDagNode(
                kind=kind,
                content_sha256=model.digest("content", kind, generation),
                owner_reference=owner,
                geometry=geometry,
                floor=1,
                generation=generation,
                parent_pids=tuple(parent.pid for parent in parents),
                parent_identity_sha256s=tuple(parent.identity_sha256 for parent in parents),
                source_state_receipt_sha256=model.digest("receipt", kind),
                metadata_sha256=model.digest("metadata", kind),
            )

        apex = tuple(make(f"CUBE_BODY_APEX_{index}", 0) for index in range(6))
        slot = make("OMEGA_SLOT", 0)
        trained = make("TRAINED_OMEGA_VERSION", 1, (*apex, slot))
        function = make("PROJECTED_FUNCTION", 2, (trained,), "MULTI_GEOMETRY")
        adapters = tuple(
            make(f"GEOMETRY_ADAPTER_{name}", 3, (function,), name)
            for name in ("Q3", "TETRA12", "PI_L4_R0")
        )
        wave = make("WAVE_COMB_STEP", 4, adapters, "MULTI_GEOMETRY")
        forward = make("GNN_PROPOSAL", 5, (wave,), "MULTI_GEOMETRY")
        reverse = make("REVERSE_GAIN_PROPOSAL", 5, (wave,), "MULTI_GEOMETRY")
        recovery = make("RECOVERY_RECEIPT", 6, (forward, reverse), "MULTI_GEOMETRY")
        nodes = (*apex, slot, trained, function, *adapters, wave, forward, reverse, recovery)
        report = model.verify_pid_dag(nodes)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["nodes"], 16)
        self.assertEqual(report["multi_parent_nodes"], 3)
        self.assertEqual(report["parent_edges"], 18)
        self.assertTrue(all(item.pid == "PID-" + item.identity_sha256 for item in nodes))

        broken = model.PIDDagNode(
            kind=recovery.kind,
            content_sha256=recovery.content_sha256,
            owner_reference=recovery.owner_reference,
            geometry=recovery.geometry,
            floor=recovery.floor,
            generation=recovery.generation,
            parent_pids=recovery.parent_pids,
            parent_identity_sha256s=(recovery.parent_identity_sha256s[0], "ff" * 32),
            source_state_receipt_sha256=recovery.source_state_receipt_sha256,
            metadata_sha256=recovery.metadata_sha256,
        )
        broken_report = model.verify_pid_dag((*nodes[:-1], broken))
        self.assertEqual(broken_report["status"], "FAIL")
        self.assertGreater(broken_report["parent_hash_mismatches"], 0)

    def test_path3_digital_projection_roundtrips_each_geometry(self) -> None:
        body = b"digitally clonable function body and keyed signature lineage"
        key = b"omega-keystring-test-fixture"
        for geometry in model.GeometryFamily:
            projected = model.reversible_digital_projection(body, key, geometry.value)
            self.assertNotEqual(projected, body)
            restored = model.reversible_digital_projection(projected, key, geometry.value)
            self.assertEqual(restored, body)
        target = model.NestedUniverseAddress(0, 0, 0, 0, 0, 0, 0, "BEHCS", "EN", 0)
        descriptor = model.Path3Projection(
            function_sha256="11" * 32,
            signature_lineage_commitment_sha256="22" * 32,
            omega_keystring_sha256="33" * 32,
            source_pid="PID-SOURCE",
            target=target,
            geometry=model.GeometryFamily.CUBIC_6_APEX,
        )
        self.assertTrue(descriptor.projection_id.startswith("PATH3-"))
        self.assertEqual(descriptor.pid, "PID-" + descriptor.identity_sha256)
        with self.assertRaises(ValueError):
            model.Path3Projection(
                function_sha256="not-a-sha",
                signature_lineage_commitment_sha256="22" * 32,
                omega_keystring_sha256="33" * 32,
                source_pid="PID-SOURCE",
                target=target,
                geometry=model.GeometryFamily.CUBIC_6_APEX,
            )


class ImprovementAndGlyphLanguageTests(unittest.TestCase):
    @staticmethod
    def content_pid(label: str) -> str:
        return "PID-" + model.digest("TEST_CONTENT_PID", label)

    def improvement_parts(
        self, stochastic: bool = False
    ) -> tuple[
        model.ImprovementPrecommit,
        model.HeldoutEvaluation,
        model.HeldoutEvaluation,
    ]:
        parent_pid = self.content_pid("parent")
        child_pid = self.content_pid("child")
        heldout = model.digest("sealed-heldout-set")
        evaluator = model.digest("sealed-evaluator")
        precommit = model.ImprovementPrecommit(
            parent_pid=parent_pid,
            heldout_set_sha256=heldout,
            evaluator_sha256=evaluator,
            evaluator_version="EVALUATOR-V1",
            committed_tick_us=10,
        )
        if stochastic:
            parent_scores = (390_000, 400_000, 410_000)
            child_scores = (440_000, 450_000, 460_000)
            parent_seeds = child_seeds = (101, 202, 303)
            parent_bounds = (388_000, 412_000)
            child_bounds = (438_000, 462_000)
        else:
            parent_scores = (400_000,)
            child_scores = (450_000,)
            parent_seeds = child_seeds = ()
            parent_bounds = (400_000, 400_000)
            child_bounds = (450_000, 450_000)
        parent = model.HeldoutEvaluation(
            subject_pid=parent_pid,
            heldout_set_sha256=heldout,
            evaluator_sha256=evaluator,
            evaluator_version="EVALUATOR-V1",
            score_ppm=400_000,
            trial_scores_ppm=parent_scores,
            seeds=parent_seeds,
            confidence_low_ppm=parent_bounds[0],
            confidence_high_ppm=parent_bounds[1],
            evaluated_tick_us=15,
            stochastic=stochastic,
        )
        child = model.HeldoutEvaluation(
            subject_pid=child_pid,
            heldout_set_sha256=heldout,
            evaluator_sha256=evaluator,
            evaluator_version="EVALUATOR-V1",
            score_ppm=450_000,
            trial_scores_ppm=child_scores,
            seeds=child_seeds,
            confidence_low_ppm=child_bounds[0],
            confidence_high_ppm=child_bounds[1],
            evaluated_tick_us=30,
            stochastic=stochastic,
        )
        return precommit, parent, child

    def valid_improvement(
        self, stochastic: bool = False, **changes: object
    ) -> model.ImprovementClaim:
        precommit, parent, child = self.improvement_parts(stochastic)
        values: dict[str, object] = {
            "function_family": "LEARNER",
            "precommit": precommit,
            "parent_evaluation": parent,
            "child_evaluation": child,
            "child_created_tick_us": 20,
            "noise_floor_ppm": 5_000,
            "leakage_audit_sha256": model.digest("leakage-audit"),
            "lineage_receipt_sha256": model.digest("lineage-receipt"),
            "reverse_replay_receipt_sha256": model.digest("reverse-replay"),
            "rollback_state_sha256": model.digest("rollback-state"),
            "leakage_audit_pass": True,
            "reverse_replay_pass": True,
        }
        values.update(changes)
        return model.ImprovementClaim(**values)

    def glyph_values(self) -> dict[str, object]:
        witness = model.NativeGlyphLanguageWitness(
            body_kind="BASE",
            body_ordinal=1,
            body_leaf_sha256=model.digest("body-leaf", 1),
            body_receipt_sha256=model.digest("body-receipt", 1),
            formation_receipt_sha256=model.digest("formation-receipt"),
            evidence_class="OPERATOR_OBSERVED",
            owning_catalog_import="PENDING_CURRENT_34_CATALOG_CITATION",
        )
        message = model.digest("native-message")
        semantic = model.digest("semantic-meaning")
        catalog = model.digest("native-catalog")
        return {
            "witness_pid": witness.pid,
            "cube_body_pid": witness.body_pid,
            "native_language_pid": witness.native_language_pid,
            "aligned_cube_body_pid": self.content_pid("aligned-cube"),
            "training_corpus_sha256": model.digest("training-corpus"),
            "native_message_sha256": message,
            "omega_message_sha256": model.digest("omega-message"),
            "recovered_native_message_sha256": message,
            "native_semantic_sha256": semantic,
            "aligned_semantic_sha256": semantic,
            "native_catalog_before_sha256": catalog,
            "native_catalog_after_sha256": catalog,
            "absence_audit_sha256": model.digest("absence-audit"),
            "forward_translation_receipt_sha256": model.digest("forward-receipt"),
            "reverse_translation_receipt_sha256": model.digest("reverse-receipt"),
            "cross_cube_receipt_sha256": model.digest("cross-cube-receipt"),
            "grammar_rule_count": 3,
            "compositional_operator_count": 2,
            "novel_message_absent_from_training": True,
            "symbol_substitution_only": False,
        }

    def test_deterministic_improvement_reconstructs_from_precommit_and_receipts(self) -> None:
        claim = self.valid_improvement()
        self.assertEqual(claim.delta_ppm, 50_000)
        self.assertEqual(claim.pid, "PID-" + claim.identity_sha256)
        self.assertLess(claim.precommit.committed_tick_us, claim.child_created_tick_us)

    def test_stochastic_improvement_records_repeated_seeded_trials_and_bounds(self) -> None:
        claim = self.valid_improvement(stochastic=True)
        self.assertEqual(len(claim.parent_evaluation.seeds), 3)
        self.assertGreater(
            claim.child_evaluation.confidence_low_ppm,
            claim.parent_evaluation.confidence_high_ppm,
        )

    def test_precommit_must_precede_child_generation(self) -> None:
        precommit, parent, child = self.improvement_parts()
        late = replace(precommit, committed_tick_us=20)
        with self.assertRaises(ValueError):
            self.valid_improvement(
                precommit=late,
                parent_evaluation=parent,
                child_evaluation=child,
            )

    def test_parent_and_child_must_use_same_precommitted_inputs(self) -> None:
        precommit, parent, child = self.improvement_parts()
        changed = replace(child, heldout_set_sha256=model.digest("changed-heldout"))
        with self.assertRaises(ValueError):
            self.valid_improvement(
                precommit=precommit,
                parent_evaluation=parent,
                child_evaluation=changed,
            )

    def test_stochastic_evaluation_rejects_missing_trials_or_seeds(self) -> None:
        _, _, child = self.improvement_parts(stochastic=True)
        with self.assertRaises(ValueError):
            replace(child, trial_scores_ppm=(450_000,), seeds=(101,))
        with self.assertRaises(ValueError):
            replace(child, seeds=(101, 202))

    def test_improvement_must_clear_noise_and_nonoverlapping_confidence(self) -> None:
        with self.assertRaises(ValueError):
            self.valid_improvement(noise_floor_ppm=50_000)
        _, _, child = self.improvement_parts(stochastic=True)
        overlapping = replace(child, confidence_low_ppm=410_000)
        with self.assertRaises(ValueError):
            self.valid_improvement(stochastic=True, child_evaluation=overlapping)

    def test_leakage_and_reverse_replay_are_hard_gates(self) -> None:
        with self.assertRaises(ValueError):
            self.valid_improvement(leakage_audit_pass=False)
        with self.assertRaises(ValueError):
            self.valid_improvement(reverse_replay_pass=False)

    def test_native_language_witnesses_are_distinct_and_do_not_invent_catalog_bytes(self) -> None:
        first = model.NativeGlyphLanguageWitness(
            "BASE",
            1,
            model.digest("body", 1),
            model.digest("receipt", 1),
            model.digest("formation"),
            "OPERATOR_OBSERVED",
            "PENDING_CURRENT_34_CATALOG_CITATION",
        )
        second = replace(first, body_ordinal=2, body_leaf_sha256=model.digest("body", 2))
        self.assertNotEqual(first.body_pid, second.body_pid)
        self.assertNotEqual(first.native_language_pid, second.native_language_pid)
        with self.assertRaises(ValueError):
            replace(first, native_catalog_sha256=model.digest("invented-catalog"))

    def test_valid_glyph_language_evaluation_reconstructs(self) -> None:
        claim = model.GlyphLanguageEvaluation(**self.glyph_values())
        self.assertEqual(claim.pid, "PID-" + claim.identity_sha256)

    def test_glyph_language_rejects_symbol_substitution_only(self) -> None:
        values = self.glyph_values() | {"symbol_substitution_only": True}
        with self.assertRaises(ValueError):
            model.GlyphLanguageEvaluation(**values)

    def test_glyph_language_requires_novel_compositional_message(self) -> None:
        values = self.glyph_values() | {"novel_message_absent_from_training": False}
        with self.assertRaises(ValueError):
            model.GlyphLanguageEvaluation(**values)

    def test_glyph_language_requires_reversible_native_omega_translation(self) -> None:
        values = self.glyph_values() | {
            "recovered_native_message_sha256": model.digest("lossy-recovery")
        }
        with self.assertRaises(ValueError):
            model.GlyphLanguageEvaluation(**values)

    def test_glyph_language_requires_cross_cube_meaning_preservation(self) -> None:
        values = self.glyph_values() | {
            "aligned_semantic_sha256": model.digest("changed-meaning")
        }
        with self.assertRaises(ValueError):
            model.GlyphLanguageEvaluation(**values)

    def test_glyph_language_alignment_must_retain_native_catalog(self) -> None:
        values = self.glyph_values() | {
            "native_catalog_after_sha256": model.digest("overwritten-catalog")
        }
        with self.assertRaises(ValueError):
            model.GlyphLanguageEvaluation(**values)


class FeedbackAndOmegaTests(unittest.TestCase):
    def test_catalog_event_emits_paired_unlearned_edges(self) -> None:
        parent = node(())
        child = node((1,))
        event = model.CatalogEvent(
            node_pid=child.pid,
            kind="IDEA",
            payload="residualize a settled function result",
            glyph="BH1024:IDEA:OMEGA",
            logical_tick_us=40,
        )
        forward, reverse = model.paired_learning_edges(parent.pid, child.pid, event)
        self.assertEqual(forward.pair_id, reverse.pair_id)
        self.assertEqual(forward.source_pid, reverse.target_pid)
        self.assertEqual(forward.target_pid, reverse.source_pid)
        self.assertEqual((forward.learned, reverse.learned), (0, 0))
        self.assertEqual(reverse.logical_tick_us, forward.logical_tick_us + 1)
        self.assertEqual(forward.pid, "PID-" + forward.identity_sha256)
        self.assertNotEqual(forward.pid, reverse.pid)

    def test_sister_table_detects_collision_and_consensus(self) -> None:
        first = model.Response(
            agent_pid="PID-A",
            request_id="REQ-1",
            protected_scope="OMEGA-CHECKPOINT",
            route="PIPE-1",
            verdict="WRITE-A",
            payload="alpha",
            logical_tick_us=100,
        )
        second = model.Response(
            agent_pid="PID-B",
            request_id="REQ-1",
            protected_scope="OMEGA-CHECKPOINT",
            route="PIPE-1",
            verdict="WRITE-B",
            payload="beta",
            logical_tick_us=101,
        )
        collision = model.supervisor_collision_table(first, second, overlap_window_us=2)
        self.assertEqual(collision["collision"], 1)
        self.assertEqual(collision["action"], "HELD_FOR_SUPERVISOR")
        consensus = model.supervisor_collision_table(first, first, overlap_window_us=0)
        self.assertEqual(consensus["classification"], "CONSENSUS")

    def test_omega_gnn_is_six_way_bidirectional_junction(self) -> None:
        binding = model.OmegaBinding(
            apex_body_pids=tuple(f"PID-APEX-{index}" for index in range(6)),
            omega_body_pid="PID-TRAINED-OMEGA-OMNIBIT",
            settled_epoch=10,
        )
        rows = binding.edge_rows()
        self.assertEqual(len(rows), 12)
        self.assertEqual(sum(row["relation"] == "OMEGA_FORWARD_FANIN" for row in rows), 6)
        self.assertEqual(sum(row["relation"] == "OMEGA_REVERSE_GAIN_FANOUT" for row in rows), 6)
        self.assertEqual(len({row["pid"] for row in rows}), 12)
        self.assertTrue(all(str(row["pid"]).startswith("PID-") for row in rows))
        self.assertTrue(binding.omega_gnn_pid.startswith("PID-"))
        with self.assertRaises(ValueError):
            model.OmegaBinding(("PID-X",) * 6, "PID-OMEGA", 0)

    def test_promotion_requires_runtime_and_three_seats(self) -> None:
        checks = {
            "source_sha": True,
            "hbi_restore": True,
            "reversible_replay": True,
            "typed_routes": True,
            "collision_table": True,
            "authority_identity": True,
            "access_cosign": True,
            "runtime_ready": False,
            "claim_specific_proof": True,
        }
        held = model.engine_promotion_gate(
            checks,
            {"LIRIS": "PASS", "ACER": "PENDING", "RELIC": "PENDING"},
        )
        self.assertEqual(held["status"], "HELD")
        checks["authority_identity"] = False
        identity_held = model.engine_promotion_gate(
            checks,
            {"LIRIS": "PASS", "ACER": "PASS", "RELIC": "PASS"},
        )
        self.assertEqual(identity_held["status"], "HELD")
        checks["authority_identity"] = True
        checks["runtime_ready"] = True
        active = model.engine_promotion_gate(
            checks,
            {"LIRIS": "PASS", "ACER": "PASS", "RELIC": "PASS"},
        )
        self.assertEqual(active["status"], "ACTIVE")

    def test_model_has_no_network_or_process_imports(self) -> None:
        tree = ast.parse(inspect.getsource(model))
        imported: set[str] = set()
        for item in ast.walk(tree):
            if isinstance(item, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in item.names)
            elif isinstance(item, ast.ImportFrom) and item.module:
                imported.add(item.module.split(".")[0])
        self.assertTrue(imported.isdisjoint({"socket", "subprocess", "requests", "urllib", "http"}))


class ReceiptSemanticForgeryTests(unittest.TestCase):
    artifacts = Path(__file__).resolve().parent / "artifacts"

    @staticmethod
    def replace_field(source: str, key: str, value: object) -> str:
        parts = source.split("|")
        marker = key + "="
        for index, item in enumerate(parts):
            if item.startswith(marker):
                parts[index] = f"{key}={value}"
                return "|".join(parts)
        raise AssertionError(f"field not found: {key}")

    @staticmethod
    def reseal(root: Path, rows: list[str]) -> None:
        hbp = root / prepare.HBP_NAME
        hbi = root / prepare.HBI_NAME
        hex_path = root / prepare.HEX_NAME
        prepare.write_lf(hbp, rows)
        prepare.write_lf(hbi, prepare.hbi_rows(rows))
        prepare.write_lf(hex_path, [hbp.read_bytes().hex()])
        for path in (hbp, hbi, hex_path):
            prepare.write_sidecar(path)
        sums = root / prepare.SUMS_NAME
        prepare.write_lf(
            sums,
            [
                f"{prepare.sha256_file(path)}  {path.name}"
                for path in (hbp, hbi, hex_path)
            ],
        )
        prepare.write_sidecar(sums)

    def assert_resealed_forgery_rejected(
        self, mutate: object, expected: str
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="asolaria-floor1-forgery-") as temporary:
            root = Path(temporary) / "artifacts"
            shutil.copytree(self.artifacts, root)
            hbp = root / prepare.HBP_NAME
            rows = hbp.read_text(encoding="utf-8").splitlines()
            mutate(rows)
            self.reseal(root, rows)
            with self.assertRaises((prepare.PreparationError, ValueError)) as context:
                prepare.verify(root)
            self.assertIn(expected, str(context.exception))

    def test_resealed_witness_footer_forgery_is_rejected(self) -> None:
        def mutate(rows: list[str]) -> None:
            index = next(i for i, row in enumerate(rows) if row.startswith("NATIVEGLYPHGATE|"))
            rows[index] = self.replace_field(rows[index], "witness_objects", "35_OF_35")

        self.assert_resealed_forgery_rejected(mutate, "native-glyph witness gate")

    def test_resealed_witness_body_and_recomputed_pids_still_fail_source_root(self) -> None:
        def mutate(rows: list[str]) -> None:
            index = next(
                i for i, row in enumerate(rows) if row.startswith("NATIVEGLYPHWITNESS|")
            )
            tag, fields = prepare.parse_fields(rows[index])
            fields["body_leaf_sha256"] = "f0" * 32
            witness = model.NativeGlyphLanguageWitness(
                body_kind=fields["body_kind"],
                body_ordinal=int(fields["body_ordinal"]),
                body_leaf_sha256=fields["body_leaf_sha256"],
                body_receipt_sha256=fields["body_receipt_sha256"],
                formation_receipt_sha256=fields["formation_receipt_sha256"],
                evidence_class=fields["evidence"],
                owning_catalog_import=fields["owning_catalog_import"],
            )
            fields.update(
                body_pid=witness.body_pid,
                native_language_pid=witness.native_language_pid,
                witness_pid=witness.pid,
                identity_sha256=witness.identity_sha256,
            )
            fields.pop("json")
            rows[index] = prepare.row(tag, **fields)
            witness_rows = [
                prepare.parse_fields(row)[1]
                for row in rows
                if row.startswith("NATIVEGLYPHWITNESS|")
            ]
            reconstructed = [
                model.NativeGlyphLanguageWitness(
                    body_kind=item["body_kind"],
                    body_ordinal=int(item["body_ordinal"]),
                    body_leaf_sha256=item["body_leaf_sha256"],
                    body_receipt_sha256=item["body_receipt_sha256"],
                    formation_receipt_sha256=item["formation_receipt_sha256"],
                    evidence_class=item["evidence"],
                    owning_catalog_import=item["owning_catalog_import"],
                )
                for item in witness_rows
            ]
            source_root = model.digest(
                "CDC_BODY_WITNESS_SOURCE_SET_V1",
                tuple(
                    (
                        item.body_kind,
                        item.body_ordinal,
                        item.body_leaf_sha256,
                        item.body_receipt_sha256,
                    )
                    for item in reconstructed
                ),
            )
            witness_root = model.digest(
                "NATIVE_GLYPH_LANGUAGE_WITNESS_SET_V1",
                tuple(item.identity_sha256 for item in reconstructed),
            )
            gate = next(i for i, row in enumerate(rows) if row.startswith("NATIVEGLYPHGATE|"))
            rows[gate] = self.replace_field(rows[gate], "source_set_sha256", source_root)
            rows[gate] = self.replace_field(rows[gate], "witness_set_sha256", witness_root)

        self.assert_resealed_forgery_rejected(mutate, "sealed 34-body population")

    def test_resealed_improvement_schema_cannot_claim_materialized_proof(self) -> None:
        def mutate(rows: list[str]) -> None:
            index = next(
                i for i, row in enumerate(rows) if row.startswith("IMPROVEMENTAUDITSCHEMA|")
            )
            rows[index] = self.replace_field(rows[index], "materialized_claims", 1)

        self.assert_resealed_forgery_rejected(mutate, "improvement audit schema")

    def test_resealed_glyph_schema_cannot_claim_semantic_evaluations(self) -> None:
        def mutate(rows: list[str]) -> None:
            index = next(
                i
                for i, row in enumerate(rows)
                if row.startswith("GLYPHLANGUAGEAUDITSCHEMA|")
            )
            rows[index] = self.replace_field(rows[index], "materialized_evaluations", 34)

        self.assert_resealed_forgery_rejected(mutate, "glyph-language audit schema")

    def test_resealed_unresolved_authority_signer_is_rejected(self) -> None:
        def mutate(rows: list[str]) -> None:
            index = next(
                i
                for i, row in enumerate(rows)
                if row.startswith("AUTHORITYREF|") and "name=AUTO_SELF_REFLECT_LEVELS|" in row
            )
            rows[index] = self.replace_field(rows[index], "can_sign", 1)

        self.assert_resealed_forgery_rejected(mutate, "cannot sign or parent")

    def test_resealed_pid_dag_footer_forgery_is_rejected(self) -> None:
        def mutate(rows: list[str]) -> None:
            index = next(i for i, row in enumerate(rows) if row.startswith("PIDDAGGATE|"))
            rows[index] = self.replace_field(rows[index], "nodes", 19)

        self.assert_resealed_forgery_rejected(mutate, "PID DAG gate field mismatch")

    def test_resealed_engine_promotion_forgery_is_rejected(self) -> None:
        def mutate(rows: list[str]) -> None:
            index = next(i for i, row in enumerate(rows) if row.startswith("ENGINEPROMOTION|"))
            rows[index] = self.replace_field(rows[index], "claim_specific_proof", 1)
            rows[index] = self.replace_field(rows[index], "active_engine", 1)
            rows[index] = self.replace_field(rows[index], "status", "ACTIVE")

        self.assert_resealed_forgery_rejected(mutate, "engine promotion escaped")


if __name__ == "__main__":
    unittest.main()
