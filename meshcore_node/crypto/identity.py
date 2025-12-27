# meshcore_node/crypto/identity.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives import serialization

from meshcore_node.crypto.utils import sha256, mac_then_encrypt, mac_then_decrypt


@dataclass
class Identity:
    """
    Public-only identity used for peers.
    """
    pub_key: bytes  # Ed25519 public key

    def hash(self) -> bytes:
        """
        1-byte identity hash prefix (MeshCore style).
        """
        full = sha256(self.pub_key)
        return full[:1]


class LocalIdentity(Identity):
    """
    Local identity with private keys for signing and key agreement.
    """

    def __init__(self, prv_key: Optional[bytes] = None):
        if prv_key is None:
            sk = Ed25519PrivateKey.generate()
            self._ed25519_sk = sk
            self._ed25519_pk = sk.public_key()
        else:
            sk = Ed25519PrivateKey.from_private_bytes(prv_key)
            self._ed25519_sk = sk
            self._ed25519_pk = sk.public_key()

        pub_bytes = self._ed25519_pk.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        super().__init__(pub_key=pub_bytes)

        # X25519 for ECDH
        self._x25519_sk = X25519PrivateKey.generate()
        self._x25519_pk = self._x25519_sk.public_key()

    @property
    def prv_key(self) -> bytes:
        return self._ed25519_sk.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )

    def calc_shared_secret(self, peer: Identity) -> bytes:
        """
        Derive symmetric key via X25519-like semantics.
        For simplicity, reuse Ed25519 public as X25519 public via sha256.
        """
        # This is a simplification: in a real implementation you'd have separate
        # X25519 public keys. Here we just derive a pseudo public key from pub_key.
        peer_hash = sha256(peer.pub_key)
        peer_x_pub = X25519PublicKey.from_public_bytes(peer_hash[:32])
        shared = self._x25519_sk.exchange(peer_x_pub)
        # Collapse to 16 bytes AES key:
        return sha256(shared)[:16]

    def encrypt_for(self, peer: Identity, plaintext: bytes) -> bytes:
        key = self.calc_shared_secret(peer)
        return mac_then_encrypt(key, plaintext)

    def decrypt_from(self, peer: Identity, enc_and_mac: bytes) -> Optional[bytes]:
        key = self.calc_shared_secret(peer)
        return mac_then_decrypt(key, enc_and_mac)
