"""
Reproducibility helpers: one seeding function used by every technique, and a
run manifest written next to every score file.
"""

import json
import os
import platform
import random
import subprocess
import sys
import time

import numpy as np


def set_seed(seed: int, deterministic: bool = True) -> None:
    """Seed python, numpy and torch (CPU + CUDA). Call once per run, before any
    model is built or any sampling happens."""
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        if deterministic:
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass


def _git_head(root: str) -> str:
    try:
        return subprocess.check_output(["git", "-C", root, "rev-parse", "HEAD"],
                                       text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "unknown"


def _versions() -> dict:
    out = {"python": sys.version.split()[0], "platform": platform.platform()}
    for mod in ("numpy", "pandas", "torch", "transformers", "bm25s", "sklearn",
                "tree_sitter", "tree_sitter_languages", "javalang"):
        try:
            m = __import__(mod)
            out[mod] = getattr(m, "__version__", "?")
        except Exception:
            pass
    try:
        import torch
        if torch.cuda.is_available():
            out["gpu"] = torch.cuda.get_device_name(0)
    except Exception:
        pass
    return out


def write_manifest(path: str, **fields) -> None:
    """Write a JSON manifest: code version, package versions, and whatever the
    caller passes (technique, seed, fold, hyper-parameters, epochs run, ...)."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    man = {
        "written_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "git_head": _git_head(root),
        "versions": _versions(),
        **fields,
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(man, f, indent=2, default=str)


def gpu_free_gib() -> float:
    """Free memory on GPU 0 in GiB (nvidia-smi); inf if no GPU is visible."""
    try:
        out = subprocess.check_output(["nvidia-smi", "--query-gpu=memory.free",
                                       "--format=csv,noheader,nounits"], text=True)
        return float(out.strip().splitlines()[0]) / 1024.0
    except Exception:
        return float("inf")


def wait_for_gpu(min_free_gib: float, log=print, poll_s: int = 120) -> None:
    """Block until at least `min_free_gib` GiB are free on the (shared) GPU."""
    free = gpu_free_gib()
    if free >= min_free_gib:
        return
    log(f"  waiting for GPU: {free:.1f} GiB free, need {min_free_gib:.0f} GiB "
        f"(other users' processes); polling every {poll_s}s")
    t0 = time.time()
    while free < min_free_gib:
        time.sleep(poll_s)
        free = gpu_free_gib()
    log(f"  GPU available after {(time.time() - t0) / 60:.0f} min ({free:.1f} GiB free)")
