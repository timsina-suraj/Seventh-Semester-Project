"""A single CART (Classification And Regression Tree) implementation, built
from scratch on top of numpy array ops only (no scikit-learn / xgboost).

Shared by DecisionTree, RandomForest, and GradientBoosting in this package —
regression trees split on variance reduction, classification trees split on
information gain (entropy).
"""
from __future__ import annotations

import numpy as np


class _Node:
    __slots__ = ("feature_index", "threshold", "left", "right", "value")

    def __init__(self, feature_index=None, threshold=None, left=None, right=None, value=None):
        self.feature_index = feature_index
        self.threshold = threshold
        self.left = left
        self.right = right
        self.value = value  # leaf prediction (float for regression, dict of class->prob for classification)

    @property
    def is_leaf(self) -> bool:
        return self.value is not None


def _variance(y: np.ndarray) -> float:
    if len(y) == 0:
        return 0.0
    return float(np.var(y))


def _entropy(y: np.ndarray, n_classes: int) -> float:
    if len(y) == 0:
        return 0.0
    counts = np.bincount(y, minlength=n_classes)
    probs = counts / len(y)
    probs = probs[probs > 0]
    return float(-np.sum(probs * np.log2(probs)))


class CARTTree:
    """One CART tree that can operate in 'regression' or 'classification' mode.

    Parameters
    ----------
    task: 'regression' | 'classification'
    max_depth: maximum recursion depth
    min_samples_split: minimum samples required to attempt a split
    max_features: if set, only this many randomly-chosen features are
        considered per split (used by Random Forest for de-correlation)
    n_classes: required for classification mode
    """

    def __init__(
        self,
        task: str = "regression",
        max_depth: int = 8,
        min_samples_split: int = 4,
        max_features: int | None = None,
        n_classes: int | None = None,
        random_state: int | None = None,
    ):
        assert task in ("regression", "classification")
        self.task = task
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.max_features = max_features
        self.n_classes = n_classes
        self.root: _Node | None = None
        self._rng = np.random.RandomState(random_state)

    # -- fitting -----------------------------------------------------------

    def fit(self, X: np.ndarray, y: np.ndarray) -> "CARTTree":
        X = np.asarray(X, dtype=float)
        if self.task == "classification":
            y = np.asarray(y, dtype=int)
            if self.n_classes is None:
                self.n_classes = int(y.max()) + 1
            assert self.n_classes is not None
        else:
            y = np.asarray(y, dtype=float)
        self.root = self._grow(X, y, depth=0)
        return self

    def _leaf_value(self, y: np.ndarray):
        if self.task == "regression":
            return float(np.mean(y)) if len(y) else 0.0
        assert self.n_classes is not None
        counts = np.bincount(y, minlength=self.n_classes).astype(float)
        total = counts.sum()
        probs = counts / total if total > 0 else np.ones(self.n_classes) / self.n_classes
        return probs

    def _impurity(self, y: np.ndarray) -> float:
        if self.task == "regression":
            return _variance(y)
        assert self.n_classes is not None
        return _entropy(y, self.n_classes)

    def _grow(self, X: np.ndarray, y: np.ndarray, depth: int) -> _Node:
        n_samples, n_features = X.shape

        if (
            depth >= self.max_depth
            or n_samples < self.min_samples_split
            or (self.task == "classification" and len(np.unique(y)) == 1)
            or (self.task == "regression" and _variance(y) <= 1e-12)
        ):
            return _Node(value=self._leaf_value(y))

        best = self._best_split(X, y)
        if best is None:
            return _Node(value=self._leaf_value(y))

        feature_index, threshold, left_mask = best
        right_mask = ~left_mask

        left = self._grow(X[left_mask], y[left_mask], depth + 1)
        right = self._grow(X[right_mask], y[right_mask], depth + 1)
        return _Node(feature_index=feature_index, threshold=threshold, left=left, right=right)

    def _best_split(self, X: np.ndarray, y: np.ndarray):
        n_samples, n_features = X.shape
        parent_impurity = self._impurity(y)
        if parent_impurity == 0:
            return None

        feature_indices = np.arange(n_features)
        if self.max_features is not None and self.max_features < n_features:
            feature_indices = self._rng.choice(n_features, size=self.max_features, replace=False)

        best_gain = 0.0
        best = None

        for feat in feature_indices:
            column = X[:, feat]
            # Candidate thresholds: midpoints between unique sorted values
            # (subsampled if there are many to keep training fast).
            uniques = np.unique(column)
            if len(uniques) > 32:
                quantiles = np.linspace(0, 1, 33)[1:-1]
                candidates = np.unique(np.quantile(uniques, quantiles))
            else:
                candidates = (uniques[:-1] + uniques[1:]) / 2.0 if len(uniques) > 1 else uniques

            for threshold in candidates:
                left_mask = column <= threshold
                n_left = int(left_mask.sum())
                n_right = n_samples - n_left
                if n_left == 0 or n_right == 0:
                    continue

                left_impurity = self._impurity(y[left_mask])
                right_impurity = self._impurity(y[~left_mask])
                weighted_impurity = (n_left / n_samples) * left_impurity + (n_right / n_samples) * right_impurity
                gain = parent_impurity - weighted_impurity

                if gain > best_gain:
                    best_gain = gain
                    best = (feat, threshold, left_mask)

        return best

    # -- prediction ----------------------------------------------------------

    def _predict_one(self, x: np.ndarray):
        node = self.root
        if node is None:
            raise RuntimeError("CARTTree must be fitted before prediction.")
        while not node.is_leaf:
            if node.feature_index is None or node.threshold is None:
                raise RuntimeError("CARTTree contains an invalid internal node.")
            if x[node.feature_index] <= node.threshold:
                next_node = node.left
            else:
                next_node = node.right
            if next_node is None:
                raise RuntimeError("CARTTree contains an invalid internal node.")
            node = next_node
        return node.value

    def predict(self, X: np.ndarray) -> np.ndarray:
        X = np.asarray(X, dtype=float)
        if self.task == "regression":
            return np.array([self._predict_one(x) for x in X], dtype=float)
        # classification: return the argmax class
        probs = np.array([self._predict_one(x) for x in X])
        return probs.argmax(axis=1)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        assert self.task == "classification"
        X = np.asarray(X, dtype=float)
        return np.array([self._predict_one(x) for x in X])
