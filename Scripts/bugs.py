"""
Bug-level data access for the experiments: the kept bugs with their study
class, report text, dates and fix files, and the chronological split.

Every lookup is keyed by (repo_name, bug_id). bug_id alone is NOT unique in
bug_reports_clean.parquet (57 214 rows, 53 604 distinct ids across 98 repos):
the earlier experiment driver built `{bug_id: text}` dicts and silently queried
749 of the 3 594 kept bugs (20.8 %) with another repository's report. Use
`uid(repo, bug_id)` whenever a single string key is needed.
"""

import json
import os
import sys
from functools import lru_cache

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Scripts import paths as P
from Scripts.classification_rules import DEFAULT_TOGGLES, classify_file

# The advisor-locked headline grain (2026-09-06). A bug is Poly-fix for the
# experiments iff grain_broad is True; label-Poly bugs outside the grain
# (tier-3 only: e.g. Java + .properties) are kept in the ranking runs but
# excluded from every Mono-vs-Poly comparison.
STUDY_GRAIN = "grain_broad"
MONO, POLY, POLY_T3 = "Mono-fix", "Poly-fix", "Poly-tier3"
NO_PRIMARY = "No-primary"   # category (c): the fix changes no Java/Python file

TEST_FRAC = 0.20
VAL_FRAC = 0.10          # of the training pool, newest bugs ...
VAL_MIN = 20             # ... but never fewer than this many (before purging)
FOLDS = {
    # fold: (pool_end, test_end) as fractions of the date-sorted project bugs
    1: (0.80, 1.00),     # train/val on oldest 80 %, test on newest 20 %
    2: (0.60, 0.80),     # rolling origin: oldest 60 % -> next 20 %
}


def uid(repo: str, bug_id) -> str:
    return f"{repo}#{bug_id}"


@lru_cache(maxsize=1)
def _reports() -> pd.DataFrame:
    b = pd.read_parquet(P.BUG_REPORTS_PATH)
    b["bug_id"] = b["bug_id"].astype(str)
    for c in ("creation_date", "fix_date"):
        b[c] = pd.to_datetime(b[c], utc=True, errors="coerce")
    assert not b.duplicated(["repo_name", "bug_id"]).any()
    return b


@lru_cache(maxsize=1)
def load_kept() -> pd.DataFrame:
    """Kept bugs (RULESET 0.2.0) with study class, report text and dates."""
    c = pd.read_parquet(P.BUG_CLASSIFICATION_PARQUET)
    c = c[c["keep"]].copy()
    c["bug_id"] = c["bug_id"].astype(str)
    r = _reports()[["repo_name", "bug_id", "bug_report_text", "creation_date",
                    "fix_date", "pre_fix_commit_sha"]]
    df = c.merge(r, on=["repo_name", "bug_id"], how="left", validate="one_to_one")
    assert df["bug_report_text"].notna().all(), "kept bug without own-repo report"
    assert df["creation_date"].notna().all(), "kept bug without creation_date"
    df["study_class"] = np.where(df["class"] == "Mono-fix", MONO,
                                 np.where(df[STUDY_GRAIN], POLY, POLY_T3))
    df["uid"] = [uid(a, b) for a, b in zip(df["repo_name"], df["bug_id"])]
    return df.reset_index(drop=True)


REMOVED_PARQUET = os.path.join(P.OBJ2_DATA_DIR, "removed_bugs.parquet")


@lru_cache(maxsize=1)
def load_removed() -> pd.DataFrame:
    """
    The bugs BeetleBox removed because their report names a fixed file
    (Scripts/removed_bugs.py), restricted to those passing the keep filter.
    Ids are "R<issue>". Never used for training: they are appended to the test
    set of the fold whose test period contains their report date.
    """
    if not os.path.exists(REMOVED_PARQUET):
        return pd.DataFrame()
    df = pd.read_parquet(REMOVED_PARQUET)
    df = df[df["keep"]].copy()
    df["study_class"] = np.where(df["class"] == "Mono-fix", MONO,
                                 np.where(df[STUDY_GRAIN], POLY, POLY_T3))
    df["uid"] = [uid(a, b) for a, b in zip(df["repo_name"], df["bug_id"])]
    df["source"] = "removed"
    return df.reset_index(drop=True)


@lru_cache(maxsize=1)
def load_noprimary() -> pd.DataFrame:
    """
    Category (c), decided 2026-11-01: bugs the keep filter dropped because
    their fix changes no file in the project's primary language, but that do
    have counted fix files (label Mono-fix in another language, Other-fix, or
    Poly-fix without the primary language). 984 bugs; 421 of the 520 Mono-fix
    ones are dolphinscheduler's TypeScript/Vue front-end. Parser-dependent
    techniques can reach none of their fix files by construction. They are
    never used for training; BM25 scores those in the test windows
    (OBJ2_NOPRIMARY_TECHS) and they are analysed as a separate stratum.
    """
    c = pd.read_parquet(P.BUG_CLASSIFICATION_PARQUET)
    c = c[(~c["keep"]) & c["class"].isin(["Mono-fix", "Poly-fix", "Other-fix"])].copy()
    c["bug_id"] = c["bug_id"].astype(str)
    r = _reports()[["repo_name", "bug_id", "bug_report_text", "creation_date",
                    "fix_date", "pre_fix_commit_sha"]]
    df = c.merge(r, on=["repo_name", "bug_id"], how="left", validate="one_to_one")
    df = df[df["bug_report_text"].notna() & df["creation_date"].notna()]
    df["study_class"] = NO_PRIMARY
    df["uid"] = [uid(a, b) for a, b in zip(df["repo_name"], df["bug_id"])]
    df["source"] = "no_primary"
    return df.reset_index(drop=True)


@lru_cache(maxsize=1)
def load_all() -> pd.DataFrame:
    """Kept + removed + no-primary bugs, one row per (repo_name, bug_id); column `source`."""
    k = load_kept().copy()
    k["source"] = "kept"
    parts = [k]
    for extra in (load_removed(), load_noprimary()):
        if not extra.empty:
            parts.append(extra[[c for c in k.columns if c in extra.columns]])
    df = pd.concat(parts, ignore_index=True)
    assert not df.duplicated(["repo_name", "bug_id"]).any()
    return df


@lru_cache(maxsize=1)
def _fix_files_raw() -> pd.DataFrame:
    r = pd.read_parquet(P.FIX_FILES_RAW_PARQUET)
    r["bug_id"] = r["bug_id"].astype(str)
    return r.set_index(["repo_name", "bug_id"])


def fix_files(repo: str, bug_id) -> list:
    """Files changed by the fix commit: [{path, old_path, ext, change_type}]."""
    if str(bug_id).startswith("R"):
        r = load_removed().set_index(["repo_name", "bug_id"])
        return json.loads(r.loc[(repo, str(bug_id)), "files_raw"])
    return json.loads(_fix_files_raw().loc[(repo, str(bug_id)), "files_raw"])


def eval_ground_truth(repo: str, bug_id) -> list:
    """
    Evaluation ground truth = fix-commit files that the frozen ruleset counts
    (DEFAULT_TOGGLES: no docs, changelog fragments, lockfiles, generated,
    vendored, CI, dev-tooling, binaries, deletions). This is the same file set
    that defines Mono/Poly, so the class and the localisation target agree.

    Returns [{path, pre_path, change_type, language, category, is_test}] where pre_path
    is where the file lives in the pre-fix snapshot (old_path for renames,
    None for added files -> unreachable by construction).
    """
    out = []
    for f in fix_files(repo, bug_id):
        v = classify_file(f["path"], f.get("ext", ""), f["change_type"], DEFAULT_TOGGLES)
        if not (v.counts and v.language):
            continue
        ct = f["change_type"]
        pre = None if ct == "A" else (f.get("old_path") or f["path"]) if ct == "R" else f["path"]
        out.append({"path": f["path"], "pre_path": pre, "change_type": ct,
                    "language": v.language, "category": v.category,
                    "is_test": bool({"test", "test_asset"} & set(v.flags))})
    return out


def chrono_split(repo: str, fold: int = 1) -> dict:
    """
    Chronological split of one project's kept bugs by report creation date.

      pool = oldest  FOLDS[fold][0]  of bugs, test = the next slice up to FOLDS[fold][1]
      val  = newest VAL_FRAC of the pool, at least VAL_MIN bugs (model selection
             only), train = the rest

    Purging: a training bug whose fix landed after the validation period
    started (or a validation bug fixed after the test period started) is
    dropped, so no technique learns from a fix that did not yet exist when the
    bugs it is evaluated on were reported.
    """
    k = load_kept()
    g = k[k["repo_name"] == repo].copy()
    g["_num"] = pd.to_numeric(g["bug_id"], errors="coerce")
    g = g.sort_values(["creation_date", "_num", "bug_id"]).reset_index(drop=True)
    n = len(g)
    pool_end, test_end = FOLDS[fold]
    i_pool, i_test = int(round(n * pool_end)), int(round(n * test_end))
    pool, test = g.iloc[:i_pool], g.iloc[i_pool:i_test]
    n_val = max(int(round(len(pool) * VAL_FRAC)), min(VAL_MIN, len(pool) // 4))
    i_val = len(pool) - n_val
    train, val = pool.iloc[:i_val], pool.iloc[i_val:]

    test_start = test["creation_date"].min()
    val_start = val["creation_date"].min()
    train_kept = train[train["fix_date"] < val_start]
    val_kept = val[val["fix_date"] < test_start]
    return {
        "repo": repo, "fold": fold,
        "train": train_kept["bug_id"].tolist(),
        "val": val_kept["bug_id"].tolist(),
        "test": test["bug_id"].tolist(),
        "test_removed": _removed_in_window(repo, test["creation_date"].min(),
                                           test["creation_date"].max()),
        "test_noprimary": _noprimary_in_window(repo, test["creation_date"].min(),
                                               test["creation_date"].max()),
        "purged_train": len(train) - len(train_kept),
        "purged_val": len(val) - len(val_kept),
        "val_start": str(val_start), "test_start": str(test_start),
        "test_end": str(test["creation_date"].max()),
    }


def _noprimary_in_window(repo, lo, hi) -> list:
    r = load_noprimary()
    r = r[(r["repo_name"] == repo) & (r["creation_date"] >= lo) & (r["creation_date"] <= hi)]
    return r.sort_values("creation_date")["bug_id"].tolist()


def _removed_in_window(repo, lo, hi) -> list:
    r = load_removed()
    if r.empty:
        return []
    r = r[(r["repo_name"] == repo) & (r["creation_date"] >= lo) & (r["creation_date"] <= hi)]
    return r.sort_values("creation_date")["bug_id"].tolist()


@lru_cache(maxsize=None)
def project_history(repo: str) -> pd.DataFrame:
    """
    Every bug of the project in the dataset (kept or not) with its fix date and
    fix files -- the version history FLIM's IR features (collaborative
    filtering, bug-fixing recency/frequency) are computed from. Includes the
    BeetleBox-removed bugs (all of them, kept filter or not): they are real
    earlier fixes of the project. Callers must only use rows with
    fix_date < the query bug's creation_date.
    """
    raw = _fix_files_raw().reset_index()
    raw = raw[raw["repo_name"] == repo]
    rep = _reports()
    rep = rep[rep["repo_name"] == repo][["bug_id", "bug_report_text", "creation_date", "fix_date"]]
    h = raw[["bug_id", "files_raw"]].merge(rep, on="bug_id", how="inner")
    if os.path.exists(REMOVED_PARQUET):
        rm = pd.read_parquet(REMOVED_PARQUET)
        rm = rm[rm["repo_name"] == repo][["bug_id", "files_raw", "bug_report_text",
                                          "creation_date", "fix_date"]]
        h = pd.concat([h, rm], ignore_index=True)
    h["files"] = [[f.get("old_path") or f["path"] for f in json.loads(x) if f["change_type"] != "A"]
                  for x in h["files_raw"]]
    h = h.drop(columns=["files_raw"]).dropna(subset=["fix_date"])
    return h.sort_values("fix_date").reset_index(drop=True)


if __name__ == "__main__":
    k = load_kept()
    print(k.groupby(["repo_name", "study_class"]).size().unstack(fill_value=0))
    for fold in (1, 2):
        print(f"\nfold {fold}")
        for repo in P.SELECTED_REPO_NAMES:
            s = chrono_split(repo, fold)
            cls = k[k["repo_name"] == repo].set_index("bug_id")["study_class"]
            te = cls.loc[s["test"]].value_counts()
            print(f"  {repo:26s} train={len(s['train']):4d} (purged {s['purged_train']:3d})  "
                  f"val={len(s['val']):3d} (purged {s['purged_val']:2d})  test={len(s['test']):3d}  "
                  f"Mono={te.get(MONO, 0):3d} Poly={te.get(POLY, 0):3d} T3={te.get(POLY_T3, 0):2d}  "
                  f"test {s['test_start'][:10]}..{s['test_end'][:10]}")
