# meshcore_py_node/group.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from meshcore_py_node.crypto.utils import sha256, mac_then_encrypt, mac_then_decrypt


@dataclass
class GroupChannel:
    """
    Group channel with shared secret.
    """
    _hash_prefix: bytes  # 2-byte channel hash prefix (covers both V1 and V2)
    secret: bytes        # 16-byte AES key

    @classmethod
    def from_secret(cls, secret: bytes) -> "GroupChannel":
        full = sha256(secret)
        return cls(_hash_prefix=full[:2], secret=full[:16])

    def get_hash(self, hash_size: int = 1) -> bytes:
        """Return hash_size bytes of the channel hash (1 for V1, 2 for V2)."""
        return self._hash_prefix[:hash_size]

    @property
    def hash(self) -> bytes:
        """1-byte channel hash — V1 backward-compat alias for get_hash(1)."""
        return self._hash_prefix[:1]

    def encrypt(self, plaintext: bytes) -> bytes:
        return mac_then_encrypt(self.secret, plaintext)

    def decrypt(self, enc_and_mac: bytes) -> Optional[bytes]:
        return mac_then_decrypt(self.secret, enc_and_mac)
