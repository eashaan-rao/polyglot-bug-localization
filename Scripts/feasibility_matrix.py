"""
Step 2 — Architectural feasibility.

For each secondary file type that appears as a ground-truth localization target
in a kept Poly-fix bug, take real files of that type and record whether each
technique's ingestion path can build a representation of them:

  BM25   tokenise                          -> always succeeds (reference row)
  BLAZE  DynamicCodeSplitter               -> always succeeds (language-agnostic)
  FLIM   AST function extraction           -> structural_success | degraded_wholefile
  COOBA  AST -> graph (project's parser)   -> success | trivial_graph | parse_error

"trivial_graph" (a 1-node, 0-edge graph) is the silent architectural failure:
the technique returns *something* but it carries no structure.

CPU only. Output: results/obj2/feasibility_matrix.csv  (+ a readable pivot)

Run:  python Scripts/feasibility_matrix.py
"""

import json
import os
import subprocess
import sys
from collections import Counter, defaultdict

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Scripts import paths as P
from Scripts.classification_rules import (
    EXT_LANG, GRAMMAR_LANGUAGES, TIER1_SECONDARY, TIER2_SECONDARY,
)

N_PER_EXT = 25
LANG_DIR = dict(P.SELECTED_PROJECTS)                       # repo -> java/python
REPO_DIR = {r: os.path.join(P.REPO_BASE_PATH, l, r.replace("/", "_"))
            for r, l in P.SELECTED_PROJECTS}


def tier(lang):
    return "T1" if lang in TIER1_SECONDARY else ("T2" if lang in TIER2_SECONDARY else "T3")


def read_blob(repo_path, path, sha):
    """content of `path` at commit `sha` (fall back to working tree)."""
    try:
        return subprocess.run(["git", "-C", repo_path, "show", f"{sha}:{path}"],
                              capture_output=True, text=True, timeout=20,
                              errors="replace").stdout
    except Exception:
        pass
    fp = os.path.join(repo_path, path)
    if os.path.exists(fp):
        try:
            return open(fp, errors="replace").read()
        except Exception:
            return None
    return None


# ---- technique probes ----------------------------------------------------
def probe_bm25(content, _lang):
    import re
    toks = re.findall(r"[A-Za-z0-9_]+", content or "")
    return "success" if toks else "empty"


def probe_blaze(content, lang):
    from src.blaze.data_prep import DynamicCodeSplitter
    try:
        chunks = DynamicCodeSplitter(lang).split_text(content or "")
        return "success" if chunks else "empty"
    except Exception as e:
        return f"error:{type(e).__name__}"


def probe_flim(content, lang):
    from src.flim.pipeline import _extract_python_functions, _extract_java_functions
    try:
        funcs = (_extract_python_functions(content) if lang == "python"
                 else _extract_java_functions(content))
        # both fall back to [whole file] when nothing structural is found
        if len(funcs) == 1 and funcs[0].strip() == (content or "").strip():
            return "degraded_wholefile"
        return "structural_success" if funcs else "empty"
    except Exception as e:
        return f"error:{type(e).__name__}"


_COOBA_PARSERS = {}


def probe_cooba(content, lang):
    from src.cooba.ast_parsers import get_parser_for_language
    if lang not in _COOBA_PARSERS:
        p = get_parser_for_language(lang)
        p.glove_dict = {}
        _COOBA_PARSERS[lang] = p
    parser = _COOBA_PARSERS[lang]
    parser.node_counter = 0
    try:
        data = parser.parse(content or "")
        n_nodes = int(data.x.shape[0]) if data is not None and data.x is not None else 0
        n_edges = int(data.edge_index.shape[1]) if data is not None else 0
        if n_nodes <= 1 and n_edges == 0:
            return "trivial_graph"
        return "success"
    except Exception as e:
        return f"parse_error:{type(e).__name__}"


PROBES = {"BM25": probe_bm25, "BLAZE": probe_blaze, "FLIM": probe_flim, "COOBA": probe_cooba}


def main():
    df = pd.read_parquet(P.BUG_CLASSIFICATION_PARQUET)
    kept_poly = df[(df["keep"]) & (df["class"] == "Poly-fix")]
    long = pd.read_csv(os.path.join(P.OBJ2_DATA_DIR, "fix_files_long.csv"))

    # (ext -> list of (repo, path, sha)) restricted to files that are a secondary
    # ground-truth target of a kept Poly-fix bug
    want = set()
    for _, r in kept_poly.iterrows():
        want.add((r["repo_name"], r["fix_commit_sha"]))
    samples = defaultdict(list)
    seen_ext_repo = Counter()
    for _, r in long.iterrows():
        key = (r["repo_name"], r["fix_commit_sha"])
        if key not in want:
            continue
        ext = r["ext"]
        lang_cat = EXT_LANG.get(ext)
        if not lang_cat:
            continue
        lang, cat = lang_cat
        if lang not in GRAMMAR_LANGUAGES or cat == "source":
            continue
        if seen_ext_repo[(ext, r["repo_name"])] >= N_PER_EXT:
            continue
        seen_ext_repo[(ext, r["repo_name"])] += 1
        samples[ext].append((r["repo_name"], r["path"], r["fix_commit_sha"], lang))

    rows = []
    for ext, items in sorted(samples.items(), key=lambda kv: -len(kv[1])):
        lang = items[0][3]
        # group by the project language COOBA/FLIM would be configured for
        by_plang = defaultdict(list)
        for repo, path, sha, _l in items:
            by_plang[LANG_DIR[repo]].append((repo, path, sha))
        for plang, lst in by_plang.items():
            outcomes = {t: Counter() for t in PROBES}
            n_read = 0
            for repo, path, sha in lst:
                content = read_blob(REPO_DIR[repo], path, sha)
                if content is None:
                    continue
                n_read += 1
                for t, fn in PROBES.items():
                    outcomes[t][fn(content, plang)] += 1
            if not n_read:
                continue
            row = {"secondary_language": lang, "ext": ext, "tier": tier(lang),
                   "configured_parser_language": plang, "n_files": n_read}
            for t in PROBES:
                top = outcomes[t].most_common(1)[0][0]
                row[f"{t}_outcome"] = top
                row[f"{t}_detail"] = dict(outcomes[t])
            rows.append(row)

    out = pd.DataFrame(rows)
    out_path = os.path.join(P.RESULT_PATH, "feasibility_matrix.csv")
    out.drop(columns=[c for c in out.columns if c.endswith("_detail")]).to_csv(out_path, index=False)
    out.to_json(out_path.replace(".csv", "_detail.json"), orient="records", indent=2)

    print("FEASIBILITY MATRIX — dominant outcome per (file type x configured parser language)\n")
    print(f"{'sec.lang':12s} {'ext':10s} {'tier':4s} {'parser':7s} {'n':>4s}  "
          f"{'BM25':10s} {'BLAZE':10s} {'FLIM':20s} {'COOBA':16s}")
    for _, r in out.iterrows():
        print(f"{r['secondary_language']:12s} {r['ext']:10s} {r['tier']:4s} "
              f"{r['configured_parser_language']:7s} {r['n_files']:4d}  "
              f"{r['BM25_outcome']:10s} {r['BLAZE_outcome']:10s} "
              f"{r['FLIM_outcome']:20s} {r['COOBA_outcome']:16s}")

    print("\nReference (should all succeed): primary-language source files")
    for plang, exts in [("python", ["py"]), ("java", ["java"])]:
        repo = next(r for r, l in P.SELECTED_PROJECTS if l == plang)
        ex = long[(long.repo_name == repo) & (long.ext.isin(exts))].head(15)
        oc = {t: Counter() for t in PROBES}
        for _, r in ex.iterrows():
            c = read_blob(REPO_DIR[repo], r["path"], r["fix_commit_sha"])
            if c is None:
                continue
            for t, fn in PROBES.items():
                oc[t][fn(c, plang)] += 1
        print(f"  {plang:7s} .{exts[0]:6s} "
              + "  ".join(f"{t}={oc[t].most_common(1)[0][0]}" for t in PROBES))

    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
