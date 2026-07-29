# Prescription → Inventory FK wiring — Design

## Context

Two improvements were proposed:

1. *"Prescriptions store medicine as free text instead of an FK to medicine/inventory — wiring that up gives you real inventory auto-decrement, a nice end-to-end workflow to demo (prescribe → stock drops → low-stock alert fires)."*
2. *"Risk map uses point markers instead of real Nepal district GeoJSON polygons — swapping in real polygons is a small change with a big visual payoff for a demo."*

Investigation found **item 2 is already implemented**: `frontend/src/components/NepalRiskMap.jsx` renders real district polygons from `frontend/public/district.geojson` (a genuine ~4.5MB district boundary dataset), with hover highlighting, a legend, and popups. No work is needed there.

This spec covers **item 1 only**: wiring `PrescriptionItem` to the existing `Medicine`/`Inventory` tables so prescribing a stocked medicine actually decrements inventory, which in turn feeds the already-existing low-stock computation (`Inventory.is_low_stock`, used by the dashboard stat and the Pharmacy page's low-stock filter — no new "alert" mechanism needed there).

## Real-world grounding

Real HMIS/EMR systems separate *prescribing* (CPOE, against a large drug catalog/formulary, not limited by current stock) from *dispensing* (pharmacy staff fulfilling the order against actual on-hand inventory, where the decrement happens). MediShield has no `pharmacist` role today (`VALID_ROLES = admin, doctor, nurse, receptionist, lab_technician, patient`), and no dispense/fulfillment workflow. Introducing one is out of scope for this change.

Decision (confirmed with user): decrement happens at **prescribe time**, not via a separate dispense step. A doctor can still prescribe anything — if the medicine isn't in the hospital's catalog (or the doctor doesn't want to link it), they use free text as today, with no stock effect. If they pick a catalog medicine, stock is checked and decremented immediately.

## Data model

`PrescriptionItem` (`backend/app/models/prescription.py`) gains two nullable columns:

- `medicine_id: int | None` — FK to `medicines.id`, nullable
- `quantity: int | None` — units to dispense, nullable

`medicine_name` is unchanged and remains the display/PDF field for every item, catalog-linked or not. When a doctor selects a catalog medicine in the UI, the frontend auto-fills `medicine_name` from that medicine's name — the two are not database-enforced to match, matching the current app's level of rigor elsewhere (e.g. `MedicineRead.from_medicine`'s denormalization).

No changes to `Medicine` or `Inventory` — `Inventory.is_low_stock` already exists and is already read by `stats_service.py` (dashboard low-stock count) and `pharmacy.py` (`low_stock_only` filter).

## Validation

`PrescriptionItemCreate` (`backend/app/schemas/prescription.py`) adds:

```python
medicine_id: int | None = None
quantity: int | None = Field(default=None, ge=1)
```

with a model validator: if `medicine_id` is set, `quantity` must also be set (and is already constrained `>= 1`). If `medicine_id` is None, `quantity` is ignored/must be None (free-text items don't carry a quantity).

`PrescriptionItemRead` adds the same two fields (read-only passthrough).

## Service logic (`PrescriptionService.create_with_items`)

`PrescriptionService` currently takes `(prescription_repo, audit_service)`. It gains a `medicine_repo: MedicineRepository`.

```
1. Aggregate requested quantity per medicine_id across all items in this
   prescription (two items can reference the same medicine).
2. For each distinct medicine_id: load Medicine+Inventory via
   medicine_repo.get_with_inventory(id). If missing -> NotFoundError.
   If inventory.quantity < requested -> ValidationError naming the
   medicine, available stock, and requested amount. Nothing is saved.
3. If all pass: create the Prescription + PrescriptionItems (as today),
   decrement each affected Inventory.quantity by the aggregated amount,
   then commit — one transaction, all-or-nothing.
```

This mirrors the existing "block" behavior decided for insufficient stock: the whole prescription create fails with a 422 rather than partially saving or allowing negative stock.

`get_prescription_service` in `backend/app/dependencies.py` is updated to construct and pass a `MedicineRepository(db)`.

## API / RBAC

`GET /pharmacy` is currently gated to `admin`/`receptionist` only via a router-level `dependencies=[Depends(require_role("admin", "receptionist"))]` in `backend/app/routers/pharmacy.py`, which blocks doctors from seeing the catalog. Change:

- Remove the router-level dependency.
- `GET /pharmacy` (list): `require_role("admin", "receptionist", "doctor")`.
- `POST /pharmacy`, `PATCH /pharmacy/{id}`, `DELETE /pharmacy/{id}`: keep `require_role("admin", "receptionist")`.

No new endpoint is needed — `listPharmacyItems()` (already in `frontend/src/api/endpoints.js`) returns `id, name, unit, stock_quantity, is_low_stock`, exactly what the prescribing UI needs.

## Frontend

**`frontend/src/pages/doctor/DiagnosisPrediction.jsx`** (the doctor's prescribe form):

- Fetch the medicine catalog on mount via `api.listPharmacyItems()`.
- `EMPTY_ITEM` becomes `{ medicine_id: "", medicine_name: "", quantity: "", dosage: "", frequency: "", duration: "", instructions: "" }`.
- Replace the free-text "Medicine" input with a `<select>`:
  - First option: `— Custom (not in pharmacy) —` (default, preserves today's exact behavior).
  - Followed by catalog medicines, each showing name + unit (e.g. "Paracetamol 500mg (tablets)").
  - When a catalog medicine is selected: auto-set `medicine_name`, show available stock inline (e.g. "42 tablets in stock"), and reveal a required numeric Quantity input, soft-capped client-side at available stock (server remains authoritative).
  - When "Custom" is selected: revert to a free-text medicine name input (as today), hide the quantity input, `medicine_id` stays empty.
- Submit payload per item includes `medicine_id` (or omitted/null) and `quantity` (or omitted/null) alongside the existing fields.
- Surface the service's `ValidationError` message (insufficient stock) in the existing `error` banner — no new error UI needed, it already renders `err.response?.data?.detail`.

**`frontend/src/pages/Prescriptions.jsx`** (history/list view) and **PDF generation** (`backend/app/services/pdf_service.py` + the item-dict building in `backend/app/routers/prescriptions.py`): add a Quantity column, rendered as `item.quantity ?? "—"`, next to Medicine.

## Migration & seed data

One additive Alembic migration: adds nullable `medicine_id` (FK to `medicines.id`) and nullable `quantity` to `prescription_items`.

Per user decision, rather than backfilling the existing free-text seeded rows, the local dev SQLite DB (`backend/MediShield_db.db`) is deleted and recreated via `alembic upgrade head` + `python seed.py`.

`seed.py` currently seeds section 11 "Pharmacy Inventory" *after* section 8 "Prescriptions" — reordered so Pharmacy Inventory is seeded before Prescriptions. The existing seeded prescription item names ("Paracetamol 500mg", "ORS Sachets", "Vitamin C 500mg") already match real catalog entries, so prescription seeding links them via `medicine_id` + a small `quantity`, tracking a running remaining-stock counter so nothing goes negative. If a medicine's demo stock would be exhausted for a given item, that item falls back to free-text-only (no `medicine_id`), which naturally demonstrates the hybrid catalog/free-text behavior in the seeded data.

## Testing

Existing tests posting `{"medicine_name": "..."}` with no `medicine_id`/`quantity` are unaffected (both new fields are optional, default `None`). `PrescriptionItem(medicine_name=...)` direct-construction in `test_notification_service.py` is unaffected for the same reason.

New integration tests (in `backend/tests/integration/`, alongside the existing prescription workflow tests):

- Prescribing a catalog-linked item decrements `Inventory.quantity` by the requested amount.
- Prescribing more than available stock returns 422, and stock is left unchanged (nothing partially saved).
- A single prescription with both a catalog-linked item and a free-text item succeeds, decrementing only the catalog one.
- Two items in the same prescription referencing the same `medicine_id` have their quantities summed against available stock.

## Out of scope

- No new `pharmacist` role or dispense/fulfillment workflow.
- No changes to the low-stock alert mechanism itself (it's already reactive/derived).
- No changes to the risk map (already uses real GeoJSON polygons).
