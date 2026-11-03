"""
Score bugs with a SAVED model -- no training (Scripts/models.py layout).

This is how a stratum or analysis added after the full run is scored: load the
model a run saved and score more bugs with exactly the scoring code of the
run. `--verify` re-scores bugs the run already scored and compares with the
stored score file (the check that saved models are sufficient).

    python Scripts/rescore.py --tech BLAZE --project elastic/elasticsearch --fold 1 --seed 13 \
        --bugs R100005,R100186 --out scores.parquet
    python Scripts/rescore.py --tech FLIM ... --verify [--max-files 300]
"""

import argparse
import json
import os
import pickle
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Scripts import models as M
from Scripts.bugs import eval_ground_truth, load_all, project_history
from Scripts.universe import scored_files


def _model_dir(tech, fold, seed, repo, smoke):
    sfx = "_smoke" if smoke else ""
    return os.path.join(M.MODELS_DIR + sfx, tech, f"fold{fold}", f"seed{seed}", repo.replace("/", "_"))


def _subset(files, repo, bid, max_files, rng):
    """All files, or the bug's GT files + a random sample (fast verification)."""
    if not max_files or len(files) <= max_files:
        return files
    gt = {g["pre_path"] for g in eval_ground_truth(repo, bid) if g["pre_path"]}
    is_gt = files["path"].isin(gt)
    rest = files[~is_gt].sample(n=max_files - int(is_gt.sum()), random_state=rng)
    return pd.concat([files[is_gt], rest]).reset_index(drop=True)


# ---------------------------------------------------------------- BLAZE
def score_blaze(md, repo, bug_ids, kept, max_files=0, seed=0):
    import torch
    import torch.nn.functional as F
    import src.blaze.wp as W
    from src.blaze.model import BlazeEmbedding
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = BlazeEmbedding(model_name=W.BACKBONE, dimension=W.DIM, max_length=W.CODE_MAX_LEN,
                           residual_layers=W.RESIDUAL_LAYERS, report_prefix="", source_prefix="",
                           report_max_length=W.REPORT_MAX_LEN, trust_remote_code=True,
                           revision=W.REVISION, tokenizer_kwargs={"add_eos_token": True})
    model.load_state_dict(torch.load(os.path.join(md, "model.pt"), map_location="cpu"))
    model.to(device).eval()
    language = dict(kept.groupby("repo_name")["language"].first())[repo]
    kk = kept[kept["repo_name"] == repo].set_index("bug_id")
    splitters, out = {}, []
    for bid in bug_ids:
        files = _subset(scored_files(repo, kk.loc[bid, "pre_fix_commit_sha"]), repo, bid, max_files, seed)
        emb = {}
        for p, s in zip(files["path"], files["blob_sha"]):
            if s not in emb:
                emb[s] = W._encode_chunks(model, W._chunks(p, W.read_text(repo, s), language, splitters), device)
        with torch.no_grad(), torch.autocast(device_type="cuda", dtype=torch.bfloat16, enabled=device == "cuda"):
            q = model.get_report_embedding([kk.loc[bid, "bug_report_text"]])
        q = F.normalize(q.float(), dim=1).cpu().numpy()[0].astype(np.float32)
        sc = [float((emb[s].astype(np.float32) @ q).max()) for s in files["blob_sha"]]
        out.append(pd.DataFrame({"bug_id": bid, "path": files["path"].values, "score": np.float32(sc)}))
    return pd.concat(out, ignore_index=True)


# ---------------------------------------------------------------- FLIM
def score_flim(md, repo, bug_ids, kept, max_files=0, seed=0):
    import torch
    import src.flim.pipeline as FP
    from src.flim.encoder import CodeBERTEncoder
    from src.flim.ir_features import History
    with open(os.path.join(md, "ltr.pkl"), "rb") as f:
        ltr = pickle.load(f)
    language = dict(kept.groupby("repo_name")["language"].first())[repo]
    R = FP._Run(repo, language, kept, lambda *_: None)
    R.store.vec = ltr["vectorizer"]
    R.history = History(project_history(repo), R.store.vec)
    R.encoder = CodeBERTEncoder()
    R.encoder.model.load_state_dict(torch.load(os.path.join(md, "encoder.pt"), map_location="cpu"))
    R.encoder.model.eval()
    jobs = []
    for bid in bug_ids:
        commit, files = R.files_of(bid)
        sub = _subset(files, repo, bid, max_files, seed)
        par = files[files["parseable"]].reset_index(drop=True)
        for p, s in zip(par["path"], par["blob_sha"]):          # import graph needs all parseable files
            R.store.add(p, s, True)
        for p, s, pz in zip(sub["path"], sub["blob_sha"], sub["parseable"]):
            R.store.add(p, s, bool(pz))
        jobs.append((bid, commit, sub, par))
    R.store.finalize_tfidf()
    R.store.embed_units(R.encoder, lambda *_: None)
    out = []
    for bid, commit, sub, par in jobs:
        R.graph(commit, par, [R.store.key(s, True) for s in par["blob_sha"]])
        keys = [R.store.key(s, pz) for s, pz in zip(sub["blob_sha"], sub["parseable"])]
        f = (R.features(bid, sub, keys) - ltr["lo"]) / ltr["span"]
        out.append(pd.DataFrame({"bug_id": bid, "path": sub["path"].values,
                                 "score": ltr["ranker"].predict(f).astype(np.float32)}))
    return pd.concat(out, ignore_index=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tech", required=True, choices=["BLAZE", "BLAZE_ALL", "FLIM"])
    ap.add_argument("--project", required=True)
    ap.add_argument("--fold", type=int, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--bugs", default="", help="comma list; default with --verify: 2 scored bugs")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--max-files", type=int, default=0)
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    md = _model_dir(a.tech, a.fold, a.seed, a.project, a.smoke)
    kept = load_all()
    stored = None
    if a.verify:
        from Scripts import evaluate as EV
        sd = os.path.join(os.path.dirname(EV.SCORES_DIR), "scores_smoke" if a.smoke else "scores")
        stored = pd.read_parquet(os.path.join(sd, a.tech, f"fold{a.fold}", f"seed{a.seed}",
                                              a.project.replace("/", "_") + ".parquet"))
        stored["bug_id"] = stored["bug_id"].astype(str)
    bugs = [b for b in a.bugs.split(",") if b] or (sorted(stored["bug_id"].unique())[:2] if stored is not None else [])
    fn = score_flim if a.tech == "FLIM" else score_blaze
    if a.tech == "BLAZE_ALL":
        os.environ["BLAZE_TRAIN_ALL_FILES"] = "1"
    new = fn(md, a.project, bugs, kept, a.max_files)
    if a.out:
        new.to_parquet(a.out, index=False)
    if stored is not None:
        m = new.merge(stored, on=["bug_id", "path"], suffixes=("_new", "_stored"))
        d = (m["score_new"] - m["score_stored"]).abs()
        rk = m.groupby("bug_id").apply(lambda g: g["score_new"].rank().corr(g["score_stored"].rank()))
        print(json.dumps({"tech": a.tech, "project": a.project, "bugs": bugs, "files_compared": len(m),
                          "max_abs_diff": float(d.max()), "mean_abs_diff": float(d.mean()),
                          "rank_corr_min": float(rk.min())}, indent=1))


if __name__ == "__main__":
    main()
