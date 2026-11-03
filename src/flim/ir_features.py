"""
IR features for FLIM's learning-to-rank step.

FLIM (Liang et al., EMSE 2022, Sec. 3.5, Eq. 5) fuses its 4 function-level
semantic features with "19 features commonly used in IRBL methods (Fejzer et
al. 2021)" -- the AdaptiveBL / Ye et al. set computed by the original code in
Resources/flim-main/calculate_buglocator_features.py. We implement 18 of them
for both Java and Python; f2 (API-enriched similarity) needs JDK API
documentation and has no Python counterpart, so it is dropped (stated in the
method section).

  f1   surface lexical similarity  max(cos(report, file), max_unit cos(report, unit))
  f3   collaborative filtering     cos(report, summaries of earlier reports that fixed the file)
  f4   class-name similarity       length of the longest class name in the report summary
  f5   bug-fixing recency          1 / (months since the file's last fix + 1)
  f6   bug-fixing frequency        number of earlier fixes of the file
  f7-f10   cos(summary,     class names | method names | variable names | comments)
  f11-f14  cos(description, class names | method names | variable names | comments)
  f15-f19  import-graph out-degree, in-degree, PageRank (alpha 0.9), HITS hub, authority

Lexical similarity uses one TF-IDF space per project (fitted on the first
training snapshot, split-only tokenizer src.bm25.tokenize -- deliberately NOT
BM25's identifier-keeping tokenizer, see src/bm25.py). History features use only bugs
fixed strictly before the query bug was reported. Files the project-language
parser cannot read get 0 for f7-f19 and the basename stem as their "class
name" for f4 -- the IR features that survive are exactly the type-agnostic ones.
"""

import os
import re
import sys
from collections import defaultdict

import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.bm25 import tokenize

IR_FEATURES = ["f1", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10",
               "f11", "f12", "f13", "f14", "f15", "f16", "f17", "f18", "f19"]
FIELDS = ("cls", "meth", "var", "com")


def make_vectorizer(docs: list) -> TfidfVectorizer:
    v = TfidfVectorizer(tokenizer=tokenize, lowercase=False, preprocessor=None,
                        token_pattern=None, sublinear_tf=True, min_df=1, dtype=np.float32)
    v.fit(docs)
    return v


def _vec(v: TfidfVectorizer, texts: list) -> sp.csr_matrix:
    return normalize(v.transform(texts), norm="l2", copy=False).tocsr()


# ---------------------------------------------------------------------------
# Import graph
# ---------------------------------------------------------------------------
def _java_index(paths_pkgs):
    """fully-qualified class name -> path; package -> [paths]."""
    fq, pkg = {}, defaultdict(list)
    for path, package in paths_pkgs:
        stem = path.rsplit("/", 1)[-1][:-5]
        fq[f"{package}.{stem}" if package else stem] = path
        pkg[package].append(path)
    return fq, pkg


def _resolve_java(imp: str, fq, pkg):
    if imp.endswith(".*"):
        base = imp[:-2]
        return pkg.get(base, []) or ([fq[base]] if base in fq else [])
    parts = imp.split(".")
    for i in range(len(parts), 0, -1):          # a.b.C.Inner / static a.b.C.m -> a.b.C
        cand = ".".join(parts[:i])
        if cand in fq:
            return [fq[cand]]
    return []


def _py_module(path: str) -> str:
    m = path[:-3].replace("/", ".")
    return m[:-9] if m.endswith(".__init__") else m


def _resolve_py(imp: str, src_path: str, by_last):
    if imp.startswith("."):                       # relative import
        level = len(imp) - len(imp.lstrip("."))
        base = _py_module(src_path).split(".")
        if not src_path.endswith("__init__.py"):
            base = base[:-1]
        base = base[: len(base) - (level - 1)] if level > 1 else base
        rest = imp.lstrip(".")
        imp = ".".join(base + ([rest] if rest else []))
    if not imp:
        return []
    last = imp.rsplit(".", 1)[-1]
    hits = [(m, p) for m, p in by_last.get(last, []) if m == imp or m.endswith("." + imp)]
    if not hits:
        return []
    return [min(hits, key=lambda x: len(x[0]))[1]]


def graph_features(files: pd.DataFrame, parsed: dict, language: str) -> dict:
    """path -> (out, in, pagerank, hub, authority) over the snapshot's import graph."""
    import networkx as nx
    src = files[files["parseable"]]
    G = nx.DiGraph()
    G.add_nodes_from(src["path"])
    if language == "java":
        fq, pkg = _java_index([(p, parsed[s].package) for p, s in zip(src["path"], src["blob_sha"])])
        for p, s in zip(src["path"], src["blob_sha"]):
            for imp in parsed[s].imports:
                for q in _resolve_java(imp, fq, pkg):
                    if q != p:
                        G.add_edge(p, q)
    else:
        by_last = defaultdict(list)
        for p in src["path"]:
            m = _py_module(p)
            by_last[m.rsplit(".", 1)[-1]].append((m, p))
        for p, s in zip(src["path"], src["blob_sha"]):
            for imp in parsed[s].imports:
                for q in _resolve_py(imp, p, by_last):
                    if q != p:
                        G.add_edge(p, q)
    if G.number_of_nodes() == 0:
        return {}
    pr = nx.pagerank(G, alpha=0.9)
    try:
        hub, auth = nx.hits(G, max_iter=1000)
    except Exception:
        hub = auth = {n: 0.0 for n in G}
    out_d, in_d = dict(G.out_degree()), dict(G.in_degree())
    return {n: (out_d[n], in_d[n], pr[n], hub[n], auth[n]) for n in G}


# ---------------------------------------------------------------------------
# History (f3, f5, f6)
# ---------------------------------------------------------------------------
class History:
    """Earlier fixes of the project, queried as of a report date."""

    def __init__(self, hist: pd.DataFrame, vec: TfidfVectorizer):
        self.h = hist.reset_index(drop=True)
        titles = [str(t).strip().split("\n", 1)[0] for t in self.h["bug_report_text"].fillna("")]
        self.T = _vec(vec, titles)
        self.fix_dates = self.h["fix_date"]          # tz-aware (UTC) Series
        self.files_by_row = list(self.h["files"])

    def features(self, report_vec, created, exclude_bug_id, paths) -> dict:
        """path -> (f3, f5, f6) for the given paths (zeros if never fixed before)."""
        mask = (self.h["fix_date"] < created).values & (self.h["bug_id"] != exclude_bug_id).values
        rows = np.nonzero(mask)[0]
        if len(rows) == 0:
            return {}
        want = set(paths)
        by_file = defaultdict(list)
        for r in rows:
            for f in self.files_by_row[r]:
                if f in want:
                    by_file[f].append(r)
        out = {}
        for f, rs in by_file.items():
            agg = normalize(self.T[rs].sum(axis=0).A, norm="l2")
            f3 = float(report_vec.dot(agg.T)[0, 0]) if report_vec.nnz else 0.0
            last = self.fix_dates.iloc[rs].max()
            months = max(0.0, (created - last).days / 30.44)
            out[f] = (f3, 1.0 / (months + 1.0), float(len(rs)))
        return out


def class_name_sim(summary: str, names: list) -> float:
    toks = {t.lower() for t in re.split(r"[^A-Za-z0-9_]+", summary) if t}
    best = 0
    for n in names:
        if n and n.lower() in toks:
            best = max(best, len(n))
    return float(best)
