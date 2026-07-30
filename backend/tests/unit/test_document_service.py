from datetime import date

import pytest

from app.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.models.patient import Patient
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.services.document_service import DocumentService


@pytest.fixture(autouse=True)
def _isolated_upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))


async def _make_patient(db_session) -> Patient:
    user = User(email="doc-owner@example.com", role="patient")
    db_session.add(user)
    await db_session.flush()
    uploader = User(email="doc-uploader@example.com", role="admin")
    db_session.add(uploader)
    await db_session.flush()
    patient = Patient(
        user_id=user.id, patient_number="PAT-DOC-0001", full_name="Doc Patient",
        date_of_birth=date(1990, 1, 1), gender="Other", district="Kathmandu",
    )
    db_session.add(patient)
    await db_session.flush()
    return patient, uploader


async def test_upload_persists_file_and_metadata(db_session):
    patient, uploader = await _make_patient(db_session)
    service = DocumentService(DocumentRepository(db_session))

    document = await service.upload(patient.id, "Lab Report", "cbc.pdf", "application/pdf", b"%PDF-fake-bytes", uploader.id)

    assert document.original_filename == "cbc.pdf"
    assert document.file_size == len(b"%PDF-fake-bytes")
    assert service.read_file(document) == b"%PDF-fake-bytes"


async def test_upload_rejects_invalid_category(db_session):
    patient, uploader = await _make_patient(db_session)
    service = DocumentService(DocumentRepository(db_session))

    with pytest.raises(ValidationError):
        await service.upload(patient.id, "Not A Real Category", "f.txt", "text/plain", b"x", uploader.id)


async def test_upload_rejects_oversized_file(db_session, monkeypatch):
    monkeypatch.setattr(settings, "max_upload_size_mb", 0)  # any non-empty file now exceeds the limit
    patient, uploader = await _make_patient(db_session)
    service = DocumentService(DocumentRepository(db_session))

    with pytest.raises(ValidationError):
        await service.upload(patient.id, "Other", "f.txt", "text/plain", b"some content", uploader.id)


async def test_upload_rejects_empty_file(db_session):
    patient, uploader = await _make_patient(db_session)
    service = DocumentService(DocumentRepository(db_session))

    with pytest.raises(ValidationError):
        await service.upload(patient.id, "Other", "empty.txt", "text/plain", b"", uploader.id)


async def test_list_filtered_by_patient_and_category(db_session):
    patient, uploader = await _make_patient(db_session)
    service = DocumentService(DocumentRepository(db_session))
    await service.upload(patient.id, "Lab Report", "a.pdf", "application/pdf", b"%PDF-a", uploader.id)
    await service.upload(patient.id, "Insurance", "b.pdf", "application/pdf", b"%PDF-b", uploader.id)

    all_docs = await service.list_filtered(patient.id)
    lab_only = await service.list_filtered(patient.id, "Lab Report")

    assert len(all_docs) == 2
    assert len(lab_only) == 1
    assert lab_only[0].category == "Lab Report"


async def test_delete_removes_file_from_disk(db_session, tmp_path):
    patient, uploader = await _make_patient(db_session)
    service = DocumentService(DocumentRepository(db_session))
    document = await service.upload(patient.id, "Other", "f.pdf", "application/pdf", b"%PDF-content", uploader.id)
    stored_path = tmp_path / document.stored_filename
    assert stored_path.exists()

    await service.delete(document)

    assert not stored_path.exists()
    with pytest.raises(NotFoundError):
        await service.get_or_404(document.id)


async def test_get_or_404_raises_for_missing_document(db_session):
    service = DocumentService(DocumentRepository(db_session))
    with pytest.raises(NotFoundError):
        await service.get_or_404(999)
