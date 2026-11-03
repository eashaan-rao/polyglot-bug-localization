"""
FLIM — within-project, full-snapshot (Objective 2).

Liang et al., "Modeling function-level interactions for file-level bug
localization", EMSE 2022, reimplemented against the original code in
Resources/flim-main. Per project / fold / seed:

  1. Fine-tune CodeBERT (src/flim/encoder.py: pooler output, NL 128 / code 256,
     in-batch CE, AdamW 2e-5, <= 10 epochs, best validation MRR, patience 3)
     on (report, function) pairs: the functions of each training fix's
     ground-truth source files that the fix changed (diff overlap), else the
     first MAX_FUNCS_POS functions of the file. Validation pairs come from the
     chronological validation bugs.
  2. Features per (bug, file): 4 semantic -- max / mean cosine of the report
     summary and description with the file's functions (Eq. 3-4) -- plus 18 of
     the 19 IR features (src/flim/ir_features.py; f2 dropped).
  3. Min-max normalise features on the training rows (AdaptiveBL), train the
     adaptive pointwise LTR (src/flim/adaptive.py, ported from the original
     train_adaptive.py, 2-fold CV) on training bugs:
     their parseable ground-truth files + the top-300 non-buggy parseable files
     by lexical similarity (Ye et al.'s negative sampling).
  4. Score every file of universe T for each test bug.

Parseability is src/parsing.py's, the same as the universe's parse_status.
A file the parser accepts is represented by its functions (or, if it has
none, by line windows of its body). A file the parser cannot read is
represented by line windows of its text: this is the FLIM-fallback condition.
The evaluator's "parse" view drops those files -> FLIM-strict, the
paper-faithful condition. Training (encoder and LTR) uses parseable files
only, so both conditions share one trained model.
"""

import os
import random
import re
import sys
import time

import numpy as np
import pandas as pd
import scipy.sparse as sp

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Scripts.bugs import eval_ground_truth, project_history
from Scripts.universe import read_text, repo_obj, scored_files, snapshot
from src.flim.encoder import CODEBERT_MODEL_NAME, CodeBERTEncoder
from src.flim.ir_features import (IR_FEATURES, History, _vec, class_name_sim,
                                  graph_features, make_vectorizer)
from src.flim.adaptive import AdaptiveLTR
from src.parsing import parse_file

FINETUNE_EPOCHS = 10
FINETUNE_BATCH_SIZE = 32
FINETUNE_LR = 2e-5          # released code (README); the paper text says 5e-5
# LR grid = the two published values; selected on validation MAP (Scripts/lr_select.py)
FLIM_LR_GRID = tuple(float(x) for x in os.environ.get("FLIM_LR_GRID", "2e-5,5e-5").split(","))
PATIENCE = 3
MAX_FUNCS_POS = 5            # positives per GT file (changed functions first)
LTR_NEG_TOP = 300            # Ye et al.: top-300 lexically similar non-buggy files
WINDOW_LINES = 30            # body / fallback representation
MAX_WINDOWS = 50
SEM_FEATURES = ["s_sum_max", "s_sum_mean", "s_desc_max", "s_desc_mean"]
FEATURES = SEM_FEATURES + IR_FEATURES

CONFIG = {
    "encoder": CODEBERT_MODEL_NAME, "epochs_max": FINETUNE_EPOCHS, "batch": FINETUNE_BATCH_SIZE,
    "lr_grid": FLIM_LR_GRID, "patience": PATIENCE,
    "selection": "epochs: val MRR (run.py); LR: val MAP (Scripts/lr_select.py)",
    "nl_len": 128, "code_len": 256, "max_funcs_pos": MAX_FUNCS_POS, "ltr_neg_top": LTR_NEG_TOP,
    "window_lines": WINDOW_LINES, "max_windows": MAX_WINDOWS, "features": FEATURES,
    "dropped_features": ["f2 (API-enriched; JDK-only)"],
}


def split_report(text: str):
    """(summary, description): first non-empty line, then the rest (or all)."""
    lines = (text or "").split("\n")
    for i, ln in enumerate(lines):
        if ln.strip():
            desc = "\n".join(lines[i + 1:]).strip()
            return ln.strip(), desc or text
    return (text or "")[:300], text or ""


def _windows(text: str):
    ls = text.split("\n")
    w = ["\n".join(ls[i:i + WINDOW_LINES]) for i in range(0, len(ls), WINDOW_LINES)]
    w = [x for x in w if x.strip()]
    return w[:MAX_WINDOWS] or [text[:2000] or " "]


class _FileStore:
    """Per-run cache: parsed fields, units, TF-IDF rows, unit embeddings."""

    def __init__(self, repo: str, language: str):
        self.repo, self.language = repo, language
        self.rec: dict = {}            # key -> dict
        self.vec = None
        self.unit_rows: dict = {}      # key -> (start, end) in the global unit arrays
        self.U_txt: list = []          # unit texts (global)
        self.U_tfidf = None            # csr (n_units, V)
        self.U_emb = None              # float16 (n_units, 768), unit-normalised
        self._pending_tfidf: list = []

    @staticmethod
    def key(sha, parseable):
        return f"{sha}:{int(bool(parseable))}"

    def add(self, path, sha, parseable):
        k = self.key(sha, parseable)
        if k in self.rec:
            return k
        text = read_text(self.repo, sha)
        pf = parse_file(path, text, self.language) if parseable else None
        if pf is not None and pf.units:
            units, spans = pf.units, pf.unit_spans
        else:
            units, spans = _windows(text), []
        r = {"units": units, "spans": spans,
             "cls": pf.class_names if pf else [], "fields": None,
             "imports": pf.imports if pf else [], "package": pf.package if pf else ""}
        if pf is not None:
            r["fields"] = (" ".join(pf.class_names), " ".join(pf.method_names),
                           " ".join(pf.var_names), " ".join(pf.comments))
        r["doc"] = path + "\n" + text
        self.rec[k] = r
        self.unit_rows[k] = (len(self.U_txt), len(self.U_txt) + len(units))
        self.U_txt.extend(units)
        self._pending_tfidf.append(k)
        return k

    def fit_vectorizer(self, docs):
        self.vec = make_vectorizer(docs)

    def finalize_tfidf(self):
        """TF-IDF for every record added since the last call."""
        if not self._pending_tfidf:
            return
        ks = self._pending_tfidf
        self._pending_tfidf = []
        docs = _vec(self.vec, [self.rec[k]["doc"] for k in ks])
        for i, k in enumerate(ks):
            r = self.rec[k]
            r["doc_v"] = docs[i]
            if r["fields"] is not None:
                r["field_v"] = _vec(self.vec, list(r["fields"]))
            del r["doc"]
        start = 0 if self.U_tfidf is None else self.U_tfidf.shape[0]
        new_units = _vec(self.vec, self.U_txt[start:])
        self.U_tfidf = new_units if self.U_tfidf is None else sp.vstack([self.U_tfidf, new_units]).tocsr()

    def embed_units(self, encoder: CodeBERTEncoder, log=print):
        start = 0 if self.U_emb is None else self.U_emb.shape[0]
        todo = self.U_txt[start:]
        if not todo:
            return
        t = time.time()
        e = encoder.encode(todo, "code").astype(np.float32)
        e /= (np.linalg.norm(e, axis=1, keepdims=True) + 1e-8)
        e = e.astype(np.float16)
        self.U_emb = e if self.U_emb is None else np.vstack([self.U_emb, e])
        log(f"[FLIM]   embedded {len(todo)} units in {time.time() - t:.0f}s "
            f"(total {self.U_emb.shape[0]})")


def _changed_old_lines(repo, pre, fix, old_path, new_path):
    try:
        d = repo_obj(repo).git.diff(pre, fix, "-U0", "--", old_path, new_path)
    except Exception:
        return set()
    out = set()
    for m in re.finditer(r"^@@ -(\d+)(?:,(\d+))? \+\d+(?:,\d+)? @@", d, re.M):
        a, b = int(m.group(1)), int(m.group(2) or 1)
        out.update(range(a, a + b) if b else (a, a + 1))
    return out


def _pairs(repo, bug_ids, kk, store, rng):
    """[(group, report_text, function_text)] for the given bugs."""
    pairs = []
    for gi, bid in enumerate(bug_ids):
        meta = kk.loc[bid]
        snap = snapshot(repo, meta["pre_fix_commit_sha"]).set_index("path")
        for g in eval_ground_truth(repo, bid):
            p = g["pre_path"]
            if p is None or p not in snap.index or not snap.at[p, "parseable"]:
                continue
            k = store.add(p, snap.at[p, "blob_sha"], True)
            r = store.rec[k]
            if not r["spans"]:
                continue
            changed = _changed_old_lines(repo, meta["pre_fix_commit_sha"], meta["fix_commit_sha"],
                                         p, g["path"])
            hit = [i for i, (a, b) in enumerate(r["spans"]) if any(a <= ln <= b for ln in changed)]
            idx = hit or list(range(len(r["units"])))
            if len(idx) > MAX_FUNCS_POS:
                idx = rng.sample(idx, MAX_FUNCS_POS)
            for i in idx:
                pairs.append((gi, meta["bug_report_text"], r["units"][i]))
    return pairs


class _Run:
    def __init__(self, repo, language, kept, log):
        self.repo, self.language, self.log = repo, language, log
        self.kk = kept[kept["repo_name"] == repo].set_index("bug_id")
        self.store = _FileStore(repo, language)
        self.history = None
        self.graph_cache: dict = {}
        self.encoder = None

    def files_of(self, bug_id):
        commit = self.kk.loc[bug_id, "pre_fix_commit_sha"]
        return commit, scored_files(self.repo, commit)

    def graph(self, commit, files, keys):
        if commit not in self.graph_cache:
            parsed = {}
            class _P:  # minimal ParsedFile view for graph_features
                pass
            for sha, k in zip(files["blob_sha"], keys):
                o = _P(); r = self.store.rec[k]
                o.imports, o.package = r["imports"], r["package"]
                parsed[sha] = o
            self.graph_cache[commit] = graph_features(files, parsed, self.language)
            if len(self.graph_cache) > 64:
                self.graph_cache.pop(next(iter(self.graph_cache)))
        return self.graph_cache[commit]

    def features(self, bug_id, files: pd.DataFrame, keys: list) -> pd.DataFrame:
        meta = self.kk.loc[bug_id]
        text = meta["bug_report_text"]
        summary, desc = split_report(text)
        st = self.store
        rep_v, sum_v, desc_v = (_vec(st.vec, [x]) for x in (text, summary, desc))
        nl = self.encoder.encode([summary, desc], "nl").astype(np.float32)
        nl /= (np.linalg.norm(nl, axis=1, keepdims=True) + 1e-8)

        ranges = [st.unit_rows[k] for k in keys]
        idx = np.concatenate([np.arange(a, b) for a, b in ranges])
        starts = np.cumsum([0] + [b - a for a, b in ranges[:-1]])
        emb = st.U_emb[idx].astype(np.float32)
        s_sum, s_desc = emb @ nl[0], emb @ nl[1]
        cnt = np.array([b - a for a, b in ranges], float)
        out = pd.DataFrame(index=files.index)
        out["s_sum_max"] = np.maximum.reduceat(s_sum, starts)
        out["s_sum_mean"] = np.add.reduceat(s_sum, starts) / cnt
        out["s_desc_max"] = np.maximum.reduceat(s_desc, starts)
        out["s_desc_mean"] = np.add.reduceat(s_desc, starts) / cnt

        u_sim = np.asarray(st.U_tfidf[idx] @ rep_v.T.toarray()).ravel()
        doc_m = sp.vstack([st.rec[k]["doc_v"] for k in keys])
        f_doc = np.asarray(doc_m @ rep_v.T.toarray()).ravel()
        out["f1"] = np.maximum(f_doc, np.maximum.reduceat(u_sim, starts))

        paths = files["path"].tolist()
        h = self.history.features(rep_v, meta["creation_date"], bug_id, paths)
        out["f3"] = [h.get(p, (0, 0, 0))[0] for p in paths]
        out["f5"] = [h.get(p, (0, 0, 0))[1] for p in paths]
        out["f6"] = [h.get(p, (0, 0, 0))[2] for p in paths]
        out["f4"] = [class_name_sim(summary, st.rec[k]["cls"] or [p.rsplit("/", 1)[-1].split(".")[0]])
                     for k, p in zip(keys, paths)]

        fs = np.zeros((len(keys), 8), np.float32)
        q = sp.vstack([sum_v, desc_v]).T.toarray()                      # (V, 2)
        for i, k in enumerate(keys):
            fv = st.rec[k].get("field_v")
            if fv is not None:
                m = np.asarray(fv @ q)                                   # (4, 2)
                fs[i, :4], fs[i, 4:] = m[:, 0], m[:, 1]
        for j, f in enumerate(["f7", "f8", "f9", "f10", "f11", "f12", "f13", "f14"]):
            out[f] = fs[:, j]

        commit = meta["pre_fix_commit_sha"]
        gf = self.graph(commit, files, keys)
        z = (0, 0, 0.0, 0.0, 0.0)
        for j, f in enumerate(["f15", "f16", "f17", "f18", "f19"]):
            out[f] = [gf.get(p, z)[j] for p in paths]
        return out[FEATURES]


def _train_candidates(R, repo, train_ids, log):
    """LTR training candidates (encoder-independent): per training bug, its
    parseable GT files + the top-300 parseable non-GT files by file-level TF-IDF."""
    out = []
    for i, bid in enumerate(train_ids, 1):
        commit, files = R.files_of(bid)
        gt = {g["pre_path"] for g in eval_ground_truth(repo, bid) if g["pre_path"]}
        cand = files[files["in_ruleset"] & files["parseable"]].reset_index(drop=True)
        if cand.empty or not (gt & set(cand["path"])):
            continue
        keys_all = [R.store.key(s, True) for s in cand["blob_sha"]]
        rep_v = _vec(R.store.vec, [R.kk.loc[bid, "bug_report_text"]])
        sim = np.asarray(sp.vstack([R.store.rec[k]["doc_v"] for k in keys_all])
                         @ rep_v.T.toarray()).ravel()
        is_gt = cand["path"].isin(gt).values
        neg = np.where(~is_gt)[0]
        neg = neg[np.argsort(-sim[neg], kind="stable")][:LTR_NEG_TOP]
        keep = np.concatenate([np.where(is_gt)[0], neg])
        out.append((bid, commit, files, cand.iloc[keep].reset_index(drop=True),
                    [keys_all[j] for j in keep], is_gt[keep]))
    return out


def _fit_ltr(R, cands, seed, log):
    feats = []
    for bid, commit, files, cand, keys, lab in cands:
        par = files[files["parseable"]].reset_index(drop=True)
        R.graph(commit, par, [R.store.key(s, True) for s in par["blob_sha"]])
        f = R.features(bid, cand, keys)
        f["used_in_fix"] = lab.astype(float)
        f["bug_id"] = bid
        feats.append(f)
    if not feats:
        raise RuntimeError("FLIM: no training rows")
    train_df = pd.concat(feats, ignore_index=True)
    lo, hi = train_df[FEATURES].min(), train_df[FEATURES].max()
    span = (hi - lo).replace(0, 1.0)
    train_df[FEATURES] = (train_df[FEATURES] - lo) / span
    ranker = AdaptiveLTR(FEATURES, seed=seed, folds=2).fit(train_df)
    log(f"[FLIM]   LTR on {train_df.bug_id.nunique()} bugs / {len(train_df)} rows: {ranker.log}")
    return ranker, lo, span, train_df


def _score(R, bug_ids, ranker, lo, span, log=None, t0=None):
    out = []
    for i, bid in enumerate(bug_ids, 1):
        commit, files = R.files_of(bid)
        keys = [R.store.key(s, pz) for s, pz in zip(files["blob_sha"], files["parseable"])]
        par = files[files["parseable"]].reset_index(drop=True)
        R.graph(commit, par, [R.store.key(s, True) for s in par["blob_sha"]])
        f = (R.features(bid, files, keys) - lo) / span
        out.append(pd.DataFrame({"bug_id": bid, "path": files["path"].values,
                                 "score": ranker.predict(f).astype(np.float32)}))
        if log and i % 20 == 0:
            log(f"[FLIM]   scored {i}/{len(bug_ids)} bugs ({(time.time() - t0) / 60:.0f} min)")
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame(columns=["bug_id", "path", "score"])


def run_wp(repo: str, split: dict, kept: pd.DataFrame, seed: int, log=print):
    import torch
    from Scripts import lr_select
    from Scripts.repro import set_seed
    language = dict(kept.groupby("repo_name")["language"].first())[repo]
    R = _Run(repo, language, kept, log)
    rng = random.Random(seed)
    t0 = time.time()

    # TF-IDF space: the first training snapshot's ruleset files
    first = (split["train"] or split["test"])[0]
    _, f0 = R.files_of(first)
    f0 = f0[f0["in_ruleset"]]
    R.store.fit_vectorizer([p + "\n" + read_text(repo, s) for p, s in zip(f0["path"], f0["blob_sha"])])
    R.history = History(project_history(repo), R.store.vec)

    # encoder training pairs (independent of the LR)
    tr_pairs = _pairs(repo, split["train"], R.kk, R.store, rng)
    va_pairs = _pairs(repo, split["val"], R.kk, R.store, rng)

    # every file needed later, then one TF-IDF pass. Train snapshots: all
    # parseable files (LTR candidates are R & parseable; the import graph needs
    # every parseable file). Validation and test snapshots: all of T.
    for bid in split["train"]:
        _, files = R.files_of(bid)
        par = files[files["parseable"]]
        for p, s in zip(par["path"], par["blob_sha"]):
            R.store.add(p, s, True)
    for bid in split["val"] + split["test"]:
        _, files = R.files_of(bid)
        for p, s, pz in zip(files["path"], files["blob_sha"], files["parseable"]):
            R.store.add(p, s, bool(pz))
    R.store.finalize_tfidf()
    log(f"[FLIM]   store: {len(R.store.rec)} files, {len(R.store.U_txt)} units "
        f"({(time.time() - t0) / 60:.0f} min)")
    cands = _train_candidates(R, repo, split["train"], log)

    # LR grid (Scripts/lr_select.py): each LR -> encoder (epochs on val MRR, as
    # in run.py) -> embeddings -> LTR -> validation MAP; keep the best LR
    lrs = lr_select.grid("FLIM", split["fold"], repo, FLIM_LR_GRID)
    best = None
    runs = []
    for lr in lrs:
        set_seed(seed)
        R.encoder = CodeBERTEncoder()
        ft = R.encoder.fine_tune(tr_pairs, va_pairs, epochs=FINETUNE_EPOCHS,
                                 batch_size=FINETUNE_BATCH_SIZE, lr=lr,
                                 patience=PATIENCE, seed=seed, log=log)
        R.store.U_emb = None
        R.store.embed_units(R.encoder, log)
        ranker, lo, span, train_df = _fit_ltr(R, cands, seed, log)
        vmap = lr_select.validation_map(_score(R, split["val"], ranker, lo, span), repo) \
            if (len(lrs) > 1 and split["val"]) else float("nan")
        log(f"[FLIM] lr={lr:g}: best encoder epoch {ft['best_epoch']}"
            + (f", val MAP {vmap:.4f}" if np.isfinite(vmap) else ""))
        run = {"lr": lr, "val_map": vmap, "finetune": ft, "ltr": ranker.log}
        runs.append(run)
        if best is None or (np.isfinite(vmap) and vmap > best["run"]["val_map"]):
            best = {"run": run, "ranker": ranker, "lo": lo, "span": span, "train_df": train_df,
                    "U_emb": R.store.U_emb, "state": {k: v.detach().cpu().clone()
                                                      for k, v in R.encoder.model.state_dict().items()}}
        del R.encoder
        torch.cuda.empty_cache()
    if len(lrs) > 1:
        lr_select.record("FLIM", split["fold"], repo, best["run"]["lr"], seed, runs)
    R.encoder = CodeBERTEncoder()
    R.encoder.model.load_state_dict(best["state"])
    R.encoder.model.eval()
    R.store.U_emb = best["U_emb"]
    log(f"[FLIM] lr={best['run']['lr']:g} "
        f"({'selected on validation MAP' if len(lrs) > 1 else 'recorded choice'}); "
        f"{(time.time() - t0) / 60:.0f} min")

    # keep the trained model (Scripts/models.py) so more bugs can be scored later
    from Scripts import models as M
    md = M.model_dir("FLIM", split["fold"], seed, repo)
    torch.save(best["state"], os.path.join(md, "encoder.pt"))
    M.save_pickle(md, "ltr.pkl", {"ranker": best["ranker"], "lo": best["lo"], "span": best["span"],
                                  "vectorizer": R.store.vec, "features": FEATURES})
    M.save_meta(md, technique="FLIM", project=repo, fold=split["fold"], seed=seed,
                lr=best["run"]["lr"], best_epoch=best["run"]["finetune"]["best_epoch"], config=CONFIG)
    log(f"[FLIM] model saved -> {md}")

    # test: every file of universe T
    scores = _score(R, split["test"], best["ranker"], best["lo"], best["span"], log, t0)
    td = best["train_df"]
    info = {"selected_lr": best["run"]["lr"], "lr_grid_trained": list(lrs), "lr_runs": runs,
            "finetune": best["run"]["finetune"], "n_train_pairs": len(tr_pairs),
            "n_val_pairs": len(va_pairs), "n_files": len(R.store.rec), "n_units": len(R.store.U_txt),
            "ltr_rows": len(td), "ltr_bugs": int(td.bug_id.nunique()), "ltr": best["run"]["ltr"],
            "config": CONFIG}
    return scores, info
