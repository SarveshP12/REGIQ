"""AES-256-GCM encryption and decryption utilities for sensitive credentials at rest."""

import base64
import hashlib
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.core.config import get_settings

settings = get_settings()


def _get_key() -> bytes:
    """Derive a 256-bit (32 bytes) key from the application secret key using SHA-256."""
    return hashlib.sha256(settings.app_secret_key.encode("utf-8")).digest()


def encrypt_field(plain_text: str) -> str:
    """Encrypt a string using AES-256-GCM.

    Returns a base64-encoded string combining the 12-byte nonce and ciphertext.
    """
    if not plain_text:
        return ""
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct_bytes = aesgcm.encrypt(nonce, plain_text.encode("utf-8"), None)
    return base64.b64encode(nonce + ct_bytes).decode("utf-8")


def decrypt_field(cipher_text: str) -> str:
    """Decrypt an AES-256-GCM encrypted base64 string back to plaintext."""
    if not cipher_text:
        return ""
    key = _get_key()
    aesgcm = AESGCM(key)
    try:
        data = base64.b64decode(cipher_text.encode("utf-8"))
        if len(data) < 12:
            raise ValueError("Ciphertext is too short")
        nonce = data[:12]
        ct = data[12:]
        pt_bytes = aesgcm.decrypt(nonce, ct, None)
        return pt_bytes.decode("utf-8")
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}")
