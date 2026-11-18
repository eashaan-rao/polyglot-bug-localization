"""
RQ1 over every eligible BeetleBox project (second internal review, 2.1): the
13 Java and Python projects with at least 100 bug reports, classified with the
frozen ruleset (0.2.0), plus the selection proxy for each.

  * the 7 projects not in the study are cloned without file contents
    (git clone --filter=blob:none) into data/repos_extra/<language>/;
  * a fix's files come from `git diff-tree -r --no-renames` against its first
    parent (a rename counts as an addition at the new path plus a deletion,
    which the rules exclude, so the class is the same as with rename detection);
  * the fallback to the dataset's ground truth and the classifier calls are
    those of Scripts/classify_bugs.py;
  * the 6 study projects are re-classified the same way and compared with
    data/obj2/bug_classification.parquet as a check of the method;
  * proxy = share of fixes whose changed files have more than one extension.

Outputs: results/obj2/rq1_all13_bugs.csv, results/obj2/rq1_all13_summary.csv

    python Scripts/rq1_all_projects.py [--no-clone]
"""

import argparse
import json
import os
import subprocess
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Scripts import paths as P
from Scripts.classification_rules import RULESET_VERSION, classify_fix, keep_bug
from Scripts.extract_fix_commits import as_list, ext_of

EXTRA = os.path.join(P.DATA_DIR, "repos_extra")
OUT_BUGS = os.path.join(P.RESULT_PATH, "rq1_all13_bugs.csv")
OUT_SUM = os.path.join(P.RESULT_PATH, "rq1_all13_summary.csv")


def eligible():
    m = pd.read_parquet(P.PROJECTS_METADATA_PATH)
    m = m[(m.Dataset == "BettleBox") & m.language.isin(["Java", "Python"]) & (m.total_unique_bug_reports >= 100)]
    return {r.repo_name: r.language.lower() for r in m.itertuples()}


def clone_dir(repo, lang):
    if repo in P.SELECTED_REPO_NAMES:
        return os.path.join(P.REPO_BASE_PATH, lang, repo.replace("/", "_"))
    return os.path.join(EXTRA, lang, repo.replace("/", "_"))


def ensure_clone(repo, lang):
    d = clone_dir(repo, lang)
    if not os.path.exists(d):
        os.makedirs(os.path.dirname(d), exist_ok=True)
        print(f"cloning {repo} (no file contents) ...", flush=True)
        subprocess.run(["git", "clone", "--filter=blob:none", "--no-checkout", "--quiet",
                        f"https://github.com/{repo}.git", d], check=True)
    return d


def fix_files(d, sha):
    """Changed files of a commit against its first parent, without rename detection."""
    try:
        parents = subprocess.run(["git", "-C", d, "rev-list", "--parents", "-n", "1", sha],
                                 capture_output=True, text=True, check=True).stdout.split()[1:]
    except subprocess.CalledProcessError:
        return None, None
    args = ["git", "-C", d, "diff-tree", "-r", "--no-renames", "--name-status", "-z"]
    args += [parents[0], sha] if parents else ["--root", sha]
    out = subprocess.run(args, capture_output=True, check=True).stdout.decode("utf-8", "surrogateescape")
    parts = [p for p in out.split("\0") if p]
    if not parents:          # --root prints the commit sha first
        parts = parts[1:]
    files = [{"path": parts[i + 1], "old_path": None, "ext": ext_of(parts[i + 1]), "change_type": parts[i][0]}
             for i in range(0, len(parts) - 1, 2)]
    return files, len(parents)


def classify(files, gt, lang):
    """Same fallback as Scripts/classify_bugs.py."""
    covered = all(any(f["path"] == g or f["path"].endswith("/" + g) for f in files) for g in gt) if (files and gt) else None
    if files is None or not files or (gt and not covered):
        seen = {f["path"] for f in (files or [])}
        files = list(files or []) + [{"path": g, "ext": ext_of(g), "change_type": "M"} for g in gt if g not in seen]
    fc = classify_fix(files, lang)
    return fc, keep_bug(fc, lang), files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-clone", action="store_true")
    a = ap.parse_args()
    projects = eligible()
    reports = pd.read_parquet(P.BUG_REPORTS_PATH)
    reports = reports[(reports.source_dataset == "BeetleBox") & reports.repo_name.isin(projects)]
    rows = []
    for repo, lang in sorted(projects.items()):
        if not a.no_clone:
            ensure_clone(repo, lang)
        d = clone_dir(repo, lang)
        g = reports[reports.repo_name == repo]
        print(f"{repo} ({lang}): {len(g)} bugs", flush=True)
        for r in g.itertuples():
            files, n_par = fix_files(d, str(r.fix_commit_sha).strip()) if os.path.exists(d) else (None, None)
            gt = as_list(r.ground_truth_files)
            fc, keep, used = classify(files, gt, lang)
            exts = {f["ext"] for f in (files or []) if f["ext"]}
            rows.append(dict(repo_name=repo, language=lang, selected=repo in P.SELECTED_REPO_NAMES,
                             bug_id=str(r.bug_id), commit_recovered=files is not None,
                             multi_ext=len(exts) > 1 if files else None, cls=fc.label, keep=keep,
                             broad=bool(fc.grains["broad"]), headline=bool(fc.grains["headline"]),
                             strict=bool(fc.grains["strict"]), ruleset=RULESET_VERSION))
    b = pd.DataFrame(rows)
    b.to_csv(OUT_BUGS, index=False)
    kept = b[b.keep]
    s = b.groupby(["repo_name", "language", "selected"]).agg(
        bugs=("bug_id", "size"), recovered=("commit_recovered", "mean"), proxy_multi_ext=("multi_ext", "mean")).reset_index()
    k = kept.groupby("repo_name").agg(kept=("bug_id", "size"), mono=("cls", lambda x: (x == "Mono-fix").sum()),
                                      poly_broad=("broad", "sum"), poly_headline=("headline", "sum"),
                                      poly_strict=("strict", "sum")).reset_index()
    s = s.merge(k, on="repo_name", how="left")
    for c in ("broad", "headline", "strict"):
        s[f"share_{c}"] = s[f"poly_{c}"] / s["kept"]
    s.to_csv(OUT_SUM, index=False)
    print(s.round(3).to_string(index=False))
    for sel, lab in ((True, "6 selected"), (False, "7 not selected"), (None, "all 13")):
        kk = kept if sel is None else kept[kept.selected == sel]
        print(f"{lab}: kept {len(kk)}, broad {kk.broad.mean():.3f}, headline {kk.headline.mean():.3f}, "
              f"strict {kk.strict.mean():.3f}")
    # method check on the 6 study projects
    ref = pd.read_parquet(P.BUG_CLASSIFICATION_PARQUET)[["repo_name", "bug_id", "class", "keep", "grain_broad"]]
    ref["bug_id"] = ref.bug_id.astype(str)
    chk = b[b.selected].merge(ref, on=["repo_name", "bug_id"], suffixes=("", "_ref"))
    print(f"method check (6 study projects, {len(chk)} bugs): class agrees {(chk.cls == chk['class']).mean():.4f}, "
          f"keep agrees {(chk.keep == chk.keep_ref).mean():.4f}, broad agrees "
          f"{(chk.broad == chk.grain_broad.astype(bool)).mean():.4f}")


if __name__ == "__main__":
    main()
