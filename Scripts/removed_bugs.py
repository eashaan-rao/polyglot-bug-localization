"""
The bugs BeetleBox removed because their report names a fixed file.

BLAZE's authors removed from BeetleBox every bug whose issue title or body
mentions a file changed by the fix, and released those bugs separately
(Zenodo 15122980, BeetleBoxRemoved.zip). Naming the file is where lexical
retrieval is strongest, so the kept dataset is a population in which BM25's
main advantage was filtered out. This script builds that stratum for our six
projects with exactly the kept bugs' procedure, so it can be analysed
separately ("the dataset's own filter undone"):

  1. fix files = the fix commit diffed against its first parent
     (extract_fix_commits.changed_files); before_fix_sha is that parent for
     all 1 226 bugs
  2. Mono/Poly with the frozen ruleset 0.2.0 (classify_fix, keep_bug, grains)
  3. named files: which counted fix files the report names (path or basename,
     case-insensitive), and whether they are primary- or secondary-language
  4. test-window assignment: a removed bug belongs to fold F's test window if
     its report date lies inside that fold's test period of the kept bugs.
     Removed bugs are never used for training, so every technique scores them
     with the model trained on the kept bugs (no retraining)
  5. R1: prevalence among removed vs kept bugs

Bug ids are "R<issue>" so they can never collide with a kept bug id.

Outputs
  data/obj2/removed_bugs.parquet
  results/obj2/removed/prevalence_removed.csv, prevalence_removed.md

    python Scripts/removed_bugs.py
"""

import json
import os
import re
import sys

import git
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Scripts import paths as P
from Scripts.classification_rules import RULESET_VERSION, classify_fix, keep_bug
from Scripts.extract_fix_commits import changed_files

SRC = os.path.join(P.OBJ2_DATA_DIR, "beetlebox_removed", "BeetleBoxRemoved")
OUT = os.path.join(P.OBJ2_DATA_DIR, "removed_bugs.parquet")
RES = os.path.join(P.RESULT_PATH, "removed")
LANG = dict(P.SELECTED_PROJECTS)
PRIMARY = {"java": "Java", "python": "Python"}


def _named(text: str, path: str) -> bool:
    t = text.lower()
    base = path.rsplit("/", 1)[-1].lower()
    return path.lower() in t or (len(base) > 3 and re.search(r"(?<![\w.-])" + re.escape(base) + r"(?![\w-])", t) is not None)


def build() -> pd.DataFrame:
    from datasets import load_from_disk
    d = load_from_disk(SRC)
    raw = pd.concat([d[s].to_pandas().assign(bb_split=s) for s in d], ignore_index=True)
    raw = raw[raw["repo_name"].isin(LANG)].reset_index(drop=True)
    rows = []
    for repo, g in raw.groupby("repo_name"):
        lang = LANG[repo]
        R = git.Repo(os.path.join(P.REPO_BASE_PATH, lang, repo.replace("/", "_")))
        for _, r in g.iterrows():
            c = R.commit(r["after_fix_sha"])
            files = changed_files(c)
            fc = classify_fix(files, lang)
            text = f"{(r['title'] or '').strip()}\n{r['body'] or ''}"
            counted = [v for v in fc.per_file if v.counts and v.language]
            named = [v for v in counted if _named(text, v.path)]
            rows.append({
                "repo_name": repo, "language": lang, "bug_id": f"R{int(r['issue_id'])}",
                "issue_id": int(r["issue_id"]), "bb_split": r["bb_split"],
                "fix_commit_sha": r["after_fix_sha"], "pre_fix_commit_sha": r["before_fix_sha"],
                "n_parents": len(c.parents), "ruleset_version": RULESET_VERSION,
                "class": fc.label, "keep": keep_bug(fc, lang),
                "primary_language": fc.primary_language,
                "languages": json.dumps(fc.languages),
                "secondary_languages": json.dumps(fc.secondary_languages),
                "grain_headline": fc.grains["headline"], "grain_broad": fc.grains["broad"],
                "grain_strict": fc.grains["strict"], "grain_tier3_only": fc.grains["tier3_only"],
                "n_files_raw": fc.n_files_raw, "n_files_counted": fc.n_files_counted,
                "tangled_flag": len(c.parents) > 1,
                "files_raw": json.dumps(files),
                "bug_report_text": text,
                "creation_date": pd.Timestamp(r["report_datetime"]).tz_convert("UTC"),
                "fix_date": pd.Timestamp(r["commit_datetime"]).tz_convert("UTC"),
                "n_named": len(named),
                "named_primary": any(v.language == PRIMARY[lang] for v in named),
                "named_secondary": any(v.language != PRIMARY[lang] for v in named),
                "named_files": json.dumps([v.path for v in named]),
            })
    return pd.DataFrame(rows)


def assign_windows(df: pd.DataFrame) -> pd.DataFrame:
    from Scripts.bugs import chrono_split
    df = df.copy()
    for fold in (1, 2):
        col = f"test_fold{fold}"
        df[col] = False
        for repo in LANG:
            s = chrono_split(repo, fold)
            lo, hi = pd.Timestamp(s["test_start"]), pd.Timestamp(s["test_end"])
            m = (df["repo_name"] == repo) & (df["creation_date"] >= lo) & (df["creation_date"] <= hi)
            df.loc[m, col] = True
    return df


def report(df: pd.DataFrame):
    from Scripts.bugs import load_kept
    os.makedirs(RES, exist_ok=True)
    kept = load_kept()
    rows = []
    for name, d in (("kept", kept), ("removed", df[df["keep"]])):
        for repo, g in list(d.groupby("repo_name")) + [("POOLED", d)]:
            n = len(g)
            rows.append({"set": name, "project": repo, "n": n,
                         "poly_broad_pct": round(100 * g["grain_broad"].mean(), 1) if n else None,
                         "poly_headline_pct": round(100 * g["grain_headline"].mean(), 1) if n else None,
                         "poly_strict_pct": round(100 * g["grain_strict"].mean(), 1) if n else None})
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(RES, "prevalence_removed.csv"), index=False)
    k = df[df["keep"]]
    poly = k[k["grain_broad"]]
    lines = [
        f"# Removed bugs (BeetleBoxRemoved) — RULESET {RULESET_VERSION}", "",
        f"{len(df)} removed bugs in the six projects; {int(df['keep'].sum())} pass the keep filter "
        f"({100 * df['keep'].mean():.1f} %; kept set: 72.0 %).", "",
        "## Poly-fix prevalence, removed vs kept", "",
        t.pivot(index="project", columns="set", values="poly_broad_pct").to_markdown(), "",
        "## Which file does the report name? (kept-filter removed bugs)", "",
        f"- reports naming at least one counted fix file: {100 * (k['n_named'] > 0).mean():.1f} %",
        f"- Poly-fix: naming a secondary-language file: {100 * poly['named_secondary'].mean():.1f} %; "
        f"naming a primary-language file: {100 * poly['named_primary'].mean():.1f} %", "",
        "## In the test windows", "",
        f"- fold 1: {int((k['test_fold1']).sum())} bugs "
        f"(Poly-fix {int((k['test_fold1'] & k['grain_broad']).sum())})",
        f"- fold 2: {int((k['test_fold2']).sum())} bugs "
        f"(Poly-fix {int((k['test_fold2'] & k['grain_broad']).sum())})",
    ]
    with open(os.path.join(RES, "prevalence_removed.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    df = assign_windows(build())
    df.to_parquet(OUT, index=False)
    report(df)
    print(f"-> {OUT}")
