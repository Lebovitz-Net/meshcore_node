# meshcore_node/packet/advert.py

from __future__ import annotations
from dataclasses import dataclass

from meshcore_node.crypto.identity import Identity


@dataclass
class Advert:
    identity: Identity
    timestamp: int
    app_data: bytes


def build_advert_payload(identity: Identity, timestamp: int, app_data: bytes) -> bytes:
    """
    Simple format:
      pubkey[32] | timestamp[4, big-endian] | app_data[..]
    """
    pub = identity.pub_key
    if len(pub) != 32:
        raise ValueError("Expected 32-byte public key")
    ts_bytes = timestamp.to_bytes(4, "big")
    return pub + ts_bytes + app_data


def parse_advert(payload: bytes) -> Advert:
    if len(payload) < 32 + 4:
        raise ValueError("ADVERT payload too short")

    pub = payload[:32]
    ts = int.from_bytes(payload[32:36], "big")
    app_data = payload[36:]

    ident = Identity(pub_key=pub)
    return Advert(identity=ident, timestamp=ts, app_data=app_data)
