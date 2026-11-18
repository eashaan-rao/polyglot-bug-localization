"""
Result figures for the Objective 2 paper, built only from stored statistics
(results/obj2/stats/*.csv), like Scripts/analysis/paper_tables.py.

  fig_effects.pdf     RQ3 adjusted class effect and RQ4 interaction, AP vs RR
  fig_decomp.pdf      MAP on Mono-fix files, Poly-fix primary and secondary files
  fig_sensitivity.pdf RQ4 interaction under each sensitivity condition

Palette: the first three slots of the dataviz reference palette (blue, orange,
aqua; validated all-pairs, light), always with a second encoding (marker shape
or position) and a legend, so the figures also read in grayscale print.

    python Scripts/analysis/paper_figures.py      # -> paper/figures/*.pdf, *.png
"""

import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager as fm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Scripts import paths as P

ST = os.path.join(P.RESULT_PATH, "stats")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "paper", "figures")

BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d9d8d4"
for f in ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
          "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"):
    if os.path.exists(f):
        fm.fontManager.addfont(f)
plt.rcParams.update({
    "font.family": "Liberation Sans", "font.size": 7.5, "axes.labelsize": 7.5,
    "axes.titlesize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK,
    "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0, "pdf.fonttype": 42,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
})
CM = 1 / 2.54
FULL, HALF = 17.6 * CM, 8.5 * CM


def load(n):
    return pd.read_csv(os.path.join(ST, n))


def one(df, **kw):
    for k, v in kw.items():
        df = df[df[k] == v]
    if len(df) != 1:
        raise ValueError(f"{len(df)} rows for {kw}")
    return df.iloc[0]


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, name + ".pdf"), bbox_inches="tight", pad_inches=0.02)
    fig.savefig(os.path.join(OUT, name + ".png"), bbox_inches="tight", pad_inches=0.02, dpi=300)
    plt.close(fig)
    print("wrote", name)


def forest(ax, labels, series, xlabel, groups=None):
    """Dot + 95% CI per row; `series` = [(name, color, marker, [(est, lo, hi)])]."""
    n = len(labels)
    y = np.arange(n)[::-1].astype(float)
    off = np.linspace(0.16, -0.16, len(series)) if len(series) > 1 else [0.0]
    ax.axvline(0, color=INK2, lw=0.7, zorder=1)
    for (name, col, mk, vals), o in zip(series, off):
        for yi, v in zip(y, vals):
            if v is None:
                continue
            est, lo, hi = v
            ax.plot([lo, hi], [yi + o] * 2, color=col, lw=1.4, solid_capstyle="round", zorder=2)
            filled = lo > 0 or hi < 0
            ax.plot(est, yi + o, marker=mk, ms=4.6, color=col, mfc=col if filled else "white",
                    mew=1.1, zorder=3, ls="none")
        ax.plot([], [], marker=mk, color=col, ls="none", ms=4.6, label=name)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_ylim(-0.6, n - 0.4)
    ax.grid(axis="x", color=GRID, lw=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xlabel(xlabel)
    if groups:
        for g_y, g_lab in groups:
            ax.axhline(g_y, color=GRID, lw=0.6, ls=(0, (2, 2)))
    return y


# ------------------------------------------------------------------ effects
def fig_effects():
    m, inv = load("rq3_models.csv"), load("rq4_inversion.csv")
    tech = [("BM25", "BM25", "all", "ap", "rr"), ("BLAZE", "BLAZE", "all", "ap", "rr"),
            ("FLIM-fallback", "FLIM", "all", "ap", "rr"), ("FLIM-strict", "FLIM", "parse", "ap", "rr"),
            ("LocAgent$^{\\dagger}$", "LocAgent", "all", "ap10", "rr10"),
            ("SweRank", "SweRank", "all", "ap", "rr"),
            ("SweRank, retriever", "SweRankEmbed", "all", "ap", "rr")]
    pairs = [("BM25 $-$ FLIM-strict", "BM25 vs FLIM-strict", "ap", "rr"),
             ("BM25 $-$ FLIM-fallback", "BM25 vs FLIM-fallback", "ap", "rr"),
             ("BM25-parse $-$ FLIM-strict\n(control)", "BM25-parse vs FLIM-strict (control)", "ap", "rr"),
             ("BM25 $-$ LocAgent$^{\\dagger}$", "BM25 vs LocAgent", "ap10", "rr10"),
             ("BM25 $-$ SweRank", "BM25 vs SweRank", "ap", "rr")]

    def ce(t, v, o):
        r = one(m, condition="primary", tech=t, view=v, outcome=o)
        return r.class_effect_poly, r.ci_lo, r.ci_hi

    def ia(p, o):
        r = one(inv, condition="primary", pair=p, outcome=o)
        return r.interaction_poly, r.ci_lo, r.ci_hi

    fig, (a, b) = plt.subplots(1, 2, figsize=(FULL, 5.4 * CM), gridspec_kw=dict(wspace=0.9))
    forest(a, [t[0] for t in tech],
           [("AP (primary outcome)", BLUE, "o", [ce(t[1], t[2], t[3]) for t in tech]),
            ("RR (first relevant file)", ORANGE, "s", [ce(t[1], t[2], t[4]) for t in tech])],
           "Poly-fix $-$ Mono-fix, adjusted", groups=[(4.5, "")])
    a.set_title("(a) RQ3: class effect per technique", loc="left", color=INK)
    forest(b, [p[0] for p in pairs],
           [("AP", BLUE, "o", [ia(p[1], p[2]) for p in pairs]),
            ("RR", ORANGE, "s", [ia(p[1], p[3]) for p in pairs])],
           "interaction: BM25 gain on Poly-fix $-$ on Mono-fix")
    b.set_title("(b) RQ4: BM25 against each parser-dependent technique", loc="left", color=INK)
    h, l = a.get_legend_handles_labels()
    h.append(plt.Line2D([], [], ls="none"))
    l.append("filled: 95% CI excludes 0;  $\\dagger$ AP@10 / RR@10, Python projects")
    fig.legend(h, l, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.2),
               handletextpad=0.3, columnspacing=1.6)
    save(fig, "fig_effects")


# ------------------------------------------------------------------ decomposition
def fig_decomp():
    """Decomposition with the other GT files of each bug removed from the ranking
    (Scripts/analysis/review_checks.py); error bar on the primary-language bar =
    Mono-fix MAP + 95% bootstrap CI of (Poly-fix primary - Mono-fix)."""
    import json
    rc = json.load(open(os.path.join(ST, "review_checks.json")))["decomposition"]
    spec = [("BM25", "BM25-all-ap"), ("BLAZE", "BLAZE-all-ap"), ("FLIM-\nfallback", "FLIM-all-ap"),
            ("FLIM-\nstrict", "FLIM-parse-ap"), ("Loc-\nAgent$^{\\dagger}$", "LocAgent-all-ap10"),
            ("SweRank", "SweRank-all-ap")]
    spec = [(lab, key, "parse" if key == "FLIM-parse-ap" else "all") for lab, key in spec]
    pp = load("rq3_per_project.csv")
    src = {"BM25-all-ap": ("BM25", "all", "ap"), "BLAZE-all-ap": ("BLAZE", "all", "ap"), "FLIM-all-ap": ("FLIM", "all", "ap"),
           "FLIM-parse-ap": ("FLIM", "parse", "ap"), "LocAgent-all-ap10": ("LocAgent", "all", "ap10"),
           "SweRank-all-ap": ("SweRank", "all", "ap")}
    mono = [one(pp, condition="primary", tech=src[k][0], view=src[k][1], outcome=src[k][2], project="POOLED").mean_mono
            for _, k, _ in spec]           # same source as the tables (rounding consistency)
    prim = [rc[k]["poly_prim_removed"] for _, k, _ in spec]
    sec = [0.0 if k == "FLIM-parse-ap" else rc[k]["poly_sec_removed"] for _, k, _ in spec]
    err = np.array([[rc[k]["poly_prim_removed"] - (m_ + rc[k]["poly_prim_removed_minus_mono_ci"][0]),
                     m_ + rc[k]["poly_prim_removed_minus_mono_ci"][1] - rc[k]["poly_prim_removed"]]
                    for (_, k, _), m_ in zip(spec, mono)]).T
    x = np.arange(len(spec))
    w = 0.26
    fig, ax = plt.subplots(figsize=(HALF, 5.0 * CM))
    for i, (vals, col, lab, hatch) in enumerate([
            (mono, BLUE, "Mono-fix bugs, all fix files", None),
            (prim, AQUA, "Poly-fix bugs, primary-language files", None),
            (sec, ORANGE, "Poly-fix bugs, secondary-language files", None)]):
        bars = ax.bar(x + (i - 1) * (w + 0.02), vals, w, color=col, label=lab, zorder=2, linewidth=0)
        if i == 1:
            ax.errorbar(x, vals, yerr=err, fmt="none", ecolor=INK2, elinewidth=0.8, capsize=1.6, zorder=3)
        if i == 2:
            for xi, v, (_, key, vw) in zip(x, vals, spec):
                txt = "n/a" if key == "FLIM-parse-ap" else f"{v:.3f}".replace("0.", ".", 1)
                ax.text(xi + (w + 0.02), v + 0.012, txt, ha="center", va="bottom", fontsize=5.6, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels([s[0] for s in spec])
    ax.set_ylabel("MAP")
    ax.set_ylim(0, 0.55)
    ax.grid(axis="y", color=GRID, lw=0.5, zorder=0)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="x", length=0)
    ax.legend(loc="lower left", frameon=False, ncol=1, bbox_to_anchor=(-0.02, 1.0), handlelength=1.0,
              borderaxespad=0.2)
    save(fig, "fig_decomp")


# ------------------------------------------------------------------ sensitivity
def fig_sensitivity():
    inv = load("rq4_inversion.csv")
    conds = [("primary", "Main analysis"), ("P_behavioural", "Poly-fix: behaviour-bearing"),
             ("P_test_only", "Poly-fix: test-asset only"), ("S1_no_tests", "S1 no test files in GT"),
             ("S2_headline", "S2 data-format grain"), ("S2_strict", "S2 strict grain"),
             ("S3_universe_T", "S3 text universe T"), ("S4_untangled", "S4 merge commits removed"),
             ("S5_fold1", "S5 fold 1 only"), ("S5_fold2", "S5 fold 2 only"),
             ("S6_removed", "S6 filter-excluded bugs only")]
    panels = [("X = FLIM-strict", "BM25 vs FLIM-strict", "ap"),
              ("Control, X = FLIM-strict", "BM25-parse vs FLIM-strict (control)", "ap"),
              ("X = LocAgent (AP@10)$^{\\dagger}$", "BM25 vs LocAgent", "ap10"),
              ("X = SweRank$^{\\dagger}$", "BM25 vs SweRank", "ap")]
    fig, axes = plt.subplots(1, 4, figsize=(FULL, 6.2 * CM), sharey=True, gridspec_kw=dict(wspace=0.12))
    for k, (ax, (title, pair, out)) in enumerate(zip(axes, panels)):
        vals = []
        for c, _ in conds:
            d = inv[(inv.condition == c) & (inv.pair == pair) & (inv.outcome == out)]
            vals.append(None if d.empty else (d.iloc[0].interaction_poly, d.iloc[0].ci_lo, d.iloc[0].ci_hi))
        forest(ax, [c[1] for c in conds], [("", BLUE, "o", vals)], "")
        ax.set_xlim(-0.2, 0.4)
        ax.set_xticks([-0.1, 0, 0.1, 0.2, 0.3])
        ax.set_xticklabels(["$-$.1", "0", ".1", ".2", ".3"])
        ax.set_title(title, loc="left", fontsize=6.6, color=INK)
        ax.axhline(9.5, color=GRID, lw=0.6, ls=(0, (2, 2)))
        if k:
            ax.tick_params(axis="y", length=0)
    fig.supxlabel("interaction BM25 $-$ X (AP): BM25 gain on Poly-fix $-$ on Mono-fix.  Filled: 95% CI excludes 0.  "
                  "$\\dagger$ Python projects",
                  fontsize=7, y=-0.04, color=INK)
    save(fig, "fig_sensitivity")


def main():
    fig_effects()
    fig_decomp()
    fig_sensitivity()


if __name__ == "__main__":
    main()
