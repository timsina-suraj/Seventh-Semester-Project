"""Gradient Boosted Trees — the spec's 'XGBoost Regressor/Classifier',
implemented from scratch: sequential shallow regression trees fit on the
gradient of the loss (residuals for MSE, gradient of log-loss for
classification), combined with learning-rate shrinkage. This mirrors
XGBoost's core idea (weak learner trees + gradient calculation + boosted
prediction) without depending on the xgboost package.
"""
import numpy as np

from app.ml.tree_core import CARTTree


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -500, 500)))


class GBRegressor:
    def __init__(
        self,
        n_estimators: int = 60,
        learning_rate: float = 0.1,
        max_depth: int = 3,
        min_samples_split: int = 4,
    ):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.trees: list[CARTTree] = []
        self.base_prediction: float = 0.0

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        self.base_prediction = float(np.mean(y))
        prediction = np.full(shape=y.shape, fill_value=self.base_prediction)

        self.trees = []
        for _ in range(self.n_estimators):
            residuals = y - prediction  # negative gradient of 0.5*(y-pred)^2
            tree = CARTTree(
                task="regression",
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
            )
            tree.fit(X, residuals)
            update = tree.predict(X)
            prediction = prediction + self.learning_rate * update
            self.trees.append(tree)
        return self

    def predict(self, X) -> np.ndarray:
        X = np.asarray(X, dtype=float)
        prediction = np.full(shape=(X.shape[0],), fill_value=self.base_prediction)
        for tree in self.trees:
            prediction = prediction + self.learning_rate * tree.predict(X)
        return prediction


class GBClassifier:
    """Binary gradient-boosted classifier: boosts on the log-odds, using the
    gradient of log-loss (y - sigmoid(current_score)) as the pseudo-residual
    target for each new regression tree, same as the core idea in XGBoost."""

    def __init__(
        self,
        n_estimators: int = 60,
        learning_rate: float = 0.1,
        max_depth: int = 3,
        min_samples_split: int = 4,
    ):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.trees: list[CARTTree] = []
        self.base_log_odds: float = 0.0

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)  # 0/1
        p = np.clip(np.mean(y), 1e-6, 1 - 1e-6)
        self.base_log_odds = float(np.log(p / (1 - p)))
        score = np.full(shape=y.shape, fill_value=self.base_log_odds)

        self.trees = []
        for _ in range(self.n_estimators):
            proba = _sigmoid(score)
            pseudo_residuals = y - proba  # gradient of log-loss w.r.t. score
            tree = CARTTree(
                task="regression",
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
            )
            tree.fit(X, pseudo_residuals)
            update = tree.predict(X)
            score = score + self.learning_rate * update
            self.trees.append(tree)
        return self

    def predict_proba(self, X) -> np.ndarray:
        X = np.asarray(X, dtype=float)
        score = np.full(shape=(X.shape[0],), fill_value=self.base_log_odds)
        for tree in self.trees:
            score = score + self.learning_rate * tree.predict(X)
        p1 = _sigmoid(score)
        return np.stack([1 - p1, p1], axis=1)

    def predict(self, X) -> np.ndarray:
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)

    @property
    def feature_importances_(self) -> np.ndarray:
        per_tree = np.array([tree.feature_importances() for tree in self.trees])
        return per_tree.mean(axis=0)
