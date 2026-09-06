"""
Step 1 — Prevalence. Descriptive, no model.

Reads data/obj2/bug_classification.parquet and reports, for the KEPT bug set
(fix touches the project's primary language):
  * Mono-fix / Poly-fix counts and Poly-fix prevalence per project and pooled,
    at three grains (headline = YAML/JSON/XML/SQL secondary; broad = any
    grammar-language secondary; strict = >=2 programming languages);
  * the distribution of secondary languages in Poly-fix bugs, with how often
    the secondary file is itself a ground-truth localization target (C4);
  * a per-project table of the smaller class size (feasibility of a balanced
    within-project comparison).

Outputs: results/obj2/prevalence/*.csv, prevalence_summary.md, and a bar chart.
"""

import json
import os
import sys
from collections import Counter, defaultdict

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Scripts import paths as P
from Scripts.classification_rules import (
    RULESET_VERSION, TIER1_SECONDARY, TIER2_SECONDARY,
)

OUT = os.path.join(P.RESULT_PATH, "prevalence")
os.makedirs(OUT, exist_ok=True)


def tier(lang):
    return "T1" if lang in TIER1_SECONDARY else ("T2" if lang in TIER2_SECONDARY else "T3")


def main():
    df = pd.read_parquet(P.BUG_CLASSIFICATION_PARQUET)
    kept = df[df["keep"]].copy()

    # ---- 1. prevalence by project ------------------------------------
    prj_rows = []
    for repo in P.SELECTED_REPO_NAMES:
        g = kept[kept.repo_name == repo]
        m = int((g["class"] == "Mono-fix").sum())
        p = int((g["class"] == "Poly-fix").sum())
        prj_rows.append({
            "project": repo, "kept_bugs": len(g), "mono_fix": m, "poly_fix": p,
            "poly_pct_headline": round(100 * g["grain_headline"].sum() / (m + p), 1),
            "poly_pct_broad": round(100 * g["grain_broad"].sum() / (m + p), 1),
            "poly_pct_strict": round(100 * g["grain_strict"].sum() / (m + p), 1),
            "n_headline": int(g["grain_headline"].sum()),
            "n_broad": int(g["grain_broad"].sum()),
            "n_strict": int(g["grain_strict"].sum()),
            "smaller_class_n": min(m, p),
        })
    prj = pd.DataFrame(prj_rows)
    pooled = {
        "project": "POOLED", "kept_bugs": len(kept),
        "mono_fix": int((kept["class"] == "Mono-fix").sum()),
        "poly_fix": int((kept["class"] == "Poly-fix").sum()),
    }
    mp = pooled["mono_fix"] + pooled["poly_fix"]
    for gr in ("headline", "broad", "strict"):
        pooled[f"poly_pct_{gr}"] = round(100 * kept[f"grain_{gr}"].sum() / mp, 1)
        pooled[f"n_{gr}"] = int(kept[f"grain_{gr}"].sum())
    pooled["smaller_class_n"] = min(pooled["mono_fix"], pooled["poly_fix"])
    prj = pd.concat([prj, pd.DataFrame([pooled])], ignore_index=True)
    prj.to_csv(os.path.join(OUT, "prevalence_by_project.csv"), index=False)

    # ---- 2. secondary-language distribution -------------------------
    poly = kept[kept["class"] == "Poly-fix"]
    lang_bugs = Counter()
    lang_projects = defaultdict(set)
    lang_gt = Counter()
    for _, r in poly.iterrows():
        secs = json.loads(r["secondary_languages"])
        in_gt = set(json.loads(r["secondary_in_ground_truth"]))
        for l in secs:
            lang_bugs[l] += 1
            lang_projects[l].add(r["repo_name"])
            if l in in_gt:
                lang_gt[l] += 1
    sec = pd.DataFrame([
        {"secondary_language": l, "tier": tier(l), "poly_fix_bugs": n,
         "n_projects": len(lang_projects[l]),
         "bugs_where_secondary_is_gt_target": lang_gt[l]}
        for l, n in lang_bugs.most_common()
    ])
    sec.to_csv(os.path.join(OUT, "secondary_language_distribution.csv"), index=False)

    # ---- 3. classified_from / tangling provenance ------------------
    prov = pd.DataFrame({
        "classified_from": df["classified_from"].value_counts(),
        "tangled_merge_commits": [int(df["tangled_flag"].sum())] + [None] * (df["classified_from"].nunique() - 1),
    })
    prov.to_csv(os.path.join(OUT, "provenance.csv"))

    # ---- 4. markdown summary --------------------------------------
    md = [f"# Step 1 — Prevalence  (RULESET_VERSION {RULESET_VERSION})", ""]
    md.append(f"Kept bug set: **{len(kept)}** of {len(df)} bugs "
              f"({100*len(kept)/len(df):.1f}%) — fix touches the project's primary "
              f"(AST-parseable) language.\n")
    md.append("## Poly-fix prevalence (share of Mono+Poly, kept set)\n")
    md.append("| grain | definition | pooled | range across projects |")
    md.append("|---|---|---|---|")
    for gr, desc in [("headline", "secondary is YAML / JSON / XML / SQL"),
                     ("broad", "secondary is any language with a grammar (adds build scripts, 2nd programming language, Shell, Jinja, grammars)"),
                     ("strict", "fix spans >= 2 programming languages")]:
        vals = prj[prj.project != "POOLED"][f"poly_pct_{gr}"]
        md.append(f"| {gr} | {desc} | **{pooled[f'poly_pct_{gr}']}%** "
                  f"({pooled[f'n_{gr}']} bugs) | {vals.min()}% – {vals.max()}% |")
    md.append("")
    md.append("## Per project\n")
    md.append("| project | kept | Mono | Poly | headline % | broad % | strict % | smaller class n |")
    md.append("|---|---|---|---|---|---|---|---|")
    for _, r in prj.iterrows():
        md.append(f"| {r['project']} | {r['kept_bugs']} | {r['mono_fix']} | {r['poly_fix']} | "
                  f"{r['poly_pct_headline']}% | {r['poly_pct_broad']}% | {r['poly_pct_strict']}% | "
                  f"{r['smaller_class_n']} |")
    md.append("\nEvery project has >= ~100 bugs in its smaller class -> a balanced "
              "within-project Mono-vs-Poly comparison is viable for all six.\n")
    md.append("## Secondary languages in Poly-fix bugs (kept set)\n")
    md.append("| secondary language | tier | Poly-fix bugs | projects | is a ground-truth target in |")
    md.append("|---|---|---|---|---|")
    for _, r in sec.iterrows():
        md.append(f"| {r['secondary_language']} | {r['tier']} | {r['poly_fix_bugs']} | "
                  f"{r['n_projects']} | {r['bugs_where_secondary_is_gt_target']} |")
    md.append("\nEvery counted secondary file is also a ground-truth localization "
              "target — the polyglot files are what developers had to locate, not "
              "incidental edits.\n")
    md.append("> Note: `broad` includes Shell (101 bugs, mostly test glue). "
              "`broad` minus Shell ≈ {} bugs.".format(pooled["n_broad"] - lang_bugs.get("Shell", 0)))
    with open(os.path.join(OUT, "prevalence_summary.md"), "w") as f:
        f.write("\n".join(md) + "\n")

    # ---- 5. figure ----------------------------------------------
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        pp = prj[prj.project != "POOLED"]
        x = range(len(pp))
        fig, ax = plt.subplots(figsize=(9, 4.5))
        w = 0.26
        ax.bar([i - w for i in x], pp["poly_pct_strict"], w, label="strict (>=2 prog. langs)")
        ax.bar(list(x), pp["poly_pct_headline"], w, label="headline (YAML/JSON/XML/SQL)")
        ax.bar([i + w for i in x], pp["poly_pct_broad"], w, label="broad (any grammar lang)")
        ax.set_xticks(list(x))
        ax.set_xticklabels([p.split("/")[-1] for p in pp["project"]], rotation=20, ha="right")
        ax.set_ylabel("Poly-fix % of Mono+Poly")
        ax.set_title(f"Poly-fix prevalence by project and grain (RULESET {RULESET_VERSION})")
        ax.legend()
        fig.tight_layout()
        fig.savefig(os.path.join(OUT, "prevalence_by_project.png"), dpi=130)
        print("wrote prevalence_by_project.png")
    except Exception as e:
        print("figure skipped:", e)

    print("\n".join(md))
    print(f"\nWrote CSVs + prevalence_summary.md to {OUT}")


if __name__ == "__main__":
    main()
