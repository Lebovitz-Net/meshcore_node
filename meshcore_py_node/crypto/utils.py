# meshcore_py_node/crypto/utils.py

from __future__ import annotations
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import hashlib


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def random_bytes(n: int) -> bytes:
    return os.urandom(n)


def mac_then_encrypt(key: bytes, plaintext: bytes) -> bytes:
    """
    AES-128-GCM style: random 12-byte nonce + ciphertext+tag.
    MeshCore uses "MAC-then-encrypt" semantics; here we treat
    GCM as a combined mode.
    """
    if len(key) != 16:
        raise ValueError("Expected 16-byte AES key")
    aes = AESGCM(key)
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, plaintext, None)
    return nonce + ct


def mac_then_decrypt(key: bytes, enc: bytes) -> Optional[bytes]:
    if len(key) != 16:
        return None
    if len(enc) < 12 + 16:
        return None
    nonce = enc[:12]
    ct = enc[12:]
    aes = AESGCM(key)
    try:
        return aes.decrypt(nonce, ct, None)
    except Exception:
        return None
