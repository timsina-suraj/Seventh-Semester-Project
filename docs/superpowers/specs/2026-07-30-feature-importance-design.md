# Diagnosis Classifier Feature Importance — Design

## Context

The dengue diagnosis classifier (`train_diagnosis.py`, trained on `dengue_dataset_withsymptoms.csv`) already reports accuracy/precision/recall/F1/confusion-matrix per model ([metrics.py](../../../backend/app/ml/metrics.py)), but gives no insight into *which* symptoms, comorbidities, or lab values actually drive its predictions. This spec adds feature importance — "what did the model actually rely on" — as an explainability layer on top of the existing from-scratch CART/Random-Forest/Gradient-Boosting implementation in `backend/app/ml/`.

Scope decisions (confirmed with user):
- **Diagnosis classifier only** — not the dengue climate regressor (`train_dengue_prediction.py`).
- **All 3 model types** (Decision Tree, Random Forest, "XGBoost"/Gradient Boosting) get importance computed, so the report/demo can show whether the models agree on what matters.
- **Backend + API + frontend chart** — a real chart on the Analytics dashboard, not just backend-only data.

## Algorithm

Standard **Mean Decrease in Impurity (MDI)**: every time a tree splits on feature `f`, the impurity reduction (`gain`) at that split, weighted by how many samples passed through that node, is attributed to `f`. Summed across all splits in a tree and normalized to sum to 1, this ranks features by how much they actually reduced uncertainty during training. No new dependency — `gain` is already computed (and discarded) in `CARTTree._best_split`.

## Core changes — `backend/app/ml/tree_core.py`

`_best_split` currently returns `(feature_index, threshold, left_mask)`; it will additionally return the `gain` it already computes: `(feature_index, threshold, left_mask, gain)`.

`CARTTree.fit()` initializes `self._raw_importances = np.zeros(X.shape[1])`. `_grow()` accumulates `self._raw_importances[feature_index] += gain * n_samples_at_node` whenever a split is chosen (before recursing into children).

New method:

```python
def feature_importances(self) -> np.ndarray:
    total = self._raw_importances.sum()
    return self._raw_importances / total if total > 0 else np.zeros_like(self._raw_importances)
```

A tree with no splits (pure/tiny leaf) returns an all-zero vector rather than dividing by zero.

## Wrapper changes

- **`decision_tree.py`** (`DecisionTreeClassifier` only): add `feature_importances_` property returning `self.tree.feature_importances()` directly (single tree, already normalized).
- **`random_forest.py`** (`RandomForestClassifier`): add `feature_importances_` property. Averages each of the 100 trees' *normalized* per-tree importances (standard convention — matches scikit-learn's `RandomForestClassifier.feature_importances_`, useful if ever cited in the report).
- **`gradient_boosting.py`** (`GBClassifier`): same averaging across its 100 sequential boosting trees. These trees are fit on residuals/pseudo-residuals (`task="regression"` internally even for the classifier — see existing docstring), but MDI still validly ranks "which feature reduced error most" regardless of what target the tree was fit on.

`DecisionTreeRegressor`/`RandomForestRegressor`/`GBRegressor` (used only by the out-of-scope dengue regressor) are left untouched — no wiring for them in this change, though the underlying `CARTTree.feature_importances()` method works for any task type if needed later.

## Naming helper — `backend/app/ml/metrics.py`

One small addition, alongside the existing `classification_report`/`regression_report`:

```python
def named_feature_importance(importances: np.ndarray, feature_names: list[str]) -> list[dict]:
    pairs = sorted(zip(feature_names, importances.tolist()), key=lambda p: p[1], reverse=True)
    return [{"feature": name, "importance": round(value, 4)} for name, value in pairs]
```

## Training wiring — `backend/app/ml/train_diagnosis.py`

After all 3 models are fitted (existing loop over `models.items()`), compute and attach:

```python
feature_importance = {
    name: named_feature_importance(model.feature_importances_, feature_names)
    for name, model in fitted.items()
}
```

Stored in the artifact as `artifact["feature_importance"]` (dict keyed by `"decision_tree"` / `"random_forest"` / `"xgboost"`, each a full ranked list) — mirroring how `metrics` is already stored per-model. Full 3-way data persists for report/comparison use even though only the best model is charted live (next section).

## API exposure — `backend/app/routers/analytics.py`

`GET /analytics` gains two response fields, built the same way `classification_data`/`cm` already are (keyed off `best_diagnosis_model`):

- `featureImportance`: top 10 entries of `diagnosis_artifact["feature_importance"][best_diagnosis_model]`.
- `bestDiagnosisModel`: display-formatted name (reuses the existing `display_name` formatting logic already applied to `classification_data` model names), so the frontend chart title can say which model it's showing.

## Frontend — `frontend/src/pages/admin/Analytics.jsx`

One new card, visually consistent with the existing "🤒 Symptoms Frequency" horizontal bar chart (same `BarChart layout="vertical"` pattern already used there and in the RMSE/MAE chart):

```jsx
{/* Feature Importance */}
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
```

`bestDiagnosisModel` and `featureImportance` are destructured from the existing `data` object alongside the other analytics fields already read at the top of the component.

## Testing

New unit tests in `backend/tests/unit/` (new file, e.g. `test_feature_importance.py`), following the existing pytest style used for other `app/ml/` pieces:

- `CARTTree.feature_importances()` on a small synthetic dataset where one feature is constructed to be obviously predictive and the rest are noise — assert the predictive feature ranks highest and the returned vector sums to ~1.0 (within floating-point tolerance).
- A tree with no valid split (e.g. all identical `y`) returns an all-zero vector without raising.
- `RandomForestClassifier.feature_importances_` and `GBClassifier.feature_importances_` on the same synthetic dataset — assert the same predictive feature ranks highest after averaging across trees, and the result sums to ~1.0.
- `named_feature_importance()` returns entries sorted descending by importance with the correct feature names attached.

No changes needed to existing tests — `_best_split`'s new 4-tuple return is an internal, unexported detail of `tree_core.py` with no external callers besides `_grow`.

## Out of scope

- The dengue climate regressor (`train_dengue_prediction.py`) — no feature importance wired for it in this change, though the underlying `CARTTree.feature_importances()` works for regression trees too if this is revisited later.
- Cross-validation (a separately discussed, independent improvement) — not part of this change.
- A full 3-model comparison view in the frontend (e.g., "do all 3 models agree") — the artifact stores all 3 for report use, but the live dashboard only charts the best model, per the "one clean chart" scope decision.
