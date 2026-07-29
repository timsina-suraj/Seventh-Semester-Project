"""Decision Tree Regressor / Classifier — thin, sklearn-like wrappers around
the shared CARTTree engine (variance-reduction splits for regression,
information-gain/entropy splits for classification)."""
import numpy as np

from app.ml.tree_core import CARTTree


class DecisionTreeRegressor:
    def __init__(self, max_depth: int = 8, min_samples_split: int = 4):
        self.tree = CARTTree(task="regression", max_depth=max_depth, min_samples_split=min_samples_split)

    def fit(self, X, y):
        self.tree.fit(X, y)
        return self

    def predict(self, X) -> np.ndarray:
        return self.tree.predict(X)


class DecisionTreeClassifier:
    def __init__(self, max_depth: int = 8, min_samples_split: int = 4, n_classes: int = 2):
        self.n_classes = n_classes
        self.tree = CARTTree(
            task="classification",
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            n_classes=n_classes,
        )

    def fit(self, X, y):
        self.tree.fit(X, y)
        return self

    def predict(self, X) -> np.ndarray:
        return self.tree.predict(X)

    def predict_proba(self, X) -> np.ndarray:
        return self.tree.predict_proba(X)

    @property
    def feature_importances_(self) -> np.ndarray:
        return self.tree.feature_importances()
