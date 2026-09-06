"""
Step 3 — Within-project (WP) and same-language cross-project (CP) reranking runs.

ARMS
  (a) WP  : for each of the 6 projects, one training run on 80% of the KEPT bugs
            (both classes), evaluated on the held-out 20%. Models: BLAZE, FLIM.
  (b) CP  : same-language directed pairs (Java<->Java, Python<->Python), trained
            on 100% source + 20% target, evaluated on 80% of target. Models:
            BLAZE, COOBA (COOBA in its designed transfer setting).

The Mono-vs-Poly comparison is NOT done here — it is done in analysis by slicing
the per-bug diagnostics (which carry `bug_class`) and balanced-subsampling.
Retrieval recall by class (retrieval_recall_by_class.py) must be run first.

GPU. Expect ~45 min per model-run; the full grid is ~2.5-3 days. Resumable:
each finished run is appended to results/obj2/wp_cp_summary.csv and skipped on
rerun. Per-bug diagnostics go to results/obj2/diagnostics/.

Smoke test:  OBJ2_SMOKE=1 python Scripts/run_obj2_experiments.py
             (1 project, BLAZE only, 1 epoch)

Run:         python Scripts/run_obj2_experiments.py
"""

import itertools
import json
import os
import sys
import time

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Scripts import paths as P
from Scripts.classification_rules import EXT_LANG, GRAMMAR_LANGUAGES

SMOKE = os.environ.get("OBJ2_SMOKE") == "1"
ONLY_MODELS = set(os.environ.get("OBJ2_MODELS", "").split(",")) - {""}  # e.g. OBJ2_MODELS=BM25
ONLY_ARMS = set(os.environ.get("OBJ2_ARMS", "").split(",")) - {""}      # e.g. OBJ2_ARMS=WP
SEED = 42
FAISS_TOP_K = 300
OUT_DIR = P.RESULT_PATH
DIAG_DIR = os.path.join(OUT_DIR, "diagnostics")
SUMMARY_CSV = os.path.join(OUT_DIR, "wp_cp_summary.csv")
os.makedirs(DIAG_DIR, exist_ok=True)

SUMMARY_COLS = [
    "arm", "model", "source_project", "target_project", "scenario",
    "bug_class", "n_test_bugs", "n_gt_files",
    "top1", "top5", "top10", "MAP", "MRR", "wall_time_sec",
]


# ---------------------------------------------------------------------------
def load_kept():
    df = pd.read_parquet(P.BUG_CLASSIFICATION_PARQUET)
    df = df[df["keep"]].copy()
    df["bug_id"] = df["bug_id"].astype(str)
    return df


def wp_split(bug_ids):
    train_pool, test = train_test_split(sorted(bug_ids), test_size=0.20, random_state=SEED)
    return train_pool, test


def cp_pairs():
    by_lang = {"java": [], "python": []}
    for repo, lang in P.SELECTED_PROJECTS:
        by_lang[lang].append(repo)
    pairs = []
    for lang, repos in by_lang.items():
        for s, t in itertools.permutations(repos, 2):
            pairs.append((s, t))
    return pairs


def already_done(arm, model, src, tgt, scenario):
    if not os.path.exists(SUMMARY_CSV):
        return False
    d = pd.read_csv(SUMMARY_CSV)
    return ((d.arm == arm) & (d.model == model) & (d.source_project == src)
            & (d.target_project == tgt) & (d.scenario == scenario)).any()


def append_rows(rows):
    df = pd.DataFrame(rows)
    df.to_csv(SUMMARY_CSV, mode="a", header=not os.path.exists(SUMMARY_CSV),
              index=False, columns=SUMMARY_COLS)


def metrics_by_class(diag: pd.DataFrame, cls_map: dict):
    """diag: per-(bug,gt_file) rows with columns bug_id, model_rank. -> per-class dict."""
    diag = diag.copy()
    diag["bug_class"] = diag["bug_id"].map(cls_map)
    out = []
    for bclass, g in list(diag.groupby("bug_class")) + [("ALL", diag)]:
        by_bug = g.groupby("bug_id")["model_rank"]
        first = by_bug.min()
        rr = (1.0 / first.where(first > 0, np.inf)).replace(np.inf, 0.0)
        def topk(k):
            return float((first.between(1, k)).mean())
        # MAP
        aps = []
        for _, gg in g.groupby("bug_id"):
            ranks = sorted(r for r in gg["model_rank"] if r and r > 0)
            if not ranks:
                aps.append(0.0); continue
            aps.append(float(np.mean([(i + 1) / r for i, r in enumerate(ranks)])))
        out.append({
            "bug_class": bclass, "n_test_bugs": g["bug_id"].nunique(), "n_gt_files": len(g),
            "top1": round(topk(1), 4), "top5": round(topk(5), 4), "top10": round(topk(10), 4),
            "MAP": round(float(np.mean(aps)) if aps else 0.0, 4),
            "MRR": round(float(rr.mean()), 4),
        })
    return out


# ---------------------------------------------------------------------------
# BLAZE — train once, evaluate with per-bug diagnostics (ported from
# blaze_faiss_restricted_sweep.py, adapted to WP/CP and class diagnostics).
# ---------------------------------------------------------------------------
def run_blaze(arm, src, tgt, scenario, source_train_ids, target_train_ids,
              target_test_ids, cls_map, epochs):
    import copy, math, git, torch, torch.nn.functional as F, torch.optim as optim, transformers
    from src.blaze.model import BlazeEmbedding, NTXentLoss
    from src.blaze.data_prep import (
        create_contrastive_samples, get_path_to_sha_map, get_project_path,
        load_project_databases,
    )
    from src.blaze.pipeline import (
        BGE_EMBEDDING_DIM, BGE_MODEL_NAME, FREEZE_TRANSFORMER, GRAD_ACCUM_STEPS,
        HARD_NEGATIVE_SCALE, HARD_POSITIVE_SCALE, LEARNING_RATE, PATIENCE,
        POSITIVE_SCALE, RESIDUAL_LAYERS, TAU, WARMUP_RATIO, WEIGHT_DECAY,
        _build_dataloader, _encode_snapshot_blobs, _train_epoch, _val_loss, _wait_for_gpu,
    )
    device = "cuda" if torch.cuda.is_available() else "cpu"
    df_bugs = pd.read_parquet(P.BUG_REPORTS_PATH)
    df_meta = pd.read_parquet(P.PROJECTS_METADATA_PATH)

    s_bug_db, s_blob_db, s_lang = (load_project_databases(src, df_meta) if source_train_ids
                                   else (None, None, None))
    t_bug_db, t_blob_db, t_lang = load_project_databases(tgt, df_meta)
    t_repo = git.Repo(get_project_path(tgt, t_lang))

    def _split(ids, ratio):
        if not ids or len(ids) * ratio < 1:
            return ids, []
        return train_test_split(ids, test_size=ratio, random_state=SEED)

    s_tr, s_val = _split(source_train_ids, 0.2)
    t_tr, t_val = _split(target_train_ids, 0.2)
    mk = create_contrastive_samples
    s_tr_s = mk(src, s_lang, s_bug_db, df_bugs, s_tr) if s_tr else []
    s_val_s = mk(src, s_lang, s_bug_db, df_bugs, s_val) if s_val else []
    t_tr_s = mk(tgt, t_lang, t_bug_db, df_bugs, t_tr) if t_tr else []
    t_val_s = mk(tgt, t_lang, t_bug_db, df_bugs, t_val) if t_val else []
    if not s_tr_s and not t_tr_s:
        print("  no training samples, skip"); return None

    s_tr_l = _build_dataloader(s_tr_s, shuffle=True, drop_last=True)
    s_val_l = _build_dataloader(s_val_s, shuffle=False, drop_last=False)
    t_tr_l = _build_dataloader(t_tr_s, shuffle=True, drop_last=True)
    t_val_l = _build_dataloader(t_val_s, shuffle=False, drop_last=False)

    torch.cuda.empty_cache()
    model = BlazeEmbedding(model_name=BGE_MODEL_NAME, dimension=BGE_EMBEDDING_DIM,
                           max_length=512, residual_layers=RESIDUAL_LAYERS).to(device)
    if FREEZE_TRANSFORMER:
        for p_ in model.transformer.parameters():
            p_.requires_grad = False
        model.transformer.eval()
    loss_fn = NTXentLoss(tau=TAU, hard_negative_scale=HARD_NEGATIVE_SCALE,
                         hard_positive_scale=HARD_POSITIVE_SCALE, positive_scale=POSITIVE_SCALE)
    opt = optim.AdamW([p_ for p_ in model.parameters() if p_.requires_grad],
                      lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    nb = (len(s_tr_l) if s_tr_l else 0) + (len(t_tr_l) if t_tr_l else 0)
    steps = max(1, math.ceil(nb / GRAD_ACCUM_STEPS)) * epochs
    sch = transformers.get_linear_schedule_with_warmup(opt, max(1, int(steps * WARMUP_RATIO)), steps)
    scaler = torch.amp.GradScaler("cuda")
    best, best_state, patience = float("inf"), None, 0
    for ep in range(epochs):
        _wait_for_gpu(model, device)
        tl = _train_epoch(model, loss_fn, opt, sch, scaler, s_tr_l, t_tr_l, device, ep)
        if s_val_l or t_val_l:
            vl = _val_loss(model, loss_fn, s_val_l, t_val_l, device)
            if vl < best:
                best, best_state, patience = vl, copy.deepcopy(model.state_dict()), 0
            else:
                patience += 1
                if patience >= PATIENCE:
                    break
        else:
            best_state = copy.deepcopy(model.state_dict())
        print(f"  epoch {ep+1}: train_loss={tl:.4f}")
    if best_state:
        model.load_state_dict(best_state)

    # ---- evaluate: per-gt-file model_rank, restricted to FAISS top-K ----
    model.eval()
    bug_text = pd.Series(df_bugs["bug_report_text"].values, index=df_bugs["bug_id"].astype(str)).to_dict()
    diag = []
    blob_cache = {}
    for bug_id in target_test_ids:
        meta = t_bug_db.get(str(bug_id))
        if not meta:
            continue
        sha = meta.get("commit_sha", "")
        txt = bug_text.get(str(bug_id), "")
        if not sha or not txt:
            continue
        p2s = get_path_to_sha_map(t_repo, sha)
        if not p2s:
            continue
        gt_shas = {s for p, s in p2s.items()
                   if any(p == g or p.endswith("/" + g) for g in meta.get("ground_truth_files", []))}
        if not gt_shas:
            continue
        chunk_embs = _encode_snapshot_blobs(model, t_repo, p2s, t_lang, device, blob_cache)
        with torch.no_grad(), torch.amp.autocast(device_type="cuda"):
            q = model.get_report_embedding([txt])
        q = F.normalize(q, p=2, dim=1).cpu().numpy()[0]
        scores = {s: float((ce @ q).max()) for s, ce in chunk_embs.items()}
        # FAISS top-K restriction
        snap = [s for s in p2s.values() if s in t_blob_db]
        if snap:
            E = np.stack([t_blob_db[s].astype("float32") for s in snap])
            E /= (np.linalg.norm(E, axis=1, keepdims=True) + 1e-10)
            be = meta["embedding"].astype("float32"); be /= (np.linalg.norm(be) + 1e-10)
            order = np.argsort(E @ be)[::-1]
            faiss_ranked = [snap[i] for i in order]
        else:
            faiss_ranked = []
        # obj2: NO retrieval stage -- BLAZE ranks the whole snapshot
        ranked = [s for s, _ in sorted(scores.items(), key=lambda x: -x[1])]
        rank_of = {s: i + 1 for i, s in enumerate(ranked)}
        faiss_rank_of = {s: i + 1 for i, s in enumerate(faiss_ranked)}
        sha2path = {v: k for k, v in p2s.items()}
        for gs in gt_shas:
            gp = sha2path.get(gs, "")
            diag.append({
                "bug_id": str(bug_id), "gt_sha": gs, "gt_path": gp,
                "ext": gp.rsplit(".", 1)[-1].lower() if "." in gp.rsplit("/", 1)[-1] else "[noext]",
                "faiss_rank": faiss_rank_of.get(gs, -1),
                "model_rank": rank_of.get(gs, -1),
            })
    return pd.DataFrame(diag)


# ---------------------------------------------------------------------------
# BM25 — classical IR baseline. Ranks the WHOLE snapshot (every embedded blob),
# NOT the FAISS top-K: classical retrieval processes every file type by
# construction, so restricting it to the neural retriever's candidates would
# defeat the point of the Step 4 comparison. CPU, no training.
# ---------------------------------------------------------------------------
_TOK = None
BM25_MAX_DOCS = 40000        # cap tokenised docs per snapshot (large repos)


def _tokenize(text):
    import re
    global _TOK
    if _TOK is None:
        _TOK = (re.compile(r"[^A-Za-z0-9]+"), re.compile(r"(?<=[a-z0-9])(?=[A-Z])"))
    parts = _TOK[0].split(text or "")
    out = []
    for p in parts:
        for q in _TOK[1].split(p):
            if q:
                out.append(q.lower())
    return out


def run_bm25(tgt, target_test_ids, cls_map):
    import pickle, git
    import bm25s
    stub = tgt.replace("/", "_")
    lang = dict(P.SELECTED_PROJECTS)[tgt]
    blob_db = pickle.load(open(os.path.join(P.EMBEDDING_DB_DIR, f"{stub}_blob_embeddings32.pkl"), "rb"))
    bug_db = pickle.load(open(os.path.join(P.EMBEDDING_DB_DIR, f"{stub}_bug_metadata32.pkl"), "rb"))
    df_bugs = pd.read_parquet(P.BUG_REPORTS_PATH)
    bug_text = pd.Series(df_bugs["bug_report_text"].values,
                         index=df_bugs["bug_id"].astype(str)).to_dict()
    repo = git.Repo(os.path.join(P.REPO_BASE_PATH, lang, stub))
    MAX_BYTES = 2_000_000
    diag = []
    doc_cache = {}   # sha -> tokenised doc, reused across bugs sharing a snapshot
    for bug_id in target_test_ids:
        meta = bug_db.get(str(bug_id))
        if not meta:
            continue
        sha = meta.get("commit_sha", "")
        gts = list(meta.get("ground_truth_files", []))
        if not sha or not gts:
            continue
        try:
            commit = repo.commit(sha)
            p2s = {b.path: b.hexsha for b in commit.tree.traverse()
                   if b.type == "blob" and b.hexsha in blob_db}
        except Exception:
            continue
        if not p2s:
            continue
        gt_shas = {s for p, s in p2s.items()
                   if any(p == g or p.endswith("/" + g) for g in gts)}
        if not gt_shas:
            continue
        sha2path = {v: k for k, v in p2s.items()}

        # FAISS order (for the "where would the neural retriever put it" column)
        snap = list(p2s.values())
        E = np.stack([blob_db[s].astype("float32") for s in snap])
        E /= (np.linalg.norm(E, axis=1, keepdims=True) + 1e-10)
        be = meta["embedding"].astype("float32"); be /= (np.linalg.norm(be) + 1e-10)
        faiss_order = [snap[i] for i in np.argsort(E @ be)[::-1]]
        faiss_rank_of = {s: i + 1 for i, s in enumerate(faiss_order)}

        # BM25 over the WHOLE snapshot (cap at BM25_MAX_DOCS)
        items = list(p2s.items())[:BM25_MAX_DOCS]
        docs, keep_shas = [], []
        for path, s in items:
            if s in doc_cache:
                docs.append(doc_cache[s]); keep_shas.append(s); continue
            try:
                blob = commit.tree / path
                if blob.size > MAX_BYTES:
                    tok = _tokenize(path)
                else:
                    tok = _tokenize(path + " " + blob.data_stream.read().decode("utf-8", "replace"))
            except Exception:
                tok = _tokenize(path)
            doc_cache[s] = tok
            docs.append(tok); keep_shas.append(s)
        if not docs:
            continue
        retriever = bm25s.BM25()
        retriever.index(docs, show_progress=False)
        res, _sc = retriever.retrieve(
            [_tokenize(bug_text.get(str(bug_id), "")) or ["_"]],
            k=len(docs), show_progress=False,
        )
        rank_of = {keep_shas[int(idx)]: r + 1 for r, idx in enumerate(res[0])}
        for gs in gt_shas:
            gp = sha2path.get(gs, "")
            diag.append({
                "bug_id": str(bug_id), "gt_sha": gs, "gt_path": gp,
                "ext": gp.rsplit(".", 1)[-1].lower() if "." in gp.rsplit("/", 1)[-1] else "[noext]",
                "faiss_rank": faiss_rank_of.get(gs, -1),
                "model_rank": rank_of.get(gs, -1),
            })
    d = pd.DataFrame(diag)
    if not d.empty:
        d["bug_class"] = d["bug_id"].map(cls_map)
    return d


# ---------------------------------------------------------------------------
# FLIM — WP, full-snapshot (no retrieval filter). We monkey-patch
# TOP_K_CANDIDATES so LAYER 1 returns every file, and set FLIM_DIAG_CSV so the
# patched pipeline dumps per-(bug,file) scores; we then compute per-GT-file
# ranks and slice by class ourselves.
# ---------------------------------------------------------------------------
def run_flim(tgt, t_tr, target_test_ids, cls_map, epochs):
    import pickle
    import src.flim.pipeline as flp
    flp.TOP_K_CANDIDATES = 10 ** 9        # LAYER 1 returns the whole snapshot
    flp._FUNC_EMB_CACHE.clear()
    if epochs:
        flp.FINETUNE_EPOCHS = epochs
    diag_csv = os.path.join(DIAG_DIR, f"_flim_raw_{tgt.replace('/', '_')}.csv")
    os.environ["FLIM_DIAG_CSV"] = diag_csv

    flp.run_flim_experiment(tgt, tgt, [], t_tr, [str(b) for b in target_test_ids], "WP-large")
    if not os.path.exists(diag_csv):
        return pd.DataFrame()
    raw = pd.read_csv(diag_csv, dtype={"bug_id": str})

    # per bug: rank files by 'result' desc, read off each ground-truth file's rank
    stub = tgt.replace("/", "_")
    bug_db = pickle.load(open(os.path.join(P.EMBEDDING_DB_DIR, f"{stub}_bug_metadata32.pkl"), "rb"))
    rows = []
    for bug_id, g in raw.groupby("bug_id"):
        g = g.sort_values("result", ascending=False).reset_index(drop=True)
        g["rank"] = g.index + 1
        gt = g[g["used_in_fix"] == 1.0]
        gts_meta = bug_db.get(str(bug_id), {}).get("ground_truth_files", [])
        for _, rr in gt.iterrows():
            rows.append({
                "bug_id": str(bug_id), "gt_sha": rr["blob_sha"], "gt_path": "",
                "ext": "", "faiss_rank": -1, "model_rank": int(rr["rank"]),
            })
        # ground-truth files FLIM never scored (no functions / not in candidate list) -> rank -1
        scored = set(gt["blob_sha"])
        n_missing = max(0, len(gts_meta) - len(scored))
        for _ in range(n_missing):
            rows.append({"bug_id": str(bug_id), "gt_sha": "", "gt_path": "",
                         "ext": "", "faiss_rank": -1, "model_rank": -1})
    d = pd.DataFrame(rows)
    if not d.empty:
        d["bug_class"] = d["bug_id"].map(cls_map)
    return d


# ---------------------------------------------------------------------------
def main():
    kept = load_kept()
    cls_map = dict(zip(kept["bug_id"], kept["class"]))
    epochs = 1 if SMOKE else 10

    # ---- WP arm only (no retrieval stage: every technique ranks the full snapshot) ----
    _smoke_proj = os.environ.get("OBJ2_SMOKE_PROJECT", "localstack/localstack")
    wp_projects = [_smoke_proj] if SMOKE else P.SELECTED_REPO_NAMES
    models = ["BM25", "BLAZE"] if SMOKE else ["BM25", "BLAZE", "FLIM"]
    if ONLY_MODELS:
        models = [m for m in models if m in ONLY_MODELS]

    jobs = []
    for repo in wp_projects:
        ids = kept[kept.repo_name == repo]["bug_id"].tolist()
        tr, te = wp_split(ids)                       # 80 / 20
        for mdl in models:
            jobs.append(dict(model=mdl, tgt=repo, t_tr=tr, t_test=te))

    print(f"{len(jobs)} runs  (WP only, full-snapshot  SMOKE={SMOKE}  models={models})")
    for i, j in enumerate(jobs, 1):
        if already_done("WP", j["model"], j["tgt"], j["tgt"], "WP"):
            print(f"[{i}/{len(jobs)}] {j['model']} {j['tgt']} — done, skip")
            continue
        print(f"\n[{i}/{len(jobs)}] WP {j['model']} {j['tgt']}")
        t0 = time.time()
        try:
            if j["model"] == "BLAZE":
                diag = run_blaze("WP", j["tgt"], j["tgt"], "WP", [], j["t_tr"],
                                 j["t_test"], cls_map, epochs)
            elif j["model"] == "BM25":
                diag = run_bm25(j["tgt"], j["t_test"], cls_map)
            else:  # FLIM
                diag = run_flim(j["tgt"], j["t_tr"], j["t_test"], cls_map, epochs if SMOKE else 0)
            if diag is None or diag.empty:
                print("  no diagnostics"); continue
            tag = f"WP_{j['model']}_{j['tgt'].replace('/', '_')}"
            diag["bug_class"] = diag["bug_id"].map(cls_map)
            diag.to_csv(os.path.join(DIAG_DIR, tag + ".csv"), index=False)
            per_class = metrics_by_class(diag, cls_map)
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"  ERROR: {type(e).__name__}: {e}")
            continue
        wt = round(time.time() - t0, 1)
        append_rows([{"arm": "WP", "model": j["model"], "source_project": j["tgt"],
                      "target_project": j["tgt"], "scenario": "WP", "wall_time_sec": wt, **pc}
                     for pc in per_class])
        print(f"  done in {wt/60:.1f} min: " + " | ".join(
            f"{pc['bug_class']}: MRR={pc['MRR']}" for pc in per_class))

    print(f"\nSummary -> {SUMMARY_CSV}")


if __name__ == "__main__":
    main()
