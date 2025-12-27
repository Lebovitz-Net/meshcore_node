# meshcore_node/group.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from meshcore_node.crypto.utils import sha256, mac_then_encrypt, mac_then_decrypt


@dataclass
class GroupChannel:
    """
    Group channel with shared secret.
    """
    hash: bytes    # 1-byte channel hash
    secret: bytes  # 16-byte AES key

    @classmethod
    def from_secret(cls, secret: bytes) -> "GroupChannel":
        full = sha256(secret)
        return cls(hash=full[:1], secret=full[:16])

    def encrypt(self, plaintext: bytes) -> bytes:
        return mac_then_encrypt(self.secret, plaintext)

    def decrypt(self, enc_and_mac: bytes) -> Optional[bytes]:
        return mac_then_decrypt(self.secret, enc_and_mac)
