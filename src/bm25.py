"""
BM25 — the classical IR baseline. Scores every file of universe T for each
test bug; the evaluator applies the R / parse masks.

Configuration (fixed before any result was seen; not tuned on test):
  bm25s 0.3.11, method="lucene", k1=1.2, b=0.75 (Lucene defaults)
  tokens: split on non-alphanumerics; every compound identifier is kept whole
          AND split at camelCase boundaries (IndexRecoveryIT -> indexrecoveryit,
          index, recovery, it); lowercase; English stop words removed (bm25s
          STOPWORDS_EN); no stemming. Keeping the whole identifier is the usual
          IR-based bug-localization preprocessing; the first version dropped it,
          which pushed files named in the report to ranks 200-800 on
          elasticsearch (fixed 2026-11-03 before the full run).
  document = path tokens + file text; query = bug report title + body
  one index per pre-fix snapshot (IDF from that snapshot)
"""

import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Scripts.universe import read_text, scored_files

K1, B, METHOD = 1.2, 0.75, "lucene"
_SPLIT = re.compile(r"[^A-Za-z0-9]+")
_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
_STOP = None


def _stopwords():
    global _STOP
    if _STOP is None:
        from bm25s.stopwords import STOPWORDS_EN
        _STOP = set(STOPWORDS_EN)
    return _STOP


def tokenize_identifiers(text: str) -> list:
    """BM25's tokenizer: whole compound identifiers plus their camelCase parts."""
    stop = _stopwords()
    out = []
    for part in _SPLIT.split(text or ""):
        if not part:
            continue
        subs = [t.lower() for t in _CAMEL.split(part) if t]
        if len(subs) > 1:
            out.append(part.lower())
        out.extend(t for t in subs if t not in stop)
    return out


def tokenize(text: str) -> list:
    """Split-only tokenizer, kept UNCHANGED for FLIM's IR features (its saved
    TF-IDF vectorizers reference this function by name). Not used by BM25."""
    global _STOP
    if _STOP is None:
        from bm25s.stopwords import STOPWORDS_EN
        _STOP = set(STOPWORDS_EN)
    out = []
    for part in _SPLIT.split(text or ""):
        for t in _CAMEL.split(part):
            t = t.lower()
            if t and t not in _STOP:
                out.append(t)
    return out


def run_wp(repo: str, split: dict, kept: pd.DataFrame, seed: int, log=print) -> pd.DataFrame:
    import bm25s
    kk = kept[kept["repo_name"] == repo].set_index("bug_id")
    doc_cache: dict = {}
    rows = []
    for i, bug_id in enumerate(split["test"], 1):
        meta = kk.loc[bug_id]
        files = scored_files(repo, meta["pre_fix_commit_sha"])
        docs = []
        for path, sha in zip(files["path"], files["blob_sha"]):
            if sha not in doc_cache:
                doc_cache[sha] = tokenize_identifiers(read_text(repo, sha))
            docs.append(tokenize_identifiers(path) + doc_cache[sha])
        retr = bm25s.BM25(k1=K1, b=B, method=METHOD)
        retr.index(docs, show_progress=False)
        q = tokenize_identifiers(meta["bug_report_text"])
        sc = retr.get_scores(q) if q else np.zeros(len(docs), np.float32)
        rows.append(pd.DataFrame({"bug_id": bug_id, "path": files["path"].values,
                                  "score": np.asarray(sc, np.float32)}))
        if i % 25 == 0:
            log(f"  BM25 {repo}: {i}/{len(split['test'])}")
    return pd.concat(rows, ignore_index=True)


CONFIG = {"k1": K1, "b": B, "method": METHOD, "stopwords": "bm25s.STOPWORDS_EN",
          "tokenizer": "tokenize_identifiers (whole identifier + camelCase parts)",
          "stemming": None, "document": "path tokens + text", "query": "title + body"}
