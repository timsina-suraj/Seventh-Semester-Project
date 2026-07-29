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
