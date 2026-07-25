"""AES-256-GCM field-level encryption for sensitive healthcare data at rest.
"""
import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import String
from sqlalchemy.types import TypeDecorator

from app.config import settings

_NONCE_SIZE = 12  # bytes, recommended size for AES-GCM


def _get_key() -> bytes:
    key = base64.urlsafe_b64decode(settings.encryption_key.encode())
    if len(key) != 32:
        raise ValueError("encryption_key must decode to exactly 32 bytes for AES-256")
    return key


def encrypt_value(plaintext: str) -> str:
    """Encrypts a string, returning a urlsafe-base64 blob of nonce||ciphertext."""
    if plaintext is None:
        return None
    aesgcm = AESGCM(_get_key())
    nonce = os.urandom(_NONCE_SIZE)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), associated_data=None)
    return base64.urlsafe_b64encode(nonce + ciphertext).decode("utf-8")


def decrypt_value(token: str) -> str:
    """Reverses encrypt_value. Returns the token unchanged if it isn't valid
    ciphertext (defensive, e.g. for legacy/plaintext rows during migration)."""
    if token is None:
        return None
    try:
        raw = base64.urlsafe_b64decode(token.encode("utf-8"))
        nonce, ciphertext = raw[:_NONCE_SIZE], raw[_NONCE_SIZE:]
        aesgcm = AESGCM(_get_key())
        return aesgcm.decrypt(nonce, ciphertext, associated_data=None).decode("utf-8")
    except Exception:
        return token


class EncryptedString(TypeDecorator):
    """A SQLAlchemy column type that transparently AES-256-GCM encrypts on
    write and decrypts on read."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return encrypt_value(str(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return decrypt_value(value)
