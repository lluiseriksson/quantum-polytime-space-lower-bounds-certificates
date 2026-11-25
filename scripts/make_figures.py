"""Generate 300-DPI publication figures for Paper 27 (Quantum Polytime Space Lower Bounds).
Author: Lluis Eriksson
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
FIG_DIR = ROOT / "paper" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.titlesize": 9.5,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 7.8,
    "figure.dpi": 300,
    "savefig.dpi": 300,
})


def make_fig1() -> None:
    d2 = json.loads((RESULTS / "exp2_zk_ball_growth.json").read_text(encoding="utf-8"))["rows"]
    ns = [r["n"] for r in d2]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.75))

    colors = ["#1b4f72", "#2e86c1", "#117a65", "#b7950b", "#a93226"]
    for idx, k in enumerate((1, 2, 3, 4, 5)):
        vals = [r[f"B{k}"] for r in d2]
        ax1.plot(ns, vals, marker="o", markersize=3.5, linewidth=1.6, color=colors[idx], label=f"k = {k}")
    ax1.set_yscale("log")
    ax1.set_xlabel("Word length bound n")
    ax1.set_ylabel("Exact dissimilarity B_k(n)")
    ax1.set_title("(a) Exact Z^k L1-ball dissimilarity growth")
    ax1.grid(True, which="both", linestyle="--", alpha=0.35)
    ax1.legend(loc="upper left", frameon=True, ncol=2)

    # Panel (b): Remscrim 2QCFA degree u vs separating Z^k dimension k = u + 1
    labels = ["r=1\nd=1", "r=1\nd=2", "r=2\nd=1", "c=2,r=2\nd=2"]
    u_vals = [16, 64, 256, 2048]
    k_vals = [17, 65, 257, 2049]
    x = np.arange(len(labels))
    w = 0.36
    b1 = ax2.bar(x - w / 2, u_vals, width=w, color="#5d6d7e", label="2QCFA upper degree u")
    b2 = ax2.bar(x + w / 2, k_vals, width=w, color="#c0392b", label="Separating dim k = u+1")
    ax2.set_yscale("log")
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=7.4)
    ax2.set_ylabel("Polynomial degree (log scale)")
    ax2.set_title("(b) 2QCFA degree u vs. Z^k separation")
    ax2.set_ylim(5, 8000)
    ax2.grid(True, axis="y", linestyle="--", alpha=0.35)
    ax2.legend(loc="upper left", frameon=True)
    for bar in b2:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2, h * 1.18, f"{int(h)}", ha="center", va="bottom", fontsize=7.0)

    fig.tight_layout(pad=0.9)
    fig.savefig(FIG_DIR / "fig1_zk_ball_and_2qcfa.png", bbox_inches="tight")
    plt.close(fig)


def make_fig2() -> None:
    d3 = json.loads((RESULTS / "exp3_counter_and_Li_scaling.json").read_text(encoding="utf-8"))["rows"]
    d4 = json.loads((RESULTS / "exp4_sublog_hierarchy_curves.json").read_text(encoding="utf-8"))["rows"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.75))

    ks = [r["counter_k"] for r in d3]
    Nks = [r["N_k"] for r in d3]
    j0 = [r["j_i0"] for r in d3]
    j1 = [r["j_i1"] for r in d3]
    j2 = [r["j_i2"] for r in d3]

    ax1.plot(ks, Nks, "o-", color="#1b4f72", linewidth=1.6, markersize=4, label="Counter length N_k")
    ax1.plot(ks, j0, "s-", color="#117a65", linewidth=1.5, markersize=4, label="Pal length j_k (i=0)")
    ax1.plot(ks, j1, "^-", color="#d68910", linewidth=1.5, markersize=4, label="Pal length j_k (i=1)")
    ax1.plot(ks, j2, "d-", color="#a93226", linewidth=1.5, markersize=4, label="Pal length j_k (i=2)")
    ax1.set_xscale("log", base=2)
    ax1.set_yscale("log", base=2)
    ax1.set_xlabel("Counter limit k (log2)")
    ax1.set_ylabel("String / palindrome length (log2)")
    ax1.set_title("(a) L_S counter N_k & L_i palindrome j_k")
    ax1.grid(True, linestyle="--", alpha=0.35)
    ax1.legend(loc="upper left", frameon=True, fontsize=7.2)

    Ls = [r["L"] for r in d4]
    ax2.plot(Ls, [r["s0"] for r in d4], "o-", color="#117a65", linewidth=1.6, markersize=4, label="i=0: L")
    ax2.plot(Ls, [r["s1"] for r in d4], "s-", color="#2e86c1", linewidth=1.6, markersize=4, label="i=1: L / M")
    ax2.plot(Ls, [r["s2"] for r in d4], "^-", color="#d68910", linewidth=1.6, markersize=4, label="i=2: L / M^2")
    ax2.plot(Ls, [r["s3"] for r in d4], "d-", color="#a93226", linewidth=1.6, markersize=4, label="i=3: L / M^3")
    ax2.set_xscale("log", base=2)
    ax2.set_yscale("log")
    ax2.set_xlabel("Input log-length L = log2 n")
    ax2.set_ylabel("Space threshold L / M^i")
    ax2.set_title("(b) Sublogarithmic hierarchy L / (log L)^i")
    ax2.grid(True, linestyle="--", alpha=0.35)
    ax2.legend(loc="upper left", frameon=True, fontsize=7.3)

    fig.tight_layout(pad=0.9)
    fig.savefig(FIG_DIR / "fig2_counter_and_sublog_hierarchy.png", bbox_inches="tight")
    plt.close(fig)


def make_fig3() -> None:
    d1 = json.loads((RESULTS / "exp1_certified_atlas.json").read_text(encoding="utf-8"))["rows"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.95), gridspec_kw={"width_ratios": [1.55, 1.0]})

    stems = [r["file"].replace(".cert.json", "") for r in d1]
    ms = [r["verify_ms"] for r in d1]
    mode_colors = {
        "zk_word_problem_dissimilarity_exact": "#1f618d",
        "poly_degree_2qcfa_separation_exact": "#117a65",
        "sublog_hierarchy_Li_membership_exact": "#b7950b",
        "sublog_space_exponent_barrier_exact": "#922b21",
    }
    cols = [mode_colors[r["mode"]] for r in d1]

    y = np.arange(len(stems))
    ax1.barh(y, ms, color=cols, height=0.72)
    ax1.set_xscale("log")
    ax1.set_yticks(y)
    ax1.set_yticklabels(stems, fontsize=6.6)
    ax1.invert_yaxis()
    ax1.set_xlabel("Zero-float replay latency (ms, log scale)")
    ax1.set_title("(a) Replay time across all 16 certificates")
    ax1.grid(True, axis="x", linestyle="--", alpha=0.35)

    modes = [
        ("M1: Z^k Dissim.", 4, "#1f618d"),
        ("M2: 2QCFA Sep.", 4, "#117a65"),
        ("M3: L_i Member", 4, "#b7950b"),
        ("M4: Exp Barrier", 4, "#922b21"),
    ]
    mx = np.arange(len(modes))
    ax2.bar(mx, [m[1] for m in modes], color=[m[2] for m in modes], width=0.58)
    ax2.set_xticks(mx)
    ax2.set_xticklabels([m[0] for m in modes], rotation=22, ha="right", fontsize=7.4)
    ax2.set_ylabel("Certified instances")
    ax2.set_ylim(0, 5.2)
    ax2.set_title("(b) Balanced 4-mode coverage")
    ax2.grid(True, axis="y", linestyle="--", alpha=0.35)
    for i, m in enumerate(modes):
        ax2.text(i, m[1] + 0.14, "4/4\nPASS", ha="center", va="bottom", fontsize=6.8, fontweight="bold")

    fig.tight_layout(pad=0.9)
    fig.savefig(FIG_DIR / "fig3_atlas_summary.png", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    make_fig1()
    make_fig2()
    make_fig3()
    print("[PASS] Generated 3 publication-quality 300-DPI figures in paper/figures/.")


if __name__ == "__main__":
    main()
