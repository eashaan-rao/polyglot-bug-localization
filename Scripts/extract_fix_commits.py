"""
Step 0 (part 1) — Extract, for every BeetleBox bug in the six selected projects,
the COMPLETE set of files changed by its fix commit, before any filtering.

For each bug:
  - resolve `fix_commit_sha` in the local clone;
  - diff the commit against its first parent (NULL_TREE for a root commit);
  - record every changed path with its extension and change type;
  - carry the dataset's `ground_truth_files` alongside, for reconciliation.

A bug whose fix commit cannot be resolved is RECORDED (commit_recovered=False),
not dropped.

Outputs (data/obj2/):
  fix_files_raw.parquet   one row per bug: files_raw (list of dicts), counts,
                          commit metadata, ground-truth reconciliation fields
  fix_files_long.csv      one row per (bug, changed file) — for extension enumeration

Run inside the obj1 venv:
    python Scripts/extract_fix_commits.py
"""

import json
import os
import sys
from collections import Counter

import git
import pandas as pd
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Scripts import paths as P

OUT_PARQUET = P.FIX_FILES_RAW_PARQUET
OUT_LONG_CSV = os.path.join(P.OBJ2_DATA_DIR, "fix_files_long.csv")


def repo_dir(repo_name: str, language: str) -> str:
    return os.path.join(P.REPO_BASE_PATH, language, repo_name.replace("/", "_"))


def ext_of(path: str) -> str:
    """Lowercased substring after the final '.' in the basename; '' if none."""
    base = path.rsplit("/", 1)[-1]
    if "." not in base or base.startswith(".") and base.count(".") == 1:
        # dotfiles like .gitignore -> treat the whole name as the "extension"
        return base.lower() if base.startswith(".") else ""
    return base.rsplit(".", 1)[-1].lower()


def changed_files(commit: "git.Commit") -> list:
    """
    List of {path, old_path, ext, change_type} for a commit, diffed against its
    first parent (or the empty tree for a root commit). Renames keep both paths.
    """
    if commit.parents:
        diffs = commit.parents[0].diff(commit)
    else:
        diffs = commit.diff(git.NULL_TREE)
    out = []
    for d in diffs:
        path = d.b_path or d.a_path
        out.append({
            "path": path,
            "old_path": d.a_path if d.renamed_file else None,
            "ext": ext_of(path),
            "change_type": d.change_type,  # A M D R T etc.
        })
    return out


def as_list(x):
    if isinstance(x, (list, tuple)):
        return list(x)
    try:
        import numpy as np
        if isinstance(x, np.ndarray):
            return x.tolist()
    except Exception:
        pass
    return [] if x is None else list(x)


def main():
    df = pd.read_parquet(P.BUG_REPORTS_PATH)
    df = df[(df.source_dataset == "BeetleBox") & (df.repo_name.isin(P.SELECTED_REPO_NAMES))].copy()
    print(f"Bugs to process: {len(df)} across {df.repo_name.nunique()} projects")

    lang_of = dict(P.SELECTED_PROJECTS)
    rows = []
    ext_counter = Counter()
    per_project = Counter()
    per_project_recovered = Counter()

    for repo_name, g in df.groupby("repo_name"):
        language = lang_of[repo_name]
        rd = repo_dir(repo_name, language)
        repo = git.Repo(rd)
        print(f"\n{repo_name}  ({language})  {len(g)} bugs  @ {rd}")
        for _, r in tqdm(g.iterrows(), total=len(g), desc=repo_name):
            per_project[repo_name] += 1
            sha = str(r["fix_commit_sha"]).strip()
            gt = as_list(r["ground_truth_files"])
            rec = {
                "repo_name": repo_name,
                "language": language,
                "bug_id": str(r["bug_id"]),
                "fix_commit_sha": sha,
                "pre_fix_commit_sha": str(r.get("pre_fix_commit_sha", "")),
                "commit_recovered": False,
                "n_parents": None,
                "commit_summary": None,
                "files_raw": None,
                "n_files_raw": 0,
                "gt_files": gt,
                "n_gt_files": len(gt),
                "gt_covered_by_commit": None,   # every gt file path is a suffix of some changed path
                "n_gt_in_commit": 0,
            }
            try:
                c = repo.commit(sha)
                files = changed_files(c)
                rec["commit_recovered"] = True
                rec["n_parents"] = len(c.parents)
                rec["commit_summary"] = c.summary[:200]
                rec["files_raw"] = files
                rec["n_files_raw"] = len(files)
                changed_paths = [f["path"] for f in files]
                n_hit = sum(
                    1 for gtf in gt
                    if any(cp == gtf or cp.endswith("/" + gtf) for cp in changed_paths)
                )
                rec["n_gt_in_commit"] = n_hit
                rec["gt_covered_by_commit"] = (n_hit == len(gt)) if gt else None
                for f in files:
                    ext_counter[f["ext"] or "[noext]"] += 1
                per_project_recovered[repo_name] += 1
            except Exception as e:
                rec["commit_summary"] = f"__ERROR__ {type(e).__name__}: {e}"[:200]
            rows.append(rec)

    out = pd.DataFrame(rows)
    os.makedirs(P.OBJ2_DATA_DIR, exist_ok=True)
    # store files_raw as JSON so parquet is happy
    out_store = out.copy()
    out_store["files_raw"] = out_store["files_raw"].apply(
        lambda v: json.dumps(v) if v is not None else None
    )
    out_store["gt_files"] = out_store["gt_files"].apply(json.dumps)
    out_store.to_parquet(OUT_PARQUET, index=False)

    long_rows = []
    for _, r in out.iterrows():
        for f in (r["files_raw"] or []):
            long_rows.append({
                "repo_name": r["repo_name"], "bug_id": r["bug_id"],
                "fix_commit_sha": r["fix_commit_sha"],
                "path": f["path"], "ext": f["ext"] or "[noext]",
                "change_type": f["change_type"],
            })
    pd.DataFrame(long_rows).to_csv(OUT_LONG_CSV, index=False)

    # ---- report ----------------------------------------------------------
    print("\n" + "=" * 68)
    print("COMMIT RECOVERY")
    for p in P.SELECTED_REPO_NAMES:
        tot, rec = per_project[p], per_project_recovered[p]
        print(f"  {p:28s} {rec:5d}/{tot:<5d}  ({100*rec/tot:.1f}%)" if tot else f"  {p}: 0")
    tot = len(out); rec = int(out.commit_recovered.sum())
    print(f"  {'TOTAL':28s} {rec:5d}/{tot:<5d}  ({100*rec/tot:.1f}%)")

    rok = out[out.commit_recovered]
    print(f"\nMean changed files / fix (recovered): {rok.n_files_raw.mean():.2f}")
    print(f"Merge fix commits (n_parents>1): {(rok.n_parents > 1).sum()} "
          f"({100*(rok.n_parents > 1).mean():.1f}%)")
    gt_nonempty = rok[rok.n_gt_files > 0]
    print(f"Bugs where the fix commit contains ALL ground-truth files: "
          f"{gt_nonempty.gt_covered_by_commit.sum()}/{len(gt_nonempty)} "
          f"({100*gt_nonempty.gt_covered_by_commit.mean():.1f}%)")

    print("\nTop 40 extensions across all changed files (raw, unfiltered):")
    for ext, n in ext_counter.most_common(40):
        print(f"  {ext:16s} {n}")
    print(f"\nDistinct extensions: {len(ext_counter)}")
    print(f"\nWrote {OUT_PARQUET}\n      {OUT_LONG_CSV}")


if __name__ == "__main__":
    main()
