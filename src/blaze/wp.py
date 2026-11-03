"""
BLAZE — within-project, full-snapshot (Objective 2).

Chakraborty et al., TSE 2025, reimplemented against the original code in
Resources/BLAZE/15122980/Blaze (config blaze/embedding/config/main-sage.yaml,
utils/convert_to_chunks.py):

  backbone      codesage/codesage-small, FULL fine-tuning (configure_optimizers
                uses every parameter), mean pooling, 2-layer residual adapters
                per modality, embedding dim 1024
  inputs        report <= 1024 tokens, code chunk <= 512 tokens
  chunks        dynamic programming over tree-sitter class / function
                boundaries, general_cost 50, max_window_size 30 lines
  training data (report, chunk) pairs for every chunk of every ground-truth file
                whose extension is the project language (.py / .java) --
                convert_to_chunks.py keeps only those
  loss          NTXent with hard-example scaling, tau 0.3 (NTXentlossImplemented)
  optimiser     AdamW lr 2e-7, weight decay 0.01, linear warm-up 100 steps,
                grad-norm 1.0, batch 20
  epochs        15 (paper, Sec. III-E); model selection on validation loss
                (ModelCheckpoint(monitor="val_loss")), patience 3

Departures, stated in the method: hard examples are weighted in-batch by the
loss (the paper's GPT-mined hard-example set is BeetleBox-specific and not
reproducible within project); comments are not stripped before chunking.

LR: the paper's 2e-7 was set for ~11 K training bugs; our per-project
training sets are 20-50x smaller. Each LR of LR_GRID is trained (epochs selected
on validation loss, as in the original) and the LR with the highest
**validation MAP** is kept -- the shared rule in Scripts/lr_select.py, also used
for FLIM. The choice is made with the first seed and reused by later seeds (selection on
validation only, reported in the manifest).

Scoring: every universe-T file is chunked (dynamic chunking for the project
language, fixed 30-line windows otherwise) and scored by the max cosine of
its chunk embeddings with the report embedding.
"""

import copy
import math
import os
import random
import sys
import time

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
import transformers

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Scripts.bugs import eval_ground_truth
from Scripts.universe import read_text, scored_files, snapshot
from src.blaze.data_prep import DynamicCodeSplitter, _fallback_chunk
from src.blaze.model import BlazeEmbedding, NTXentLoss
from src.parsing import file_language

BACKBONE = "codesage/codesage-small"
REVISION = "4d2a4f3fa73a3c8a4dd59dba2712202f1f54e109"
DIM = 1024
REPORT_MAX_LEN, CODE_MAX_LEN = 1024, 512
RESIDUAL_LAYERS = 2
EPOCHS = 15
BATCH = 20
LR_GRID = tuple(float(x) for x in os.environ.get("BLAZE_LR_GRID", "2e-7,2e-6,2e-5").split(","))
WARMUP_STEPS = 100
WEIGHT_DECAY = 0.01
PATIENCE = 3
TAU, HARD_NEG, HARD_POS, POS_SCALE = 0.3, 1.2, 1.2, 1.001
FALLBACK_LINES = 30
MAX_CHUNKS_PER_FILE = 200
EVAL_BATCH = 64

CONFIG = {"backbone": BACKBONE, "revision": REVISION, "full_finetune": True,
          "report_max_len": REPORT_MAX_LEN, "code_max_len": CODE_MAX_LEN, "epochs_max": EPOCHS,
          "batch": BATCH, "lr_grid": LR_GRID, "warmup_steps": WARMUP_STEPS,
          "weight_decay": WEIGHT_DECAY, "patience": PATIENCE,
          "selection": "epochs: val loss; LR: val MAP (Scripts/lr_select.py)",
          "tau": TAU, "chunking": "dynamic (general_cost 50, window 30)",
          "max_chunks_per_file": MAX_CHUNKS_PER_FILE}


def _chunks(path, text, project_language, splitters):
    lang = file_language(path, project_language)
    if lang is None:
        ch = _fallback_chunk(text, FALLBACK_LINES)
    else:
        if lang not in splitters:
            splitters[lang] = DynamicCodeSplitter(language=lang)
        ch = splitters[lang].split_text(text)
    ch = [c for c in ch if c.strip()]
    return (ch or [text[:2000] or " "])[:MAX_CHUNKS_PER_FILE]


def train_all_files() -> bool:
    """Ablation BLAZE_ALL (decided 2026-11-01): train on chunks of EVERY fix
    file (YAML, JSON, SQL, ...), not only project-language ones. Tests whether
    the weak ranking of secondary files is a training-data (semantic) limit.
    Read at call time: one driver process can run BLAZE and BLAZE_ALL."""
    return os.environ.get("BLAZE_TRAIN_ALL_FILES") == "1"


def _samples(repo, bug_ids, kk, language, splitters):
    """[(issue_int, chunk, report)] -- all chunks of source-language GT files
    (original BLAZE), or of every text GT file under the BLAZE_ALL ablation."""
    all_files = train_all_files()
    out = []
    for gi, bid in enumerate(bug_ids):
        meta = kk.loc[bid]
        snap = snapshot(repo, meta["pre_fix_commit_sha"]).set_index("path")
        for g in eval_ground_truth(repo, bid):
            p = g["pre_path"]
            if p is None or p not in snap.index or not snap.at[p, "is_text"]:
                continue
            if not all_files and file_language(p, language) is None:   # .py / .java only
                continue
            for c in _chunks(p, read_text(repo, snap.at[p, "blob_sha"]), language, splitters):
                out.append((gi, c, meta["bug_report_text"]))
    return out


def _batches(samples, rng=None):
    idx = list(range(len(samples)))
    if rng is not None:
        rng.shuffle(idx)
    for i in range(0, len(idx), BATCH):
        b = [samples[j] for j in idx[i:i + BATCH]]
        if len(b) >= 2:
            yield b


def _loss(model, loss_fn, b, device):
    with torch.autocast(device_type="cuda", dtype=torch.bfloat16, enabled=device == "cuda"):
        out = model([x[2] for x in b], [x[1] for x in b])
    lab = torch.tensor([x[0] for x in b], device=device)
    return loss_fn(out["report"].float(), out["code"].float(), lab)


@torch.no_grad()
def _val_loss(model, loss_fn, samples, device):
    """Mean NTXent over validation batches. Batches are shuffled with a FIXED
    seed: identical across epochs (comparable) and mixed across bugs like the
    training batches. Unshuffled batches hold chunks of one or two bugs, almost
    every pair is a positive, and the loss collapses towards 0 (0.21 vs a
    training loss of 2.35 in the first smoke run) -- useless for selection."""
    model.eval()
    tot, n = 0.0, 0
    for b in _batches(samples, random.Random(0)):
        tot += _loss(model, loss_fn, b, device).item(); n += 1
    return tot / n if n else float("nan")


def _train_one_lr(lr, tr, va, seed, device, log):
    torch.manual_seed(seed)
    model = BlazeEmbedding(model_name=BACKBONE, dimension=DIM, max_length=CODE_MAX_LEN,
                           residual_layers=RESIDUAL_LAYERS, report_prefix="", source_prefix="",
                           report_max_length=REPORT_MAX_LEN, trust_remote_code=True,
                           revision=REVISION, tokenizer_kwargs={"add_eos_token": True}).to(device)
    loss_fn = NTXentLoss(tau=TAU, hard_negative_scale=HARD_NEG,
                         hard_positive_scale=HARD_POS, positive_scale=POS_SCALE)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=WEIGHT_DECAY)
    steps = max(1, math.ceil(len(tr) / BATCH)) * EPOCHS
    sch = transformers.get_linear_schedule_with_warmup(opt, min(WARMUP_STEPS, steps // 10 or 1), steps)
    rng = random.Random(seed)
    hist, best, best_state, best_ep, bad = [], float("inf"), None, None, 0
    v0 = _val_loss(model, loss_fn, va, device)
    log(f"[BLAZE] lr={lr:g}: {len(tr)} train / {len(va)} val chunks, epoch 0 val_loss={v0:.4f}")
    for ep in range(1, EPOCHS + 1):
        model.train()
        tot, n = 0.0, 0
        for b in _batches(tr, rng):
            loss = _loss(model, loss_fn, b, device)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step(); sch.step()
            tot += loss.item(); n += 1
        vl = _val_loss(model, loss_fn, va, device)
        hist.append({"epoch": ep, "train_loss": tot / max(n, 1), "val_loss": vl})
        log(f"[BLAZE]   lr={lr:g} epoch {ep}: train_loss={tot / max(n, 1):.4f}  val_loss={vl:.4f}")
        if np.isnan(vl) or vl < best:
            best, best_ep, bad = (vl if not np.isnan(vl) else best), ep, 0
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        else:
            bad += 1
            if bad >= PATIENCE:
                log(f"[BLAZE]   early stop after epoch {ep} (best epoch {best_ep})")
                break
    model.load_state_dict(best_state)
    return model, {"lr": lr, "val_loss_epoch0": v0, "best_val_loss": best,
                   "best_epoch": best_ep, "epochs_run": len(hist), "history": hist}


@torch.no_grad()
def _encode_chunks(model, texts, device):
    model.eval()
    out = []
    order = np.argsort([len(t) for t in texts])
    res = np.zeros((len(texts), DIM), np.float16)
    for i in range(0, len(texts), EVAL_BATCH):
        idx = order[i:i + EVAL_BATCH]
        with torch.autocast(device_type="cuda", dtype=torch.bfloat16, enabled=device == "cuda"):
            e = model.get_source_embedding([texts[j] for j in idx])
        res[idx] = F.normalize(e.float(), dim=1).cpu().numpy().astype(np.float16)
    return res


def _score_bugs(model, bug_ids, kk, repo, language, splitters, device, cache, log=None, t0=None):
    """Score every universe-T file of each bug: max cosine of its chunk
    embeddings with the report embedding. Chunk embeddings cached by sha."""
    out = []
    for i, bid in enumerate(bug_ids, 1):
        files = scored_files(repo, kk.loc[bid, "pre_fix_commit_sha"])
        new = [(p, s) for p, s in zip(files["path"], files["blob_sha"]) if s not in cache]
        texts, owner = [], []
        for p, s in dict((s, (p, s)) for p, s in new).values():
            ch = _chunks(p, read_text(repo, s), language, splitters)
            texts.extend(ch); owner.extend([s] * len(ch))
        if texts:
            E = _encode_chunks(model, texts, device)
            owner = np.array(owner)
            for s in np.unique(owner):
                cache[s] = E[owner == s]
        with torch.no_grad(), torch.autocast(device_type="cuda", dtype=torch.bfloat16,
                                             enabled=device == "cuda"):
            q = model.get_report_embedding([kk.loc[bid, "bug_report_text"]])
        q = F.normalize(q.float(), dim=1).cpu().numpy()[0].astype(np.float32)
        sc = np.array([float((cache[s].astype(np.float32) @ q).max()) for s in files["blob_sha"]],
                      np.float32)
        out.append(pd.DataFrame({"bug_id": bid, "path": files["path"].values, "score": sc}))
        if log and i % 20 == 0:
            log(f"[BLAZE]   scored {i}/{len(bug_ids)} bugs "
                f"({len(cache)} files cached, {(time.time() - t0) / 60:.0f} min)")
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame(columns=["bug_id", "path", "score"])


def run_wp(repo: str, split: dict, kept: pd.DataFrame, seed: int, log=print):
    from Scripts import lr_select
    device = "cuda" if torch.cuda.is_available() else "cpu"
    language = dict(kept.groupby("repo_name")["language"].first())[repo]
    kk = kept[kept["repo_name"] == repo].set_index("bug_id")
    splitters: dict = {}
    t0 = time.time()
    tr = _samples(repo, split["train"], kk, language, splitters)
    va = _samples(repo, split["val"], kk, language, splitters)

    if train_all_files():
        # the ablation reuses the LR selected for the main BLAZE run, so the
        # only difference is the training data
        rec = lr_select.recorded("BLAZE", split["fold"], repo)
        if rec is None:
            raise RuntimeError("BLAZE_ALL needs the main BLAZE run of this project/fold first")
        lrs = (rec,)
    else:
        lrs = lr_select.grid("BLAZE", split["fold"], repo, LR_GRID)
    runs = []
    for lr in lrs:
        model, info = _train_one_lr(lr, tr, va, seed, device, log)
        if len(lrs) > 1 and split["val"]:
            vs = _score_bugs(model, split["val"], kk, repo, language, splitters, device, {})
            info["val_map"] = lr_select.validation_map(vs, repo)
            log(f"[BLAZE] lr={lr:g}: best val_loss {info['best_val_loss']:.4f}, "
                f"val MAP {info['val_map']:.4f}")
        runs.append((-info.get("val_map", 0.0), lr, model, info))
        if len(lrs) > 1:
            model.cpu()
    runs.sort(key=lambda x: x[0])
    _, lr, model, info = runs[0]
    if len(lrs) > 1 and not train_all_files():
        lr_select.record("BLAZE", split["fold"], repo, lr, seed, [r[3] for r in runs])
    for r in runs[1:]:
        del r
    model.to(device)
    torch.cuda.empty_cache()
    log(f"[BLAZE] lr={lr:g} ({'selected on validation MAP' if len(lrs) > 1 else 'recorded choice'}; "
        f"best val_loss {info['best_val_loss']:.4f}, epoch {info['best_epoch']}); "
        f"training {(time.time() - t0) / 60:.1f} min")

    # keep the trained model (Scripts/models.py) so more bugs can be scored later
    from Scripts import models as M
    md = M.model_dir("BLAZE", split["fold"], seed, repo)
    torch.save({k: v.detach().cpu() for k, v in model.state_dict().items()}, os.path.join(md, "model.pt"))
    M.save_meta(md, technique=os.environ.get("OBJ2_CURRENT_TECH", "BLAZE"), project=repo,
                fold=split["fold"], seed=seed, lr=lr, best_epoch=info["best_epoch"],
                train_all_files=train_all_files(), config=CONFIG)
    log(f"[BLAZE] model saved -> {md}")

    scores = _score_bugs(model, split["test"], kk, repo, language, splitters, device, {}, log, t0)
    info = {**info, "selected_lr": lr, "lr_grid_trained": list(lrs),
            "lr_runs": [r[3] for r in runs] if len(runs) > 1 else None,
            "n_train_chunks": len(tr), "n_val_chunks": len(va), "config": CONFIG}
    return scores, info
