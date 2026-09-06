"""
Step 3 prerequisite — retrieval recall by class, reported as a PROPERTY OF THE
SETUP (not a research question).

For each of the six projects, for every KEPT bug, walk the pre-fix snapshot,
build a per-bug FAISS index over the cached BGE blob embeddings, retrieve the
Top-K, and record where each ground-truth file lands. Aggregate Recall@K:

  * bug-level  — fraction of bugs with >=1 ground-truth file in the Top-K
  * file-level — fraction of ground-truth FILES in the Top-K
  split by Mono-fix / Poly-fix, and (file-level) by ground-truth file extension.

Uses only cached embeddings — no model load, CPU, ~minutes/project.

Outputs (results/obj2/):
  retrieval_recall_by_class.csv
  retrieval_recall_by_extension.csv
  retrieval_recall.md         (with the chosen operating K)

Run:  python Scripts/retrieval_recall_by_class.py
"""

import json
import os
import pickle
import sys
from collections import defaultdict

import faiss
import git
import numpy as np
import pandas as pd
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Scripts import paths as P
from Scripts.classification_rules import EXT_LANG, GRAMMAR_LANGUAGES

K_VALUES = [10, 30, 50, 75, 100, 150, 200, 300, 500]
MAXK = max(K_VALUES)
LANG = dict(P.SELECTED_PROJECTS)


def ext_of(path):
    base = path.rsplit("/", 1)[-1]
    if base.startswith(".") and base.count(".") == 1:
        return base.lower()
    return base.rsplit(".", 1)[-1].lower() if "." in base else "[noext]"


def repo_path(repo, lang):
    return os.path.join(P.REPO_BASE_PATH, lang, repo.replace("/", "_"))


def build_index(embs):
    x = np.asarray(embs, dtype="float32").copy()
    faiss.normalize_L2(x)
    idx = faiss.IndexFlatIP(x.shape[1])
    idx.add(x)
    return idx


def main():
    cls = pd.read_parquet(P.BUG_CLASSIFICATION_PARQUET)
    cls = cls[cls["keep"]].set_index(["repo_name", "bug_id"])

    file_rows = []          # one row per (bug, ground-truth file)
    endswith_collisions = 0
    endswith_total = 0

    for repo, lang in P.SELECTED_PROJECTS:
        stub = repo.replace("/", "_")
        blob_db = pickle.load(open(os.path.join(P.EMBEDDING_DB_DIR, f"{stub}_blob_embeddings32.pkl"), "rb"))
        bug_db = pickle.load(open(os.path.join(P.EMBEDDING_DB_DIR, f"{stub}_bug_metadata32.pkl"), "rb"))
        r = git.Repo(repo_path(repo, lang))
        tree_cache = {}

        kept_ids = [b for (rp, b) in cls.index if rp == repo]
        for bug_id in tqdm(kept_ids, desc=repo, leave=False):
            meta = bug_db.get(str(bug_id))
            if not meta:
                continue
            sha = meta.get("commit_sha")
            gts = list(meta.get("ground_truth_files", []))
            if not sha or not gts:
                continue
            if sha not in tree_cache:
                try:
                    commit = r.commit(sha)
                    tree_cache[sha] = {bl.path: bl.hexsha for bl in commit.tree.traverse()
                                       if bl.type == "blob" and bl.hexsha in blob_db}
                except Exception:
                    tree_cache[sha] = {}
            path2sha = tree_cache[sha]
            if not path2sha:
                continue

            paths = list(path2sha)
            embs = [blob_db[path2sha[p]] for p in paths]
            idx = build_index(embs)
            q = np.asarray(meta["embedding"], dtype="float32").reshape(1, -1).copy()
            faiss.normalize_L2(q)
            k = min(MAXK, len(paths))
            _, I = idx.search(q, k)
            ranked = [paths[i] for i in I[0]]
            rank_of = {p: n + 1 for n, p in enumerate(ranked)}

            row_cls = cls.loc[(repo, bug_id)]
            bclass = row_cls["class"]
            for gt in gts:
                # exact match: full path or a path ending in "/<gt>"
                exact = [p for p in paths if p == gt or p.endswith("/" + gt)]
                ends = [p for p in paths if p.endswith(gt)]
                endswith_total += 1
                if len(ends) > len(exact):
                    endswith_collisions += 1
                match_paths = exact or ends           # fall back to endswith if exact finds nothing
                best = min((rank_of.get(p, np.inf) for p in match_paths), default=np.inf)
                e = ext_of(gt)
                lang_cat = EXT_LANG.get(e, (None, None))
                is_secondary = (lang_cat[0] in GRAMMAR_LANGUAGES
                                and lang_cat[1] != "source"
                                and lang_cat[0] != row_cls["primary_language"])
                file_rows.append({
                    "repo_name": repo, "bug_id": bug_id, "bug_class": bclass,
                    "grain_headline": bool(row_cls["grain_headline"]),
                    "gt_path": gt, "ext": e,
                    "kind": "secondary" if is_secondary else "primary_or_other",
                    "rank": best, "n_candidates": len(paths),
                })

    fr = pd.DataFrame(file_rows)
    fr.to_parquet(os.path.join(P.OBJ2_DATA_DIR, "retrieval_ranks.parquet"), index=False)

    # ---- bug-level & file-level recall@K by class -------------------
    def recall_table(df, group_cols):
        out = []
        for keys, g in df.groupby(group_cols):
            keys = keys if isinstance(keys, tuple) else (keys,)
            rec = dict(zip(group_cols, keys))
            rec["n_bugs"] = g[["repo_name", "bug_id"]].drop_duplicates().shape[0]
            rec["n_gt_files"] = len(g)
            for K in K_VALUES:
                # file-level
                rec[f"file_recall@{K}"] = round((g["rank"] <= K).mean(), 4)
                # bug-level: >=1 gt file within K
                bl = g.groupby(["repo_name", "bug_id"])["rank"].min() <= K
                rec[f"bug_recall@{K}"] = round(bl.mean(), 4)
            out.append(rec)
        return pd.DataFrame(out)

    by_class = pd.concat([
        recall_table(fr.assign(scope="per_project"), ["repo_name", "bug_class"]),
        recall_table(fr.assign(repo_name="POOLED"), ["repo_name", "bug_class"]),
    ], ignore_index=True)
    by_class.to_csv(os.path.join(P.RESULT_PATH, "retrieval_recall_by_class.csv"), index=False)

    # secondary-file recall by extension (Poly-fix only)
    sec = fr[(fr.kind == "secondary")]
    by_ext = recall_table(sec.assign(repo_name="POOLED"), ["repo_name", "ext"])
    by_ext.to_csv(os.path.join(P.RESULT_PATH, "retrieval_recall_by_extension.csv"), index=False)

    # ---- choose operating K --------------------------------------
    pooled = by_class[(by_class.repo_name == "POOLED")]
    mono = pooled[pooled.bug_class == "Mono-fix"].iloc[0]
    poly = pooled[pooled.bug_class == "Poly-fix"].iloc[0]
    chosen = None
    for K in K_VALUES:
        if mono[f"bug_recall@{K}"] >= 0.95 and poly[f"bug_recall@{K}"] >= 0.85:
            chosen = K
            break
    chosen = chosen or MAXK

    md = ["# Retrieval recall by class (property of the setup)", ""]
    md.append("Bug-level Recall@K — fraction of bugs with ≥1 ground-truth file in the Top-K:\n")
    md.append("| K | Mono-fix | Poly-fix |")
    md.append("|---|---|---|")
    for K in K_VALUES:
        md.append(f"| {K} | {mono[f'bug_recall@{K}']:.3f} | {poly[f'bug_recall@{K}']:.3f} |")
    md.append(f"\n**Operating K = {chosen}** (smallest K with Mono bug-recall ≥ 0.95 and "
              f"Poly bug-recall ≥ 0.85; falls back to {MAXK} if none).\n")
    md.append("File-level Recall@{} for secondary-language ground-truth files, by extension:\n".format(chosen))
    md.append("| ext | n files | file-recall@{} |".format(chosen))
    md.append("|---|---|---|")
    for _, r in by_ext.sort_values("n_gt_files", ascending=False).head(15).iterrows():
        md.append(f"| {r['ext']} | {r['n_gt_files']} | {r[f'file_recall@{chosen}']:.3f} |")
    md.append(f"\nendswith-vs-exact ground-truth match collisions: "
              f"{endswith_collisions}/{endswith_total} "
              f"({100*endswith_collisions/max(endswith_total,1):.2f}%)")
    with open(os.path.join(P.RESULT_PATH, "retrieval_recall.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    print("\n".join(md))
    print(f"\nWrote retrieval_recall_by_class.csv, retrieval_recall_by_extension.csv, retrieval_recall.md")


if __name__ == "__main__":
    main()
