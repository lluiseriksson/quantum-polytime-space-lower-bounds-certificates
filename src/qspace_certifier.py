"""Pure-stdlib zero-float verifier for QUANTUM-SPACE-LB-CERT-1.0 certificates.
Supports four exact-Z/Q verification modes aligned with A. C. Cem Say (arXiv:2611.32633, Nov 24, 2026)
"Lower space bounds for polynomial-time quantum computation":
  1. zk_word_problem_dissimilarity_exact   (Sec 3.1.2, Thm 2: Z^k word-problem dissimilarity & unary encoding <= (k+2)n)
  2. poly_degree_2qcfa_separation_exact    (Sec 3.1.2, Fact 13 vs Eq. 3: Remscrim u=c(2r)^4 d^2, k>u -> c_k n^u < n^k)
  3. sublog_hierarchy_Li_membership_exact  (Sec 4, Lemmas 16-17, Eqs 4-7: L_S counter, L_i two-track palindrome & 2^(j/2))
  4. sublog_space_exponent_barrier_exact   (Sec 4, Lemma 17, Thm 3: space halving & double-exp beats poly exponent)

Author: Lluis Eriksson
"""
from __future__ import annotations

import re
from fractions import Fraction
from typing import Any, Dict, List

from src.qspace_exact import (
    bin_str_exact,
    build_counter_string_LS,
    li_palindrome_len_exact,
    zk_displacement,
    zk_l1_ball_size_exact,
    zk_unary_encode,
)

SCHEMA_VERSION = "QUANTUM-SPACE-LB-CERT-1.0"
_CANON_INT_RE = re.compile(r"\A(?:0|-?[1-9][0-9]*)\Z")
_CANON_FRAC_RE = re.compile(r"\A-?[1-9][0-9]*/[1-9][0-9]*\Z")


class QuantumSpaceLBCertificateError(ValueError):
    """Raised whenever any QUANTUM-SPACE-LB-CERT-1.0 verification check fails."""


def _assert_strict_json_types(obj: Any, path: str = "root") -> None:
    t = type(obj)
    if t is int or t is str or obj is None:
        return
    if t is dict:
        for k, v in obj.items():
            if type(k) is not str:
                raise QuantumSpaceLBCertificateError(f"Non-str dict key at {path}: {type(k).__name__}")
            _assert_strict_json_types(v, f"{path}.{k}")
        return
    if t is list:
        for i, v in enumerate(obj):
            _assert_strict_json_types(v, f"{path}[{i}]")
        return
    raise QuantumSpaceLBCertificateError(f"Forbidden type {t.__name__} at {path}")


def _parse_int(val: Any, name: str) -> int:
    if type(val) is not int:
        raise QuantumSpaceLBCertificateError(f"{name} must be strict int, got {type(val).__name__}")
    return val


def _parse_rat(val: Any, name: str) -> Fraction:
    if type(val) is int:
        return Fraction(val, 1)
    if type(val) is str:
        if _CANON_INT_RE.match(val):
            return Fraction(int(val), 1)
        if _CANON_FRAC_RE.match(val):
            num_s, den_s = val.split("/")
            num, den = int(num_s), int(den_s)
            if den < 2:
                raise QuantumSpaceLBCertificateError(f"{name} denominator must be >= 2: {val!r}")
            q = Fraction(num, den)
            if q.numerator != num or q.denominator != den:
                raise QuantumSpaceLBCertificateError(f"{name} unreduced fraction: {val!r}")
            return q
        raise QuantumSpaceLBCertificateError(f"{name} non-canonical rational string: {val!r}")
    raise QuantumSpaceLBCertificateError(f"{name} invalid type {type(val).__name__}")


def _verify_mode1_zk_dissimilarity(cert: Dict[str, Any]) -> Dict[str, Any]:
    req = {
        "schema", "mode", "name", "dim_k", "max_len_n", "words",
        "claimed_ball_size", "claimed_max_encoded_len",
    }
    if set(cert.keys()) != req:
        raise QuantumSpaceLBCertificateError(f"Mode 1 key mismatch: {sorted(set(cert.keys()) ^ req)}")
    k = _parse_int(cert["dim_k"], "dim_k")
    n = _parse_int(cert["max_len_n"], "max_len_n")
    if not (1 <= k <= 8) or not (1 <= n <= 32):
        raise QuantumSpaceLBCertificateError(f"Require 1 <= k <= 8 and 1 <= n <= 32, got k={k}, n={n}")

    w_raw = cert["words"]
    if type(w_raw) is not list or len(w_raw) < 2 or len(w_raw) > 256:
        raise QuantumSpaceLBCertificateError("words must be list of length in [2, 256]")

    disps = []
    max_enc_len = 0
    for idx, w in enumerate(w_raw):
        if type(w) is not list or len(w) > n:
            raise QuantumSpaceLBCertificateError(f"words[{idx}] must be list of length <= {n}")
        syms = [_parse_int(s, f"words[{idx}][{j}]") for j, s in enumerate(w)]
        if any(s == 0 or abs(s) > k for s in syms):
            raise QuantumSpaceLBCertificateError(f"words[{idx}] contains invalid Z^{k} generator")
        disps.append(zk_displacement(k, syms))
        enc = zk_unary_encode(k, syms)
        if len(enc) > (k + 2) * n:
            raise QuantumSpaceLBCertificateError(f"words[{idx}] unary encoding exceeds (k+2)*n")
        if len(enc) > max_enc_len:
            max_enc_len = len(enc)

    if len(set(disps)) != len(disps):
        raise QuantumSpaceLBCertificateError("words are NOT pairwise W_{Z^k}-dissimilar (duplicate net displacement)")

    # Verify explicit pairwise separating suffix v = w_i^{-1}
    for i in range(len(disps)):
        di = disps[i]
        for j in range(i + 1, len(disps)):
            dj = disps[j]
            if all(dj[c] - di[c] == 0 for c in range(k)):
                raise QuantumSpaceLBCertificateError(f"Pair ({i},{j}) not separated by w_i^-1")

    ball = zk_l1_ball_size_exact(k, n)
    if len(disps) > ball:
        raise QuantumSpaceLBCertificateError("Impossible: more distinct displacements than L1 ball size")
    if _parse_int(cert["claimed_ball_size"], "claimed_ball_size") != ball:
        raise QuantumSpaceLBCertificateError(f"claimed_ball_size mismatch: exact={ball}")
    if _parse_int(cert["claimed_max_encoded_len"], "claimed_max_encoded_len") != max_enc_len:
        raise QuantumSpaceLBCertificateError(f"claimed_max_encoded_len mismatch: exact={max_enc_len}")

    return {
        "verified": True,
        "mode": cert["mode"],
        "dim_k": k,
        "max_len_n": n,
        "dissimilar_count": len(disps),
        "ball_size": ball,
        "max_encoded_len": max_enc_len,
    }


def _verify_mode2_poly_separation(cert: Dict[str, Any]) -> Dict[str, Any]:
    req = {
        "schema", "mode", "name", "remscrim_c", "qubits_r", "states_d",
        "claimed_u", "dim_k", "const_ck", "witness_n",
    }
    if set(cert.keys()) != req:
        raise QuantumSpaceLBCertificateError(f"Mode 2 key mismatch: {sorted(set(cert.keys()) ^ req)}")
    rc = _parse_int(cert["remscrim_c"], "remscrim_c")
    rr = _parse_int(cert["qubits_r"], "qubits_r")
    rd = _parse_int(cert["states_d"], "states_d")
    if rc < 1 or rr < 1 or rd < 1 or rc > 64 or rr > 8 or rd > 32:
        raise QuantumSpaceLBCertificateError("Remscrim 2QCFA parameters out of certified range")
    u = rc * ((2 * rr) ** 4) * (rd * rd)
    if _parse_int(cert["claimed_u"], "claimed_u") != u:
        raise QuantumSpaceLBCertificateError(f"claimed_u mismatch: exact={u}")

    k = _parse_int(cert["dim_k"], "dim_k")
    ck = _parse_int(cert["const_ck"], "const_ck")
    n = _parse_int(cert["witness_n"], "witness_n")
    if k <= u or k > u + 64 or ck < 1 or n <= ck or n > 10000:
        raise QuantumSpaceLBCertificateError(f"Require u < k <= u+64 and 1 <= const_ck < witness_n <= 10000")
    if not (ck * (n ** u) < (n ** k)):
        raise QuantumSpaceLBCertificateError("Polynomial degree domination c_k * n^u < n^k failed")

    return {
        "verified": True,
        "mode": cert["mode"],
        "u_2qcfa": u,
        "dim_k": k,
        "witness_n": n,
        "margin_bits": (n ** k).bit_length() - (ck * (n ** u)).bit_length(),
    }


def _verify_mode3_Li_membership(cert: Dict[str, Any]) -> Dict[str, Any]:
    req = {
        "schema", "mode", "name", "level_i", "counter_k",
        "upper_track", "lower_track", "claimed_N_k", "claimed_j_k", "claimed_dissim_log2",
    }
    if set(cert.keys()) != req:
        raise QuantumSpaceLBCertificateError(f"Mode 3 key mismatch: {sorted(set(cert.keys()) ^ req)}")
    i_lvl = _parse_int(cert["level_i"], "level_i")
    k_max = _parse_int(cert["counter_k"], "counter_k")
    if not (0 <= i_lvl <= 4) or not (4 <= k_max <= 256):
        raise QuantumSpaceLBCertificateError(f"Require 0 <= level_i <= 4 and 4 <= counter_k <= 256")
    upper = cert["upper_track"]
    lower = cert["lower_track"]
    if type(upper) is not str or type(lower) is not str:
        raise QuantumSpaceLBCertificateError("upper_track and lower_track must be str")

    expected_upper = build_counter_string_LS(k_max)
    if upper != expected_upper:
        raise QuantumSpaceLBCertificateError("upper_track does not match exact L_S string bin(0)$...$bin(k)")
    Nk = len(upper)
    if len(lower) != Nk:
        raise QuantumSpaceLBCertificateError(f"lower_track length {len(lower)} != N_k={Nk}")

    # Verify Eq. (4): (1/2) log2(N_k) <= L <= log2(N_k) <-> 2^L <= N_k <= 2^(2L)
    L, M, e, jk = li_palindrome_len_exact(k_max, i_lvl)
    if not ((1 << L) <= Nk <= (1 << (2 * L))):
        raise QuantumSpaceLBCertificateError(f"Eq. (4) length bound 2^L <= N_k <= 2^(2L) violated (L={L}, N_k={Nk})")
    if jk > Nk or (jk % 2 != 0):
        raise QuantumSpaceLBCertificateError(f"Palindrome length j_k={jk} invalid for N_k={Nk}")

    pal = lower[:jk]
    pad = lower[jk:]
    if any(ch not in "01" for ch in pal) or any(ch != "#" for ch in pad):
        raise QuantumSpaceLBCertificateError("lower_track does not match {0,1}^{j_k} #*")
    if pal != pal[::-1]:
        raise QuantumSpaceLBCertificateError("lower_track prefix is NOT a palindrome")

    half = jk // 2
    if _parse_int(cert["claimed_N_k"], "claimed_N_k") != Nk:
        raise QuantumSpaceLBCertificateError(f"claimed_N_k mismatch: exact={Nk}")
    if _parse_int(cert["claimed_j_k"], "claimed_j_k") != jk:
        raise QuantumSpaceLBCertificateError(f"claimed_j_k mismatch: exact={jk}")
    if _parse_int(cert["claimed_dissim_log2"], "claimed_dissim_log2") != half:
        raise QuantumSpaceLBCertificateError(f"claimed_dissim_log2 mismatch: exact={half}")

    return {
        "verified": True,
        "mode": cert["mode"],
        "level_i": i_lvl,
        "counter_k": k_max,
        "N_k": Nk,
        "j_k": jk,
        "dissim_log2": half,
    }


def _verify_mode4_exponent_barrier(cert: Dict[str, Any]) -> Dict[str, Any]:
    req = {
        "schema", "mode", "name", "level_i", "log_n_L", "loglog_n_M",
        "d2", "b0", "a0", "poly_deg_c", "claimed_F_lb", "claimed_exp_margin",
    }
    if set(cert.keys()) != req:
        raise QuantumSpaceLBCertificateError(f"Mode 4 key mismatch: {sorted(set(cert.keys()) ^ req)}")
    i_lvl = _parse_int(cert["level_i"], "level_i")
    L = _parse_int(cert["log_n_L"], "log_n_L")
    M = _parse_int(cert["loglog_n_M"], "loglog_n_M")
    c_poly = _parse_int(cert["poly_deg_c"], "poly_deg_c")
    if not (0 <= i_lvl <= 4) or L < 16 or M < 4 or c_poly < 1:
        raise QuantumSpaceLBCertificateError("Invalid level_i, L, M, or poly_deg_c")
    if not ((1 << (M - 1)) <= L < (1 << M)):
        raise QuantumSpaceLBCertificateError(f"M={M} does not match exact bit-length |bin(L)| for L={L}")

    d2 = _parse_rat(cert["d2"], "d2")
    b0 = _parse_rat(cert["b0"], "b0")
    a0 = _parse_rat(cert["a0"], "a0")
    if d2 <= 0 or b0 <= 0 or a0 <= 0 or not (2 * b0 * a0 <= d2):
        raise QuantumSpaceLBCertificateError("Require d2, b0, a0 > 0 and 2*b0*a0 <= d2 (Lemma 17 halving)")

    X = Fraction(L, M ** i_lvl)
    F_lb = (d2 - b0 * a0) * X
    if not (F_lb >= (d2 / 2) * X):
        raise QuantumSpaceLBCertificateError("Impossible: halving lower bound failed")
    f_floor = int(F_lb)
    if f_floor < 1 or f_floor > 200:
        raise QuantumSpaceLBCertificateError(f"floor(F_lb)={f_floor} outside certified range [1, 200]")

    b0S = b0 * a0 * X
    lhs = Fraction(1 << f_floor, 1) - b0S
    rhs = Fraction(c_poly * L, 1)
    if not (lhs > rhs):
        raise QuantumSpaceLBCertificateError(f"Superpolynomial exponent barrier failed: {lhs} <= {rhs}")

    if _parse_rat(cert["claimed_F_lb"], "claimed_F_lb") != F_lb:
        raise QuantumSpaceLBCertificateError(f"claimed_F_lb mismatch: exact={F_lb}")
    if _parse_rat(cert["claimed_exp_margin"], "claimed_exp_margin") != lhs - rhs:
        raise QuantumSpaceLBCertificateError(f"claimed_exp_margin mismatch: exact={lhs - rhs}")

    return {
        "verified": True,
        "mode": cert["mode"],
        "level_i": i_lvl,
        "L": L,
        "F_lb": str(F_lb),
        "floor_F": f_floor,
        "beats_poly_deg": c_poly,
    }


def verify_quantum_space_lb_certificate_exact(cert: Dict[str, Any]) -> Dict[str, Any]:
    if type(cert) is not dict:
        raise QuantumSpaceLBCertificateError("Certificate root must be a dict")
    _assert_strict_json_types(cert)
    if cert.get("schema") != SCHEMA_VERSION:
        raise QuantumSpaceLBCertificateError(f"Invalid schema: {cert.get('schema')!r}")
    name = cert.get("name")
    if type(name) is not str or not name.strip():
        raise QuantumSpaceLBCertificateError(f"Certificate name must be non-empty str, got {name!r}")
    mode = cert.get("mode")
    if mode == "zk_word_problem_dissimilarity_exact":
        return _verify_mode1_zk_dissimilarity(cert)
    if mode == "poly_degree_2qcfa_separation_exact":
        return _verify_mode2_poly_separation(cert)
    if mode == "sublog_hierarchy_Li_membership_exact":
        return _verify_mode3_Li_membership(cert)
    if mode == "sublog_space_exponent_barrier_exact":
        return _verify_mode4_exponent_barrier(cert)
    raise QuantumSpaceLBCertificateError(f"Unknown mode: {mode!r}")
