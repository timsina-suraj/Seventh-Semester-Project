# Prescription → Inventory FK Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Link `PrescriptionItem` to the existing `Medicine`/`Inventory` catalog so prescribing a stocked medicine decrements real inventory (blocked if insufficient stock), while free-text prescribing for anything not in the pharmacy catalog keeps working exactly as today.

**Architecture:** Two new nullable columns on `PrescriptionItem` (`medicine_id` FK, `quantity`). `PrescriptionService.create_with_items` aggregates requested quantity per medicine across the prescription, validates stock, and decrements `Inventory.quantity` in the same transaction as creating the prescription (all-or-nothing). `GET /pharmacy` opens to the `doctor` role (read-only) so the prescribe form can populate a catalog dropdown; write endpoints stay `admin`/`receptionist`-only. Decrement happens at prescribe time — there is no separate dispense step and no new role (see `docs/superpowers/specs/2026-07-29-prescription-inventory-fk-design.md` for why).

**Tech Stack:** FastAPI + SQLAlchemy 2.0 (async) + Pydantic v2 + Alembic, backend/tests via pytest (`asyncio_mode = auto`, no `@pytest.mark.asyncio` needed). React 18 + Vite frontend, axios client, no JS test framework configured (frontend changes are verified manually in-browser).

## Global Constraints

- Backend tests run against an in-memory SQLite schema built directly from the SQLAlchemy models (`tests/conftest.py`, `Base.metadata.create_all`) — they do **not** go through Alembic. The Alembic migration (Task 5) is only exercised against the real dev DB.
- Insufficient stock must **block** prescription creation entirely (422, nothing saved) — never allow negative stock.
- `medicine_name` stays the source of truth for display/PDF on every item, catalog-linked or not. The frontend auto-fills it from the selected catalog medicine; it is not DB-enforced to match `Medicine.name`.
- `quantity` is required if and only if `medicine_id` is set (Pydantic-enforced).
- Existing tests that POST `{"medicine_name": "..."}` with no `medicine_id`/`quantity` must keep passing unchanged.

---

### Task 1: `PrescriptionItem` model + schema — nullable `medicine_id` / `quantity`

**Files:**
- Modify: `backend/app/models/prescription.py`
- Modify: `backend/app/schemas/prescription.py`
- Test: `backend/tests/unit/test_prescription_schema.py` (new)

**Interfaces:**
- Produces: `PrescriptionItem.medicine_id: int | None`, `PrescriptionItem.quantity: int | None` (used by Task 2's service and Task 5's migration).
- Produces: `PrescriptionItemCreate(medicine_name, medicine_id=None, quantity=None, dosage=None, frequency=None, duration=None, instructions=None)` — raises `pydantic.ValidationError` if exactly one of `medicine_id`/`quantity` is set without the other.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_prescription_schema.py`:

```python
import pytest
from pydantic import ValidationError

from app.schemas.prescription import PrescriptionItemCreate


def test_medicine_id_without_quantity_is_rejected():
    with pytest.raises(ValidationError):
        PrescriptionItemCreate(medicine_name="Paracetamol", medicine_id=1)


def test_quantity_without_medicine_id_is_rejected():
    with pytest.raises(ValidationError):
        PrescriptionItemCreate(medicine_name="Paracetamol", quantity=5)


def test_quantity_below_one_is_rejected():
    with pytest.raises(ValidationError):
        PrescriptionItemCreate(medicine_name="Paracetamol", medicine_id=1, quantity=0)


def test_medicine_id_and_quantity_together_is_valid():
    item = PrescriptionItemCreate(medicine_name="Paracetamol", medicine_id=1, quantity=5)
    assert item.medicine_id == 1
    assert item.quantity == 5


def test_free_text_item_without_either_is_valid():
    item = PrescriptionItemCreate(medicine_name="Paracetamol")
    assert item.medicine_id is None
    assert item.quantity is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/unit/test_prescription_schema.py -v`
Expected: FAIL — `ImportError` or `AttributeError`, since `medicine_id`/`quantity` don't exist on the schema yet (extra fields are currently silently ignored by Pydantic's default config, so the "rejected" tests fail by not raising).

- [ ] **Step 3: Update the model**

In `backend/app/models/prescription.py`, change the import line and `PrescriptionItem` class:

```python
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
```

```python
class PrescriptionItem(Base):
    __tablename__ = "prescription_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    prescription_id: Mapped[int] = mapped_column(ForeignKey("prescriptions.id"), nullable=False)

    medicine_name: Mapped[str] = mapped_column(String(128), nullable=False)
    medicine_id: Mapped[int | None] = mapped_column(ForeignKey("medicines.id"), nullable=True)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dosage: Mapped[str | None] = mapped_column(String(64), nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(64), nullable=True)
    duration: Mapped[str | None] = mapped_column(String(64), nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)

    prescription = relationship("Prescription", back_populates="items")
```

(Only the import line and the two new `medicine_id`/`quantity` lines are new — everything else in the file is unchanged.)

- [ ] **Step 4: Update the schema**

Replace `backend/app/schemas/prescription.py` in full with:

```python
from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class PrescriptionItemCreate(BaseModel):
    medicine_name: str = Field(min_length=1, max_length=128)
    medicine_id: int | None = None
    quantity: int | None = Field(default=None, ge=1)
    dosage: str | None = None
    frequency: str | None = None
    duration: str | None = None
    instructions: str | None = None

    @model_validator(mode="after")
    def validate_quantity_paired_with_medicine_id(self) -> "PrescriptionItemCreate":
        if self.medicine_id is not None and self.quantity is None:
            raise ValueError("quantity is required when medicine_id is set")
        if self.medicine_id is None and self.quantity is not None:
            raise ValueError("quantity can only be set together with medicine_id")
        return self


class PrescriptionItemRead(PrescriptionItemCreate):
    id: int

    class Config:
        from_attributes = True


class PrescriptionCreate(BaseModel):
    patient_id: int
    medical_record_id: int | None = None
    items: list[PrescriptionItemCreate] = Field(min_length=1)


class PrescriptionRead(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    medical_record_id: int | None
    created_at: datetime
    items: list[PrescriptionItemRead]

    class Config:
        from_attributes = True
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/unit/test_prescription_schema.py -v`
Expected: PASS (5 passed)

- [ ] **Step 6: Run the full existing test suite to check nothing broke**

Run: `cd backend && python -m pytest -v`
Expected: all pre-existing tests still pass (they post `medicine_name` only, which remains valid — `medicine_id`/`quantity` default to `None`/`None`, satisfying the validator).

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/prescription.py backend/app/schemas/prescription.py backend/tests/unit/test_prescription_schema.py
git commit -m "feat: add nullable medicine_id/quantity to PrescriptionItem"
```

---

### Task 2: `PrescriptionService` — stock validation and decrement

**Files:**
- Modify: `backend/app/services/prescription_service.py`
- Test: `backend/tests/unit/test_prescription_service.py` (new)

**Interfaces:**
- Consumes: `PrescriptionItem.medicine_id`/`quantity` (Task 1), `MedicineRepository.get_with_inventory(id) -> Medicine | None` (`backend/app/repositories/medicine_repository.py`, already exists — eager-loads `.inventory`), `Inventory.quantity` (`backend/app/models/inventory.py`, already exists).
- Produces: `PrescriptionService.__init__(prescription_repo, medicine_repo, audit_service)` (signature changes — Task 3 must update the DI wiring accordingly). `create_with_items(...)` keeps its existing signature and return type but now raises `app.core.exceptions.ValidationError` (422) if requested quantity exceeds available stock for any referenced medicine, and `app.core.exceptions.NotFoundError` (404) if `medicine_id` doesn't exist.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/unit/test_prescription_service.py`:

```python
from datetime import date

import pytest

from app.core.exceptions import ValidationError
from app.models.doctor import Doctor
from app.models.inventory import Inventory
from app.models.medicine import Medicine
from app.models.patient import Patient
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.medicine_repository import MedicineRepository
from app.repositories.prescription_repository import PrescriptionRepository
from app.services.audit_service import AuditService
from app.services.prescription_service import PrescriptionService


async def _setup(db_session, stock_quantity=10):
    doctor_user = User(email="doc-rx@example.com", role="doctor")
    db_session.add(doctor_user)
    await db_session.flush()
    doctor = Doctor(
        user_id=doctor_user.id, employee_id="DOC-RX01", full_name="Dr. Rx", department="General",
        specialization="GP", license_number="LIC-RX01",
    )
    db_session.add(doctor)

    patient_user = User(email="pat-rx@example.com", role="patient")
    db_session.add(patient_user)
    await db_session.flush()
    patient = Patient(
        user_id=patient_user.id, patient_number="PAT-RX-0001", full_name="Rx Patient",
        date_of_birth=date(1990, 1, 1), gender="Other", district="Kathmandu",
    )
    db_session.add(patient)

    medicine = Medicine(name="Paracetamol 500mg", unit="tablets")
    db_session.add(medicine)
    await db_session.flush()
    db_session.add(Inventory(medicine_id=medicine.id, quantity=stock_quantity, reorder_threshold=5))
    await db_session.commit()

    service = PrescriptionService(
        PrescriptionRepository(db_session),
        MedicineRepository(db_session),
        AuditService(AuditLogRepository(db_session)),
    )
    return service, doctor, patient, doctor_user, medicine


def _item(medicine_name, medicine_id=None, quantity=None):
    return {
        "medicine_name": medicine_name, "medicine_id": medicine_id, "quantity": quantity,
        "dosage": None, "frequency": None, "duration": None, "instructions": None,
    }


async def test_create_with_catalog_item_decrements_inventory(db_session):
    service, doctor, patient, doctor_user, medicine = await _setup(db_session)

    await service.create_with_items(
        patient.id, doctor.id, None,
        [_item(medicine.name, medicine.id, 4)],
        doctor_user.id,
    )

    await db_session.refresh(medicine.inventory)
    assert medicine.inventory.quantity == 6


async def test_create_blocks_when_insufficient_stock(db_session):
    service, doctor, patient, doctor_user, medicine = await _setup(db_session, stock_quantity=10)

    with pytest.raises(ValidationError):
        await service.create_with_items(
            patient.id, doctor.id, None,
            [_item(medicine.name, medicine.id, 99)],
            doctor_user.id,
        )

    await db_session.refresh(medicine.inventory)
    assert medicine.inventory.quantity == 10


async def test_create_sums_repeated_medicine_across_items_before_blocking(db_session):
    service, doctor, patient, doctor_user, medicine = await _setup(db_session, stock_quantity=10)

    with pytest.raises(ValidationError):
        await service.create_with_items(
            patient.id, doctor.id, None,
            [_item(medicine.name, medicine.id, 6), _item(medicine.name, medicine.id, 6)],
            doctor_user.id,
        )

    await db_session.refresh(medicine.inventory)
    assert medicine.inventory.quantity == 10  # nothing saved — both items would need 12 total, only 10 available


async def test_create_allows_free_text_item_without_decrementing(db_session):
    service, doctor, patient, doctor_user, medicine = await _setup(db_session)

    prescription = await service.create_with_items(
        patient.id, doctor.id, None,
        [_item("Something not stocked")],
        doctor_user.id,
    )

    await db_session.refresh(medicine.inventory)
    assert medicine.inventory.quantity == 10
    assert prescription.items[0].medicine_id is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/unit/test_prescription_service.py -v`
Expected: FAIL — `PrescriptionService(...)` called with 3 positional args but current `__init__` only takes `(prescription_repo, audit_service)` → `TypeError`.

- [ ] **Step 3: Implement the service logic**

Replace `backend/app/services/prescription_service.py` in full with:

```python
from app.core.exceptions import NotFoundError, ValidationError
from app.models.prescription import Prescription, PrescriptionItem
from app.repositories.medicine_repository import MedicineRepository
from app.repositories.prescription_repository import PrescriptionRepository
from app.services.audit_service import AuditService


class PrescriptionService:
    def __init__(
        self,
        prescription_repo: PrescriptionRepository,
        medicine_repo: MedicineRepository,
        audit_service: AuditService,
    ):
        self.prescription_repo = prescription_repo
        self.medicine_repo = medicine_repo
        self.audit_service = audit_service

    async def create_with_items(
        self,
        patient_id: int,
        doctor_id: int,
        medical_record_id: int | None,
        items: list[dict],
        actor_user_id: int,
    ) -> Prescription:
        # Aggregate requested quantity per medicine across this prescription
        # (two items can reference the same medicine_id) and validate stock
        # for every referenced medicine BEFORE creating anything, so an
        # insufficient-stock error never leaves a partial prescription saved.
        needed: dict[int, int] = {}
        for item in items:
            medicine_id = item.get("medicine_id")
            if medicine_id is not None:
                needed[medicine_id] = needed.get(medicine_id, 0) + item["quantity"]

        medicines = {}
        for medicine_id, quantity in needed.items():
            medicine = await self.medicine_repo.get_with_inventory(medicine_id)
            if not medicine:
                raise NotFoundError(f"Medicine {medicine_id} not found")
            available = medicine.inventory.quantity if medicine.inventory else 0
            if available < quantity:
                raise ValidationError(
                    f"Insufficient stock for {medicine.name}: available {available}, requested {quantity}"
                )
            medicines[medicine_id] = medicine

        prescription = Prescription(patient_id=patient_id, doctor_id=doctor_id, medical_record_id=medical_record_id)
        self.prescription_repo.add(prescription)
        await self.prescription_repo.flush()

        for item in items:
            self.prescription_repo.add(PrescriptionItem(prescription_id=prescription.id, **item))

        for medicine_id, quantity in needed.items():
            medicines[medicine_id].inventory.quantity -= quantity

        await self.audit_service.record(actor_user_id, "created_prescription", "prescription", prescription.id)
        await self.prescription_repo.commit()

        return await self.prescription_repo.get_with_items(prescription.id)

    async def list_filtered(self, patient_id: int | None = None) -> list[Prescription]:
        return await self.prescription_repo.list_filtered(patient_id)

    async def get_with_items(self, prescription_id: int) -> Prescription | None:
        return await self.prescription_repo.get_with_items(prescription_id)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/unit/test_prescription_service.py -v`
Expected: PASS (4 passed)

Note: this will also break `backend/app/dependencies.py::get_prescription_service`, which still constructs `PrescriptionService(PrescriptionRepository(db), audit_service)` with only 2 args — that's fixed in Task 3. Don't run the full suite yet; the integration tests hitting `POST /prescriptions` will fail until Task 3 is done.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/prescription_service.py backend/tests/unit/test_prescription_service.py
git commit -m "feat: validate and decrement inventory stock in PrescriptionService"
```

---

### Task 3: Dependency wiring + Pharmacy RBAC + integration tests

**Files:**
- Modify: `backend/app/dependencies.py:136-140`
- Modify: `backend/app/routers/pharmacy.py`
- Test: `backend/tests/integration/test_clinical_workflows.py` (append to the "EMR + Prescriptions" section)

**Interfaces:**
- Consumes: `PrescriptionService.__init__(prescription_repo, medicine_repo, audit_service)` (Task 2), `MedicineRepository` (already imported in `dependencies.py`).
- Produces: `GET /pharmacy` now allows `doctor` role in addition to `admin`/`receptionist`; `POST`/`PATCH`/`DELETE /pharmacy` remain `admin`/`receptionist`-only.

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/integration/test_clinical_workflows.py`, right after `test_emr_and_prescription_flow_with_nurse_read_only_access` (i.e. after line 193, before the `# ── Lab request / result` section header):

```python
async def test_doctor_can_read_pharmacy_catalog_but_not_write(client, world):
    resp = await client.get("/pharmacy", headers=world["doctor"])
    assert resp.status_code == 200, resp.text

    resp = await client.post(
        "/pharmacy", headers=world["doctor"],
        json={"name": "Should Not Be Created", "unit": "tablets", "stock_quantity": 10, "reorder_threshold": 5},
    )
    assert resp.status_code == 403


async def test_prescribing_catalog_medicine_decrements_stock(client, world):
    resp = await client.post(
        "/pharmacy", headers=world["admin"],
        json={"name": "Ibuprofen 400mg", "unit": "tablets", "stock_quantity": 20, "reorder_threshold": 5},
    )
    assert resp.status_code == 200, resp.text
    medicine = resp.json()

    resp = await client.post(
        "/prescriptions",
        headers=world["doctor"],
        json={
            "patient_id": world["patient_id"],
            "items": [
                {"medicine_name": medicine["name"], "medicine_id": medicine["id"], "quantity": 6, "dosage": "400mg"},
                {"medicine_name": "Herbal tea (not stocked)"},
            ],
        },
    )
    assert resp.status_code == 200, resp.text
    items = resp.json()["items"]
    assert next(i for i in items if i["medicine_id"] == medicine["id"])["quantity"] == 6
    assert next(i for i in items if i["medicine_name"] == "Herbal tea (not stocked)")["medicine_id"] is None

    resp = await client.get("/pharmacy", headers=world["admin"], params={"search": "Ibuprofen"})
    assert resp.json()[0]["stock_quantity"] == 14  # 20 - 6


async def test_prescribing_more_than_available_stock_is_blocked(client, world):
    resp = await client.post(
        "/pharmacy", headers=world["admin"],
        json={"name": "Aspirin 75mg", "unit": "tablets", "stock_quantity": 5, "reorder_threshold": 2},
    )
    medicine = resp.json()

    resp = await client.post(
        "/prescriptions",
        headers=world["doctor"],
        json={
            "patient_id": world["patient_id"],
            "items": [{"medicine_name": medicine["name"], "medicine_id": medicine["id"], "quantity": 6}],
        },
    )
    assert resp.status_code == 422, resp.text

    resp = await client.get("/pharmacy", headers=world["admin"], params={"search": "Aspirin"})
    assert resp.json()[0]["stock_quantity"] == 5  # unchanged — nothing was saved
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/integration/test_clinical_workflows.py -v -k "pharmacy_catalog or decrements_stock or is_blocked"`
Expected: FAIL — `test_doctor_can_read_pharmacy_catalog_but_not_write` fails (doctor currently gets 403 on `GET /pharmacy`); the other two fail with 500 (DI mismatch from Task 2 not yet wired into `get_prescription_service`).

- [ ] **Step 3: Fix the dependency wiring**

In `backend/app/dependencies.py`, replace:

```python
def get_prescription_service(
    db: AsyncSession = Depends(get_db),
    audit_service: AuditService = Depends(get_audit_service),
) -> PrescriptionService:
    return PrescriptionService(PrescriptionRepository(db), audit_service)
```

with:

```python
def get_prescription_service(
    db: AsyncSession = Depends(get_db),
    audit_service: AuditService = Depends(get_audit_service),
) -> PrescriptionService:
    return PrescriptionService(PrescriptionRepository(db), MedicineRepository(db), audit_service)
```

(`MedicineRepository` is already imported at the top of the file — no new import needed.)

- [ ] **Step 4: Split the Pharmacy router's RBAC**

Replace `backend/app/routers/pharmacy.py` in full with:

```python
from fastapi import APIRouter, Depends

from app.dependencies import get_pharmacy_service
from app.schemas.pharmacy import MedicineCreate, MedicineRead, MedicineStockUpdate
from app.security.rbac import require_role
from app.services.pharmacy_service import PharmacyService

router = APIRouter(prefix="/pharmacy", tags=["pharmacy"])


@router.post("", response_model=MedicineRead, dependencies=[Depends(require_role("admin", "receptionist"))])
async def create_medicine(payload: MedicineCreate, service: PharmacyService = Depends(get_pharmacy_service)):
    medicine = await service.create_medicine_with_stock(
        payload.name, payload.category, payload.expiry_date, payload.unit, payload.stock_quantity, payload.reorder_threshold
    )
    return MedicineRead.from_medicine(medicine)


@router.get("", response_model=list[MedicineRead], dependencies=[Depends(require_role("admin", "receptionist", "doctor"))])
async def list_medicines(
    low_stock_only: bool = False, search: str | None = None, service: PharmacyService = Depends(get_pharmacy_service)
):
    medicines = await service.list_medicines(search)
    items = [MedicineRead.from_medicine(m) for m in medicines]
    if low_stock_only:
        items = [i for i in items if i.is_low_stock]
    return items


@router.patch("/{medicine_id}", response_model=MedicineRead, dependencies=[Depends(require_role("admin", "receptionist"))])
async def update_stock(medicine_id: int, payload: MedicineStockUpdate, service: PharmacyService = Depends(get_pharmacy_service)):
    medicine = await service.update_stock(medicine_id, payload.stock_quantity, payload.reorder_threshold)
    return MedicineRead.from_medicine(medicine)


@router.delete("/{medicine_id}", status_code=204, dependencies=[Depends(require_role("admin", "receptionist"))])
async def delete_medicine(medicine_id: int, service: PharmacyService = Depends(get_pharmacy_service)):
    await service.delete_medicine(medicine_id)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/integration/test_clinical_workflows.py -v`
Expected: all tests in the file PASS, including the 3 new ones.

- [ ] **Step 6: Run the full backend suite**

Run: `cd backend && python -m pytest -v`
Expected: all tests pass (this confirms Task 1/2's changes plus the DI fix haven't broken any other router/service that touches prescriptions or pharmacy).

- [ ] **Step 7: Commit**

```bash
git add backend/app/dependencies.py backend/app/routers/pharmacy.py backend/tests/integration/test_clinical_workflows.py
git commit -m "feat: wire MedicineRepository into PrescriptionService; open pharmacy catalog read access to doctors"
```

---

### Task 4: Quantity display — prescription PDF and list view

**Files:**
- Modify: `backend/app/services/pdf_service.py:93-125`
- Modify: `backend/app/routers/prescriptions.py:98-109`
- Modify: `frontend/src/pages/Prescriptions.jsx:73-94`

**Interfaces:**
- Consumes: `PrescriptionItem.quantity` (Task 1), `PrescriptionRead.items[].quantity` (Task 1, already serialized).
- No new interfaces produced — this task is purely additive display.

- [ ] **Step 1: Add a Quantity column to the PDF table**

In `backend/app/services/pdf_service.py`, inside `build_prescription_pdf`, replace:

```python
    rows = [["Medicine", "Dosage", "Frequency", "Duration", "Instructions"]]
    for item in prescription["items"]:
        rows.append([
            item.get("medicine_name") or "—", item.get("dosage") or "—", item.get("frequency") or "—",
            item.get("duration") or "—", item.get("instructions") or "—",
        ])
    table = Table(rows, colWidths=[100, 70, 80, 70, 140])
```

with:

```python
    rows = [["Medicine", "Qty", "Dosage", "Frequency", "Duration", "Instructions"]]
    for item in prescription["items"]:
        rows.append([
            item.get("medicine_name") or "—", str(item.get("quantity") or "—"), item.get("dosage") or "—",
            item.get("frequency") or "—", item.get("duration") or "—", item.get("instructions") or "—",
        ])
    table = Table(rows, colWidths=[95, 35, 65, 75, 65, 125])
```

- [ ] **Step 2: Pass `quantity` through in the router's PDF dict**

In `backend/app/routers/prescriptions.py`, inside `download_prescription_pdf`, replace:

```python
            "items": [
                {
                    "medicine_name": item.medicine_name, "dosage": item.dosage, "frequency": item.frequency,
                    "duration": item.duration, "instructions": item.instructions,
                }
                for item in prescription.items
            ],
```

with:

```python
            "items": [
                {
                    "medicine_name": item.medicine_name, "quantity": item.quantity, "dosage": item.dosage,
                    "frequency": item.frequency, "duration": item.duration, "instructions": item.instructions,
                }
                for item in prescription.items
            ],
```

- [ ] **Step 3: Run the existing PDF test to confirm no regression**

Run: `cd backend && python -m pytest tests/unit/test_pdf_service.py -v`
Expected: PASS — `test_build_prescription_pdf_includes_items` doesn't pass a `quantity` key, so `item.get("quantity")` is `None` and renders as `"—"`; the assertion only checks the PDF still starts with `%PDF`.

- [ ] **Step 4: Add a Quantity column to the Prescriptions list page**

In `frontend/src/pages/Prescriptions.jsx`, replace the table header:

```jsx
              <tr>
                <th>Medicine</th>
                <th>Dosage</th>
                <th>Frequency</th>
                <th>Duration</th>
                <th>Instructions</th>
              </tr>
```

with:

```jsx
              <tr>
                <th>Medicine</th>
                <th>Qty</th>
                <th>Dosage</th>
                <th>Frequency</th>
                <th>Duration</th>
                <th>Instructions</th>
              </tr>
```

and the row body:

```jsx
                  <tr key={item.id}>
                    <td>{item.medicine_name}</td>
                    <td>{item.dosage || "—"}</td>
                    <td>{item.frequency || "—"}</td>
                    <td>{item.duration || "—"}</td>
                    <td>{item.instructions || "—"}</td>
                  </tr>
```

with:

```jsx
                  <tr key={item.id}>
                    <td>{item.medicine_name}</td>
                    <td>{item.quantity ?? "—"}</td>
                    <td>{item.dosage || "—"}</td>
                    <td>{item.frequency || "—"}</td>
                    <td>{item.duration || "—"}</td>
                    <td>{item.instructions || "—"}</td>
                  </tr>
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/pdf_service.py backend/app/routers/prescriptions.py frontend/src/pages/Prescriptions.jsx
git commit -m "feat: show prescription item quantity in PDF and list view"
```

---

### Task 5: Alembic migration + dev DB reset

**Files:**
- Create: `backend/alembic/versions/44008e621ef2_prescription_items_medicine_fk.py`

**Interfaces:**
- Consumes: nothing (schema-only change matching Task 1's model).
- Produces: `prescription_items.medicine_id` (nullable FK to `medicines.id`) and `prescription_items.quantity` (nullable integer) columns on the real (non-test) database.

- [ ] **Step 1: Create the migration file**

Create `backend/alembic/versions/44008e621ef2_prescription_items_medicine_fk.py`:

```python
"""prescription items: medicine_id fk + quantity

Revision ID: 44008e621ef2
Revises: 7436577d53f6
Create Date: 2026-07-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '44008e621ef2'
down_revision: Union[str, None] = '7436577d53f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # batch mode: SQLite can't ALTER TABLE ADD CONSTRAINT directly — batch
    # mode handles the recreate-and-copy dance for it, and is a no-op
    # wrapper (plain ALTER TABLE) on backends that do support it directly.
    with op.batch_alter_table('prescription_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('medicine_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('quantity', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_prescription_items_medicine_id', 'medicines', ['medicine_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('prescription_items', schema=None) as batch_op:
        batch_op.drop_constraint('fk_prescription_items_medicine_id', type_='foreignkey')
        batch_op.drop_column('quantity')
        batch_op.drop_column('medicine_id')
```

- [ ] **Step 2: Reset the local dev database**

Per the design decision (dev/demo data, not worth backfilling): delete the SQLite file so it gets rebuilt clean from the new migration chain.

Run (from `backend/`):
```bash
rm -f MediShield_db.db
```
(On Windows PowerShell: `Remove-Item -Force MediShield_db.db -ErrorAction SilentlyContinue`)

- [ ] **Step 3: Apply the migration chain to the fresh database**

Run: `cd backend && alembic upgrade head`
Expected: output ending in applying `44008e621ef2` with no errors; a new `MediShield_db.db` now exists with the updated `prescription_items` schema.

- [ ] **Step 4: Verify the new columns exist**

Run:
```bash
cd backend && python -c "
import sqlite3
conn = sqlite3.connect('MediShield_db.db')
cols = [row[1] for row in conn.execute('PRAGMA table_info(prescription_items)')]
assert 'medicine_id' in cols and 'quantity' in cols, cols
print('OK:', cols)
"
```
Expected: prints `OK: [...]` including `medicine_id` and `quantity` in the column list.

- [ ] **Step 5: Commit**

```bash
git add backend/alembic/versions/44008e621ef2_prescription_items_medicine_fk.py
git commit -m "feat: add migration for prescription_items.medicine_id/quantity"
```

(The reset `MediShield_db.db` itself is a local runtime artifact — already covered by `backend/*.db` in the root `.gitignore`, so it won't get committed.)

---

### Task 6: Seed data — link seeded prescriptions to the medicine catalog

**Files:**
- Modify: `backend/seed.py`

**Interfaces:**
- Consumes: `Medicine`, `Inventory` models (already imported in `seed.py`), `PrescriptionItem.medicine_id`/`quantity` (Task 1).
- Produces: seeded `prescription_items` rows where the medicine name matches a catalog entry now carry `medicine_id`/`quantity`, with the corresponding `Inventory.quantity` decremented to match — so the freshly-seeded dev DB already demonstrates linked stock, and the Pharmacy page's low-stock states are still reachable.

Prerequisite: Task 5's dev DB reset must have already happened (or happen again after this task, since seed data changes) — the DB needs the new schema before `seed.py` can populate it.

- [ ] **Step 1: Move the "Pharmacy Inventory" section before "Prescriptions"**

In `backend/seed.py`, the sections currently run in this order (numbered headers `# ── N. ...`):
```
7. Medical Records        (line 321)
8. Prescriptions          (line 383)
9. Lab Tests / Results    (line 411)
10. Vitals / Med Admin    (line 443)
11. Pharmacy Inventory    (line 474)
11b. Documents            (line 511)
12. Alerts                (line 543)
13. Security demo data    (line 576)
```

Cut the entire "Pharmacy Inventory" block — from the header comment through its trailing blank line (currently lines 474–510, i.e. from `# ── 11. Pharmacy Inventory (Medicines + Inventory) ──` through the blank line right before `# ── 11b. Documents ──`) — and paste it immediately before the `# ── 8. Prescriptions ──` header (currently line 383), so it runs right after "Medical Records" and before "Prescriptions".

Renumber every section header comment to keep the sequence clean:

| Old label | New label |
|---|---|
| `7. Medical Records` | unchanged |
| *(moved block)* `11. Pharmacy Inventory (Medicines + Inventory)` | `8. Pharmacy Inventory (Medicines + Inventory)` |
| `8. Prescriptions` | `9. Prescriptions` |
| `9. Lab Tests / Results` | `10. Lab Tests / Results` |
| `10. Patient Vitals / Medicine Administration` | `11. Patient Vitals / Medicine Administration` |
| `11b. Documents` | `12. Documents` |
| `12. Alerts` | `13. Alerts` |
| `13. Security demo data (OTP / login / audit logs)` | `14. Security demo data (OTP / login / audit logs)` |

Each is a one-line comment edit, e.g. `# ── 8. Prescriptions ──...` becomes `# ── 9. Prescriptions ──...` (keep each line's existing trailing dashes/length as-is — only the number changes).

- [ ] **Step 2: Link prescription items to the catalog by name, tracking remaining stock**

In the (renumbered) "Prescriptions" section, replace:

```python
if db.query(Prescription).count() == 0:
    count = 0
    for mr in medical_records:
        if not mr.ml_dengue_predicted and rng.random() > 0.3:
            continue
        items = DENGUE_PRESCRIPTION_ITEMS if mr.ml_dengue_predicted else OTHER_PRESCRIPTION_ITEMS
        presc = Prescription(patient_id=mr.patient_id, doctor_id=mr.doctor_id, medical_record_id=mr.id, created_at=mr.created_at)
        db.add(presc)
        db.flush()
        for item in items:
            db.add(PrescriptionItem(prescription_id=presc.id, **item))
        count += 1
    db.flush()
    print(f"  + {count} prescriptions created")
else:
    print(f"  ~ {db.query(Prescription).count()} prescriptions already exist, skipping")
```

with:

```python
# Medicine name -> Medicine row, so seeded prescription items can link to
# the real catalog/inventory the same way the app does at prescribe time.
_medicine_by_name = {m.name: m for m in db.query(Medicine).all()}


def _link_item(item: dict) -> dict:
    """Link an item to its catalog medicine + a small quantity, decrementing
    that medicine's live inventory row as we go. If stock would run out,
    falls back to a free-text-only item (no medicine_id) — the same
    fallback a doctor gets in the real UI when something isn't stocked."""
    medicine = _medicine_by_name.get(item["medicine_name"])
    if not medicine or not medicine.inventory:
        return item
    qty = rng.randint(2, 5)
    if medicine.inventory.quantity < qty:
        return item
    medicine.inventory.quantity -= qty
    return {**item, "medicine_id": medicine.id, "quantity": qty}


if db.query(Prescription).count() == 0:
    count = 0
    for mr in medical_records:
        if not mr.ml_dengue_predicted and rng.random() > 0.3:
            continue
        items = DENGUE_PRESCRIPTION_ITEMS if mr.ml_dengue_predicted else OTHER_PRESCRIPTION_ITEMS
        presc = Prescription(patient_id=mr.patient_id, doctor_id=mr.doctor_id, medical_record_id=mr.id, created_at=mr.created_at)
        db.add(presc)
        db.flush()
        for item in items:
            db.add(PrescriptionItem(prescription_id=presc.id, **_link_item(item)))
        count += 1
    db.flush()
    print(f"  + {count} prescriptions created")
else:
    print(f"  ~ {db.query(Prescription).count()} prescriptions already exist, skipping")
```

- [ ] **Step 3: Run the seeder against the freshly-migrated dev DB**

Run (from `backend/`, after Task 5's `alembic upgrade head` has already been applied to a clean `MediShield_db.db`):
```bash
python seed.py
```
Expected: completes with no errors; console output shows `+ N medicines + inventory rows created` in the (renumbered) Pharmacy section *before* the `+ N prescriptions created` line.

- [ ] **Step 4: Verify the linkage landed in the DB**

Run:
```bash
cd backend && python -c "
import sqlite3
conn = sqlite3.connect('MediShield_db.db')
linked = conn.execute('SELECT COUNT(*) FROM prescription_items WHERE medicine_id IS NOT NULL').fetchone()[0]
total = conn.execute('SELECT COUNT(*) FROM prescription_items').fetchone()[0]
print(f'{linked}/{total} prescription items linked to a catalog medicine')
assert linked > 0
"
```
Expected: prints a nonzero `linked` count (e.g. `.../... prescription items linked`).

- [ ] **Step 5: Commit**

```bash
git add backend/seed.py
git commit -m "feat: seed prescriptions linked to real medicine catalog stock"
```

---

### Task 7: Frontend — catalog dropdown + quantity in the prescribe form

**Files:**
- Modify: `frontend/src/pages/doctor/DiagnosisPrediction.jsx`

**Interfaces:**
- Consumes: `api.listPharmacyItems()` (`frontend/src/api/endpoints.js:70-71`, already exists — now readable by `doctor` role per Task 3) returning `[{id, name, category, expiry_date, unit, stock_quantity, reorder_threshold, is_low_stock}, ...]`. `api.createPrescription(payload)` (`frontend/src/api/endpoints.js:130`, unchanged) — payload's `items[]` now may include `medicine_id`/`quantity`.
- Produces: nothing consumed elsewhere — this is the leaf UI change.

Prerequisite: Task 3 (RBAC) and ideally Task 6 (seed data, so the dropdown has realistic options with visible stock) should already be done so this can be verified end-to-end against a running dev server.

- [ ] **Step 1: Add medicine catalog state + fetch it on mount**

In `frontend/src/pages/doctor/DiagnosisPrediction.jsx`, change:

```jsx
const EMPTY_ITEM = { medicine_name: "", dosage: "", frequency: "", duration: "", instructions: "" };
```

to:

```jsx
const EMPTY_ITEM = { medicine_id: "", medicine_name: "", quantity: "", dosage: "", frequency: "", duration: "", instructions: "" };
```

and change:

```jsx
export default function DiagnosisPrediction() {
  const [patients, setPatients] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [items, setItems] = useState([{ ...EMPTY_ITEM }]);
  const [labTests, setLabTests] = useState([""]);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
```

to:

```jsx
export default function DiagnosisPrediction() {
  const [patients, setPatients] = useState([]);
  const [medicines, setMedicines] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [items, setItems] = useState([{ ...EMPTY_ITEM }]);
  const [labTests, setLabTests] = useState([""]);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
```

and change the existing mount effect:

```jsx
  useEffect(() => {
    // Doctors only see their linked patients now based on backend logic
    api.listPatients().then((res) => setPatients(res.data)).catch(() => {});
  }, []);
```

to:

```jsx
  useEffect(() => {
    // Doctors only see their linked patients now based on backend logic
    api.listPatients().then((res) => setPatients(res.data)).catch(() => {});
    api.listPharmacyItems().then((res) => setMedicines(res.data)).catch(() => {});
  }, []);
```

- [ ] **Step 2: Add a handler for picking a catalog medicine**

Right after the existing `handleItemChange`/`addItemRow`/`removeItemRow` block:

```jsx
  const handleItemChange = (index, field, value) => {
    setItems((rows) => rows.map((row, i) => (i === index ? { ...row, [field]: value } : row)));
  };
  const addItemRow = () => setItems((rows) => [...rows, { ...EMPTY_ITEM }]);
  const removeItemRow = (index) => setItems((rows) => rows.filter((_, i) => i !== index));
```

add:

```jsx
  const handleMedicineSelect = (index, medicineId) => {
    if (!medicineId) {
      setItems((rows) => rows.map((row, i) => (i === index ? { ...row, medicine_id: "", medicine_name: "", quantity: "" } : row)));
      return;
    }
    const medicine = medicines.find((m) => String(m.id) === medicineId);
    setItems((rows) => rows.map((row, i) => (i === index ? { ...row, medicine_id: medicineId, medicine_name: medicine.name, quantity: "" } : row)));
  };
```

- [ ] **Step 3: Build the submit payload with `medicine_id`/`quantity`**

Replace:

```jsx
      const prescriptionItems = items.filter((row) => row.medicine_name.trim());
      if (prescriptionItems.length > 0) {
        await api.createPrescription({
          patient_id: Number(form.patient_id),
          medical_record_id: record.id,
          items: prescriptionItems,
        });
      }
```

with:

```jsx
      const prescriptionItems = items
        .filter((row) => row.medicine_name.trim())
        .map((row) => ({
          medicine_name: row.medicine_name,
          medicine_id: row.medicine_id ? Number(row.medicine_id) : null,
          quantity: row.quantity ? Number(row.quantity) : null,
          dosage: row.dosage,
          frequency: row.frequency,
          duration: row.duration,
          instructions: row.instructions,
        }));
      if (prescriptionItems.length > 0) {
        await api.createPrescription({
          patient_id: Number(form.patient_id),
          medical_record_id: record.id,
          items: prescriptionItems,
        });
      }
```

- [ ] **Step 4: Replace the free-text Medicine field with the catalog dropdown + quantity**

Replace:

```jsx
          <div className="section-title" style={{ marginTop: 20 }}>Prescription (optional)</div>
          {items.map((row, i) => (
            <div key={i} className="form-row" style={{ alignItems: "flex-end", marginBottom: 8 }}>
              <div className="form-group">
                <label>Medicine</label>
                <input value={row.medicine_name} onChange={(e) => handleItemChange(i, "medicine_name", e.target.value)} placeholder="e.g. Paracetamol 500mg" />
              </div>
              <div className="form-group">
                <label>Dosage</label>
                <input value={row.dosage} onChange={(e) => handleItemChange(i, "dosage", e.target.value)} placeholder="500mg" />
              </div>
              <div className="form-group">
                <label>Frequency</label>
                <input value={row.frequency} onChange={(e) => handleItemChange(i, "frequency", e.target.value)} placeholder="3x/day" />
              </div>
              <div className="form-group">
                <label>Duration</label>
                <input value={row.duration} onChange={(e) => handleItemChange(i, "duration", e.target.value)} placeholder="5 days" />
              </div>
              <div className="form-group">
                <label>Instructions</label>
                <input value={row.instructions} onChange={(e) => handleItemChange(i, "instructions", e.target.value)} placeholder="After meals" />
              </div>
              {items.length > 1 && (
                <button type="button" className="btn secondary" onClick={() => removeItemRow(i)} style={{ marginBottom: 14 }}>
                  Remove
                </button>
              )}
            </div>
          ))}
```

with:

```jsx
          <div className="section-title" style={{ marginTop: 20 }}>Prescription (optional)</div>
          {items.map((row, i) => {
            const selectedMedicine = medicines.find((m) => String(m.id) === row.medicine_id);
            return (
              <div key={i} className="form-row" style={{ alignItems: "flex-end", marginBottom: 8 }}>
                <div className="form-group">
                  <label>Medicine</label>
                  <select value={row.medicine_id} onChange={(e) => handleMedicineSelect(i, e.target.value)}>
                    <option value="">— Custom (not in pharmacy) —</option>
                    {medicines.map((m) => (
                      <option key={m.id} value={m.id}>{m.name} ({m.unit})</option>
                    ))}
                  </select>
                  {!row.medicine_id && (
                    <input
                      style={{ marginTop: 6 }}
                      value={row.medicine_name}
                      onChange={(e) => handleItemChange(i, "medicine_name", e.target.value)}
                      placeholder="e.g. Paracetamol 500mg"
                    />
                  )}
                </div>
                {row.medicine_id && (
                  <div className="form-group">
                    <label>Quantity</label>
                    <input
                      type="number"
                      min={1}
                      max={selectedMedicine?.stock_quantity}
                      value={row.quantity}
                      onChange={(e) => handleItemChange(i, "quantity", e.target.value)}
                      placeholder="e.g. 10"
                    />
                    <div style={{ fontSize: 12, color: "var(--color-text-muted)", marginTop: 4 }}>
                      {selectedMedicine?.stock_quantity ?? 0} {selectedMedicine?.unit} in stock
                    </div>
                  </div>
                )}
                <div className="form-group">
                  <label>Dosage</label>
                  <input value={row.dosage} onChange={(e) => handleItemChange(i, "dosage", e.target.value)} placeholder="500mg" />
                </div>
                <div className="form-group">
                  <label>Frequency</label>
                  <input value={row.frequency} onChange={(e) => handleItemChange(i, "frequency", e.target.value)} placeholder="3x/day" />
                </div>
                <div className="form-group">
                  <label>Duration</label>
                  <input value={row.duration} onChange={(e) => handleItemChange(i, "duration", e.target.value)} placeholder="5 days" />
                </div>
                <div className="form-group">
                  <label>Instructions</label>
                  <input value={row.instructions} onChange={(e) => handleItemChange(i, "instructions", e.target.value)} placeholder="After meals" />
                </div>
                {items.length > 1 && (
                  <button type="button" className="btn secondary" onClick={() => removeItemRow(i)} style={{ marginBottom: 14 }}>
                    Remove
                  </button>
                )}
              </div>
            );
          })}
```

- [ ] **Step 5: Manually verify in the browser**

This app has no JS test framework (`frontend/package.json` has no `test` script) — verify by running the app:

1. Start the backend: `cd backend && uvicorn app.main:app --reload` (serves on `http://127.0.0.1:8000`, interactive docs at `/docs`).
2. Start the frontend: `cd frontend && npm run dev` (serves on `http://127.0.0.1:5173`, proxies `/api` to the backend).
3. Log in as a seeded doctor, e.g. `sharma@example.com` / `Doctor@1234` (from `backend/seed.py`'s `DOCTOR_DATA` — email is the doctor's second name word, lowercased, `@example.com`; password `Doctor@1234` for all seeded doctors).
4. Navigate to the "Fill Diagnosis & Record" page (`DiagnosisPrediction.jsx`, routed in `frontend/src/App.jsx`).
5. Select a patient, and in the Prescription section: confirm the Medicine field is now a dropdown listing seeded catalog medicines (e.g. "Paracetamol 500mg (tablets)") plus "— Custom (not in pharmacy) —".
6. Pick a catalog medicine: confirm a Quantity field appears showing "<N> tablets in stock".
7. Enter a quantity well within stock, save the record: confirm success, then check the Pharmacy page (admin/receptionist) shows that medicine's stock reduced by the requested amount.
8. Repeat, entering a quantity greater than the displayed stock: confirm the save fails with an error message mentioning insufficient stock (surfaced via the existing `error` banner, which already renders `err.response?.data?.detail`).
9. Add a second item, leave it on "— Custom (not in pharmacy) —", type a free-text name: confirm it saves successfully with no stock effect.
10. Check the Prescriptions history page and the downloaded PDF for that prescription: confirm the Quantity column/field shows correctly for the catalog item and "—" for the custom one.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/doctor/DiagnosisPrediction.jsx
git commit -m "feat: prescribe from pharmacy catalog with quantity, auto-decrementing stock"
```

---

## Post-plan check

After all 7 tasks: run `cd backend && python -m pytest -v` one final time (full suite) and confirm the manual browser walkthrough in Task 7 Step 5 was completed. At that point the feature described in the design spec — prescribe → stock drops → low-stock reflected on the Pharmacy/dashboard views — is fully wired, with free-text prescribing for non-catalog medicines preserved.
