"""
Adaptive pointwise learning-to-rank used by FLIM (Sec. 4.3: "we adopted the
pointwise LTR model proposed by Fejzer et al. (2021)"), ported from the
original code Resources/flim-main/train_adaptive.py (Adaptive_Process):

  1. 13 feature-weighting methods, each scored by 2-fold CV MAP; the best
     weight vector w gives a pre-score s = X @ w
  2. target = s + used_in_fix * max(s); 16 SGDRegressors (4 losses x 4
     penalties, alpha 1e-4) x 6 "cut" training-subset rules, each scored by
     2-fold CV MAP on the minimal reasonable set; the best is refit on all rows
  3. prediction = regressor(X)  (use_reg_model_always = True in the original)

Changes from the original, all mechanical or for correctness:
  * sklearn >= 1.2 names: loss "squared_loss" -> "squared_error",
    penalty "none" -> None
  * MAP in cross-validation uses expected ranks under random tie-breaking,
    and rows are shuffled within each bug (seeded) before fitting. The
    previous simplified ranker (src/flim/model.py) used a stable sort on rows
    that listed ground-truth files first, so a constant predictor scored MAP
    1.0, won selection, and FLIM output one score for every file.
  * no joblib parallelism inside (the experiment driver is already one
    process per run); n_jobs=-1 for the tree ensembles
"""

from itertools import product

import numpy as np
import pandas as pd
from scipy.stats import kruskal, levene, ttest_ind
from sklearn.decomposition import FastICA
from sklearn.ensemble import AdaBoostClassifier, ExtraTreesClassifier, GradientBoostingRegressor
from sklearn.feature_selection import VarianceThreshold, chi2, mutual_info_classif
from sklearn.linear_model import SGDRegressor
from sklearn.model_selection import KFold


def _norm(w):
    w = np.nan_to_num(np.asarray(w, float), nan=0.0, posinf=0.0, neginf=0.0)
    s = w.sum()
    return w / s if s > 0 else w


def _per_class(X, y, fn):
    out = []
    for c in X:
        a, b = X[c][y == 0], X[c][y == 1]
        try:
            out.append(abs(fn(a, b)[0]))
        except Exception:
            out.append(0.0)
    return np.array(out)


def w_chi2(df, cols, y, seed):          return _norm(chi2(df[cols].clip(lower=0), y)[0])
def w_mutual_info(df, cols, y, seed):   return _norm(mutual_info_classif(df[cols], y, discrete_features=False, random_state=seed))
def w_fastica(df, cols, y, seed):       return _norm(FastICA(n_components=1, random_state=seed, max_iter=400).fit(df[cols]).components_[0])
def w_variance(df, cols, y, seed):      return _norm(np.clip(VarianceThreshold().fit(df[cols]).variances_, 0, None))
def w_const(df, cols, y, seed):         return np.ones(len(cols)) * 0.5
def w_extra_trees(df, cols, y, seed):   return _norm(ExtraTreesClassifier(n_estimators=100, random_state=seed, n_jobs=-1).fit(df[cols], y).feature_importances_)
def w_gboost(df, cols, y, seed):        return _norm(GradientBoostingRegressor(n_estimators=100, random_state=seed).fit(df[cols], y).feature_importances_)
def w_adaboost(df, cols, y, seed):      return _norm(AdaBoostClassifier(n_estimators=100, random_state=seed).fit(df[cols], y).feature_importances_)
def w_kruskal(df, cols, y, seed):       return _norm(_per_class(df[cols], y, kruskal))
def w_ttest(df, cols, y, seed):         return _norm(_per_class(df[cols], y, lambda a, b: ttest_ind(a, b, equal_var=False)))
def w_levene(df, cols, y, seed):        return _norm(_per_class(df[cols], y, lambda a, b: levene(a, b, center="median")))


def w_mean_var(df, cols, y, seed):
    p, n = df[cols][y == 1], df[cols][y == 0]
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.nan_to_num(((p.var() / p.mean()) / (n.var() / n.mean())).values,
                             nan=0.0, posinf=0.0, neginf=0.0)


def w_mad(df, cols, y, seed):
    p = df[cols][y == 1]
    return np.mean(np.abs(p - p.max()), axis=0).values


WEIGHT_METHODS = [w_adaboost, w_extra_trees, w_gboost, w_const, w_variance, w_chi2,
                  w_mutual_info, w_fastica, w_kruskal, w_ttest, w_levene, w_mean_var, w_mad]


def sk_models(seed):
    losses = ["squared_error", "huber", "epsilon_insensitive", "squared_epsilon_insensitive"]
    penalties = [None, "l2", "l1", "elasticnet"]
    return [SGDRegressor(max_iter=1000, shuffle=False, loss=l, penalty=p, alpha=1e-4, random_state=seed)
            for l, p in product(losses, penalties)]


def cut_set(y, score, perc):
    """size_selectf_only_fixes_p: fixes + the perc*n_fixes lowest positive scores, score > 0."""
    s = pd.Series(score)
    ret = (y == 1)
    pos = s[s > 0]
    k = int(perc * ret.sum())
    if k > 0 and len(pos):
        ret = ret | (s <= pos.nsmallest(k).max()).values
    return ret & (s > 0).values


CUT_PERCS = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]


def tie_aware_map(bug, y, score) -> float:
    """MAP over bugs on the minimal reasonable set (rows scoring >= the lowest
    fix), with expected ranks under random tie-breaking."""
    aps = []
    d = pd.DataFrame({"b": bug, "y": y, "s": score})
    for _, g in d.groupby("b", sort=False):
        if g["y"].sum() == 0:
            continue
        s = np.sort(g["s"].values)
        n = len(s)
        q = g["s"].values[g["y"].values == 1]
        lo, hi = np.searchsorted(s, q, "left"), np.searchsorted(s, q, "right")
        ranks = np.sort((n - hi) + (hi - lo + 1) / 2.0)
        aps.append(float(np.mean(np.arange(1, len(ranks) + 1) / ranks)))
    return float(np.mean(aps)) if aps else 0.0


class AdaptiveLTR:
    def __init__(self, columns, seed=0, folds=2):
        self.columns, self.seed, self.folds = list(columns), seed, folds
        self.weights = None
        self.reg = None
        self.log = {}

    def _prep(self, df):
        rng = np.random.default_rng(self.seed)
        df = df.copy()
        df["_r"] = rng.random(len(df))
        bugs = pd.Series(df["bug_id"].unique())
        order = {b: i for i, b in enumerate(bugs.sample(frac=1.0, random_state=self.seed))}
        df["_b"] = df["bug_id"].map(order)
        return df.sort_values(["_b", "_r"]).reset_index(drop=True)

    def fit(self, df: pd.DataFrame):
        """df: columns + used_in_fix + bug_id."""
        df = self._prep(df)
        X, y, cols = df[self.columns], df["used_in_fix"].values.astype(int), self.columns
        kf = KFold(n_splits=self.folds, shuffle=False)
        splits = list(kf.split(df))

        best_w, best_name, best_w_map = None, None, -1.0
        for m in WEIGHT_METHODS:
            vals, ws = [], []
            for tr, te in splits:
                try:
                    w = m(df.iloc[tr], cols, y[tr], self.seed)
                    vals.append(tie_aware_map(df["bug_id"].values[te], y[te], X.values[te] @ w))
                    ws.append(w)
                except Exception:
                    vals.append(0.0)
            if ws and np.mean(vals) > best_w_map:
                best_w_map, best_name, best_w = float(np.mean(vals)), m.__name__, np.mean(ws, axis=0)
        self.weights = best_w if best_w is not None else w_const(df, cols, y, self.seed)
        self.log["weights_method"], self.log["weights_cv_map"] = best_name, best_w_map

        score = X.values @ self.weights
        target = score + y * np.max(score)
        best = (-1.0, None, None)
        for reg, perc in product(sk_models(self.seed), CUT_PERCS):
            vals = []
            for tr, te in splits:
                try:
                    cs = cut_set(y[tr], score[tr], perc)
                    if cs.sum() < 2:
                        vals.append(0.0); continue
                    reg.fit(X.values[tr][cs], target[tr][cs])
                    pred = reg.predict(X.values[te])
                    vals.append(tie_aware_map(df["bug_id"].values[te], y[te], pred))
                except Exception:
                    vals.append(0.0)
            if np.mean(vals) > best[0]:
                best = (float(np.mean(vals)), reg, perc)
        cv_map, reg, perc = best
        cs = cut_set(y, score, perc)
        self.reg = reg.fit(X.values[cs], target[cs]) if reg is not None and cs.sum() >= 2 else None
        self.log.update({"regressor": str(reg), "cut_perc": perc, "reg_cv_map": cv_map})
        return self

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        X = df[self.columns].values
        return self.reg.predict(X) if self.reg is not None else X @ self.weights
