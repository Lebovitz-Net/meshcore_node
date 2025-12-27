# meshcore_node/packet/packet.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from meshcore_node.packet.header import RouteType, PayloadType, PayloadVersion
from meshcore_node.constants import PATH_HASH_SIZE, MAX_PATH_LEN
from meshcore_node.crypto.utils import sha256


@dataclass
class MeshCorePacket:
    route: RouteType
    payload_type: PayloadType
    version: PayloadVersion
    path_len: int
    path: bytes
    payload: bytes
    snr: Optional[float] = None
    rssi: Optional[float] = None

    @classmethod
    def from_bytes(cls, raw: bytes) -> "MeshCorePacket":
        if len(raw) < 2:
            raise ValueError("Packet too short")

        header = raw[0]
        path_len = raw[1]

        route = RouteType((header >> 6) & 0x03)
        payload_type = PayloadType(header & 0x3F)

        offset = 2
        path_bytes = path_len
        if len(raw) < offset + path_bytes:
            raise ValueError("Packet path truncated")

        path = raw[offset : offset + path_bytes]
        offset += path_bytes

        payload = raw[offset:]

        return cls(
            route=route,
            payload_type=payload_type,
            version=PayloadVersion.V1,
            path_len=path_len,
            path=path,
            payload=payload,
        )

    def to_bytes(self) -> bytes:
        header = ((self.route & 0x03) << 6) | (self.payload_type & 0x3F)
        return bytes([header, self.path_len]) + self.path + self.payload

    def compute_hash(self) -> bytes:
        """
        Hash used for dedupe.
        """
        return sha256(self.to_bytes())

    def iter_path_hashes(self):
        """
        For PATH packets: yield each hop's 1-byte hash.
        For TRACE packets: yield each hop's hash (ignoring SNR).
        """
        if self.path_len == 0:
            return
        if self.payload_type == PayloadType.TRACE:
            per_hop = 1 + PATH_HASH_SIZE
            for i in range(self.path_len):
                _snr_byte = self.path[i * per_hop]
                h = self.path[i * per_hop + 1]
                yield h.to_bytes(1, "little")
        else:
            for i in range(self.path_len):
                yield self.path[i : i + 1]

    def iter_trace_entries(self):
        """
        For TRACE packets: yield (snr_float, hash_byte).
        """
        if self.payload_type != PayloadType.TRACE:
            return
        per_hop = 1 + PATH_HASH_SIZE
        for i in range(self.path_len):
            snr_byte = self.path[i * per_hop]
            h = self.path[i * per_hop + 1]
            snr = snr_byte / 4.0
            yield (snr, h.to_bytes(1, "little"))
