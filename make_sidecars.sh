#!/bin/bash
# HBP source of record + HBI exact row projection + SHA-256 sidecars for the v3 layer.
# json=0 on every HBP/HBI row (repo discipline). Pure text; no network.
set -euo pipefail
cd "$(dirname "$0")"
RUN=METATAG-V3-ORBIT-OMEGA-20260714

hbp=PARTICLE-ORBIT-AND-OMEGA-2026-07-14.hbp
{
  code_sha=$(sha256sum metatag_v2_behcs.py | cut -d' ' -f1)
  doc_sha=$(sha256sum PARTICLE-ORBIT-AND-OMEGA-2026-07-14.md | cut -d' ' -f1)
  # regenerate the demo orbit deterministically for the receipt
  omega=$(python3 -c "import metatag_v2_behcs as m; p1=m.AsolariaMetatag('Electron',[1.2e-35,-2.3e-35,3.1e-35],[1.6e-27,-2.8e-27,3.5e-27],'Up',-1,9.11e-31,1); p2=m.AsolariaMetatag('Electron',[-1.2e-35,2.3e-35,-3.1e-35],[-1.6e-27,2.8e-27,-3.5e-27],'Down',-1,9.11e-31,2); print(m.omega_commitment([p1,p2],0)['omega'])")
  anti=$(python3 -c "import metatag_v2_behcs as m; p1=m.AsolariaMetatag('Electron',[1.2e-35,-2.3e-35,3.1e-35],[1.6e-27,-2.8e-27,3.5e-27],'Up',-1,9.11e-31,1); print(p1.antiparticle()['antiparticle_pid'])")
  echo "V3HDR|run=$RUN|date=2026-07-14|seat=LIRIS|layer=particle_orientation_orbit_plus_omega|doctrine=TRILATERAL-PHYSICS-AND-COMPUTATION-EVIDENCE|json=0"
  echo "V3CODE|file=metatag_v2_behcs.py|sha256=$code_sha|added=orientation_orbit,antiparticle,omega_commitment|group=C2^3|gates=squares,commutators,RNQ_total_reversal|distinctness=reported_not_asserted|claim=MEASURED_REPO|json=0"
  echo "V3DOC|file=PARTICLE-ORBIT-AND-OMEGA-2026-07-14.md|sha256=$doc_sha|json=0"
  echo "V3MEASURED|isotropy_800pass_half_range_pct=0.26|isotropy_100pass_spread_pct=42.5|wide_isotropy_partial_pct=0.19|wide_vs_mid_density_delta_pct=18|source_run=github_29339920613|source_omega=537dc90bb173883e7fed15e51bf1b5199bc2f295da55f5723cea9b080123d444|isotropy_run_complete=8of8_views|wide_run_partial=4of8_views|tier=MEASURED_REPO_text_not_physical|json=0"
  echo "V3ORBIT|antiparticle_view=nqr|antiparticle_pid=$anti|relation=total_bit_reversal_black_white_flip|reversible=1|shared_key=source_state_sha256|json=0"
  echo "V3OMEGA|epoch=0|method=sha256_over_sorted_pids_LF|omega=$omega|is_oracle=0|seeds_next_epoch=1|json=0"
  echo "V3BOUNDARY|physical_particle=UNVERIFIED|planck_cell=UNVERIFIED|quantum_network=UNVERIFIED|no_inflate_gate=HONORED|json=0"
  echo "V3END|run=$RUN|state=LIRIS_AUTHORED_AWAIT_ACER_RELIC_VERIFY|json=0"
} > "$hbp"

# HBI: exact per-row projection (offset, byte length, row sha256, hex mirror)
hbi=PARTICLE-ORBIT-AND-OMEGA-2026-07-14.hbi
{
  n=$(wc -l < "$hbp")
  echo "HBIHDR|artifact=$hbp|rows=$n|encoding=utf8|newline=LF|offset_unit=utf8_bytes|offset_base=0|row_hash=sha256|json=0"
  off=0; i=0
  while IFS= read -r line; do
    i=$((i+1))
    rb=$(printf '%s\n' "$line" | wc -c)
    rsha=$(printf '%s' "$line" | sha256sum | cut -d' ' -f1)
    tag=${line%%|*}
    echo "HBIROW|n=$i|tag=$tag|offset=$off|bytes=$rb|sha256=$rsha|json=0"
    off=$((off+rb))
  done < "$hbp"
  echo "HBIEND|rows=$i|bytes=$off|json=0"
} > "$hbi"

# SHA-256 sidecars (coreutils style) for both
for f in "$hbp" "$hbi"; do
  sha256sum "$f" | sed "s| .*| *$f|" > "$f.sha256"
done

echo "== sidecars written:"
sha256sum "$hbp" "$hbi" PARTICLE-ORBIT-AND-OMEGA-2026-07-14.md metatag_v2_behcs.py
echo "== HBI self-check (recompute row hashes vs projection):"
ok=1; off=0; i=0
while IFS= read -r line; do
  i=$((i+1)); rsha=$(printf '%s' "$line" | sha256sum | cut -d' ' -f1)
  grep -q "|n=$i|.*|sha256=$rsha|" "$hbi" || { echo "ROW $i MISMATCH"; ok=0; }
done < "$hbp"
[ $ok -eq 1 ] && echo "HBI_VERIFY_OK rows=$i"
