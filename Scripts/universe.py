"""
The file universe: one table per pre-fix snapshot that every technique scores
and the evaluator ranks over. Replaces each technique's own candidate set
(BM25/FLIM used "blobs that have a BGE embedding", BLAZE used every blob in
the tree incl. images and jars).

Per snapshot (repo, commit), cached to data/obj2/universe/<stub>/<commit>.parquet:

  path, blob_sha, ext, size
  is_text      size <= MAX_BYTES and no NUL byte in the first 8 KB
  in_ruleset   classify_file(path, ext, "M", DEFAULT_TOGGLES).counts -- the
               same rule that defines Mono/Poly, so docs, changelog fragments,
               lockfiles, generated/vendored, CI, dev-tooling, binaries and
               unknown extensions are out
  language, category        from the ruleset
  parse_status, n_units     from src/parsing.py with the project-language parser

Two evaluation universes are derived from it:
  R (primary)      is_text & in_ruleset
  T (sensitivity)  is_text
Techniques score every T file; R is a mask applied by the evaluator.

Build ahead of the GPU runs (CPU, parallel per project):
    python Scripts/universe.py            # all six projects, all split bugs
"""

import os
import sys
from functools import lru_cache

import git
import pandas as pd
from git import Blob
from git.util import hex_to_bin

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Scripts import paths as P
from Scripts.classification_rules import DEFAULT_TOGGLES, classify_file
from src.parsing import PARSEABLE, parse_file, file_language

MAX_BYTES = 1_000_000
UNIVERSE_DIR = os.path.join(P.OBJ2_DATA_DIR, "universe")
LANG = dict(P.SELECTED_PROJECTS)


def _ext(path: str) -> str:
    base = path.rsplit("/", 1)[-1]
    return base.rsplit(".", 1)[-1].lower() if "." in base else ""


@lru_cache(maxsize=None)
def repo_obj(repo: str) -> git.Repo:
    return git.Repo(os.path.join(P.REPO_BASE_PATH, LANG[repo], repo.replace("/", "_")))


@lru_cache(maxsize=200_000)
def read_blob(repo: str, blob_sha: str) -> bytes:
    try:
        return Blob(repo_obj(repo), hex_to_bin(blob_sha)).data_stream.read()
    except Exception:
        return b""


def read_text(repo: str, blob_sha: str) -> str:
    return read_blob(repo, blob_sha).decode("utf-8", "replace")


# per-process memo of blob properties: (sha, is_project_lang) -> (is_text, status, n_units)
_PROPS: dict = {}


def _blob_props(repo: str, sha: str, size: int, path: str):
    plang = file_language(path, LANG[repo]) is not None
    key = (sha, plang)
    if key in _PROPS:
        return _PROPS[key]
    if size > MAX_BYTES:
        out = (False, "too_large", 0)
    else:
        data = read_blob(repo, sha)
        if b"\x00" in data[:8192]:
            out = (False, "binary", 0)
        else:
            pf = parse_file(path, data.decode("utf-8", "replace"), LANG[repo])
            out = (True, pf.status, len(pf.units))
    _PROPS[key] = out
    return out


def _cache_path(repo: str, commit: str) -> str:
    return os.path.join(UNIVERSE_DIR, repo.replace("/", "_"), f"{commit}.parquet")


def snapshot(repo: str, commit: str) -> pd.DataFrame:
    """Universe table for one pre-fix snapshot (built once, then cached)."""
    fp = _cache_path(repo, commit)
    if os.path.exists(fp):
        return pd.read_parquet(fp)
    rows = []
    for b in repo_obj(repo).commit(commit).tree.traverse():
        if b.type != "blob":
            continue
        path, ext = b.path, _ext(b.path)
        is_text, status, n_units = _blob_props(repo, b.hexsha, b.size, path)
        v = classify_file(path, ext, "M", DEFAULT_TOGGLES)
        rows.append((path, b.hexsha, ext, b.size, is_text, bool(v.counts and v.language),
                     v.language or "", v.category, status, n_units))
    df = pd.DataFrame(rows, columns=["path", "blob_sha", "ext", "size", "is_text", "in_ruleset",
                                     "language", "category", "parse_status", "n_units"])
    df["parseable"] = df["parse_status"].isin(PARSEABLE)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    df.to_parquet(fp, index=False)
    return df


def scored_files(repo: str, commit: str) -> pd.DataFrame:
    """The files every technique must score for a bug: universe T."""
    s = snapshot(repo, commit)
    return s[s["is_text"]].reset_index(drop=True)


def _build_project(repo: str) -> str:
    from Scripts.bugs import chrono_split, load_all
    k = load_all()
    k = k[k["repo_name"] == repo].set_index("bug_id")
    ids = set()
    for fold in (1, 2):
        s = chrono_split(repo, fold)
        ids |= (set(s["train"]) | set(s["val"]) | set(s["test"]) | set(s["test_removed"])
                | set(s["test_noprimary"]))
    commits = sorted({k.loc[b, "pre_fix_commit_sha"] for b in ids})
    for i, c in enumerate(commits, 1):
        snapshot(repo, c)
        if i % 50 == 0:
            print(f"  {repo}: {i}/{len(commits)} snapshots", flush=True)
    return f"{repo}: {len(commits)} snapshots"


if __name__ == "__main__":
    from multiprocessing import Pool
    repos = sys.argv[1:] or P.SELECTED_REPO_NAMES
    with Pool(min(len(repos), 6)) as pool:
        for msg in pool.imap_unordered(_build_project, repos):
            print(msg, flush=True)
