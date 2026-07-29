"""Evaluation metrics + train/test split, implemented from scratch on numpy."""
import numpy as np


def train_test_split(X: np.ndarray, y: np.ndarray, test_size: float = 0.2, random_state: int = 42):
    n = X.shape[0]
    rng = np.random.RandomState(random_state)
    indices = rng.permutation(n)
    n_test = int(n * test_size)
    test_idx, train_idx = indices[:n_test], indices[n_test:]
    return X[train_idx], X[test_idx], y[train_idx], y[test_idx]


# -- Regression metrics ------------------------------------------------------

def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return 1.0 if ss_res == 0 else 0.0
    return float(1 - ss_res / ss_tot)


def regression_report(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    return {"mae": mae(y_true, y_pred), "rmse": rmse(y_true, y_pred), "r2": r2_score(y_true, y_pred)}


# -- Classification metrics ---------------------------------------------------

def accuracy_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(y_true == y_pred))


def precision_score(y_true: np.ndarray, y_pred: np.ndarray, positive_label: int = 1) -> float:
    tp = np.sum((y_pred == positive_label) & (y_true == positive_label))
    fp = np.sum((y_pred == positive_label) & (y_true != positive_label))
    return float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0


def recall_score(y_true: np.ndarray, y_pred: np.ndarray, positive_label: int = 1) -> float:
    tp = np.sum((y_pred == positive_label) & (y_true == positive_label))
    fn = np.sum((y_pred != positive_label) & (y_true == positive_label))
    return float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0


def f1_score(y_true: np.ndarray, y_pred: np.ndarray, positive_label: int = 1) -> float:
    p = precision_score(y_true, y_pred, positive_label)
    r = recall_score(y_true, y_pred, positive_label)
    return float(2 * p * r / (p + r)) if (p + r) > 0 else 0.0


def confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, positive_label: int = 1) -> dict:
    tp = np.sum((y_pred == positive_label) & (y_true == positive_label))
    fp = np.sum((y_pred == positive_label) & (y_true != positive_label))
    fn = np.sum((y_pred != positive_label) & (y_true == positive_label))
    tn = np.sum((y_pred != positive_label) & (y_true != positive_label))
    return {"TP": int(tp), "FP": int(fp), "FN": int(fn), "TN": int(tn)}


def classification_report(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred),
        "recall": recall_score(y_true, y_pred),
        "f1": f1_score(y_true, y_pred),
        "confusion_matrix": confusion_matrix(y_true, y_pred)
    }


# -- Feature importance -------------------------------------------------------

def named_feature_importance(importances: np.ndarray, feature_names: list[str]) -> list[dict]:
    pairs = sorted(zip(feature_names, importances.tolist()), key=lambda p: p[1], reverse=True)
    return [{"feature": name, "importance": round(value, 4)} for name, value in pairs]
