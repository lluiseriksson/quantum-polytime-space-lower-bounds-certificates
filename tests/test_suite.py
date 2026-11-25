"""Comprehensive verification, brute-force cross-checks, and 57-attack red-team suite
for QUANTUM-SPACE-LB-CERT-1.0 (Paper 27).
Author: Lluis Eriksson
"""
from __future__ import annotations

import copy
import itertools
import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.qspace_certifier import (
    QuantumSpaceLBCertificateError,
    verify_quantum_space_lb_certificate_exact,
)
from src.qspace_exact import (
    bin_str_exact,
    build_counter_string_LS,
    li_palindrome_len_exact,
    zk_displacement,
    zk_l1_ball_size_exact,
    zk_unary_encode,
)

CERT_DIR = ROOT / "results" / "certificates"


def _load(name: str) -> Dict[str, Any]:
    return json.loads((CERT_DIR / name).read_text(encoding="utf-8"))


def test_bruteforce_zk_l1_ball_and_Li_counter_cross_checks() -> None:
    """Independent brute-force enumeration of Z^k L1-balls and L_S/L_i invariants."""
    # 1. Brute-force enumerate all integer points in Z^k with ||x||_1 <= n
    for k, max_n in [(1, 6), (2, 5), (3, 4), (4, 3)]:
        for n in range(0, max_n + 1):
            brute = sum(
                1 for vec in itertools.product(range(-n, n + 1), repeat=k)
                if sum(abs(c) for c in vec) <= n
            )
            assert zk_l1_ball_size_exact(k, n) == brute
            # Cross-check exact closed forms from Lean Theorems 4, 5, 6
            if k == 1:
                assert brute == 2 * n + 1
            elif k == 2:
                assert brute == 2 * n * n + 2 * n + 1
            elif k == 3:
                assert 3 * brute == 4 * (n ** 3) + 6 * (n ** 2) + 8 * n + 3

    # 2. Verify Eq. (4) and strict monotonicity of L_S populated lengths N_k for k = 4..128
    prev_len = 0
    for k_max in range(4, 129):
        u = build_counter_string_LS(k_max)
        Nk = len(u)
        assert Nk > prev_len
        prev_len = Nk
        L = k_max.bit_length()
        assert (1 << L) <= Nk <= (1 << (2 * L))
        for i_lvl in (0, 1, 2):
            _, _, _, jk = li_palindrome_len_exact(k_max, i_lvl)
            assert jk >= 2 and jk % 2 == 0 and jk <= Nk

    # 3. Verify unary encoding injectivity on all length-<=2 words in Z^3
    alphabet = [1, -1, 2, -2, 3, -3]
    seen_enc = set()
    for length in range(0, 3):
        for w in itertools.product(alphabet, repeat=length):
            enc = zk_unary_encode(3, list(w))
            assert len(enc) <= (3 + 2) * length
            assert enc not in seen_enc
            seen_enc.add(enc)


def test_all_16_certificates_verify_cleanly() -> None:
    cert_files = sorted(CERT_DIR.glob("*.cert.json"))
    assert len(cert_files) == 16
    for p in cert_files:
        cert = json.loads(p.read_text(encoding="utf-8"))
        res = verify_quantum_space_lb_certificate_exact(cert)
        assert res["verified"] is True


def test_57_live_adversarial_red_team_attacks_rejected() -> None:
    m1 = _load("zk_dissim_k2_n4.cert.json")
    m2 = _load("poly_sep_r1_d1.cert.json")
    m3 = _load("Li_member_i0_k15.cert.json")
    m4 = _load("exp_barrier_i0_L64.cert.json")

    def mutate(base: Dict[str, Any], fn: Callable[[Dict[str, Any]], None]) -> Dict[str, Any]:
        c = copy.deepcopy(base)
        fn(c)
        return c

    attacks: List[Tuple[str, Any]] = [
        # --- Global AST / schema / type attacks (1-14) ---
        ("01_root_not_dict", [1, 2, 3]),
        ("02_bad_schema", mutate(m1, lambda c: c.__setitem__("schema", "QUANTUM-SPACE-LB-CERT-2.0"))),
        ("03_unknown_mode", mutate(m1, lambda c: c.__setitem__("mode", "fake_mode"))),
        ("04_empty_name", mutate(m1, lambda c: c.__setitem__("name", "   "))),
        ("05_float_injected", mutate(m4, lambda c: c.__setitem__("d2", 0.3333))),
        ("06_bool_as_int", mutate(m1, lambda c: c.__setitem__("dim_k", True))),
        ("07_decimal_injected", mutate(m4, lambda c: c.__setitem__("b0", Decimal("0.5")))),
        ("08_complex_injected", mutate(m2, lambda c: c.__setitem__("dim_k", 17 + 0j))),
        ("09_tuple_injected", mutate(m1, lambda c: c.__setitem__("words", tuple(c["words"])))),
        ("10_non_str_key", {**m2, 99: "bad"}),
        ("11_unreduced_frac", mutate(m4, lambda c: c.__setitem__("d2", "2/6"))),
        ("12_denom_one_str", mutate(m4, lambda c: c.__setitem__("d2", "1/1"))),
        ("13_neg_zero_str", mutate(m4, lambda c: c.__setitem__("a0", "-0"))),
        ("14_extra_key", mutate(m2, lambda c: c.__setitem__("rogue", 1))),

        # --- Mode 1: Z^k word-problem dissimilarity attacks (15-26) ---
        ("15_m1_missing_key", mutate(m1, lambda c: c.pop("claimed_ball_size"))),
        ("16_m1_dim_k_zero", mutate(m1, lambda c: c.__setitem__("dim_k", 0))),
        ("17_m1_dim_k_too_large", mutate(m1, lambda c: c.__setitem__("dim_k", 9))),
        ("18_m1_max_len_zero", mutate(m1, lambda c: c.__setitem__("max_len_n", 0))),
        ("19_m1_too_few_words", mutate(m1, lambda c: c.__setitem__("words", [[]]))),
        ("20_m1_word_too_long", mutate(m1, lambda c: c["words"].__setitem__(0, [1, 1, 1, 1, 1]))),
        ("21_m1_zero_generator", mutate(m1, lambda c: c["words"].__setitem__(0, [0]))),
        ("22_m1_out_of_range_gen", mutate(m1, lambda c: c["words"].__setitem__(0, [3]))),
        ("23_m1_duplicate_displacement", mutate(m1, lambda c: c["words"].__setitem__(1, [1, -1]))),
        ("24_m1_commuting_collision", mutate(m1, lambda c: c["words"].__setitem__(0, [1, 2]) or c["words"].__setitem__(1, [2, 1]))),
        ("25_m1_wrong_ball_size", mutate(m1, lambda c: c.__setitem__("claimed_ball_size", 42))),
        ("26_m1_wrong_max_enc_len", mutate(m1, lambda c: c.__setitem__("claimed_max_encoded_len", 15))),

        # --- Mode 2: Polynomial degree 2QCFA separation attacks (27-35) ---
        ("27_m2_missing_key", mutate(m2, lambda c: c.pop("witness_n"))),
        ("28_m2_zero_qubits", mutate(m2, lambda c: c.__setitem__("qubits_r", 0))),
        ("29_m2_zero_states", mutate(m2, lambda c: c.__setitem__("states_d", 0))),
        ("30_m2_wrong_claimed_u", mutate(m2, lambda c: c.__setitem__("claimed_u", 15))),
        ("31_m2_k_equals_u", mutate(m2, lambda c: c.__setitem__("dim_k", 16))),
        ("32_m2_k_less_than_u", mutate(m2, lambda c: c.__setitem__("dim_k", 12))),
        ("33_m2_n_le_ck", mutate(m2, lambda c: c.__setitem__("witness_n", 63) or c.__setitem__("const_ck", 63))),
        ("34_m2_ck_zero", mutate(m2, lambda c: c.__setitem__("const_ck", 0))),
        ("35_m2_witness_n_huge", mutate(m2, lambda c: c.__setitem__("witness_n", 10001))),

        # --- Mode 3: Sublogarithmic hierarchy L_i membership attacks (36-46) ---
        ("36_m3_missing_key", mutate(m3, lambda c: c.pop("claimed_j_k"))),
        ("37_m3_bad_level_i", mutate(m3, lambda c: c.__setitem__("level_i", 5))),
        ("38_m3_counter_k_too_small", mutate(m3, lambda c: c.__setitem__("counter_k", 3))),
        ("39_m3_corrupted_upper_track", mutate(m3, lambda c: c.__setitem__("upper_track", "1" + c["upper_track"][1:]))),
        ("40_m3_truncated_lower_track", mutate(m3, lambda c: c.__setitem__("lower_track", c["lower_track"][:-1]))),
        ("41_m3_non_palindrome_lower", mutate(m3, lambda c: c.__setitem__("lower_track", ("0" if c["lower_track"][0] == "1" else "1") + c["lower_track"][1:]))),
        ("42_m3_bad_pad_char", mutate(m3, lambda c: c.__setitem__("lower_track", c["lower_track"][:-1] + "0"))),
        ("43_m3_bad_pal_char", mutate(m3, lambda c: c.__setitem__("lower_track", "#" + c["lower_track"][1:]))),
        ("44_m3_wrong_Nk", mutate(m3, lambda c: c.__setitem__("claimed_N_k", c["claimed_N_k"] + 1))),
        ("45_m3_wrong_jk", mutate(m3, lambda c: c.__setitem__("claimed_j_k", c["claimed_j_k"] - 2))),
        ("46_m3_wrong_dissim_log2", mutate(m3, lambda c: c.__setitem__("claimed_dissim_log2", c["claimed_dissim_log2"] + 1))),

        # --- Mode 4: Sublogarithmic exponent barrier attacks (47-57) ---
        ("47_m4_missing_key", mutate(m4, lambda c: c.pop("claimed_F_lb"))),
        ("48_m4_L_too_small", mutate(m4, lambda c: c.__setitem__("log_n_L", 8))),
        ("49_m4_M_mismatch_L", mutate(m4, lambda c: c.__setitem__("loglog_n_M", 6))),
        ("50_m4_d2_nonpositive", mutate(m4, lambda c: c.__setitem__("d2", "0"))),
        ("51_m4_a0_negative", mutate(m4, lambda c: c.__setitem__("a0", "-1/4"))),
        ("52_m4_halving_violated", mutate(m4, lambda c: c.__setitem__("a0", "1/2"))),
        ("53_m4_poly_deg_zero", mutate(m4, lambda c: c.__setitem__("poly_deg_c", 0))),
        ("54_m4_barrier_violated_huge_c", mutate(m4, lambda c: c.__setitem__("poly_deg_c", 10000))),
        ("55_m4_wrong_F_lb", mutate(m4, lambda c: c.__setitem__("claimed_F_lb", "41/3"))),
        ("56_m4_wrong_margin", mutate(m4, lambda c: c.__setitem__("claimed_exp_margin", "1"))),
        ("57_m4_level_i_out_of_range", mutate(m4, lambda c: c.__setitem__("level_i", -1))),
    ]

    assert len(attacks) == 57
    for label, payload in attacks:
        with pytest.raises(QuantumSpaceLBCertificateError, match="."):
            verify_quantum_space_lb_certificate_exact(payload)
