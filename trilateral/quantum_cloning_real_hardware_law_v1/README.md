# Real-hardware encrypted quantum-cloning law

Status: `MEASURED_EXTERNAL_PRIMARY_SOURCE` for the cited experiment; repo-side PID registration only; `fire=0`.

## Correction

The blanket statement “physical quantum cloning is impossible” is false.

Yamaguchi, Rullkötter, Shehzad, Wagner, Tutschku, and Kempf report encrypted quantum cloning on physical IBM Heron-R2 superconducting hardware in [arXiv:2602.10695v1](https://arxiv.org/abs/2602.10695v1). The LIRIS source copy used for this receipt has SHA-256:

`95febbd44ed31c9072acedee156c928f27ce38fffcc159696f3c864d6dafa755`

The extracted 20-page text used for row-by-row review has SHA-256:

`06200fc399e89a32e496b58d51afe299368574956ecb84b68f923d05a2669c9e`

## Measured experiment

- Up to 154 physical transmon qubits on IBM Heron-R2 hardware.
- 77 physical encrypted clones in the largest iterated run.
- Selected-clone entanglement fidelity `0.286 ± 0.009`, above the maximally mixed floor `0.25`.
- Entanglement witnessed through 27 encrypted clones.
- CHSH violation survived through three encrypted clones in the reported successful timing scenarios.
- Multipartite GHZ tests were also executed.

These are measurements reported by the paper’s authors and independently checked here against the frozen paper bytes. This repository did not rerun the IBM hardware experiment.

## Law and necessary boundary

For every finite clone count in the ideal protocol, the encrypted signal marginals reveal no input-state information, while the quantum key allows recovery of one freely selected clone:

`MARGINAL(ENC_n(rho), signal_i) = I/2; DEC_nj(signal_j, key) = rho`

The decryption key is single-use. Decrypting the selected clone consumes the key and leaves the remaining encrypted clones indecipherable. The paper therefore does not demonstrate unrestricted simultaneously readable plaintext copies, abolish the no-cloning theorem, replicate arbitrary particles, test prismed laser light, authenticate a UAP video, or establish a cosmological model.

Classical Q-Prism or branch-copy artifacts are not this hardware experiment. Conversely, that boundary must not be used to deny the measured real-hardware encrypted-cloning result.

## Asolaria relation

The paper is a real-hardware possibility anchor for a separately designed Q-Prism/photonic experiment. That bridge remains a design until a precommitted physical channel experiment, key ledger, model charge, and independent replay exist.

The cross-seat SHA receipts and the paper's quantum key share an abstract architecture:
distributed representations are bound to a common verification or recovery anchor. The digital
mechanism is a public content commitment; the physical protocol uses a single-use quantum
decryption key. The two endpoint mechanisms are measured in their own domains; the shared-pattern
mapping is a scoped architectural interpretation. The mechanisms are not identical.

The operator-observed raw values `1.8 .18 %` are preserved verbatim in the HBP. Their numeric interpretation and relationship to the paper remain unresolved and are not rewritten here.

## Build and verify

```powershell
python .\build_packet.py
python .\verify.py
python .\verify.py --paper <path-to-v1-pdf> --paper-text <path-to-pdftotext-layout-output>
```

The verifier checks LF encoding, every HBI byte range, every row SHA-256, the hex mirror, sidecars, the scoped law fields, and optional frozen primary-source bytes. CI rebuilds the packet and requires a zero diff.
