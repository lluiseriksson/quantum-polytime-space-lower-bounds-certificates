"""Pure-stdlib zero-float exact-Z/Q engine for polynomial-time quantum space lower bounds.
Aligned with A. C. Cem Say (arXiv:2611.32633, Nov 24, 2026)
"Lower space bounds for polynomial-time quantum computation".

Author: Lluis Eriksson
"""
from __future__ import annotations

from fractions import Fraction
from typing import List, Sequence, Tuple


def zk_l1_ball_size_exact(k: int, n: int) -> int:
    """Exact cardinality B_k(n) of the L1 ball {v in Z^k : sum |v_i| <= n} via exact integer DP."""
    if k < 0 or n < 0:
        raise ValueError("k, n must be >= 0")
    dp = [1] * (n + 1)  # B_0(r) = 1 for all r >= 0
    for _ in range(k):
        nxt = [0] * (n + 1)
        pref = 0
        for r in range(n + 1):
            nxt[r] = dp[r] + 2 * pref
            pref += dp[r]
        dp = nxt
    return dp[n]


def zk_displacement(k: int, word: Sequence[int]) -> Tuple[int, ...]:
    """Compute exact net displacement in Z^k for word over {+1, -1, ..., +k, -k}."""
    vec = [0] * k
    for sym in word:
        if sym == 0 or abs(sym) > k:
            raise ValueError(f"Invalid generator symbol {sym} for Z^{k}")
        idx = abs(sym) - 1
        vec[idx] += 1 if sym > 0 else -1
    return tuple(vec)


def zk_unary_encode(k: int, word: Sequence[int]) -> str:
    """Encode Z^k word into binary string kappa_k(w) with length <= (k+2)*|w| (Section 3.1.2).
    Encoding: +r -> '1' + '0'*(r) + '1' (len r+2 <= k+2), -r -> '0' + '1'*(r) + '0' (len r+2 <= k+2).
    """
    parts = []
    for sym in word:
        r = abs(sym)
        if sym > 0:
            parts.append("1" + ("0" * r) + "1")
        else:
            parts.append("0" + ("1" * r) + "0")
    return "".join(parts)


def bin_str_exact(m: int) -> str:
    """Shortest binary representation bin(m) without leading zeros (bin(0) = '0')."""
    if m < 0:
        raise ValueError("m must be >= 0")
    return format(m, "b")


def build_counter_string_LS(k_max: int) -> str:
    """Build exact L_S string bin(0)$bin(1)$...$bin(k_max) (Section 4)."""
    if k_max < 1:
        raise ValueError("k_max must be >= 1")
    return "$".join(bin_str_exact(m) for m in range(k_max + 1))


def ceil_div_int(a: int, b: int) -> int:
    if b <= 0:
        raise ValueError("denominator must be > 0")
    return (a + b - 1) // b


def li_palindrome_len_exact(k_max: int, level_i: int) -> Tuple[int, int, int, int]:
    """Return (L = |bin(k_max)|, M = |bin(L)|, e = ceil(L / M^i), j = 2^e) for language L_i (Eq. 5)."""
    L = len(bin_str_exact(k_max))
    M = len(bin_str_exact(L))
    e = ceil_div_int(L, M ** level_i)
    j = 1 << e
    return L, M, e, j


def fmt_rat(q: Fraction) -> str:
    if q.denominator == 1:
        return str(q.numerator)
    return f"{q.numerator}/{q.denominator}"
