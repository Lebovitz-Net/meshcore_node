# meshcore_py_node/packet/packet.py

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from meshcore_py_node.packet.header import RouteType, PayloadType, PayloadVersion
from meshcore_py_node.constants import PATH_HASH_SIZE_V1, PATH_HASH_SIZE_V2, MAX_PATH_LEN
from meshcore_py_node.crypto.utils import sha256


@dataclass
class MeshCorePacket:
    route: RouteType
    payload_type: PayloadType
    version: PayloadVersion
    path_len: int        # raw byte count from wire (not hop count)
    path: bytes
    payload: bytes
    snr: Optional[float] = None
    rssi: Optional[float] = None
    transport_codes: Optional[bytes] = None  # 4 bytes, only for TRANSPORT_* routes

    @property
    def hash_size(self) -> int:
        """Number of bytes per hash entry for this packet's version."""
        return PATH_HASH_SIZE_V2 if self.version == PayloadVersion.V2 else PATH_HASH_SIZE_V1

    @classmethod
    def from_bytes(cls, raw: bytes) -> "MeshCorePacket":
        if len(raw) < 2:
            raise ValueError("Packet too short")

        header = raw[0]
        # Firmware header layout: bits[1:0]=ROUTE, bits[5:2]=TYPE, bits[7:6]=VER
        route = RouteType(header & 0x03)
        payload_type = PayloadType((header >> 2) & 0x0F)
        version = PayloadVersion((header >> 6) & 0x03)

        offset = 1

        # Transport codes present only for TRANSPORT_FLOOD / TRANSPORT_DIRECT
        transport_codes: Optional[bytes] = None
        if route in (RouteType.TRANSPORT_FLOOD, RouteType.TRANSPORT_DIRECT):
            if len(raw) < offset + 4:
                raise ValueError("Packet transport codes truncated")
            transport_codes = raw[offset : offset + 4]
            offset += 4

        if len(raw) < offset + 1:
            raise ValueError("Packet too short for path_len")
        path_len = raw[offset]
        offset += 1

        if path_len > MAX_PATH_LEN:
            raise ValueError(f"path_len {path_len} exceeds MAX_PATH_LEN {MAX_PATH_LEN}")
        if len(raw) < offset + path_len:
            raise ValueError("Packet path truncated")

        path = raw[offset : offset + path_len]
        offset += path_len

        payload = raw[offset:]

        return cls(
            route=route,
            payload_type=payload_type,
            version=version,
            path_len=path_len,
            path=path,
            payload=payload,
            transport_codes=transport_codes,
        )

    def to_bytes(self) -> bytes:
        # Firmware header: bits[1:0]=ROUTE, bits[5:2]=TYPE, bits[7:6]=VER
        header = (
            (self.route & 0x03)
            | ((self.payload_type & 0x0F) << 2)
            | ((self.version & 0x03) << 6)
        )
        buf = bytes([header])
        if self.transport_codes is not None:
            buf += self.transport_codes
        buf += bytes([self.path_len]) + self.path + self.payload
        return buf

    def compute_hash(self) -> bytes:
        """Hash used for dedupe."""
        return sha256(self.to_bytes())

    def iter_path_hashes(self):
        """
        Yield each hop's hash bytes from the path field.
        Hash size is 1 byte (V1) or 2 bytes (V2).
        For TRACE packets the SNR byte preceding each hash is skipped.
        path_len is the raw byte count; hop count is derived from it.
        """
        if self.path_len == 0:
            return
        hs = self.hash_size
        if self.payload_type == PayloadType.TRACE:
            per_hop = 1 + hs   # 1 SNR byte + hash bytes
            n_hops = self.path_len // per_hop
            for i in range(n_hops):
                yield self.path[i * per_hop + 1 : i * per_hop + 1 + hs]
        else:
            n_hops = self.path_len // hs
            for i in range(n_hops):
                yield self.path[i * hs : (i + 1) * hs]

    def iter_trace_entries(self):
        """
        For TRACE packets: yield (snr_float, hash_bytes) per hop.
        SNR is stored as quarter-dB units (multiply by 0.25 to get dB).
        Hash size is 1 byte (V1) or 2 bytes (V2).
        """
        if self.payload_type != PayloadType.TRACE:
            return
        hs = self.hash_size
        per_hop = 1 + hs
        n_hops = self.path_len // per_hop
        for i in range(n_hops):
            snr_byte = self.path[i * per_hop]
            h = self.path[i * per_hop + 1 : i * per_hop + 1 + hs]
            snr = snr_byte / 4.0
            yield (snr, h)
