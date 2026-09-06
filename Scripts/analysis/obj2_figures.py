"""
Paper figures. Robust to techniques not yet run.

Outputs: results/obj2/figures/*.png

Run:  python Scripts/analysis/obj2_figures.py
"""

import glob
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Scripts import paths as P
from Scripts.classification_rules import EXT_LANG, GRAMMAR_LANGUAGES, TIER1_SECONDARY

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = os.path.join(P.RESULT_PATH, "figures")
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"figure.autolayout": True, "font.size": 10})


def short(p):
    return p.split("/")[-1]


def fig_prevalence():
    d = pd.read_csv(os.path.join(P.RESULT_PATH, "prevalence", "prevalence_by_project.csv"))
    d = d[d.project != "POOLED"]
    x = np.arange(len(d)); wdt = 0.26
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(x - wdt, d["poly_pct_strict"], wdt, label="strict (≥2 prog. langs)")
    ax.bar(x, d["poly_pct_headline"], wdt, label="headline (YAML/JSON/XML/SQL)")
    ax.bar(x + wdt, d["poly_pct_broad"], wdt, label="broad (any grammar lang)")
    ax.set_xticks(x); ax.set_xticklabels([short(p) for p in d.project], rotation=20, ha="right")
    ax.set_ylabel("Poly-fix % of Mono+Poly"); ax.set_title("Poly-fix prevalence by project and grain")
    ax.legend(fontsize=8)
    fig.savefig(os.path.join(OUT, "fig1_prevalence.png"), dpi=140)
    plt.close(fig)


def fig_secondary_dist():
    d = pd.read_csv(os.path.join(P.RESULT_PATH, "prevalence", "secondary_language_distribution.csv"))
    d = d.head(14).iloc[::-1]
    colours = {"T1": "#1f77b4", "T2": "#ff7f0e", "T3": "#999999"}
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.barh(d.secondary_language, d.poly_fix_bugs,
            color=[colours[t] for t in d.tier])
    ax.set_xlabel("Poly-fix bugs (kept set)")
    ax.set_title("Secondary languages in Poly-fix bugs")
    for t, c in colours.items():
        ax.barh([], [], color=c, label=t)
    ax.legend(title="tier", fontsize=8)
    fig.savefig(os.path.join(OUT, "fig2_secondary_languages.png"), dpi=140)
    plt.close(fig)


def _diag():
    frames = []
    for f in glob.glob(os.path.join(P.RESULT_PATH, "diagnostics", "*.csv")):
        parts = os.path.basename(f)[:-4].split("_")
        d = pd.read_csv(f, dtype={"bug_id": str})
        d["model"] = parts[1]
        d["project"] = "_".join(parts[2:])
        frames.append(d)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def fig_mono_vs_poly():
    s = os.path.join(P.RESULT_PATH, "wp_cp_summary.csv")
    if not os.path.exists(s):
        return
    d = pd.read_csv(s)
    d = d[(d.arm == "WP") & d.bug_class.isin(["Mono-fix", "Poly-fix"])]
    piv = d.groupby(["model", "bug_class"]).MRR.mean().unstack()
    if piv.empty:
        return
    x = np.arange(len(piv)); wdt = 0.35
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(x - wdt / 2, piv.get("Mono-fix", 0), wdt, label="Mono-fix")
    ax.bar(x + wdt / 2, piv.get("Poly-fix", 0), wdt, label="Poly-fix")
    ax.set_xticks(x); ax.set_xticklabels(piv.index)
    ax.set_ylabel("MRR (macro-avg over 6 projects)")
    ax.set_title("Within-project MRR: Mono-fix vs Poly-fix")
    ax.legend()
    fig.savefig(os.path.join(OUT, "fig3_mono_vs_poly_mrr.png"), dpi=140)
    plt.close(fig)


def fig_per_extension_mrr():
    dg = _diag()
    if dg.empty:
        return
    dg["rr"] = 1.0 / np.where(dg.model_rank > 0, dg.model_rank, np.inf)
    dg["lang"] = dg.ext.map(lambda e: EXT_LANG.get(str(e), (None,))[0])
    sec = dg[dg.lang.isin(TIER1_SECONDARY)]
    if sec.empty:
        return
    piv = sec.groupby(["lang", "model"]).rr.mean().unstack()
    piv = piv.reindex([l for l in ["YAML", "JSON", "XML", "SQL"] if l in piv.index])
    ax = piv.plot(kind="bar", figsize=(7, 4))
    ax.set_ylabel("MRR on ground-truth files of this type")
    ax.set_title("Ranking of secondary-language ground-truth files, by technique")
    ax.figure.savefig(os.path.join(OUT, "fig4_per_extension_mrr.png"), dpi=140)
    plt.close(ax.figure)


if __name__ == "__main__":
    for fn in (fig_prevalence, fig_secondary_dist, fig_mono_vs_poly, fig_per_extension_mrr):
        try:
            fn()
            print("ok:", fn.__name__)
        except Exception as e:
            print("skip:", fn.__name__, "-", e)
    print(f"figures -> {OUT}")
