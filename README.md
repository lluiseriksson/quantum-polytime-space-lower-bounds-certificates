# Machine-Checked Exact-Rational Dissimilarity, Binary-Counter, and Superpolynomial Space-Lower-Bound Certificates for Polynomial-Time Quantum Computation

**Author:** Lluis Eriksson (with transparent AI assistance via Google Antigravity)  
**License:** MIT (code, Lean 4 proofs, certificates) / CC-BY-4.0 (manuscript)

Zero-dependency Lean 4 formalization and pure-stdlib exact-$\mathbb{Z}/\mathbb{Q}$ certificate verifier (`QUANTUM-SPACE-LB-CERT-1.0`) for the finite combinatorial, dissimilarity-growth, binary-counter, and superpolynomial exponent-separation backbone of A. C. Cem Say (*Lower space bounds for polynomial-time quantum computation*, `arXiv:2611.32633`, November 24, 2026).

## Verification Summary
- **Lean 4 Kernel (`lean/QuantumSpaceLowerBounds.lean`, Lean 4.35.0):** 18/18 constructive theorems, 0 warnings, 0 `sorry`, 0 `Classical.choice`, formalizing arbitrary-dimension $\mathbb{Z}^k$ word-problem cancellation & dissimilarity (`Fin k -> Int`), unary binary-alphabet encoding length $\le (k+2)n$, exact 1D/2D/3D $L_1$-ball bounds, polynomial-degree domination $c\,n^u < n^k$, Remscrim 2QCFA exponent bound $u = c(2r)^4 d^2 \ge 16$, $L_S$ binary-counter monotonicity, $L_i$ palindrome prefix separation on `List Bool` yielding $2^{j/2}$ dissimilar strings, Lemma 17 space-gap halving, and double-exponential vs. polynomial-degree dominance.
- **Exact-$\mathbb{Z}/\mathbb{Q}$ Certificate Atlas (`results/certificates/*.cert.json`):** 16 canonical certificates across 4 modes ($\mathbb{Z}^k$ word-problem full $L_1$-ball dissimilarity up to $k=4, 129$ words; Remscrim 2QCFA degree separation up to $u=2048, k=2049$; two-track $L_i$ membership & $2^{j/2}$ dissimilarity for $i=0..3$; Lemma 17 superpolynomial exponent barriers up to $L=2^{20}, 2^{31} \gg 100 L$), replayed with zero floats in `0.013`–`4.440 ms`.
- **Cross-Checks & Red-Team Suite (`tests/test_suite.py`):** Direct brute-force $\mathbb{Z}^k$ $L_1$-ball enumeration across $k=1..4$, exhaustive $L_S$/$L_i$ length-bound sweeps for $k=4..128$, unary encoding injectivity check on $\mathbb{Z}^3$, 16/16 certificate replays, and **57/57** live adversarial attacks rejected.

## One-Command Reproducibility
```bash
python scripts/verify_all.py
```
To regenerate all certificates, experiment JSONs, and 300-DPI figures from scratch:
```bash
python scripts/run_all_experiments.py
python scripts/make_figures.py
python scripts/verify_all.py
```
