"""Generate all 16 canonical QUANTUM-SPACE-LB-CERT-1.0 certificates and 4 experiment JSONs for Paper 27.
Author: Lluis Eriksson
"""
from __future__ import annotations

import json
import pathlib
import sys
import time
from fractions import Fraction
from typing import Dict, List

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.qspace_certifier import verify_quantum_space_lb_certificate_exact
from src.qspace_exact import (
    build_counter_string_LS,
    fmt_rat,
    li_palindrome_len_exact,
    zk_l1_ball_size_exact,
    zk_unary_encode,
)

RESULTS = ROOT / "results"
CERTS = RESULTS / "certificates"
RESULTS.mkdir(parents=True, exist_ok=True)
CERTS.mkdir(parents=True, exist_ok=True)


def _emit_cert(filename: str, cert: Dict) -> Dict:
    t0 = time.perf_counter()
    summary = verify_quantum_space_lb_certificate_exact(cert)
    ms = (time.perf_counter() - t0) * 1000.0
    (CERTS / filename).write_text(json.dumps(cert, indent=2) + "\n", encoding="utf-8")
    return {"file": filename, "mode": cert["mode"], "verify_ms": round(ms, 4), "summary": summary}


def _gen_l1_ball_words(k: int, n: int, limit: int) -> List[List[int]]:
    """Generate distinct canonical words in Z^k of L1 length <= n (up to `limit`)."""
    words: List[List[int]] = []

    def rec(dim: int, rem: int, cur: List[int]) -> None:
        if len(words) >= limit:
            return
        if dim == k:
            words.append(list(cur))
            return
        # Try 0, then +1..-rem
        rec(dim + 1, rem, cur)
        for step in range(1, rem + 1):
            rec(dim + 1, rem - step, cur + [dim + 1] * step)
            rec(dim + 1, rem - step, cur + [-(dim + 1)] * step)

    rec(0, n, [])
    return words[:limit]


def main() -> None:
    atlas_rows = []

    # =========================================================================
    # MODE 1: 4 Z^k Word-Problem Dissimilarity & Unary Encoding Certificates (Thm 2)
    # =========================================================================
    m1_specs = [
        ("zk_dissim_k1_n6.cert.json", "mode1_zk_k1_n6", 1, 6, 13),
        ("zk_dissim_k2_n4.cert.json", "mode1_zk_k2_n4", 2, 4, 41),
        ("zk_dissim_k3_n3.cert.json", "mode1_zk_k3_n3", 3, 3, 63),
        ("zk_dissim_k4_n3.cert.json", "mode1_zk_k4_n3", 4, 3, 129),
    ]
    for fname, cname, k, n, lim in m1_specs:
        ws = _gen_l1_ball_words(k, n, lim)
        ball = zk_l1_ball_size_exact(k, n)
        max_enc = max(len(zk_unary_encode(k, w)) for w in ws)
        atlas_rows.append(_emit_cert(fname, {
            "schema": "QUANTUM-SPACE-LB-CERT-1.0",
            "mode": "zk_word_problem_dissimilarity_exact",
            "name": cname,
            "dim_k": k,
            "max_len_n": n,
            "words": ws,
            "claimed_ball_size": ball,
            "claimed_max_encoded_len": max_enc,
        }))

    # =========================================================================
    # MODE 2: 4 Remscrim 2QCFA Polynomial-Degree Separation Certificates (Thm 2)
    # =========================================================================
    m2_specs = [
        ("poly_sep_r1_d1.cert.json", "mode2_2qcfa_r1_d1", 1, 1, 1, 17, 50, 64),
        ("poly_sep_r1_d2.cert.json", "mode2_2qcfa_r1_d2", 1, 1, 2, 65, 100, 128),
        ("poly_sep_r2_d1.cert.json", "mode2_2qcfa_r2_d1", 1, 2, 1, 257, 200, 256),
        ("poly_sep_c2_r2_d2.cert.json", "mode2_2qcfa_c2_r2_d2", 2, 2, 2, 2049, 500, 512),
    ]
    for fname, cname, rc, rr, rd, k, ck, wn in m2_specs:
        u = rc * ((2 * rr) ** 4) * (rd * rd)
        atlas_rows.append(_emit_cert(fname, {
            "schema": "QUANTUM-SPACE-LB-CERT-1.0",
            "mode": "poly_degree_2qcfa_separation_exact",
            "name": cname,
            "remscrim_c": rc,
            "qubits_r": rr,
            "states_d": rd,
            "claimed_u": u,
            "dim_k": k,
            "const_ck": ck,
            "witness_n": wn,
        }))

    # =========================================================================
    # MODE 3: 4 Sublogarithmic Space-Hierarchy Language L_i Membership Certificates (Thm 3)
    # =========================================================================
    m3_specs = [
        ("Li_member_i0_k15.cert.json", "mode3_Li_i0_k15", 0, 15),
        ("Li_member_i1_k31.cert.json", "mode3_Li_i1_k31", 1, 31),
        ("Li_member_i2_k63.cert.json", "mode3_Li_i2_k63", 2, 63),
        ("Li_member_i3_k127.cert.json", "mode3_Li_i3_k127", 3, 127),
    ]
    for fname, cname, i_lvl, k_max in m3_specs:
        upper = build_counter_string_LS(k_max)
        Nk = len(upper)
        _, _, _, jk = li_palindrome_len_exact(k_max, i_lvl)
        half = jk // 2
        # Build non-trivial deterministic binary left-half palindrome
        left = "".join("1" if ((idx * 3 + i_lvl) % 5 in (0, 2)) else "0" for idx in range(half))
        pal = left + left[::-1]
        lower = pal + ("#" * (Nk - jk))
        atlas_rows.append(_emit_cert(fname, {
            "schema": "QUANTUM-SPACE-LB-CERT-1.0",
            "mode": "sublog_hierarchy_Li_membership_exact",
            "name": cname,
            "level_i": i_lvl,
            "counter_k": k_max,
            "upper_track": upper,
            "lower_track": lower,
            "claimed_N_k": Nk,
            "claimed_j_k": jk,
            "claimed_dissim_log2": half,
        }))

    # =========================================================================
    # MODE 4: 4 Sublogarithmic Superpolynomial Exponent Barrier Certificates (Lemma 17)
    # =========================================================================
    m4_specs = [
        ("exp_barrier_i0_L64.cert.json", "mode4_barrier_i0", 0, 64, 7, Fraction(1, 3), Fraction(1, 2), Fraction(1, 4), 10),
        ("exp_barrier_i1_L512.cert.json", "mode4_barrier_i1", 1, 512, 10, Fraction(2, 5), Fraction(1, 2), Fraction(1, 4), 20),
        ("exp_barrier_i2_L16384.cert.json", "mode4_barrier_i2", 2, 16384, 15, Fraction(2, 5), Fraction(1, 2), Fraction(1, 4), 50),
        ("exp_barrier_i3_L1048576.cert.json", "mode4_barrier_i3", 3, 1048576, 21, Fraction(2, 5), Fraction(1, 2), Fraction(1, 4), 100),
    ]
    for fname, cname, i_lvl, L, M, d2, b0, a0, c_poly in m4_specs:
        X = Fraction(L, M ** i_lvl)
        F_lb = (d2 - b0 * a0) * X
        f_floor = int(F_lb)
        b0S = b0 * a0 * X
        margin = Fraction(1 << f_floor, 1) - b0S - Fraction(c_poly * L, 1)
        atlas_rows.append(_emit_cert(fname, {
            "schema": "QUANTUM-SPACE-LB-CERT-1.0",
            "mode": "sublog_space_exponent_barrier_exact",
            "name": cname,
            "level_i": i_lvl,
            "log_n_L": L,
            "loglog_n_M": M,
            "d2": fmt_rat(d2),
            "b0": fmt_rat(b0),
            "a0": fmt_rat(a0),
            "poly_deg_c": c_poly,
            "claimed_F_lb": fmt_rat(F_lb),
            "claimed_exp_margin": fmt_rat(margin),
        }))

    (RESULTS / "exp1_certified_atlas.json").write_text(
        json.dumps({"experiment": "exp1_certified_atlas", "count": len(atlas_rows), "rows": atlas_rows}, indent=2) + "\n",
        encoding="utf-8",
    )

    # =========================================================================
    # EXP 2: Exact Z^k L1-Ball Growth B_k(n) across k = 1..5, n = 1..12
    # =========================================================================
    exp2_rows = []
    for n in range(1, 13):
        exp2_rows.append({
            "n": n,
            "B1": zk_l1_ball_size_exact(1, n),
            "B2": zk_l1_ball_size_exact(2, n),
            "B3": zk_l1_ball_size_exact(3, n),
            "B4": zk_l1_ball_size_exact(4, n),
            "B5": zk_l1_ball_size_exact(5, n),
        })
    (RESULTS / "exp2_zk_ball_growth.json").write_text(
        json.dumps({"experiment": "exp2_zk_ball_growth", "rows": exp2_rows}, indent=2) + "\n",
        encoding="utf-8",
    )

    # =========================================================================
    # EXP 3: L_S Binary Counter Populated Lengths N_k & Eq. (4) Ratios
    # =========================================================================
    exp3_rows = []
    for k_max in (7, 15, 31, 63, 127, 255):
        u = build_counter_string_LS(k_max)
        Nk = len(u)
        L, M, e0, j0 = li_palindrome_len_exact(k_max, 0)
        _, _, e1, j1 = li_palindrome_len_exact(k_max, 1)
        _, _, e2, j2 = li_palindrome_len_exact(k_max, 2)
        exp3_rows.append({
            "counter_k": k_max,
            "N_k": Nk,
            "L_bits": L,
            "M_bits": M,
            "j_i0": j0,
            "j_i1": j1,
            "j_i2": j2,
        })
    (RESULTS / "exp3_counter_and_Li_scaling.json").write_text(
        json.dumps({"experiment": "exp3_counter_and_Li_scaling", "rows": exp3_rows}, indent=2) + "\n",
        encoding="utf-8",
    )

    # =========================================================================
    # EXP 4: Sublogarithmic Hierarchy Space Thresholds L / M^i across L = 16..32768
    # =========================================================================
    exp4_rows = []
    for exp_L in (4, 6, 8, 10, 12, 15):
        L = 1 << exp_L
        M = exp_L + 1
        exp4_rows.append({
            "L": L,
            "M": M,
            "s0": round(L / 1.0, 4),
            "s1": round(L / M, 4),
            "s2": round(L / (M ** 2), 4),
            "s3": round(L / (M ** 3), 4),
        })
    (RESULTS / "exp4_sublog_hierarchy_curves.json").write_text(
        json.dumps({"experiment": "exp4_sublog_hierarchy_curves", "rows": exp4_rows}, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"[PASS] Generated & verified {len(atlas_rows)}/16 exact-Z/Q certificates and 4 experiment JSONs.")
    for r in atlas_rows:
        print(f"  {r['file']:44s} {r['verify_ms']:6.3f} ms  {r['summary']}")


if __name__ == "__main__":
    main()
