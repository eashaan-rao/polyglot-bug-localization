"""
CodeBERT bi-encoder for FLIM, following the original FLIM fine-tuning code
(Resources/flim-main/CodeBERT-finetune/run.py and cal_vec.py):

  * microsoft/codebert-base, embedding = pooler output (encoder(...)[1])
  * NL truncated to 128 tokens, code to 256 tokens (README: --nl_length 128
    --code_length 256)
  * loss: in-batch softmax cross-entropy over the NL x code dot-product matrix
    (each report's positive function vs the other functions in the batch)
  * AdamW(lr 2e-5, eps 1e-8), linear schedule without warm-up, batch 32,
    10 epochs (README: --num_train_epochs 10 --learning_rate 2e-5)
  * model selection: the epoch with the best validation MRR is kept (run.py
    saves checkpoint-best-mrr). We add early stopping with patience 3 on that
    same criterion -- the same patience BLAZE uses -- which only saves time.

One deviation, stated in the method: when one report contributes several
positive functions, the other positives of the same report are masked out of
its row of the logit matrix, so they are not treated as negatives.

The earlier implementation used BCEWithLogitsLoss(cosine, label): a cosine in
[-1, 1] used as a logit can only reach sigmoid values in [0.27, 0.73], the loss
has a floor near 0.5, and the embeddings collapsed (top elasticsearch scores
all ~0.996). It is replaced entirely.
"""

import copy
import math

import numpy as np
import torch
import torch.nn as nn
from tqdm import tqdm
from transformers import AutoModel, AutoTokenizer, get_linear_schedule_with_warmup

CODEBERT_MODEL_NAME = "microsoft/codebert-base"
NL_LENGTH = 128
CODE_LENGTH = 256


class CodeBERTEncoder:
    def __init__(self, model_name: str = CODEBERT_MODEL_NAME, device: str | None = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()
        self.history: list = []        # per-epoch {epoch, train_loss, val_mrr}
        self.best_epoch: int | None = None

    # ------------------------------------------------------------------ #
    def _batch_ids(self, texts: list, max_len: int):
        enc = self.tokenizer(texts, padding=True, truncation=True, max_length=max_len,
                             return_tensors="pt")
        return enc["input_ids"].to(self.device), enc["attention_mask"].to(self.device)

    def _embed(self, ids, mask):
        return self.model(input_ids=ids, attention_mask=mask)[1]   # pooler output

    @torch.no_grad()
    def encode(self, texts: list, kind: str, batch_size: int = 256) -> np.ndarray:
        """kind: 'nl' (128 tokens) or 'code' (256 tokens). Returns float16 (n, 768)."""
        self.model.eval()
        max_len = NL_LENGTH if kind == "nl" else CODE_LENGTH
        out = []
        order = np.argsort([len(t) for t in texts])           # length-bucketing
        for i in range(0, len(texts), batch_size):
            idx = order[i:i + batch_size]
            ids, mask = self._batch_ids([texts[j] or " " for j in idx], max_len)
            with torch.autocast(device_type="cuda", dtype=torch.float16,
                                enabled=self.device == "cuda"):
                e = self._embed(ids, mask)
            out.append((idx, e.float().cpu().numpy().astype(np.float16)))
        res = np.zeros((len(texts), self.model.config.hidden_size), np.float16)
        for idx, e in out:
            res[idx] = e
        return res

    # ------------------------------------------------------------------ #
    def _val_mrr(self, val_pairs: list) -> float:
        """run.py-style: each validation report ranks its positive among all
        validation functions (dot product of pooler embeddings)."""
        if not val_pairs:
            return float("nan")
        nl = self.encode([p[1] for p in val_pairs], "nl").astype(np.float32)
        code = self.encode([p[2] for p in val_pairs], "code").astype(np.float32)
        group = np.array([p[0] for p in val_pairs])
        s = nl @ code.T
        rr = []
        for i in range(len(val_pairs)):
            row = s[i].copy()
            same = group == group[i]
            same[i] = False
            row[same] = -np.inf            # other positives of the same report are not negatives
            rr.append(1.0 / (1 + int((row > row[i]).sum())))
        return float(np.mean(rr))

    def fine_tune(self, train_pairs: list, val_pairs: list, epochs: int = 10,
                  batch_size: int = 32, lr: float = 2e-5, patience: int = 3,
                  seed: int = 0, log=print) -> dict:
        """
        train_pairs / val_pairs: [(group_id, report_text, function_text)], one
        row per positive (report, function) pair; group_id identifies the bug.
        """
        g = torch.Generator().manual_seed(seed)
        n = len(train_pairs)
        steps_per_epoch = math.ceil(n / batch_size)
        opt = torch.optim.AdamW(self.model.parameters(), lr=lr, eps=1e-8)
        sch = get_linear_schedule_with_warmup(opt, 0, steps_per_epoch * epochs)
        ce = nn.CrossEntropyLoss()
        scaler = torch.amp.GradScaler("cuda", enabled=self.device == "cuda")
        best_mrr, best_state, bad = -1.0, None, 0
        log(f"[FLIM-enc] fine-tuning on {n} positive pairs, val {len(val_pairs)}; "
            f"{steps_per_epoch} steps/epoch, max {epochs} epochs")

        for ep in range(1, epochs + 1):
            self.model.train()
            perm = torch.randperm(n, generator=g).tolist()
            tot, k = 0.0, 0
            for i in tqdm(range(0, n, batch_size), desc=f"  FLIM epoch {ep}", leave=False):
                b = [train_pairs[j] for j in perm[i:i + batch_size]]
                if len(b) < 2:
                    continue
                nl_ids, nl_m = self._batch_ids([x[1] for x in b], NL_LENGTH)
                cd_ids, cd_m = self._batch_ids([x[2] for x in b], CODE_LENGTH)
                with torch.autocast(device_type="cuda", dtype=torch.float16,
                                    enabled=self.device == "cuda"):
                    nl_v = self._embed(nl_ids, nl_m)
                    cd_v = self._embed(cd_ids, cd_m)
                    scores = (nl_v.float() @ cd_v.float().t())
                grp = torch.tensor([x[0] for x in b], device=self.device)
                same = (grp[:, None] == grp[None, :]) & ~torch.eye(len(b), dtype=torch.bool,
                                                                   device=self.device)
                scores = scores.masked_fill(same, float("-inf"))
                loss = ce(scores, torch.arange(len(b), device=self.device))
                opt.zero_grad(set_to_none=True)
                scaler.scale(loss).backward()
                scaler.unscale_(opt)
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                scaler.step(opt)
                scaler.update()
                sch.step()
                tot += loss.item(); k += 1
            mrr = self._val_mrr(val_pairs)
            self.history.append({"epoch": ep, "train_loss": tot / max(k, 1), "val_mrr": mrr})
            log(f"[FLIM-enc]   epoch {ep}: train_loss={tot / max(k, 1):.4f}  val_mrr={mrr:.4f}")
            if np.isnan(mrr):                      # no validation pairs: keep the last epoch
                self.best_epoch = ep
                best_state = None
                continue
            if mrr > best_mrr:
                best_mrr, bad, self.best_epoch = mrr, 0, ep
                best_state = copy.deepcopy({k_: v.detach().cpu() for k_, v in self.model.state_dict().items()})
            else:
                bad += 1
                if bad >= patience:
                    log(f"[FLIM-enc]   early stop after epoch {ep} (best epoch {self.best_epoch})")
                    break
        if best_state is not None:
            self.model.load_state_dict(best_state)
        self.model.eval()
        return {"epochs_run": len(self.history), "best_epoch": self.best_epoch,
                "best_val_mrr": best_mrr, "history": self.history}
