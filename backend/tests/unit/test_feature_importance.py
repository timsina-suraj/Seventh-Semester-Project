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


from app.ml.decision_tree import DecisionTreeClassifier
from app.ml.gradient_boosting import GBClassifier
from app.ml.random_forest import RandomForestClassifier


def test_decision_tree_classifier_feature_importances():
    X, y = _make_predictive_dataset()
    model = DecisionTreeClassifier(max_depth=4, min_samples_split=2, n_classes=2)
    model.fit(X, y)

    importances = model.feature_importances_
    assert np.isclose(importances.sum(), 1.0)
    assert importances[0] == importances.max()


def test_random_forest_classifier_feature_importances():
    X, y = _make_predictive_dataset(n=300)
    model = RandomForestClassifier(n_estimators=10, max_depth=4, min_samples_split=2, n_classes=2, random_state=0)
    model.fit(X, y)

    importances = model.feature_importances_
    assert importances.shape == (3,)
    assert np.isclose(importances.sum(), 1.0)
    assert importances[0] == importances.max()


def test_gb_classifier_feature_importances():
    X, y = _make_predictive_dataset(n=300)
    model = GBClassifier(n_estimators=20, learning_rate=0.1, max_depth=2, min_samples_split=2)
    model.fit(X, y)

    importances = model.feature_importances_
    assert importances.shape == (3,)
    assert np.isclose(importances.sum(), 1.0)
    assert importances[0] == importances.max()


from app.ml.metrics import named_feature_importance


def test_named_feature_importance_sorts_descending_with_names():
    importances = np.array([0.1, 0.7, 0.2])
    feature_names = ["age", "platelet_change_rate", "wbc_count"]

    result = named_feature_importance(importances, feature_names)

    assert result == [
        {"feature": "platelet_change_rate", "importance": 0.7},
        {"feature": "wbc_count", "importance": 0.2},
        {"feature": "age", "importance": 0.1},
    ]


from app.ml import train_diagnosis


def test_train_and_store_includes_feature_importance_for_all_three_models():
    result = train_diagnosis.train_and_store()

    assert set(result["feature_importance"].keys()) == {"decision_tree", "random_forest", "xgboost"}
    for ranked in result["feature_importance"].values():
        assert len(ranked) == len(result["feature_names"])
        assert {"feature", "importance"} <= ranked[0].keys()
        total = sum(entry["importance"] for entry in ranked)
        assert 0.9 < total <= 1.01  # normalized, allowing rounding
