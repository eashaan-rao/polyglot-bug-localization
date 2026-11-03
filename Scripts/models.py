"""
Where trained models are kept (decided 2026-11-01): every BLAZE and FLIM run
saves what is needed to score more bugs later without retraining, so a new
stratum or analysis never forces a re-run.

    data/obj2/models/<TECH>/fold<F>/seed<S>/<project>/
        BLAZE: model.pt (state dict), meta.json
        FLIM:  encoder.pt (CodeBERT state dict), ltr.pkl (ranker, feature
               min/span, TF-IDF vectorizer), meta.json

The driver sets OBJ2_CURRENT_TECH so a variant (e.g. BLAZE_ALL) saves under
its own name.
"""

import json
import os
import pickle
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Scripts import paths as P

MODELS_DIR = os.path.join(P.OBJ2_DATA_DIR, "models")


def model_dir(default_tech: str, fold: int, seed: int, repo: str) -> str:
    tech = os.environ.get("OBJ2_CURRENT_TECH", default_tech)
    sfx = "_smoke" if os.environ.get("OBJ2_SMOKE") == "1" else ""
    d = os.path.join(MODELS_DIR + sfx, tech, f"fold{fold}", f"seed{seed}", repo.replace("/", "_"))
    os.makedirs(d, exist_ok=True)
    return d


def save_meta(d: str, **meta) -> None:
    with open(os.path.join(d, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2, default=str)


def save_pickle(d: str, name: str, obj) -> None:
    with open(os.path.join(d, name), "wb") as f:
        pickle.dump(obj, f)
