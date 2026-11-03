"""
Single evaluator for every technique. No technique computes its own metrics.

Input  results/obj2/scores/<TECH>/fold<F>/seed<S>/<project_stub>.parquet
       columns: bug_id (str), path (pre-fix snapshot path), score (float)
       -- one row per scored file (universe T) per test bug.

For every test bug, ranks are computed under 2 universes x 2 views:
  universe  R  is_text & in_ruleset (primary)     T  is_text (sensitivity)
  view      all    every file in the universe is a candidate
            parse  only files the project-language parser accepts are
                   candidates; ground-truth files it cannot parse count as
                   misses. For FLIM, "all" = FLIM-fallback (unparseable files
                   encoded whole) and "parse" = FLIM-strict (paper-faithful).
Ground truth = the fix-commit files the frozen ruleset counts
(Scripts.bugs.eval_ground_truth), located in the pre-fix snapshot. GT files
the fix adds, or that are not in the universe, are unreachable: recorded, but
excluded from rank metrics. A bug with no reachable GT file in a universe is
not rank-evaluated in that universe.

Primary outcome: AP per bug (mean = MAP); AP@10 when LocAgent is compared.
Secondary: complete-fix recall@10, RR (MRR), Top-k.

Ties: expected rank under random tie-breaking, n_greater + (n_equal + 1) / 2,
so a technique gains nothing from giving many files the same score.

Outputs (results/obj2/eval/):
  per_bug.parquet   one row per (tech, view, universe, gt_filter, fold, seed, bug);
                    gt_filter "no_tests" (sensitivity S1, universe R only) drops test
                    files from the ground truth; `source` = kept | removed
  per_gt.parquet    one row per (tech, view, universe, fold, seed, bug, GT file)
  summary.csv       per (tech, view, universe, fold, seed, project, class)
plus legacy diagnostics/WP_<TECH>-<view>_<project>.csv (fold 1, first seed,
universe R) so the existing analysis scripts keep working.

    python Scripts/evaluate.py            # evaluate every score file present
"""

import glob
import os
import re
import sys

import numpy as np
import pandas as pd
from scipy.special import gammaln

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Scripts import paths as P
from Scripts.bugs import MONO, NO_PRIMARY, POLY, eval_ground_truth, load_all
from Scripts.universe import snapshot

_SFX = "_smoke" if os.environ.get("OBJ2_SMOKE") == "1" else ""
SCORES_DIR = os.path.join(P.RESULT_PATH, "scores" + _SFX)
EVAL_DIR = os.path.join(P.RESULT_PATH, "eval" + _SFX)
DIAG_DIR = os.path.join(P.RESULT_PATH, "diagnostics" + _SFX)
PRIMARY_LANG = {"java": "Java", "python": "Python"}
LANG = dict(P.SELECTED_PROJECTS)
KS = (1, 5, 10)


def score_path(tech: str, fold: int, seed: int, repo: str) -> str:
    return os.path.join(SCORES_DIR, tech, f"fold{fold}", f"seed{seed}",
                        repo.replace("/", "_") + ".parquet")


def expected_ranks(cand_scores: np.ndarray, query_scores: np.ndarray) -> np.ndarray:
    """Expected rank of each query score among the candidates (ties broken at random)."""
    s = np.sort(cand_scores)
    n = len(s)
    lo = np.searchsorted(s, query_scores, side="left")
    hi = np.searchsorted(s, query_scores, side="right")
    n_greater = n - hi
    n_equal = hi - lo                      # includes the query itself if it is a candidate
    return n_greater + (n_equal + 1) / 2.0


def poly_type(study_class: str, gts: list, primary_language: str) -> str:
    """Poly-fix split (decided 2026-10-31):
      poly_behavioural  >= 1 secondary-language fix file outside test paths
                        (configuration, schema, build, other source the software reads)
      poly_test_only    every secondary-language fix file is a test asset
                        (snapshots, expected outputs, test YAML, REST test specs)
    Test paths are the ruleset's test tag (classification_rules._RE_TEST_PATH).
    Computed from all counted fix files, reachable or not: it describes the fix."""
    if study_class == MONO:
        return "mono"
    if study_class == NO_PRIMARY:
        return "no_primary"
    if study_class != POLY:
        return "poly_t3"
    sec = [g for g in gts if g["language"] != primary_language]
    return "poly_behavioural" if any(not g["is_test"] for g in sec) else "poly_test_only"


def random_baseline(n: int, m: int):
    """E[RR] and P(top-10 hit) when m relevant files are placed uniformly among n."""
    if m <= 0 or n <= 0:
        return 0.0, 0.0
    r = np.arange(1, n - m + 2)
    # P(first relevant at rank r) = C(n-r, m-1) / C(n, m)
    logp = (gammaln(n - r + 1) - gammaln(m) - gammaln(n - r - m + 2)) \
        - (gammaln(n + 1) - gammaln(m + 1) - gammaln(n - m + 1))
    p = np.exp(logp)
    top10 = float(p[:10].sum())
    return float((p / r).sum()), top10


def _ap(ranks: np.ndarray) -> float:
    """AP over all reachable GT; misses (inf) contribute 0 precision."""
    if len(ranks) == 0:
        return 0.0
    hit = np.sort(ranks[np.isfinite(ranks)])
    return float(np.sum(np.arange(1, len(hit) + 1) / hit) / len(ranks)) if len(hit) else 0.0


def evaluate_scores(tech: str, fold: int, seed: int, repo: str):
    fp = score_path(tech, fold, seed, repo)
    sc = pd.read_parquet(fp)
    sc["bug_id"] = sc["bug_id"].astype(str)
    k = load_all()
    kk = k[k["repo_name"] == repo].set_index("bug_id")
    prim = PRIMARY_LANG[LANG[repo]]
    bug_rows, gt_rows = [], []

    for bug_id, g in sc.groupby("bug_id", sort=False):
        meta = kk.loc[bug_id]
        snap = snapshot(repo, meta["pre_fix_commit_sha"])
        snapT = snap[snap["is_text"]].set_index("path")
        score = pd.Series(g["score"].values, index=g["path"].values)
        score = score[~score.index.duplicated()]
        missing_scores = int((~snapT.index.isin(score.index)).sum())
        all_scores = score.reindex(snapT.index).fillna(-np.inf).values.astype(float)

        gts = eval_ground_truth(repo, bug_id)
        n_gt, n_added = len(gts), sum(g_["pre_path"] is None for g_ in gts)
        bug_info = {
            "project": repo, "bug_id": bug_id, "study_class": meta["study_class"],
            "poly_type": poly_type(meta["study_class"], gts, prim),
            "source": meta.get("source", "kept"),
            "grain_headline": bool(meta["grain_headline"]), "grain_strict": bool(meta["grain_strict"]),
            "tangled": bool(meta.get("tangled_flag", False)),
            "report_len": len(str(meta["bug_report_text"]).split()),
        }

        for universe in ("R", "T"):
            in_u = snapT["in_ruleset"].values if universe == "R" else np.ones(len(snapT), bool)
            reach = [g_ for g_ in gts if g_["pre_path"] is not None and g_["pre_path"] in snapT.index
                     and (universe == "T" or bool(snapT.at[g_["pre_path"], "in_ruleset"]))]
            for view in ("all", "parse"):
                cand = in_u & (snapT["parseable"].values if view == "parse" else True)
                cs = all_scores[cand]
                n_cand = int(cand.sum())
                # one rank per reachable GT file; the candidate set does not depend
                # on the GT filter, so the filters below re-use these ranks
                ranked = []
                for g_ in reach:
                    p_ = g_["pre_path"]
                    parseable = bool(snapT.at[p_, "parseable"])
                    r = (float(expected_ranks(cs, np.array([score.get(p_, -np.inf)]))[0])
                         if (parseable or view == "all") else np.inf)
                    ranked.append((g_, r, parseable))
                    gt_rows.append({
                        "tech": tech, "view": view, "universe": universe, "fold": fold, "seed": seed,
                        **bug_info, "path": p_, "ext": snapT.at[p_, "ext"], "language": g_["language"],
                        "category": g_["category"], "parse_status": snapT.at[p_, "parse_status"],
                        "is_primary": g_["language"] == prim, "is_test": g_["is_test"], "rank": r,
                    })
                # GT filters: all files, and (sensitivity S1) non-test files only
                for gtf in ("all", "no_tests"):
                    if gtf == "no_tests" and universe == "T":
                        continue
                    sub = [x for x in ranked if gtf == "all" or not x[0]["is_test"]]
                    ranks = np.array([x[1] for x in sub], float)
                    row = {
                        "tech": tech, "view": view, "universe": universe, "gt_filter": gtf,
                        "fold": fold, "seed": seed, **bug_info,
                        "n_cand": n_cand, "n_gt": n_gt, "n_gt_added": n_added, "n_gt_reach": len(sub),
                        "n_gt_reach_parseable": int(sum(x[2] for x in sub)),
                        "missing_scores": missing_scores,
                    }
                    if len(sub):
                        first = float(np.min(ranks))
                        row.update({
                            "first_rank": first, "rr": 0.0 if not np.isfinite(first) else 1.0 / first,
                            "ap": _ap(ranks),
                            **{f"top{kk_}": float(first <= kk_) for kk_ in KS},
                            "cfr10": float(np.mean(ranks <= 10)),
                            "rr10": (1.0 / first) if first <= 10 else 0.0,
                            # AP@10: ranks beyond 10 count as misses -- the primary
                            # outcome whenever LocAgent (<= 10 files) is compared
                            "ap10": _ap(np.where(ranks <= 10, ranks, np.inf)),
                        })
                        isp = np.array([x[0]["language"] == prim for x in sub])
                        for lab, mask in (("primary", isp), ("secondary", ~isp)):
                            if mask.any():
                                f2 = float(np.min(ranks[mask]))
                                row[f"rr_{lab}"] = 0.0 if not np.isfinite(f2) else 1.0 / f2
                                row[f"ap_{lab}"] = _ap(ranks[mask])
                                row[f"cfr10_{lab}"] = float(np.mean(ranks[mask] <= 10))
                        n_rel = int(np.isfinite(ranks).sum()) if view == "parse" else len(sub)
                        row["rand_rr"], row["rand_top10"] = random_baseline(n_cand, n_rel)
                    bug_rows.append(row)
    return pd.DataFrame(bug_rows), pd.DataFrame(gt_rows)


def summarise(per_bug: pd.DataFrame) -> pd.DataFrame:
    d = per_bug.dropna(subset=["rr"])
    keys = ["tech", "view", "universe", "gt_filter", "source", "fold", "seed", "project"]
    out = []
    for cls_name, sub in [("ALL", d), (MONO, d[d.study_class == MONO]), (POLY, d[d.study_class == POLY]),
                          ("Poly-behavioural", d[d.poly_type == "poly_behavioural"]),
                          ("Poly-test-only", d[d.poly_type == "poly_test_only"]),
                          (NO_PRIMARY, d[d.study_class == NO_PRIMARY])]:
        if sub.empty:
            continue
        s = sub.groupby(keys).agg(n_bugs=("bug_id", "nunique"), MAP=("ap", "mean"),
                                  MAP10=("ap10", "mean"), CFR10=("cfr10", "mean"), top1=("top1", "mean"),
                                  top5=("top5", "mean"), top10=("top10", "mean"),
                                  MRR=("rr", "mean"),
                                  rand_MRR=("rand_rr", "mean")).reset_index()
        s.insert(len(keys), "bug_class", cls_name)
        out.append(s)
    return pd.concat(out, ignore_index=True).round(4) if out else pd.DataFrame()


def write_legacy_diag(per_gt: pd.DataFrame):
    """diagnostics/WP_<TECH>-<view>_<stub>.csv for the pre-existing analysis scripts."""
    os.makedirs(DIAG_DIR, exist_ok=True)
    g = per_gt[(per_gt.universe == "R") & (per_gt.fold == 1) & (per_gt.source == "kept")]
    for (tech, view, repo), x in g.groupby(["tech", "view", "project"]):
        x = x[x.seed == x.seed.min()]
        out = pd.DataFrame({
            "bug_id": x.bug_id, "gt_sha": "", "gt_path": x.path, "ext": x.ext,
            "faiss_rank": -1,
            "model_rank": np.where(np.isfinite(x["rank"]), np.ceil(x["rank"]), -1).astype(int),
            "bug_class": x.study_class,
        })
        out.to_csv(os.path.join(DIAG_DIR, f"WP_{tech}-{view}_{repo.replace('/', '_')}.csv"), index=False)


def main():
    files = sorted(glob.glob(os.path.join(SCORES_DIR, "*", "fold*", "seed*", "*.parquet")))
    if not files:
        print("no score files yet"); return
    pb, pg = [], []
    for f in files:
        m = re.search(r"scores(?:_smoke)?/([^/]+)/fold(\d+)/seed(\d+)/([^/]+)\.parquet$", f)
        tech, fold, seed, stub = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
        repo = next(r for r in P.SELECTED_REPO_NAMES if r.replace("/", "_") == stub)
        b, g = evaluate_scores(tech, fold, seed, repo)
        pb.append(b); pg.append(g)
        ok = b[(b.universe == "R") & (b.gt_filter == "all") & (b.source == "kept") & b.rr.notna()]
        print(f"{tech:10s} fold{fold} seed{seed} {repo:26s} "
              + "  ".join(f"{v}: MRR={ok[ok.view == v].rr.mean():.3f} (n={ok[ok.view == v].bug_id.nunique()})"
                          for v in ("all", "parse")))
    per_bug, per_gt = pd.concat(pb, ignore_index=True), pd.concat(pg, ignore_index=True)
    os.makedirs(EVAL_DIR, exist_ok=True)
    per_bug.to_parquet(os.path.join(EVAL_DIR, "per_bug.parquet"), index=False)
    per_gt.to_parquet(os.path.join(EVAL_DIR, "per_gt.parquet"), index=False)
    summarise(per_bug).to_csv(os.path.join(EVAL_DIR, "summary.csv"), index=False)
    write_legacy_diag(per_gt)
    print(f"-> {EVAL_DIR}")


if __name__ == "__main__":
    main()
