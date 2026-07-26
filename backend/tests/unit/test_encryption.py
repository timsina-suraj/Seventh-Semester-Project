from datetime import date

from app.models.patient import Patient
from app.models.user import User
from app.security.encryption import decrypt_value, encrypt_value


def test_encrypt_decrypt_round_trip():
    plaintext = "9800100001"
    ciphertext = encrypt_value(plaintext)

    assert ciphertext != plaintext
    assert decrypt_value(ciphertext) == plaintext


def test_encrypt_is_nondeterministic():
    """AES-GCM uses a random nonce per call, so encrypting the same
    plaintext twice must not produce the same ciphertext (otherwise
    equal-plaintext rows would be distinguishable at rest)."""
    a = encrypt_value("same-value")
    b = encrypt_value("same-value")
    assert a != b
    assert decrypt_value(a) == decrypt_value(b) == "same-value"


async def test_patient_phone_round_trips_through_the_orm(db_session):
    user = User(email="enc-test@example.com", role="patient")
    db_session.add(user)
    await db_session.flush()

    patient = Patient(
        user_id=user.id,
        patient_number="PAT-TEST-0001",
        full_name="Test Patient",
        date_of_birth=date(2000, 1, 1),
        gender="Other",
        district="Kathmandu",
        encrypted_phone="9800000000",
    )
    db_session.add(patient)
    await db_session.commit()
    await db_session.refresh(patient)

    assert patient.encrypted_phone == "9800000000"
