# Diagnosis Classifier Feature Importance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Mean-Decrease-in-Impurity feature importance to the from-scratch dengue diagnosis classifier (decision tree, random forest, gradient boosting), and surface it as a ranked bar chart on the admin Analytics dashboard.

**Architecture:** The core `CARTTree` (shared by all 3 model types) already computes an impurity-reduction `gain` at every split and discards it — this plan captures that value, accumulates it per feature during training, and exposes it as a normalized importance vector. That vector flows: `CARTTree` → classifier wrapper (`.feature_importances_`) → `train_diagnosis.train_and_store()` artifact → `GET /analytics` response → a new Recharts bar chart in `Analytics.jsx`.

**Tech Stack:** Python 3 / numpy (backend, no new dependency), pytest, React 18 / Recharts (frontend).

## Global Constraints

- No new dependencies — pure numpy, matching the existing from-scratch ML code (no scikit-learn/xgboost anywhere in `backend/app/ml/`).
- Scope is the **diagnosis classifier only**. Do not modify `train_dengue_prediction.py` or any `*Regressor` wrapper class (`DecisionTreeRegressor`, `RandomForestRegressor`, `GBRegressor`).
- All 3 diagnosis models (`decision_tree`, `random_forest`, `xgboost`) must get feature importance computed and stored, even though only the best model is charted on the frontend.
- Every returned importance vector/list must be normalized (values sum to ~1.0 per model).
- Match existing code style per file (e.g. `tree_core.py` uses `from __future__ import annotations`; `metrics.py` does not — don't add it there).

---

### Task 1: Core `feature_importances()` on `CARTTree`

**Files:**
- Modify: `backend/app/ml/tree_core.py`
- Test: `backend/tests/unit/test_feature_importance.py` (new file)

**Interfaces:**
- Produces: `CARTTree.feature_importances() -> np.ndarray`, callable after `.fit()`, length `n_features`, normalized to sum to 1 (or all-zero if the tree made no splits). Raises `RuntimeError` if called before `fit()`.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/unit/test_feature_importance.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/unit/test_feature_importance.py -v`
Expected: FAIL with `AttributeError: 'CARTTree' object has no attribute 'feature_importances'`

- [ ] **Step 3: Implement `feature_importances()` in `tree_core.py`**

In `CARTTree.__init__` (around line 71), add the new attribute right after `self.root: _Node | None = None`:

```python
        self.root: _Node | None = None
        self._raw_importances: np.ndarray | None = None
        self._rng = np.random.RandomState(random_state)
```

In `CARTTree.fit` (around line 85), initialize the accumulator before growing the tree:

```python
        else:
            y = np.asarray(y, dtype=float)
        self._raw_importances = np.zeros(X.shape[1])
        self.root = self._grow(X, y, depth=0)
        return self
```

In `CARTTree._best_split` (around line 161), carry the winning `gain` forward instead of discarding it:

```python
                if gain > best_gain:
                    best_gain = gain
                    best = (feat, threshold, left_mask, gain)

        return best
```

In `CARTTree._grow` (around line 118), unpack the new 4-tuple and accumulate the impurity reduction, weighted by how many samples reached this node, before recursing:

```python
        feature_index, threshold, left_mask, gain = best
        right_mask = ~left_mask
        assert self._raw_importances is not None
        self._raw_importances[feature_index] += gain * n_samples

        left = self._grow(X[left_mask], y[left_mask], depth + 1)
        right = self._grow(X[right_mask], y[right_mask], depth + 1)
        return _Node(feature_index=feature_index, threshold=threshold, left=left, right=right)
```

Add the new public method at the end of the class, after `predict_proba`:

```python
    def feature_importances(self) -> np.ndarray:
        """Mean Decrease in Impurity: total impurity reduction attributed to
        each feature across every split in this tree, normalized to sum to 1."""
        if self._raw_importances is None:
            raise RuntimeError("CARTTree must be fitted before requesting feature importances.")
        total = self._raw_importances.sum()
        return self._raw_importances / total if total > 0 else np.zeros_like(self._raw_importances)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/unit/test_feature_importance.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/ml/tree_core.py backend/tests/unit/test_feature_importance.py
git commit -m "feat: add feature_importances() to CARTTree (Mean Decrease in Impurity)"
```

---

### Task 2: Expose `feature_importances_` on the 3 classifier wrappers

**Files:**
- Modify: `backend/app/ml/decision_tree.py`
- Modify: `backend/app/ml/random_forest.py`
- Modify: `backend/app/ml/gradient_boosting.py`
- Test: `backend/tests/unit/test_feature_importance.py` (append)

**Interfaces:**
- Consumes: `CARTTree.feature_importances() -> np.ndarray` (Task 1).
- Produces: `DecisionTreeClassifier.feature_importances_`, `RandomForestClassifier.feature_importances_`, `GBClassifier.feature_importances_` — each a property returning `np.ndarray`, length `n_features`, normalized to sum to 1. `DecisionTreeRegressor`, `RandomForestRegressor`, `GBRegressor` are NOT touched (out of scope).

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/unit/test_feature_importance.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/unit/test_feature_importance.py -v -k "feature_importances and (Classifier or classifier)"`
Expected: FAIL with `AttributeError: 'DecisionTreeClassifier' object has no attribute 'feature_importances_'` (and similarly for the other two)

- [ ] **Step 3: Implement the properties**

In `backend/app/ml/decision_tree.py`, add to the end of `DecisionTreeClassifier` (after `predict_proba`):

```python
    @property
    def feature_importances_(self) -> np.ndarray:
        return self.tree.feature_importances()
```

In `backend/app/ml/random_forest.py`, add to the end of `RandomForestClassifier` (after `predict`):

```python
    @property
    def feature_importances_(self) -> np.ndarray:
        per_tree = np.array([tree.feature_importances() for tree in self.trees])
        return per_tree.mean(axis=0)
```

In `backend/app/ml/gradient_boosting.py`, add to the end of `GBClassifier` (after `predict`):

```python
    @property
    def feature_importances_(self) -> np.ndarray:
        per_tree = np.array([tree.feature_importances() for tree in self.trees])
        return per_tree.mean(axis=0)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/unit/test_feature_importance.py -v`
Expected: PASS (7 tests total so far)

- [ ] **Step 5: Commit**

```bash
git add backend/app/ml/decision_tree.py backend/app/ml/random_forest.py backend/app/ml/gradient_boosting.py backend/tests/unit/test_feature_importance.py
git commit -m "feat: expose feature_importances_ on the 3 diagnosis classifier wrappers"
```

---

### Task 3: `named_feature_importance` helper

**Files:**
- Modify: `backend/app/ml/metrics.py`
- Test: `backend/tests/unit/test_feature_importance.py` (append)

**Interfaces:**
- Produces: `named_feature_importance(importances: np.ndarray, feature_names: list[str]) -> list[dict]` in `app.ml.metrics`. Each dict is `{"feature": str, "importance": float}`, list sorted descending by `importance`.

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/unit/test_feature_importance.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/unit/test_feature_importance.py::test_named_feature_importance_sorts_descending_with_names -v`
Expected: FAIL with `ImportError: cannot import name 'named_feature_importance'`

- [ ] **Step 3: Implement the helper**

Add to the end of `backend/app/ml/metrics.py`:

```python
def named_feature_importance(importances: np.ndarray, feature_names: list[str]) -> list[dict]:
    pairs = sorted(zip(feature_names, importances.tolist()), key=lambda p: p[1], reverse=True)
    return [{"feature": name, "importance": round(value, 4)} for name, value in pairs]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/unit/test_feature_importance.py -v`
Expected: PASS (8 tests total so far)

- [ ] **Step 5: Commit**

```bash
git add backend/app/ml/metrics.py backend/tests/unit/test_feature_importance.py
git commit -m "feat: add named_feature_importance helper to metrics.py"
```

---

### Task 4: Wire feature importance into `train_diagnosis.train_and_store()`

**Files:**
- Modify: `backend/app/ml/train_diagnosis.py`
- Test: `backend/tests/unit/test_feature_importance.py` (append)

**Interfaces:**
- Consumes: `.feature_importances_` properties (Task 2) on `fitted[name]` models; `named_feature_importance` (Task 3).
- Produces: `train_diagnosis.train_and_store()`'s returned/persisted artifact dict gains key `"feature_importance": dict[str, list[dict]]`, keyed by `"decision_tree"` / `"random_forest"` / `"xgboost"`, each value the full ranked list from `named_feature_importance` (length == `len(feature_names)`).

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/unit/test_feature_importance.py`:

```python
from app.ml import train_diagnosis


def test_train_and_store_includes_feature_importance_for_all_three_models():
    result = train_diagnosis.train_and_store()

    assert set(result["feature_importance"].keys()) == {"decision_tree", "random_forest", "xgboost"}
    for ranked in result["feature_importance"].values():
        assert len(ranked) == len(result["feature_names"])
        assert {"feature", "importance"} <= ranked[0].keys()
        total = sum(entry["importance"] for entry in ranked)
        assert 0.9 < total <= 1.01  # normalized, allowing rounding
```

Note: this trains on the real `dengue_dataset_withsymptoms.csv` (same pattern already used by `backend/tests/unit/test_ml_preprocessing.py` and `backend/tests/integration/test_search_pdf_ml_gaps.py`, which call `train_diagnosis.train_and_store()` directly) — it will take a few seconds, not milliseconds.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/unit/test_feature_importance.py::test_train_and_store_includes_feature_importance_for_all_three_models -v`
Expected: FAIL with `KeyError: 'feature_importance'`

- [ ] **Step 3: Wire it in**

In `backend/app/ml/train_diagnosis.py`, update the metrics import (top of file):

```python
from app.ml.metrics import classification_report, named_feature_importance, train_test_split
```

After the existing `for name, model in models.items():` training loop (right after it, before the `best_model_name = ...` line), add:

```python
    feature_importance = {
        name: named_feature_importance(model.feature_importances_, feature_names)
        for name, model in fitted.items()
    }
```

Add the new key to the `artifact` dict:

```python
    artifact = {
        "models": fitted,
        "best_model_name": best_model_name,
        "feature_names": feature_names,
        "district_encoder": district_encoder,
        "metrics": metrics,
        "feature_importance": feature_importance,
        "diagnosis_dist": diagnosis_dist,
        "symptoms_data": symptoms_data,
        "dataset_quality": quality.as_dict(),
        "rows_trained_on": len(rows),
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/unit/test_feature_importance.py -v`
Expected: PASS (9 tests total so far)

- [ ] **Step 5: Commit**

```bash
git add backend/app/ml/train_diagnosis.py backend/tests/unit/test_feature_importance.py
git commit -m "feat: compute and persist feature importance in train_diagnosis artifact"
```

---

### Task 5: Expose feature importance via `GET /analytics`

**Files:**
- Modify: `backend/app/routers/analytics.py`
- Test: `backend/tests/unit/test_analytics.py` (new file)

**Interfaces:**
- Consumes: `diagnosis_artifact["feature_importance"]` (Task 4).
- Produces: `GET /analytics` JSON response gains `featureImportance: list[dict]` (top 10 entries for the best diagnosis model) and `bestDiagnosisModel: str` (display-formatted model name, e.g. `"Random Forest"` or `"XGBoost"`).

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_analytics.py`:

```python
"""GET /analytics response building — tested by calling the route function
directly (it has no DB/request dependencies, only reads trained model
artifacts from disk), matching the plain-function style already used for
app/ml/ training scripts in this test suite."""
from app.ml import train_dengue_prediction, train_diagnosis
from app.routers.analytics import get_analytics


def test_get_analytics_includes_feature_importance_for_best_model():
    train_diagnosis.train_and_store()
    train_dengue_prediction.train_and_store()

    result = get_analytics()

    assert "featureImportance" in result
    assert "bestDiagnosisModel" in result
    assert len(result["featureImportance"]) <= 10
    assert result["featureImportance"] == sorted(
        result["featureImportance"], key=lambda e: e["importance"], reverse=True
    )
    assert isinstance(result["bestDiagnosisModel"], str) and result["bestDiagnosisModel"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/unit/test_analytics.py -v`
Expected: FAIL with `KeyError: 'featureImportance'`

- [ ] **Step 3: Implement it in `analytics.py`**

In `backend/app/routers/analytics.py`, add this block right after the existing `for model_name, metrics in diagnosis_artifact["metrics"].items():` loop (which already computes `best_diagnosis_model` and `cm`), before the `return { ... }`:

```python
    feature_importance_list = diagnosis_artifact.get("feature_importance", {}).get(best_diagnosis_model, [])[:10]
    best_diagnosis_display = best_diagnosis_model.replace("_", " ").title()
    if best_diagnosis_display == "Xgboost":
        best_diagnosis_display = "XGBoost"
```

Add the two new keys to the returned dict:

```python
    return {
        "modelRegressionData": model_regression_data,
        "classificationData": classification_data,
        "CM": cm,
        "actualVsPredicted": dengue_artifact.get("actual_vs_predicted", []),
        "weatherData": dengue_artifact.get("weather_data", []),
        "diagnosisDist": diagnosis_artifact.get("diagnosis_dist", []),
        "symptomsData": diagnosis_artifact.get("symptoms_data", []),
        "featureImportance": feature_importance_list,
        "bestDiagnosisModel": best_diagnosis_display,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/unit/test_analytics.py tests/unit/test_feature_importance.py -v`
Expected: PASS (all tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/analytics.py backend/tests/unit/test_analytics.py
git commit -m "feat: expose feature importance and best model name via GET /analytics"
```

---

### Task 6: Feature Importance chart on the Analytics dashboard

**Files:**
- Modify: `frontend/src/pages/admin/Analytics.jsx`

**Interfaces:**
- Consumes: `featureImportance` (array of `{feature, importance}`) and `bestDiagnosisModel` (string) from the `GET /analytics` response (Task 5).
- Produces: a rendered chart card; no further consumers.

- [ ] **Step 1: Destructure the new fields**

In `frontend/src/pages/admin/Analytics.jsx`, update the destructuring block (around line 60):

```javascript
  const {
    actualVsPredicted,
    modelRegressionData,
    classificationData,
    CM,
    diagnosisDist,
    symptomsData,
    weatherData,
    featureImportance,
    bestDiagnosisModel,
  } = data;
```

- [ ] **Step 2: Add the new chart card**

Insert this new card between the existing "8. Symptoms Frequency" card and the "9. Weather vs Dengue Cases" card, and renumber the weather card's comment to `10.`:

```jsx
        {/* 9. Feature Importance */}
        <div className="card" style={{ gridColumn: "1 / -1" }}>
          <CardTitle>🎯 Feature Importance — {bestDiagnosisModel} (What Drives the Prediction)</CardTitle>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={featureImportance} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} fontSize={12} />
              <YAxis type="category" dataKey="feature" fontSize={11} width={160} />
              <Tooltip formatter={(v) => `${(v * 100).toFixed(1)}%`} />
              <Bar dataKey="importance" fill="#9333ea" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* 10. Weather vs Dengue Cases */}
```

(Delete the old `{/* 9. Weather vs Dengue Cases */}` comment line immediately above the `ComposedChart` card, replaced by the renumbered one above.)

- [ ] **Step 3: Retrain models so the new artifact key is populated**

The pickled artifacts on disk (`backend/app/ml/model_store/*.pkl`) predate this change and lack `feature_importance`. Retrain from the backend directory:

Run: `cd backend && python -m app.ml.train_diagnosis`
Expected: prints per-model accuracy/precision/recall/F1 lines and `Best model: <name>`, and overwrites `backend/app/ml/model_store/diagnosis_classifiers.pkl` with an artifact that now includes `feature_importance`.

- [ ] **Step 4: Manually verify the chart renders**

Start the backend (`cd backend && uvicorn app.main:app --reload`) and frontend (`cd frontend && npm run dev`) dev servers. Log in as an admin user, navigate to the Analytics page, and confirm the new "🎯 Feature Importance" card renders with horizontal bars and percentage labels, positioned between "Symptoms Frequency" and "Weather vs Dengue Cases". Use the Playwright browser tools (`browser_navigate` to the Analytics page URL, `browser_snapshot` or `browser_take_screenshot`) to capture and confirm this visually rather than relying on code inspection alone.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/admin/Analytics.jsx
git commit -m "feat: add feature importance chart to Analytics dashboard"
```

---

## Self-Review Notes

- **Spec coverage:** All 6 spec sections (Algorithm, Core changes, Wrapper changes, Naming helper, Training wiring, API exposure, Frontend, Testing) map onto Tasks 1–6 above; nothing in the spec is left unaddressed.
- **Scope guard:** No task touches `train_dengue_prediction.py` or any `*Regressor` class, matching the spec's explicit out-of-scope list.
- **Type/name consistency check:** `feature_importances()` (Task 1, on `CARTTree`) vs `feature_importances_` (Task 2, sklearn-style trailing underscore, on the 3 classifier wrappers) are intentionally different names at different layers — verified consistent through Tasks 2–4 (wrappers always call `self.tree.feature_importances()` / `tree.feature_importances()`, never the trailing-underscore name, on the internal `CARTTree` objects).
