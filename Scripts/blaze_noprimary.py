"""
Score the no-primary bugs of each test window with the stored BLAZE models
(seed 13, both folds), without retraining (second internal review, 2.4).
Uses BLAZE's own model class and scoring function (src/blaze/wp.py).

Writes results/obj2/scores/BLAZE_NP/fold<F>/seed13/<project>.parquet (no-primary
bugs only), evaluated with Scripts/analysis/append_eval.py BLAZE_NP.

    python Scripts/blaze_noprimary.py
"""

import os
import sys

import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Scripts import evaluate as EV
from Scripts import models as M
from Scripts import paths as P
from Scripts.bugs import chrono_split, load_all
from src.blaze import wp as W


def main():
    kept = load_all()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    for fold in (1, 2):
        for repo in P.SELECTED_REPO_NAMES:
            out = EV.score_path("BLAZE_NP", fold, 13, repo)
            if os.path.exists(out):
                continue
            bugs = chrono_split(repo, fold)["test_noprimary"]
            if not bugs:
                continue
            md = M.model_dir("BLAZE", fold, 13, repo)
            model = W.BlazeEmbedding(model_name=W.BACKBONE, dimension=W.DIM, max_length=W.CODE_MAX_LEN,
                                     residual_layers=W.RESIDUAL_LAYERS, report_prefix="", source_prefix="",
                                     report_max_length=W.REPORT_MAX_LEN, trust_remote_code=True,
                                     revision=W.REVISION, tokenizer_kwargs={"add_eos_token": True})
            model.load_state_dict(torch.load(os.path.join(md, "model.pt"), map_location="cpu"))
            model.to(device)
            language = dict(kept.groupby("repo_name")["language"].first())[repo]
            kk = kept[kept["repo_name"] == repo].set_index("bug_id")
            scores = W._score_bugs(model, bugs, kk, repo, language, {}, device, {})
            os.makedirs(os.path.dirname(out), exist_ok=True)
            scores.to_parquet(out, index=False)
            print(f"BLAZE_NP fold {fold} {repo}: {len(bugs)} no-primary bugs -> {out}", flush=True)
            del model
            torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
