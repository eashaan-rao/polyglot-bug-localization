"""
Learning-rate selection shared by the neural techniques (decided 2026-10-31).

Rule (same for BLAZE and FLIM): every hyper-parameter comes from the authors'
released code except the learning rate, which is chosen from a small grid
around the published value(s) by **validation MAP** (the paper's primary
outcome) on the chronological validation split. Epochs inside one LR run are
still selected by the technique's own original criterion (BLAZE: validation
loss; FLIM: validation MRR). The test set is never used.

The LR is selected once, with the first seed of a (technique, fold, project);
later seeds read the recorded choice and train only that LR.

    results/obj2/scores/<TECH>/fold<F>/lr_selection_<project>.json
"""

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Scripts import paths as P


def _path(tech: str, fold: int, repo: str) -> str:
    sfx = "_smoke" if os.environ.get("OBJ2_SMOKE") == "1" else ""
    return os.path.join(P.RESULT_PATH, "scores" + sfx, tech, f"fold{fold}",
                        f"lr_selection_{repo.replace('/', '_')}.json")


def recorded(tech: str, fold: int, repo: str):
    """The LR chosen earlier for this (technique, fold, project), or None."""
    fp = _path(tech, fold, repo)
    if os.path.exists(fp):
        with open(fp) as f:
            return float(json.load(f)["selected_lr"])
    return None


def record(tech: str, fold: int, repo: str, selected_lr: float, seed: int, runs: list):
    fp = _path(tech, fold, repo)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, "w") as f:
        json.dump({"technique": tech, "fold": fold, "project": repo, "selected_lr": selected_lr,
                   "selected_with_seed": seed, "criterion": "validation MAP (universe R)",
                   "runs": runs}, f, indent=2, default=str)


def grid(tech: str, fold: int, repo: str, default: tuple) -> tuple:
    """LRs to train: the recorded choice if there is one, else the full grid."""
    lr = recorded(tech, fold, repo)
    return (lr,) if lr is not None else tuple(default)


def validation_map(scores: pd.DataFrame, repo: str) -> float:
    """MAP over the validation bugs, universe R, expected ranks (as evaluate.py)."""
    from Scripts.bugs import eval_ground_truth, load_all
    from Scripts.evaluate import _ap, expected_ranks
    from Scripts.universe import snapshot
    k = load_all()
    kk = k[k["repo_name"] == repo].set_index("bug_id")
    aps = []
    for bid, g in scores.groupby("bug_id"):
        snap = snapshot(repo, kk.loc[bid, "pre_fix_commit_sha"])
        R = set(snap.loc[snap["is_text"] & snap["in_ruleset"], "path"])
        g = g[g["path"].isin(R)]
        gt = [x["pre_path"] for x in eval_ground_truth(repo, bid) if x["pre_path"] in R]
        if not gt or g.empty:
            continue
        sc = pd.Series(g["score"].values, index=g["path"].values)
        ranks = expected_ranks(g["score"].values, sc.reindex(gt).fillna(-np.inf).values)
        aps.append(_ap(np.asarray(ranks, float)))
    return float(np.mean(aps)) if aps else float("nan")
