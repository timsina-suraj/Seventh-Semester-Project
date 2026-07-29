"""Random Forest Regressor / Classifier — bootstrap sampling + random feature
subsets over many CARTTree instances, from scratch (no scikit-learn)."""
import numpy as np

from app.ml.tree_core import CARTTree


def _bootstrap_sample(X: np.ndarray, y: np.ndarray, rng: np.random.RandomState):
    n = X.shape[0]
    indices = rng.randint(0, n, size=n)
    return X[indices], y[indices]


class RandomForestRegressor:
    def __init__(
        self,
        n_estimators: int = 25,
        max_depth: int = 8,
        min_samples_split: int = 4,
        max_features: str | int = "sqrt",
        random_state: int = 42,
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.max_features = max_features
        self.random_state = random_state
        self.trees: list[CARTTree] = []

    def _resolve_max_features(self, n_features: int) -> int:
        if self.max_features == "sqrt":
            return max(1, int(np.sqrt(n_features)))
        if isinstance(self.max_features, int):
            return min(self.max_features, n_features)
        return n_features

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        rng = np.random.RandomState(self.random_state)
        max_feats = self._resolve_max_features(X.shape[1])

        self.trees = []
        for i in range(self.n_estimators):
            X_sample, y_sample = _bootstrap_sample(X, y, rng)
            tree = CARTTree(
                task="regression",
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                max_features=max_feats,
                random_state=self.random_state + i,
            )
            tree.fit(X_sample, y_sample)
            self.trees.append(tree)
        return self

    def predict(self, X) -> np.ndarray:
        X = np.asarray(X, dtype=float)
        predictions = np.array([tree.predict(X) for tree in self.trees])
        return predictions.mean(axis=0)


class RandomForestClassifier:
    def __init__(
        self,
        n_estimators: int = 25,
        max_depth: int = 8,
        min_samples_split: int = 4,
        max_features: str | int = "sqrt",
        n_classes: int = 2,
        random_state: int = 42,
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.max_features = max_features
        self.n_classes = n_classes
        self.random_state = random_state
        self.trees: list[CARTTree] = []

    def _resolve_max_features(self, n_features: int) -> int:
        if self.max_features == "sqrt":
            return max(1, int(np.sqrt(n_features)))
        if isinstance(self.max_features, int):
            return min(self.max_features, n_features)
        return n_features

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=int)
        rng = np.random.RandomState(self.random_state)
        max_feats = self._resolve_max_features(X.shape[1])

        self.trees = []
        for i in range(self.n_estimators):
            X_sample, y_sample = _bootstrap_sample(X, y, rng)
            tree = CARTTree(
                task="classification",
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                max_features=max_feats,
                n_classes=self.n_classes,
                random_state=self.random_state + i,
            )
            tree.fit(X_sample, y_sample)
            self.trees.append(tree)
        return self

    def predict_proba(self, X) -> np.ndarray:
        X = np.asarray(X, dtype=float)
        probs = np.array([tree.predict_proba(X) for tree in self.trees])  # (n_trees, n_samples, n_classes)
        return probs.mean(axis=0)

    def predict(self, X) -> np.ndarray:
        """Majority vote across trees (matches the spec's 'Tree1->Dengue,
        Tree2->Dengue, Tree3->Normal => Dengue Positive' example) rather than
        averaged probability, though both agree in the typical case."""
        X = np.asarray(X, dtype=float)
        votes = np.array([tree.predict(X) for tree in self.trees])  # (n_trees, n_samples)
        n_samples = votes.shape[1]
        result = np.zeros(n_samples, dtype=int)
        for i in range(n_samples):
            counts = np.bincount(votes[:, i], minlength=self.n_classes)
            result[i] = counts.argmax()
        return result

    @property
    def feature_importances_(self) -> np.ndarray:
        per_tree = np.array([tree.feature_importances() for tree in self.trees])
        return per_tree.mean(axis=0)
