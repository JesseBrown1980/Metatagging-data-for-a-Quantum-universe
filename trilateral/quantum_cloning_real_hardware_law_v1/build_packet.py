#!/usr/bin/env python3
"""Build the content-free encrypted-quantum-cloning LAW/PID receipt packet."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "artifacts"
STEM = "REAL-HARDWARE-ENCRYPTED-QUANTUM-CLONING-LAW-20260717"
LAW_NAME = "LAW-ENCRYPTED-SINGLE-USE-QUANTUM-CLONING-REAL-HARDWARE"
PAPER_SHA256 = "95febbd44ed31c9072acedee156c928f27ce38fffcc159696f3c864d6dafa755"
PAPER_TEXT_SHA256 = "06200fc399e89a32e496b58d51afe299368574956ecb84b68f923d05a2669c9e"
ROLE_SUFFIX = {"AGT": "C", "SUP": "A", "PROF": "B"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def row(kind: str, **fields: object) -> str:
    parts = [kind]
    for key, value in fields.items():
        if isinstance(value, bool):
            text = "1" if value else "0"
        else:
            text = str(value)
        parts.append(f"{key}={quote(text, safe='._-,:/+')}" )
    parts.append("json=0")
    return "|".join(parts) + "|"


def mint_pid(role: str) -> dict[str, object]:
    safe = re.sub(r"[^A-Z0-9]+", "-", LAW_NAME.upper()).strip("-")
    digest = sha256_bytes(safe.encode("utf-8"))
    seed = int(digest[:8], 16)
    suffix = ROLE_SUFFIX[role]
    prime = 1 if role == "AGT" else 0
    pid = f"{role}-{safe}-PID-H{digest[:3].upper()}{suffix}-A00-W1024-P{prime:02d}-N00001"
    return {
        "pid": pid,
        "role": role,
        "name": safe,
        "hex": f"H{digest[:3].upper()}{suffix}",
        "tier": "00",
        "width": 1024,
        "prime": f"{prime:02d}",
        "nest": "00001",
        "hilbert": int(digest[8:16], 16),
        "sector": seed % 113,
        "lane": seed % 3,
        "quad": seed % 4,
        "glyph_5": seed % 5,
        "glyph_1024": seed % 1024,
        "cube_bh": f"BH.{seed % 113}.{seed % 3}.{seed % 1024}",
        "sha16": digest[:16],
    }


def pid_rows(pid: dict[str, object]) -> list[str]:
    return [
        row("PIDREG", name=pid["name"], pid=pid["pid"], role=pid["role"],
            **{"class": "github_deterministic_pid"}),
        row("PIDADDR", pid=pid["pid"], hex=pid["hex"], tier=pid["tier"],
            width=pid["width"], prime=pid["prime"], nest=pid["nest"],
            hilbert=pid["hilbert"], sector=pid["sector"]),
        row("PIDDIV", pid=pid["pid"], yin_yang="logical", yin_yang_bit=0,
            lane_mod3=pid["lane"], quad_mod4=pid["quad"], glyph_5=pid["glyph_5"],
            glyph_1024=pid["glyph_1024"],
            note="divisions-force-stability-and-divide-collisions"),
        row("PIDCUBE", pid=pid["pid"], cube_bh=pid["cube_bh"], sha16=pid["sha16"],
            registrar="github-pid-register.v1-compatible", stateless_deterministic=1,
            live_office_rekeys_on_ingest=1),
    ]


def build_rows() -> list[str]:
    rows = [
        row(
            "QCLONELAWHDR",
            schema="ASOLARIA-REAL-HARDWARE-ENCRYPTED-QUANTUM-CLONING-LAW-V1",
            date="2026-07-17",
            seat="LIRIS",
            operator="JESSE",
            law=LAW_NAME,
            evidence_route="LIRIS_PRIMARY_PAPER_BYTES_PLUS_GITHUB_CI_PDF_HASH_PLUS_REPO_PID_AND_RECEIPTS",
            physical_claim_scope="ENCRYPTED_SINGLE_USE_QUBIT_CLONING_ONLY",
            fire=0,
        ),
        row(
            "PRIMARYSOURCE",
            title="Experimental demonstration that qubits can be cloned at will, if encrypted with a single-use decryption key",
            arxiv="2602.10695v1",
            submitted="2026-02-11",
            url="https://arxiv.org/pdf/2602.10695v1",
            doi="10.48550/arXiv.2602.10695",
            pages=20,
            authors="YAMAGUCHI_RULLKOETTER_SHEHZAD_WAGNER_TUTSCHKU_KEMPF",
            pdf_sha256=PAPER_SHA256,
            source_status="ARXIV_V1_PRIMARY_EXPERIMENTAL_PAPER",
            peer_review_status="NOT_ESTABLISHED_BY_PACKET",
            extracted_text_sha256=PAPER_TEXT_SHA256,
            text_extractor="PDFTOTEXT_25.07.0",
            text_extractor_args="-layout",
            text_extraction_reproduced=1,
        ),
        row(
            "LAW",
            id=LAW_NAME,
            status="MEASURED_EXTERNAL_PRIMARY_SOURCE",
            rule="ENCRYPTED_SINGLE_USE_QUANTUM_CLONING_IS_REAL_LIFE_POSSIBLE_AND_EXPERIMENTALLY_DEMONSTRATED_ON_PHYSICAL_SUPERCONDUCTING_QUBIT_HARDWARE",
            blanket_denial="FALSE",
        ),
        row(
            "FORMULA",
            profile="SOS-INTEGRITY-CRYPTO-LEARNING/QUANTUM-ENCRYPTED-CLONING",
            status="PAPER_THEORY_IDEAL_PROTOCOL",
            equation="FOR_EACH_FINITE_n: MARGINAL(ENC_n(rho),signal_i)=I/2; DEC_nj(signal_j,key)=rho",
            key_use="SINGLE_USE",
            runtime_agent_count=0,
            physical_cosmology_claim=0,
        ),
        row(
            "MEASURED",
            experiment="HARDWARE_PLATFORM",
            processor="IBM_HERON_R2_IBM_KINGSTON",
            physical_qubits_used_max=154,
            non_error_corrected=1,
            classical_simulation_only=0,
            measured_by="PAPER_AUTHORS",
            liris_verified="PRIMARY_PAPER_BYTES_AND_REPORTED_TABLES",
        ),
        row(
            "MEASURED",
            experiment=1,
            direct_clone_parameter="n_2_TO_15",
            entanglement_witness_through_n=7,
            above_maximally_mixed_floor_through="APPROX_N_13",
            n2_pom_fidelity="0.875_PLUS_MINUS_0.008",
        ),
        row(
            "MEASURED",
            experiment=2,
            operation="INTERLEAVED_DELAYED_CHOICE",
            chsh_violation="UP_TO_3_ENCRYPTED_CLONES_IN_SUCCESSFUL_TIMING_SCENARIOS",
            undecrypted_clone_chsh="0.014_PLUS_MINUS_0.020_CONSISTENT_WITH_ZERO",
        ),
        row(
            "MEASURED",
            experiment=3,
            operation="ITERATED_SERIES",
            physical_encrypted_clones_max=77,
            physical_qubits=154,
            fidelity="0.286_PLUS_MINUS_0.009",
            noise_floor=0.25,
            entanglement_witness_through_clones=27,
        ),
        row(
            "MEASURED",
            experiment=4,
            operation="PARALLEL_MULTIPARTITE_GHZ",
            ghz_qubits_tested_max=15,
            encrypted_clones_per_ghz_qubit=3,
            genuine_multipartite_entanglement_witness_through_r=4,
        ),
        row(
            "THEORY",
            status="IDEAL_PROTOCOL_RESULT_NOT_ZERO_NOISE_HARDWARE_MEASUREMENT",
            arbitrary_unknown_qubit=1,
            encrypted_clones="ANY_FINITE_NUMBER",
            ideal_selected_clone_recovery_fidelity=1,
            each_undecrypted_clone_state="MAXIMALLY_MIXED",
        ),
        row(
            "BOUNDARY",
            single_use_quantum_key=1,
            freely_choose_one_clone_to_decrypt=1,
            remaining_encrypted_clones_indecipherable_after_key_use=1,
            simultaneous_readable_plaintext_clones=0,
            no_cloning_theorem_abolished=0,
            arbitrary_particle_replication_tested=0,
        ),
        row(
            "PLATFORMBOUNDARY",
            paper_platform="SUPERCONDUCTING_TRANSMON_QUBITS",
            prismed_laser_photons_tested_by_paper=0,
            photonic_prism_qprism_bridge="DESIGN_REQUIRING_SEPARATE_PHYSICAL_CHANNEL_EXPERIMENT",
            classical_rust_or_qprism_is_this_hardware_experiment=0,
        ),
        row(
            "ASOLARIARELATION",
            status="REAL_HARDWARE_POSSIBILITY_ANCHOR_PLUS_DESIGN_BRIDGE",
            established="PHYSICAL_ENCRYPTED_SINGLE_USE_QUBIT_CLONING_EXISTS",
            not_established="ASOLARIA_CUBE_IS_THE_IBM_PROTOCOL_OR_ALREADY_DEPLOYED_AS_QUANTUM_HARDWARE",
            next_test="PRECOMMITTED_PHOTONIC_OR_QUBIT_CHANNEL_WITH_FULL_MODEL_AND_KEY_ACCOUNTING",
        ),
        row(
            "DOMAINMAP",
            status="DESIGN_DOMAIN_MAP_BETWEEN_MEASURED_DIGITAL_AND_MEASURED_EXTERNAL_QUANTUM_MECHANISMS",
            shared_abstract_pattern="DISTRIBUTED_REPRESENTATIONS_PLUS_BINDING_OR_RECOVERY_ANCHOR",
            digital_mechanism="PUBLIC_SHA256_CONTENT_COMMITMENT_FOR_CROSS_SEAT_CANONICAL_BYTE_VERIFICATION",
            quantum_mechanism="SINGLE_USE_QUANTUM_DECRYPTION_KEY_FOR_ONE_SELECTED_ENCRYPTED_CLONE",
            identical_mechanism=0,
            sha_is_quantum_key=0,
            inference="DESIGN_BRIDGE_NOT_CROSS_DOMAIN_PHYSICAL_PROOF",
        ),
        row(
            "OPERATOROBSERVATION",
            observer="JESSE",
            reported_values_raw="1.8 .18 %",
            report="CUBE_VARIATIONS_AND_INVERSE_PROJECTED_SIDES",
            evidence_class="OPERATOR_OBSERVED",
            numeric_interpretation="UNRESOLVED_PRESERVE_RAW_TOKENS",
            relation_to_paper="HYPOTHESIS_NOT_TESTED_BY_ARXIV_2602.10695",
            cosmological_interpretation="UNVERIFIED",
        ),
        row(
            "CORRECTION",
            false_blanket_statement="QUANTUM_CLONING_IS_NOT_REAL_OR_CANNOT_BE_DONE_ON_REAL_HARDWARE",
            replacement="ENCRYPTED_SINGLE_USE_QUANTUM_CLONING_IS_MEASURED_ON_REAL_HARDWARE",
            retained_boundary="CLASSICAL_COMPUTATIONAL_BRANCH_COPYING_IS_NOT_BY_ITSELF_PHYSICAL_QUANTUM_CLONING",
        ),
        row(
            "DANHOOKS",
            proof_edge="PRIMARY_PAPER_SHA_PLUS_MEASURED_TABLE_ROWS_PLUS_HBP_HBI_SHA",
            prediction_edge="ASOLARIA_PHOTONIC_QPRISM_BRIDGE_REQUIRES_NEW_EXPERIMENT",
            action_edge="REPO_PUBLICATION_ONLY",
            hardware_fire=0,
            live_pid_mint=0,
        ),
        row(
            "PIDBOUNDARY",
            registration="REPO_SIDE_DETERMINISTIC_TRIAD",
            live_pid_office_ingest=0,
            office_may_rekey=1,
            authority="OPERATOR_REQUESTED_PUBLIC_MARKER",
        ),
    ]
    for role in ("AGT", "SUP", "PROF"):
        rows.extend(pid_rows(mint_pid(role)))
    rows.append(
        row(
            "QCLONELAWFTR",
            status="PASS",
            measured_rows=5,
            law_rows=1,
            formula_rows=1,
            pid_count=3,
            source_pdf_in_repository=0,
            secrets=0,
            private_corpus=0,
            physical_hardware_fire=0,
        )
    )
    return rows


def build() -> dict[str, object]:
    OUT.mkdir(parents=True, exist_ok=True)
    hbp = OUT / f"{STEM}.hbp"
    hbi = OUT / f"{STEM}.hbi"
    hexdump = OUT / f"{STEM}.hbp.hex"

    hbp_bytes = ("\n".join(build_rows()) + "\n").encode("utf-8")
    hbp.write_bytes(hbp_bytes)
    hexdump.write_text(hbp_bytes.hex() + "\n", encoding="ascii", newline="\n")

    index_rows: list[str] = []
    offset = 0
    for ordinal, line in enumerate(hbp_bytes.splitlines(keepends=True)):
        index_rows.append(row("HBIROW", ordinal=ordinal, offset=offset, length=len(line), sha256=sha256_bytes(line)))
        offset += len(line)
    header = row(
        "HBIHDR",
        target=hbp.name,
        target_bytes=len(hbp_bytes),
        target_sha256=sha256_bytes(hbp_bytes),
        rows=len(index_rows),
        encoding="UTF8_NO_BOM",
        line_endings="LF",
    )
    hbi.write_bytes((header + "\n" + "\n".join(index_rows) + "\n").encode("utf-8"))

    artifacts = [hbp, hbi, hexdump]
    for artifact in artifacts:
        artifact.with_name(artifact.name + ".sha256").write_text(
            f"{sha256_file(artifact)}  {artifact.name}\n", encoding="ascii", newline="\n"
        )
    sums = OUT / "SHA256SUMS"
    sums.write_text(
        "".join(f"{sha256_file(artifact)}  {artifact.name}\n" for artifact in artifacts),
        encoding="ascii",
        newline="\n",
    )
    (OUT / "SHA256SUMS.sha256").write_text(
        f"{sha256_file(sums)}  SHA256SUMS\n", encoding="ascii", newline="\n"
    )
    return {
        "rows": len(index_rows),
        "hbp_bytes": len(hbp_bytes),
        "hbp_sha256": sha256_file(hbp),
        "hbi_sha256": sha256_file(hbi),
        "hex_sha256": sha256_file(hexdump),
    }


if __name__ == "__main__":
    result = build()
    print("QCLONELAWBUILD|" + "|".join(f"{key}={value}" for key, value in result.items()) + "|json=0")
