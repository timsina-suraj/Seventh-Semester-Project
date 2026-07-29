"""Feature importance (Mean Decrease in Impurity) for the from-scratch
CART/RandomForest/GradientBoosting diagnosis classifier."""
import numpy as np

from app.ml.tree_core import CARTTree


def _make_predictive_dataset(n=200, seed=0):
    """Feature 0 perfectly determines the label; features 1-2 are noise."""
    rng = np.random.RandomState(seed)
    X = rng.rand(n, 3)
    y = (X[:, 0] > 0.5).astype(int)
    return X, y


def test_feature_importances_ranks_predictive_feature_highest():
    X, y = _make_predictive_dataset()
    tree = CARTTree(task="classification", max_depth=4, min_samples_split=2, n_classes=2)
    tree.fit(X, y)

    importances = tree.feature_importances()

    assert importances.shape == (3,)
    assert np.isclose(importances.sum(), 1.0)
    assert importances[0] == importances.max()


def test_feature_importances_sums_to_one_for_regression_tree():
    rng = np.random.RandomState(1)
    X = rng.rand(100, 2)
    y = X[:, 0] * 10 + rng.rand(100) * 0.01
    tree = CARTTree(task="regression", max_depth=4, min_samples_split=2)
    tree.fit(X, y)

    importances = tree.feature_importances()
    assert np.isclose(importances.sum(), 1.0)
    assert importances[0] > importances[1]


def test_feature_importances_all_zero_when_no_split_possible():
    X = np.zeros((10, 2))
    y = np.zeros(10, dtype=int)
    tree = CARTTree(task="classification", max_depth=4, min_samples_split=2, n_classes=2)
    tree.fit(X, y)

    importances = tree.feature_importances()
    assert importances.shape == (2,)
    assert np.all(importances == 0.0)


def test_feature_importances_raises_if_not_fitted():
    tree = CARTTree(task="classification", n_classes=2)
    try:
        tree.feature_importances()
        assert False, "expected RuntimeError"
    except RuntimeError:
        pass
