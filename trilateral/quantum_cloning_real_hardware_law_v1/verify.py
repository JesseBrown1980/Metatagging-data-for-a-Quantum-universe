#!/usr/bin/env python3
"""Independently verify the real-hardware encrypted quantum-cloning law packet."""

from __future__ import annotations

import argparse
import hashlib
from collections import Counter
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"
STEM = "REAL-HARDWARE-ENCRYPTED-QUANTUM-CLONING-LAW-20260717"
PDF_SHA256 = "95febbd44ed31c9072acedee156c928f27ce38fffcc159696f3c864d6dafa755"
TEXT_SHA256 = "06200fc399e89a32e496b58d51afe299368574956ecb84b68f923d05a2669c9e"
LAW_NAME = "LAW-ENCRYPTED-SINGLE-USE-QUANTUM-CLONING-REAL-HARDWARE"
PAPER_TITLE = "Experimental demonstration that qubits can be cloned at will, if encrypted with a single-use decryption key"
PAPER_AUTHORS = "YAMAGUCHI_RULLKOETTER_SHEHZAD_WAGNER_TUTSCHKU_KEMPF"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_lf(path: Path) -> bytes:
    data = path.read_bytes()
    assert not data.startswith(b"\xef\xbb\xbf"), f"{path.name}: UTF-8 BOM"
    assert b"\r" not in data, f"{path.name}: non-LF line ending"
    assert data.endswith(b"\n"), f"{path.name}: missing final LF"
    return data


def parse_row(raw: bytes) -> tuple[str, dict[str, str]]:
    text = raw.decode("utf-8").rstrip("\n")
    parts = text.split("|")
    assert parts[-1] == "", f"unterminated tuple row: {text[:80]}"
    fields: dict[str, str] = {}
    for part in parts[1:-1]:
        key, value = part.split("=", 1)
        assert key not in fields, f"duplicate tuple key: {key}"
        fields[key] = unquote(value)
    assert fields.get("json") == "0", "tuple row is not json=0"
    return parts[0], fields


def one(rows: list[tuple[str, dict[str, str]]], kind: str) -> dict[str, str]:
    matches = [fields for row_kind, fields in rows if row_kind == kind]
    assert len(matches) == 1, f"expected one {kind}, got {len(matches)}"
    return matches[0]


def verify_sidecar(path: Path) -> None:
    sidecar = path.with_name(path.name + ".sha256")
    content = read_lf(sidecar).decode("ascii").strip()
    digest, name = content.split("  ", 1)
    assert name == path.name
    assert digest == sha256_file(path)


def verify(paper: Path | None, paper_text: Path | None) -> dict[str, object]:
    hbp = ARTIFACTS / f"{STEM}.hbp"
    hbi = ARTIFACTS / f"{STEM}.hbi"
    hex_path = ARTIFACTS / f"{STEM}.hbp.hex"
    sums = ARTIFACTS / "SHA256SUMS"

    hbp_bytes = read_lf(hbp)
    hbi_bytes = read_lf(hbi)
    hex_bytes = read_lf(hex_path)
    read_lf(sums)

    hbp_lines = hbp_bytes.splitlines(keepends=True)
    hbp_rows = [parse_row(line) for line in hbp_lines]
    expected_hbp_kinds = Counter(
        {
            "QCLONELAWHDR": 1,
            "PRIMARYSOURCE": 1,
            "LAW": 1,
            "FORMULA": 1,
            "MEASURED": 5,
            "THEORY": 1,
            "BOUNDARY": 1,
            "PLATFORMBOUNDARY": 1,
            "ASOLARIARELATION": 1,
            "DOMAINMAP": 1,
            "OPERATOROBSERVATION": 1,
            "CORRECTION": 1,
            "DANHOOKS": 1,
            "PIDBOUNDARY": 1,
            "PIDREG": 3,
            "PIDADDR": 3,
            "PIDDIV": 3,
            "PIDCUBE": 3,
            "QCLONELAWFTR": 1,
        }
    )
    assert len(hbp_rows) == 31
    assert Counter(kind for kind, _ in hbp_rows) == expected_hbp_kinds
    hbi_lines = hbi_bytes.splitlines(keepends=True)
    hbi_rows = [parse_row(line) for line in hbi_lines]
    assert Counter(kind for kind, _ in hbi_rows) == Counter({"HBIHDR": 1, "HBIROW": 31})
    header_kind, header = hbi_rows[0]
    assert header_kind == "HBIHDR"
    assert header["target"] == hbp.name
    assert int(header["target_bytes"]) == len(hbp_bytes)
    assert header["target_sha256"] == sha256_bytes(hbp_bytes)
    assert int(header["rows"]) == len(hbp_lines)
    assert header["encoding"] == "UTF8_NO_BOM"
    assert header["line_endings"] == "LF"

    index_rows = [fields for kind, fields in hbi_rows[1:] if kind == "HBIROW"]
    assert len(index_rows) == len(hbp_lines)
    offset = 0
    for ordinal, (line, fields) in enumerate(zip(hbp_lines, index_rows)):
        assert int(fields["ordinal"]) == ordinal
        assert int(fields["offset"]) == offset
        assert int(fields["length"]) == len(line)
        assert fields["sha256"] == sha256_bytes(line)
        assert hbp_bytes[offset : offset + len(line)] == line
        offset += len(line)
    assert offset == len(hbp_bytes)

    assert hex_bytes == (hbp_bytes.hex() + "\n").encode("ascii")
    for artifact in (hbp, hbi, hex_path, sums):
        verify_sidecar(artifact)

    sum_entries: dict[str, str] = {}
    for line in sums.read_text(encoding="ascii").splitlines():
        digest, name = line.split("  ", 1)
        sum_entries[name] = digest
    assert sum_entries == {
        hbp.name: sha256_file(hbp),
        hbi.name: sha256_file(hbi),
        hex_path.name: sha256_file(hex_path),
    }

    packet_header = one(hbp_rows, "QCLONELAWHDR")
    assert packet_header["law"] == LAW_NAME
    assert packet_header["evidence_route"] == "LIRIS_PRIMARY_PAPER_BYTES_PLUS_GITHUB_CI_PDF_HASH_PLUS_REPO_PID_AND_RECEIPTS"
    assert packet_header["fire"] == "0"
    source = one(hbp_rows, "PRIMARYSOURCE")
    assert source["arxiv"] == "2602.10695v1"
    assert source["pdf_sha256"] == PDF_SHA256
    assert source["extracted_text_sha256"] == TEXT_SHA256
    assert source["pages"] == "20"
    assert source["title"] == PAPER_TITLE
    assert source["authors"] == PAPER_AUTHORS
    assert source["submitted"] == "2026-02-11"
    assert source["text_extractor"] == "PDFTOTEXT_25.07.0"
    assert source["text_extractor_args"] == "-layout"
    assert source["text_extraction_reproduced"] == "1"
    assert source["peer_review_status"] == "NOT_ESTABLISHED_BY_PACKET"

    law = one(hbp_rows, "LAW")
    assert law["status"] == "MEASURED_EXTERNAL_PRIMARY_SOURCE"
    assert law["blanket_denial"] == "FALSE"
    assert "REAL_LIFE_POSSIBLE" in law["rule"]
    assert law["id"] == LAW_NAME
    assert law["id"] == packet_header["law"]

    formula = one(hbp_rows, "FORMULA")
    assert formula["status"] == "PAPER_THEORY_IDEAL_PROTOCOL"
    assert formula["key_use"] == "SINGLE_USE"
    assert formula["runtime_agent_count"] == "0"
    assert formula["physical_cosmology_claim"] == "0"
    assert formula["equation"] == "FOR_EACH_FINITE_n: MARGINAL(ENC_n(rho),signal_i)=I/2; DEC_nj(signal_j,key)=rho"

    theory = one(hbp_rows, "THEORY")
    assert theory["encrypted_clones"] == "ANY_FINITE_NUMBER"
    assert theory["ideal_selected_clone_recovery_fidelity"] == "1"
    assert theory["each_undecrypted_clone_state"] == "MAXIMALLY_MIXED"

    measurements = {
        fields["experiment"]: fields
        for kind, fields in hbp_rows
        if kind == "MEASURED"
    }
    assert len(measurements) == 5
    hardware = measurements["HARDWARE_PLATFORM"]
    assert hardware["processor"] == "IBM_HERON_R2_IBM_KINGSTON"
    assert hardware["physical_qubits_used_max"] == "154"
    assert hardware["classical_simulation_only"] == "0"

    experiment_one = measurements["1"]
    assert experiment_one["direct_clone_parameter"] == "n_2_TO_15"
    assert experiment_one["entanglement_witness_through_n"] == "7"
    assert experiment_one["above_maximally_mixed_floor_through"] == "APPROX_N_13"
    assert experiment_one["n2_pom_fidelity"] == "0.875_PLUS_MINUS_0.008"

    experiment_two = measurements["2"]
    assert experiment_two["chsh_violation"] == "UP_TO_3_ENCRYPTED_CLONES_IN_SUCCESSFUL_TIMING_SCENARIOS"
    assert experiment_two["undecrypted_clone_chsh"] == "0.014_PLUS_MINUS_0.020_CONSISTENT_WITH_ZERO"

    experiment_three = measurements["3"]
    assert experiment_three["physical_encrypted_clones_max"] == "77"
    assert experiment_three["physical_qubits"] == "154"
    assert experiment_three["fidelity"] == "0.286_PLUS_MINUS_0.009"
    assert experiment_three["noise_floor"] == "0.25"
    assert experiment_three["entanglement_witness_through_clones"] == "27"

    experiment_four = measurements["4"]
    assert experiment_four["ghz_qubits_tested_max"] == "15"
    assert experiment_four["encrypted_clones_per_ghz_qubit"] == "3"
    assert experiment_four["genuine_multipartite_entanglement_witness_through_r"] == "4"

    boundary = one(hbp_rows, "BOUNDARY")
    assert boundary["single_use_quantum_key"] == "1"
    assert boundary["simultaneous_readable_plaintext_clones"] == "0"
    assert boundary["no_cloning_theorem_abolished"] == "0"
    assert boundary["arbitrary_particle_replication_tested"] == "0"

    platform = one(hbp_rows, "PLATFORMBOUNDARY")
    assert platform["paper_platform"] == "SUPERCONDUCTING_TRANSMON_QUBITS"
    assert platform["prismed_laser_photons_tested_by_paper"] == "0"

    footer = one(hbp_rows, "QCLONELAWFTR")
    assert footer["status"] == "PASS"
    assert footer["physical_hardware_fire"] == "0"
    assert len([1 for kind, _ in hbp_rows if kind == "PIDREG"]) == 3
    assert len([1 for kind, _ in hbp_rows if kind == "PIDADDR"]) == 3
    domain_map = one(hbp_rows, "DOMAINMAP")
    assert domain_map["shared_abstract_pattern"] == "DISTRIBUTED_REPRESENTATIONS_PLUS_BINDING_OR_RECOVERY_ANCHOR"
    assert domain_map["identical_mechanism"] == "0"
    assert domain_map["sha_is_quantum_key"] == "0"
    assert domain_map["inference"] == "DESIGN_BRIDGE_NOT_CROSS_DOMAIN_PHYSICAL_PROOF"
    assert domain_map["status"] == "DESIGN_DOMAIN_MAP_BETWEEN_MEASURED_DIGITAL_AND_MEASURED_EXTERNAL_QUANTUM_MECHANISMS"

    operator_observation = one(hbp_rows, "OPERATOROBSERVATION")
    assert operator_observation["evidence_class"] == "OPERATOR_OBSERVED"
    assert operator_observation["reported_values_raw"] == "1.8 .18 %"
    assert operator_observation["relation_to_paper"] == "HYPOTHESIS_NOT_TESTED_BY_ARXIV_2602.10695"

    correction = one(hbp_rows, "CORRECTION")
    assert correction["replacement"] == "ENCRYPTED_SINGLE_USE_QUANTUM_CLONING_IS_MEASURED_ON_REAL_HARDWARE"
    assert correction["retained_boundary"] == "CLASSICAL_COMPUTATIONAL_BRANCH_COPYING_IS_NOT_BY_ITSELF_PHYSICAL_QUANTUM_CLONING"
    assert len([1 for kind, _ in hbp_rows if kind == "PIDDIV"]) == 3
    assert len([1 for kind, _ in hbp_rows if kind == "PIDCUBE"]) == 3

    pid_regs = [fields for kind, fields in hbp_rows if kind == "PIDREG"]
    assert {fields["role"] for fields in pid_regs} == {"AGT", "SUP", "PROF"}
    safe_name = LAW_NAME
    digest = sha256_bytes(safe_name.encode("utf-8"))
    for fields in pid_regs:
        role = fields["role"]
        suffix = {"AGT": "C", "SUP": "A", "PROF": "B"}[role]
        prime = 1 if role == "AGT" else 0
        expected_pid = f"{role}-{safe_name}-PID-H{digest[:3].upper()}{suffix}-A00-W1024-P{prime:02d}-N00001"
        assert fields["name"] == safe_name
        assert fields["pid"] == expected_pid

    if paper is not None:
        assert sha256_file(paper) == PDF_SHA256, "primary PDF SHA-256 mismatch"
    if paper_text is not None:
        assert sha256_file(paper_text) == TEXT_SHA256, "paper text SHA-256 mismatch"

    return {
        "rows": len(hbp_rows),
        "hbi_ranges": len(index_rows),
        "hbp_sha256": sha256_file(hbp),
        "hbi_sha256": sha256_file(hbi),
        "paper_checked": int(paper is not None),
        "paper_text_checked": int(paper_text is not None),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper", type=Path)
    parser.add_argument("--paper-text", type=Path)
    args = parser.parse_args()
    result = verify(args.paper, args.paper_text)
    print("QCLONELAWVERIFY|status=PASS|" + "|".join(f"{k}={v}" for k, v in result.items()) + "|json=0")


if __name__ == "__main__":
    main()
