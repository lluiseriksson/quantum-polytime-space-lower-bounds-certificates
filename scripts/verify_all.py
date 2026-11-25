"""End-to-end Gate-2 verification script for Paper 27:
  1. Lean 4 kernel build + zero-sorry / zero-warning / zero-Classical.choice axiom audit (18/18 theorems)
  2. Pure-stdlib zero-float replay of all 16 QUANTUM-SPACE-LB-CERT-1.0 certificates
  3. Full pytest suite (brute-force Z^k L1-ball & L_S/L_i cross-checks + 57 live adversarial attacks)
  4. SHA-256 manifest verification (or generation via --write-manifest)

Author: Lluis Eriksson
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.qspace_certifier import verify_quantum_space_lb_certificate_exact

EXPECTED_THEOREMS = [
    "QuantumSpaceLowerBounds.zk_word_problem_cancel_zero",
    "QuantumSpaceLowerBounds.zk_distinct_displacement_dissimilar",
    "QuantumSpaceLowerBounds.zk_unary_encoding_len_bound",
    "QuantumSpaceLowerBounds.zk_ball_1d_exact",
    "QuantumSpaceLowerBounds.zk_ball_2d_exact",
    "QuantumSpaceLowerBounds.zk_ball_3d_exact_cleared",
    "QuantumSpaceLowerBounds.poly_degree_domination",
    "QuantumSpaceLowerBounds.remscrim_2qcfa_exp_u_pos",
    "QuantumSpaceLowerBounds.binary_len_pos",
    "QuantumSpaceLowerBounds.binary_counter_step_gap",
    "QuantumSpaceLowerBounds.binary_counter_monotone_len",
    "QuantumSpaceLowerBounds.palindrome_prefix_half_even",
    "QuantumSpaceLowerBounds.palindrome_dissimilarity_exact_pow2",
    "QuantumSpaceLowerBounds.palindrome_reverse_involution",
    "QuantumSpaceLowerBounds.distinct_left_halves_separated",
    "QuantumSpaceLowerBounds.space_gap_halving_positive",
    "QuantumSpaceLowerBounds.double_exp_beats_poly_exponent",
    "QuantumSpaceLowerBounds.superpoly_pow2_dominates_linear",
]

MANIFEST_FILES = [
    "README.md",
    "pyproject.toml",
    "lean/lakefile.lean",
    "lean/lean-toolchain",
    "lean/QuantumSpaceLowerBounds.lean",
    "lean/AuditAxioms.lean",
    "src/__init__.py",
    "src/qspace_exact.py",
    "src/qspace_certifier.py",
    "scripts/run_all_experiments.py",
    "scripts/make_figures.py",
    "scripts/verify_all.py",
    "tests/test_suite.py",
    "results/exp1_certified_atlas.json",
    "results/exp2_zk_ball_growth.json",
    "results/exp3_counter_and_Li_scaling.json",
    "results/exp4_sublog_hierarchy_curves.json",
    "paper/main.tex",
    "paper/references.bib",
    "paper/main.pdf",
    "paper/figures/fig1_zk_ball_and_2qcfa.png",
    "paper/figures/fig2_counter_and_sublog_hierarchy.png",
    "paper/figures/fig3_atlas_summary.png",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def check_lean() -> None:
    lean_dir = ROOT / "lean"
    p1 = subprocess.run(["lake", "build"], cwd=lean_dir, capture_output=True, text=True, check=False)
    if p1.returncode != 0:
        raise RuntimeError(f"lake build failed:\n{p1.stdout}\n{p1.stderr}")
    if "warning:" in (p1.stdout + p1.stderr).lower():
        raise RuntimeError(f"Lean build emitted warnings:\n{p1.stdout}\n{p1.stderr}")

    p2 = subprocess.run(["lake", "env", "lean", "AuditAxioms.lean"], cwd=lean_dir, capture_output=True, text=True, check=False)
    if p2.returncode != 0:
        raise RuntimeError(f"AuditAxioms failed:\n{p2.stdout}\n{p2.stderr}")
    out = p2.stdout + p2.stderr
    for forbidden in ("sorryAx", "Classical.choice", "Lean.ofReduceBool", "Lean.trustCompiler"):
        if forbidden in out:
            raise RuntimeError(f"Forbidden Lean axiom {forbidden!r} found:\n{out}")
    for thm in EXPECTED_THEOREMS:
        if f"'{thm}'" not in out:
            raise RuntimeError(f"Missing theorem {thm} in AuditAxioms output")
    print(f"[PASS] Lean 4 kernel: {len(EXPECTED_THEOREMS)}/18 theorems, 0 warnings, 0 sorry, 0 Classical.choice")


def check_certs() -> list[str]:
    cert_dir = ROOT / "results" / "certificates"
    cert_files = sorted(cert_dir.glob("*.cert.json"))
    if len(cert_files) != 16:
        raise RuntimeError(f"Expected 16 certificates, found {len(cert_files)}")
    rel_list = []
    for cf in cert_files:
        data = json.loads(cf.read_text(encoding="utf-8"))
        res = verify_quantum_space_lb_certificate_exact(data)
        if not res.get("verified"):
            raise RuntimeError(f"Certificate failed verification: {cf.name}")
        rel_list.append(cf.relative_to(ROOT).as_posix())
    print("[PASS] Exact-Z/Q certificates: 16/16 independently verified (0 floats)")
    return rel_list


def check_pytest() -> None:
    p = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT, capture_output=True, text=True, check=False)
    if p.returncode != 0:
        raise RuntimeError(f"pytest failed:\n{p.stdout}\n{p.stderr}")
    print(f"[PASS] pytest: {p.stdout.strip()}")


def handle_manifest(cert_rels: list[str], write_manifest: bool) -> None:
    manifest_path = ROOT / "SHA256SUMS.json"
    all_files = sorted(set(MANIFEST_FILES + cert_rels))
    computed = {}
    for rel in all_files:
        p = ROOT / rel
        if not p.exists():
            raise RuntimeError(f"Manifest file missing: {rel}")
        computed[rel] = sha256_file(p)
    if write_manifest:
        manifest_path.write_text(json.dumps(computed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"[PASS] Wrote SHA256SUMS.json ({len(computed)} files)")
        return
    if not manifest_path.exists():
        raise RuntimeError("SHA256SUMS.json missing; run with --write-manifest first")
    expected = json.loads(manifest_path.read_text(encoding="utf-8"))
    if expected != computed:
        diff_keys = sorted(set(expected.keys()) ^ set(computed.keys()))
        bad_hashes = [k for k in computed if expected.get(k) != computed[k]]
        raise RuntimeError(f"SHA256SUMS mismatch! diff_keys={diff_keys}, bad_hashes={bad_hashes}")
    print(f"[PASS] SHA256SUMS.json: {len(computed)}/{len(computed)} files verified")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-manifest", action="store_true")
    args = ap.parse_args()
    check_lean()
    cert_rels = check_certs()
    check_pytest()
    handle_manifest(cert_rels, args.write_manifest)
    print("=== ALL PAPER 27 GATE-2 VERIFICATION CHECKS PASSED ===")


if __name__ == "__main__":
    main()
