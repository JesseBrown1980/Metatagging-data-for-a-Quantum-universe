#!/usr/bin/env python3
"""Deterministic cold receipt for the omega-omnibit/bit-ladder feasibility
survey. Pure repository index — E=0, fire=0, no live PID office ingest, no
agent spawn. Mirrors the receipt discipline used elsewhere in this repo
(e.g. the encrypted-cloning law packet)."""

from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import quote

SCHEMA = "ASOLARIA-OMEGA-OMNIBIT-BITLADDER-FEASIBILITY-INDEX-V1"
ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "FEASIBILITY-REPORT.md"
STEM = "OMEGA-OMNIBIT-BITLADDER-FEASIBILITY"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def field(value: object) -> str:
    return quote(str(value), safe="._~:/+-")


def row(kind: str, **fields: object) -> str:
    return kind + "|" + "|".join(f"{key}={field(value)}" for key, value in fields.items()) + "|"


def hbp_rows(report_sha: str) -> list[str]:
    return [
        row(
            "OMNIBITFEASIBILITYHDR",
            schema=SCHEMA,
            date="2026-07-17",
            seat="ACER-CLAUDE-FABLE5",
            method="40_agent_briefed_scout_survey_plus_synthesis_plus_3_adversarial_skeptics_plus_finalize",
            report_file=REPORT.name,
            report_sha256=report_sha,
            overall_feasibility="POSSIBLE_WITH_CAVEATS",
            E=0,
            fire=0,
            json=0,
        ),
        row(
            "SUBCLAIM",
            name="native_bit_depth_floor_ladder",
            verdict="SUPPORTS_WITH_CAVEATS_as_addressing_CONTRADICTED_as_compression_if_glyph_codebook_reused",
            json=0,
        ),
        row(
            "SUBCLAIM",
            name="qprism_bridging_mechanism",
            verdict="SUPPORTS_WITH_CAVEATS_addressing_recovery_only_not_compression",
            json=0,
        ),
        row(
            "SUBCLAIM",
            name="omega_family_unification",
            verdict="SUPPORTS_WITH_CAVEATS_open_geometric_question_on_12sector_vs_8pole_orbit",
            json=0,
        ),
        row(
            "SUBCLAIM",
            name="quantum_key_bridge_analogue",
            verdict="SUPPORTS_AS_METAPHOR_BOUNDED_BY_BROADBENT_GUTOSKI_STEBILA_2013_IMPOSSIBILITY_without_trust_anchor",
            json=0,
        ),
        row(
            "SUBCLAIM",
            name="rnq_axis_and_mirror_nullspace_idea",
            verdict="UNVERIFIED_no_scout_lane_assigned_no_prior_art_surfaced_either_way",
            json=0,
        ),
        row(
            "PRIORNEGATIVE",
            id=1,
            name="unified_omega_v1_core",
            result="bpc_4.14_worse_than_mix_bpc_2.65",
            cause="bijective_glyph_relabeling_before_byte_entropy_coder",
            json=0,
        ),
        row(
            "PRIORNEGATIVE",
            id=2,
            name="band_ladder_omnibit",
            result="38.9MB_vs_flat_6.8MB_5.7x_worse",
            cause_direction="entropy_invariance_bijection_cannot_help",
            cause_magnitude="separately_attributable_to_5_parallel_streams",
            json=0,
        ),
        row(
            "LIRISFRAMING",
            contribution="typed_lattice_of_coupled_manifolds",
            floor_axis="64,256,1024,4096",
            family_axis="8pole,12sector,20lens,path",
            transfer_axis="quanted_omega_bridge",
            requirement="explicit_deterministic_transition_maps_proven_commutative_diagrams_before_omnibook_claim",
            convergence_with_scout_survey=1,
            json=0,
        ),
        row(
            "MINIMALNEXTEXPERIMENT",
            description="native_integer_width_block_packing_zero_glyph_relabeling_through_existing_flat_entropy_coder",
            corpus="same_24MB_corpus_that_produced_both_prior_negatives",
            falsifiable_prediction="worse_or_neutral_result_shelves_downward_ladder_direction",
            implemented_in_this_pr=0,
            json=0,
        ),
        row(
            "CLAIMSGATE",
            registration="REPOSITORY_DESIGN_DOC_ONLY",
            live_pid_office_ingest=0,
            runtime_agent_count=0,
            E=0,
            fire=0,
            single_run_promotes_to_canon=0,
            json=0,
        ),
        row(
            "OMNIBITFEASIBILITYFTR",
            status="PASS",
            subclaims=5,
            prior_negatives=2,
            E=0,
            fire=0,
            json=0,
        ),
    ]


def main() -> int:
    report_bytes = REPORT.read_bytes()
    report_sha = sha256(report_bytes)
    rows = hbp_rows(report_sha)
    hbp = ("\n".join(rows) + "\n").encode("utf-8")
    (ROOT / f"{STEM}.hbp").write_bytes(hbp)
    (ROOT / f"{STEM}.hbp.sha256").write_bytes(f"{sha256(hbp)}  {STEM}.hbp\n".encode("ascii"))
    (ROOT / f"{REPORT.name}.sha256").write_bytes(f"{report_sha}  {REPORT.name}\n".encode("ascii"))
    print(f"BUILT|rows={len(rows)}|report_sha256={report_sha}|hbp_sha256={sha256(hbp)}|E=0|fire=0|json=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
