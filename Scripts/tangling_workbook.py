"""
Manual tangling audit (paper, Threats: "Poly-fix fixes are larger and so more
likely to be tangled; a tangled secondary file would both create the class and
cause the penalty").

  make     draws a stratified sample of evaluated test bugs (5 Poly-fix and 3
           Mono-fix per project, seed 20261122) and writes Excel workbooks to
           results/obj2/annotation/tangling/handout/:
             tangling_A.xlsx  every sampled bug (the main audit, one author)
             tangling_B.xlsx  a 12-bug subset (8 Poly-fix, 4 Mono-fix) for an
                              independent second coder, to report agreement
           One row per counted fix file (the ground truth that defines the
           class), with the bug report, the commit and a direct link to the
           file's diff; the coder marks whether the file's change is part of
           the fix for that bug.
  import   reads results/obj2/annotation/tangling/returned/tangling_{A,B}.xlsx,
           checks completeness, writes CSVs and tangling_report.md: share of
           unrelated files (primary vs secondary, Poly vs Mono), Poly-fix bugs
           whose class would change, Cohen's kappa A vs B on the overlap, and
           the AP of every technique on the audited bugs with the unrelated
           files removed from the ground truth.

    python Scripts/tangling_workbook.py make
    python Scripts/tangling_workbook.py import
"""

import argparse
import hashlib
import os
import re
import subprocess
import sys

import numpy as np
import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Scripts import paths as P
from Scripts.annotation_workbook import BAND, GREY, THIN, YELLOW, add_list, style_header
from Scripts.classification_rules import Toggles, classify_file

OUT = os.path.join(P.RESULT_PATH, "annotation", "tangling")
HANDOUT, RETURNED = os.path.join(OUT, "handout"), os.path.join(OUT, "returned")
SEED, N_POLY, N_MONO, B_POLY, B_MONO = 20261122, 5, 3, 8, 4
PART = ["yes", "no", "unsure"]
KINDS = ["refactoring or cleanup", "other feature", "other bug", "formatting or cosmetic",
         "dependency or version bump", "release or docs housekeeping", "other"]
SUBTYPE = {"poly_test_only": "test-asset-only", "poly_behavioural": "behaviour-bearing", "mono": ""}

INSTRUCTIONS = [
    ("Tangling audit: is each fixed file part of the fix for this bug?", "title"),
    ("A fix commit can contain changes unrelated to the bug (\"tangled\" commits: Herzig and Zeller 2013). In this study every counted file of the fix commit is ground truth and decides the bug's class (Mono-fix / Poly-fix). This audit estimates how often a file is there for another reason.", ""),
    ("", ""),
    ("What to do", "h"),
    ("1. Sheet '1_files': one row per counted fix file, grouped by bug (rows of one bug share a shade). For each bug, first read the report (sheet '2_bugs', or the issue link) and the commit message.", ""),
    ("2. Open the file's diff with the 'diff link' (it jumps to that file in the GitHub commit). Decide part_of_fix:", ""),
    ("   yes: the change fixes the reported problem or directly supports that fix: the code change itself; tests, test data or snapshots for that behaviour; configuration, schema, build or API-specification changes the fix needs.", ""),
    ("   no: the change is unrelated to this bug: refactoring or cleanup elsewhere, another feature, another bug, formatting, a dependency or version bump, release or documentation housekeeping. Then choose unrelated_kind.", ""),
    ("   unsure: you cannot tell from the report, the commit and the diff. Say why in notes.", ""),
    ("3. Judge the file's change, not the file's importance: a small but required config change is yes; a large refactoring in the same commit that the fix does not need is no.", ""),
    ("4. Sheet '2_bugs': after the files of a bug, mark commit_tangled = yes if at least one file is no, and add notes if useful.", ""),
    ("5. Sheet 'log': name, dates, time spent, how you worked. Save the workbook (keep the .xlsx format and the file name) and return it.", ""),
    ("", ""),
    ("Columns given to help: class and sub-type of the bug, role of the file (primary/secondary language, test or not), lines added/removed in the file, the report excerpt, the commit message. Work alone; do not discuss cases with the other coder before both workbooks are returned.", "note"),
]


def gh_diff_link(repo, sha, path):
    return f"https://github.com/{repo}/commit/{sha}#diff-{hashlib.sha256(path.encode()).hexdigest()}"


def numstat(repo, lang, sha):
    d = os.path.join(P.REPO_BASE_PATH, lang, repo.replace("/", "_"))
    try:
        out = subprocess.run(["git", "-C", d, "show", "--numstat", "--no-renames", "--format=", sha],
                             capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        return {}
    res = {}
    for line in out.splitlines():
        p = line.split("\t")
        if len(p) == 3:
            res[p[2]] = (p[0], p[1])
    return res


def sample():
    g = pd.read_parquet(os.path.join(P.RESULT_PATH, "eval", "per_gt.parquet"))
    g = g[(g.tech == "BM25") & (g.view == "all") & (g.universe == "R") & (g.source == "kept")
          & g.study_class.isin(["Mono-fix", "Poly-fix"])]
    bugs = g.groupby(["project", "bug_id"], as_index=False).agg(cls=("study_class", "first"), poly_type=("poly_type", "first"),
                                                                 fold=("fold", "first"))
    rng = np.random.default_rng(SEED)
    pick = []
    for proj, x in bugs.groupby("project"):
        for cls, n in (("Poly-fix", N_POLY), ("Mono-fix", N_MONO)):
            y = x[x.cls == cls].sort_values("bug_id")
            pick.append(y.iloc[rng.choice(len(y), size=min(n, len(y)), replace=False)])
    s = pd.concat(pick).reset_index(drop=True)
    sub = []                                        # B's overlap subset
    for cls, n in (("Poly-fix", B_POLY), ("Mono-fix", B_MONO)):
        y = s[s.cls == cls]
        sub += list(y.index[rng.choice(len(y), size=n, replace=False)])
    s["in_B"] = s.index.isin(sub)
    return s


def build_rows(s):
    cls = pd.read_parquet(P.BUG_CLASSIFICATION_PARQUET)
    cls["bug_id"] = cls.bug_id.astype(str)
    rep = pd.read_parquet(P.BUG_REPORTS_PATH)
    rep["bug_id"] = rep.bug_id.astype(str)
    ff = pd.read_csv(os.path.join(P.OBJ2_DATA_DIR, "fix_files_long.csv"), dtype=str, keep_default_na=False)
    tg = Toggles()
    files, bugs = [], []
    for b in s.itertuples():
        c = cls[(cls.repo_name == b.project) & (cls.bug_id == str(b.bug_id))].iloc[0]
        r = rep[(rep.repo_name == b.project) & (rep.bug_id == str(b.bug_id))].iloc[0]
        lang = c.language.lower()
        prim = {"java": "Java", "python": "Python"}[lang]
        ns = numstat(b.project, lang, c.fix_commit_sha)
        n = 0
        for f in ff[(ff.repo_name == b.project) & (ff.bug_id == str(b.bug_id))].itertuples():
            v = classify_file(f.path, f.ext, f.change_type, tg)
            if not v.counts:
                continue
            is_test = any(fl.startswith("test") for fl in v.flags)
            role = ("primary" if v.language == prim else "secondary") + (", test" if is_test else "")
            add, rem = ns.get(f.path, ("", ""))
            files.append(dict(repo_name=b.project, bug_id=str(b.bug_id), cls=b.cls, subtype=SUBTYPE.get(b.poly_type, ""),
                              path=f.path, change_type=f.change_type, language=v.language, role=role,
                              lines=f"+{add} / -{rem}" if add != "" else "", diff_link=gh_diff_link(b.project, c.fix_commit_sha, f.path),
                              in_B=b.in_B))
            n += 1
        text = (r.bug_report_text or "").replace("\r", "")
        title, _, body = text.partition("\n")
        bugs.append(dict(repo_name=b.project, bug_id=str(b.bug_id), cls=b.cls, subtype=SUBTYPE.get(b.poly_type, ""),
                         title=title.strip(), report_excerpt=re.sub(r"\s+", " ", body)[:700],
                         issue_link=r.bug_report_url, commit_link=f"https://github.com/{b.project}/commit/{c.fix_commit_sha}",
                         commit_message=c.commit_summary, n_files=n, in_B=b.in_B))
    return pd.DataFrame(files), pd.DataFrame(bugs)


FILE_GIVEN = ["repo_name", "bug_id", "cls", "subtype", "path", "change_type", "language", "role", "lines", "diff_link"]
FILE_ANS = ["part_of_fix", "unrelated_kind", "notes"]
BUG_GIVEN = ["repo_name", "bug_id", "cls", "subtype", "title", "report_excerpt", "issue_link", "commit_link", "commit_message", "n_files"]
BUG_ANS = ["commit_tangled", "notes"]


def link(cell, url):
    cell.hyperlink = url
    cell.value = "open"
    cell.font = Font(color="0563C1", underline="single")


def make_workbook(name, files, bugs, out):
    wb = Workbook()
    ws0 = wb.active
    ws0.title = "Start here"
    ws0.column_dimensions["A"].width = 110
    for i, (t, kind) in enumerate(INSTRUCTIONS, 1):
        c = ws0.cell(row=i, column=1, value=t)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        c.font = Font(bold=True, size=14) if kind == "title" else Font(bold=True, size=12, color="1F4E79") if kind == "h" \
            else Font(italic=True) if kind == "note" else Font()
    ws0.cell(row=len(INSTRUCTIONS) + 2, column=1, value=f"Workbook for coder {name}: {bugs.shape[0]} bugs, {files.shape[0]} files").font = Font(bold=True)
    lists = wb.create_sheet("lists")
    r_part, r_kind = add_list(lists, 1, "part_of_fix", PART), add_list(lists, 2, "unrelated_kind", KINDS)
    r_yn = add_list(lists, 3, "yes/no", ["yes", "no", "unsure"])

    wf = wb.create_sheet("1_files")
    cols = FILE_GIVEN + FILE_ANS
    wf.append(cols)
    style_header(wf, 1, len(cols))
    shade, last = False, None
    for r in files.itertuples():
        if (r.repo_name, r.bug_id) != last:
            shade, last = not shade, (r.repo_name, r.bug_id)
        wf.append([getattr(r, c) for c in FILE_GIVEN[:-1]] + [""] + [""] * len(FILE_ANS))
        row = wf.max_row
        link(wf.cell(row=row, column=len(FILE_GIVEN)), r.diff_link)
        for c in range(1, len(cols) + 1):
            cell = wf.cell(row=row, column=c)
            cell.border = Border(bottom=THIN)
            if c != len(FILE_GIVEN):
                cell.fill = (BAND if shade else GREY) if c <= len(FILE_GIVEN) else YELLOW
    n = wf.max_row
    for col, rng, prompt in (("K", r_part, "yes / no / unsure"), ("L", r_kind, "only if part_of_fix = no")):
        dv = DataValidation(type="list", formula1=f"={rng}", allow_blank=True, showErrorMessage=True,
                            error="Choose a value from the list.", prompt=prompt, showInputMessage=True)
        wf.add_data_validation(dv)
        dv.add(f"{col}2:{col}{n}")
    for col, w in zip("ABCDEFGHIJKLM", (20, 8, 9, 16, 70, 6, 11, 16, 11, 7, 11, 24, 50)):
        wf.column_dimensions[col].width = w
    wf.freeze_panes = "K2"
    wf.auto_filter.ref = f"A1:M{n}"

    wbs = wb.create_sheet("2_bugs")
    cols = BUG_GIVEN + BUG_ANS
    wbs.append(cols)
    style_header(wbs, 1, len(cols))
    for r in bugs.itertuples():
        wbs.append([getattr(r, c) for c in BUG_GIVEN])
        row = wbs.max_row
        link(wbs.cell(row=row, column=7), r.issue_link)
        link(wbs.cell(row=row, column=8), r.commit_link)
        for c in range(1, len(cols) + 1):
            cell = wbs.cell(row=row, column=c)
            cell.border = Border(bottom=THIN)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            if c not in (7, 8):
                cell.fill = GREY if c <= len(BUG_GIVEN) else YELLOW
    n = wbs.max_row
    dv = DataValidation(type="list", formula1=f"={r_yn}", allow_blank=True, showErrorMessage=True,
                        error="Choose a value from the list.", prompt="yes if at least one file is not part of the fix",
                        showInputMessage=True)
    wbs.add_data_validation(dv)
    dv.add(f"K2:K{n}")
    for col, w in zip("ABCDEFGHIJKL", (20, 8, 9, 16, 40, 70, 7, 8, 40, 7, 10, 40)):
        wbs.column_dimensions[col].width = w
    wbs.freeze_panes = "E2"

    wl = wb.create_sheet("log")
    for i, (k, v) in enumerate((("coder", name), ("started (date)", ""), ("finished (date)", ""),
                                ("time spent (min)", ""), ("how you worked (free text)", "")), 1):
        wl.cell(row=i, column=1, value=k).font = Font(bold=True)
        wl.cell(row=i, column=2, value=v).fill = YELLOW
    wl.column_dimensions["A"].width, wl.column_dimensions["B"].width = 30, 90
    lists.sheet_state = "hidden"
    wb.active = 0
    wb.save(out)


def cmd_make(a):
    os.makedirs(HANDOUT, exist_ok=True)
    os.makedirs(RETURNED, exist_ok=True)
    s = sample()
    files, bugs = build_rows(s)
    s.to_csv(os.path.join(OUT, "sample.csv"), index=False)
    make_workbook("A", files, bugs, os.path.join(HANDOUT, "tangling_A.xlsx"))
    make_workbook("B", files[files.in_B], bugs[bugs.in_B], os.path.join(HANDOUT, "tangling_B.xlsx"))
    print(f"sample: {len(bugs)} bugs ({(bugs.cls == 'Poly-fix').sum()} Poly-fix), {len(files)} files "
          f"(secondary {files.role.str.startswith('secondary').sum()}); subset for B: {bugs.in_B.sum()} bugs, "
          f"{files.in_B.sum()} files")
    print(files.groupby("bug_id").size().describe().round(1).to_string())


# ------------------------------------------------------------------ import
def read(path):
    wb = load_workbook(path, data_only=True)
    f = pd.DataFrame(list(wb["1_files"].iter_rows(values_only=True))[1:], columns=FILE_GIVEN + FILE_ANS)
    b = pd.DataFrame(list(wb["2_bugs"].iter_rows(values_only=True))[1:], columns=BUG_GIVEN + BUG_ANS)
    f = f[f.repo_name.notna()].fillna("")
    b = b[b.repo_name.notna()].fillna("")
    for d in (f, b):
        d["bug_id"] = d.bug_id.astype(str)
    return f, b


def ap_without(ranks, keep):
    """AP over the kept ground-truth files; a file the technique does not rank
    (rank NaN/inf) is a miss and stays in the denominator. Ranks are those of the
    full candidate list: removing a file from the ground truth does not move others."""
    r = np.asarray([x for x, k in zip(ranks, keep) if k], float)
    if len(r) == 0:
        return np.nan
    hit = np.sort(r[np.isfinite(r)])
    return float(np.sum(np.arange(1, len(hit) + 1) / hit) / len(r))


def cmd_import(a):
    from sklearn.metrics import cohen_kappa_score
    res, L = {}, ["# Tangling audit: results", ""]
    for who in ("A", "B"):
        p = os.path.join(RETURNED, f"tangling_{who}.xlsx")
        if os.path.exists(p):
            f, b = read(p)
            miss = f[~f.part_of_fix.isin(PART)]
            if len(miss):
                print(f"{who}: {len(miss)} files without part_of_fix, e.g. rows {list(miss.index[:10] + 2)}")
            f.to_csv(os.path.join(OUT, f"files_{who}.csv"), index=False)
            b.to_csv(os.path.join(OUT, f"bugs_{who}.csv"), index=False)
            res[who] = f
    if "A" not in res:
        sys.exit("tangling_A.xlsx not found in returned/")
    f = res["A"]
    f["unrelated"] = f.part_of_fix == "no"
    f["secondary"] = f.role.str.startswith("secondary")
    L += [f"Coder A: {f.bug_id.nunique()} bugs, {len(f)} counted fix files; part_of_fix = "
          + ", ".join(f"{k}: {v}" for k, v in f.part_of_fix.value_counts().items()), ""]
    t = f.groupby(["cls", "secondary"]).agg(files=("path", "size"), unrelated=("unrelated", "sum"))
    t["share"] = (t.unrelated / t.files).round(3)
    L += ["## Unrelated (tangled) files by class and role", "", t.reset_index().to_markdown(index=False), ""]
    bug = f.groupby(["repo_name", "bug_id", "cls"]).agg(n=("path", "size"), unrel=("unrelated", "sum"),
                                                         sec=("secondary", "sum"),
                                                         sec_unrel=("unrelated", lambda x: (x & f.loc[x.index, "secondary"]).sum()))
    bug = bug.reset_index()
    poly = bug[bug.cls == "Poly-fix"]
    L += [f"Bugs with at least one unrelated file: Poly-fix {int((poly.unrel > 0).sum())} of {len(poly)}, "
          f"Mono-fix {int((bug[bug.cls == 'Mono-fix'].unrel > 0).sum())} of {(bug.cls == 'Mono-fix').sum()}.",
          f"Poly-fix bugs whose secondary files are all unrelated (class would become Mono-fix): "
          f"{int(((poly.sec > 0) & (poly.sec_unrel == poly.sec)).sum())} of {len(poly)}.", ""]
    if "B" in res:
        j = f.merge(res["B"], on=["repo_name", "bug_id", "path"], suffixes=("_A", "_B"))
        j = j[j.part_of_fix_A.isin(PART) & j.part_of_fix_B.isin(PART)]
        k = cohen_kappa_score(j.part_of_fix_A, j.part_of_fix_B) if j.part_of_fix_A.nunique() + j.part_of_fix_B.nunique() > 2 else 1.0
        L += ["## Agreement A vs B (overlap)", "",
              f"{len(j)} files of {j.bug_id.nunique()} bugs: agreement {100 * (j.part_of_fix_A == j.part_of_fix_B).mean():.1f}%, "
              f"Cohen's kappa {k:.2f}.", ""]
        dis = j[j.part_of_fix_A != j.part_of_fix_B][["repo_name", "bug_id", "path", "part_of_fix_A", "part_of_fix_B", "notes_A", "notes_B"]]
        if len(dis):
            L += [dis.to_markdown(index=False), ""]
    # AP on the audited bugs with unrelated files removed from the ground truth
    g = pd.read_parquet(os.path.join(P.RESULT_PATH, "eval", "per_gt.parquet"))
    g = g[(g.universe == "R") & (g.source == "kept")]
    g["bug_id"] = g.bug_id.astype(str)
    unrel = set(zip(f.repo_name, f.bug_id, f.path)) & set(zip(f[f.unrelated].repo_name, f[f.unrelated].bug_id, f[f.unrelated].path))
    aud = set(zip(f.repo_name, f.bug_id))
    g = g[[(p, b) in aud for p, b in zip(g.project, g.bug_id)]]
    rows = []
    for (tech, view), x in g.groupby(["tech", "view"]):
        if (tech, view) not in {("BM25", "all"), ("FLIM", "parse"), ("BLAZE", "all"), ("LocAgent", "all"), ("SweRank", "all")}:
            continue
        per = []
        for (fold, seed, proj, b, cls), h in x.groupby(["fold", "seed", "project", "bug_id", "study_class"]):
            keep = [(proj, b, p) not in unrel for p in h.path]
            per.append(dict(fold=fold, project=proj, bug_id=b, cls=cls, ap=ap_without(h["rank"], [True] * len(h)),
                            ap_clean=ap_without(h["rank"], keep)))
        d = pd.DataFrame(per).groupby(["fold", "project", "bug_id", "cls"], as_index=False)[["ap", "ap_clean"]].mean()  # seed average
        m = d.groupby("cls")[["ap", "ap_clean"]].mean()
        if {"Mono-fix", "Poly-fix"} <= set(m.index):
            rows.append(dict(technique=f"{tech} ({view})", map_mono=m.at["Mono-fix", "ap"], map_poly=m.at["Poly-fix", "ap"],
                             gap=m.at["Poly-fix", "ap"] - m.at["Mono-fix", "ap"],
                             map_poly_clean=m.at["Poly-fix", "ap_clean"],
                             gap_clean=m.at["Poly-fix", "ap_clean"] - m.at["Mono-fix", "ap_clean"]))
    if rows:
        L += ["## Poly-fix minus Mono-fix MAP on the audited bugs, before and after removing unrelated files", "",
              "(LocAgent uses full AP here, ranks beyond its ten files count as misses.)", "",
              pd.DataFrame(rows).round(3).to_markdown(index=False), ""]
    open(os.path.join(OUT, "tangling_report.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("make")
    sub.add_parser("import")
    a = ap.parse_args()
    cmd_make(a) if a.cmd == "make" else cmd_import(a)
