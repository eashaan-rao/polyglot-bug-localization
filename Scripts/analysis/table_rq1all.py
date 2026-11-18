"""
Table of RQ1 over all 13 eligible BeetleBox projects (second internal review, 2.1).
Input : results/obj2/rq1_all13_summary.csv  (Scripts/rq1_all_projects.py)
Output: paper/tables/tab_rq1_all13.tex

    python Scripts/analysis/table_rq1all.py
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Scripts import paths as P

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
s = pd.read_csv(os.path.join(P.RESULT_PATH, "rq1_all13_summary.csv"))
s["short"] = s.repo_name.str.split("/").str[1]
s = s.sort_values(["selected", "language", "short"], ascending=[False, True, True])
pct = lambda v: f"{100 * v:.1f}"
num = lambda v: f"{int(v):,}".replace(",", "{,}")


def row(name, lang, r):
    return (f"{name} ({lang}) & {num(r['bugs'])} & {num(r['kept'])} & {pct(r['proxy'])} & "
            f"{pct(r['broad'])} & {pct(r['headline'])} & {pct(r['strict'])} \\\\")


def pooled(x):
    return dict(bugs=x.bugs.sum(), kept=x.kept.sum(),
                proxy=(x.proxy_multi_ext * x.bugs).sum() / x.bugs.sum(),
                broad=x.poly_broad.sum() / x.kept.sum(), headline=x.poly_headline.sum() / x.kept.sum(),
                strict=x.poly_strict.sum() / x.kept.sum())


L = [r"\begin{table}[t]",
     r"\caption{Poly-fix prevalence over all 13 Java and Python projects of BeetleBox with at least 100 bug "
     r"reports (ruleset 0.2.0), the six study projects and the seven others.}",
     r"\label{tab:rq1all}", r"\small", r"\setlength{\tabcolsep}{3pt}",
     r"\begin{adjustbox}{max width=\linewidth}\begin{tabular}{lrrrrrr}", r"\toprule",
     r"Project & Bugs & Anch. & Proxy & broad & data & strict \\", r"\midrule"]
for sel, lab in ((True, "Study projects"), (False, "Other eligible projects")):
    L.append(rf"\multicolumn{{7}}{{l}}{{\emph{{{lab}}}}} \\")
    x = s[s.selected == sel]
    for r in x.itertuples():
        L.append(row(r.short, r.language[0].upper(),
                     dict(bugs=r.bugs, kept=r.kept, proxy=r.proxy_multi_ext, broad=r.share_broad,
                          headline=r.share_headline, strict=r.share_strict)))
    L.append(row(r"\quad pooled", "6" if sel else "7", pooled(x)).replace(" (6)", "").replace(" (7)", ""))
    L.append(r"\midrule")
L.append(row("All 13", "", pooled(s)).replace(" ()", ""))
L += [r"\bottomrule", r"\end{tabular}\end{adjustbox}",
      r"\\[2pt]{\footnotesize Anch.: primary-anchored bugs. Proxy: share of fixes whose changed files have more "
      r"than one extension (pooled: weighted by bugs). Prevalence in \% of primary-anchored bugs; ``data'': "
      r"data-format grain. The study projects re-classified by the same script agree with the main "
      r"classification for all 4{,}995 bugs.}",
      r"\end{table}"]
out = os.path.join(ROOT, "paper", "tables", "tab_rq1_all13.tex")
open(out, "w").write("\n".join(L) + "\n")
print(out)
