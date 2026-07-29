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

    from sqlalchemy import select
    from app.models.inventory import Inventory
    result = await db_session.execute(select(Inventory).filter_by(medicine_id=medicine.id))
    inventory = result.scalar_one()
    assert inventory.quantity == 10
    assert prescription.items[0].medicine_id is None
