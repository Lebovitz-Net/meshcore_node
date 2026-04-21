# meshcore_py_node/builder.py

from __future__ import annotations

from meshcore_py_node.packet.packet import MeshCorePacket
from meshcore_py_node.packet.header import RouteType, PayloadType, PayloadVersion
from meshcore_py_node.crypto.identity import Identity, LocalIdentity
from meshcore_py_node.group import GroupChannel
from meshcore_py_node.packet.advert import build_advert_payload


def build_advert(
    identity: LocalIdentity,
    timestamp: int,
    app_data: bytes,
    version: PayloadVersion = PayloadVersion.V1,
) -> MeshCorePacket:
    payload = build_advert_payload(identity, timestamp, app_data)
    return MeshCorePacket(
        route=RouteType.FLOOD,
        payload_type=PayloadType.ADVERT,
        version=version,
        path_len=0,
        path=b"",
        payload=payload,
    )


def build_direct_datagram(
    src: LocalIdentity,
    dest: Identity,
    plaintext: bytes,
    version: PayloadVersion = PayloadVersion.V1,
) -> MeshCorePacket:
    hash_size = 1 if version == PayloadVersion.V1 else 2
    dest_hash = dest.hash(hash_size)
    src_hash = src.hash(hash_size)
    enc = src.encrypt_for(dest, plaintext)
    payload = dest_hash + src_hash + enc

    return MeshCorePacket(
        route=RouteType.DIRECT,
        payload_type=PayloadType.TXT_MSG,
        version=version,
        path_len=0,
        path=b"",
        payload=payload,
    )


def build_group_datagram(
    group: GroupChannel,
    plaintext: bytes,
    version: PayloadVersion = PayloadVersion.V1,
) -> MeshCorePacket:
    hash_size = 1 if version == PayloadVersion.V1 else 2
    enc = group.encrypt(plaintext)
    payload = group.get_hash(hash_size) + enc

    return MeshCorePacket(
        route=RouteType.FLOOD,
        payload_type=PayloadType.GRP_TXT,
        version=version,
        path_len=0,
        path=b"",
        payload=payload,
    )


def build_ack(crc: int, version: PayloadVersion = PayloadVersion.V1) -> MeshCorePacket:
    payload = crc.to_bytes(2, "little", signed=False)
    return MeshCorePacket(
        route=RouteType.FLOOD,
        payload_type=PayloadType.ACK,
        version=version,
        path_len=0,
        path=b"",
        payload=payload,
    )


def build_path_packet(
    route: RouteType,
    payload_type: PayloadType,
    version: PayloadVersion,
    path_hashes: list[bytes],
    payload: bytes,
) -> MeshCorePacket:
    path = b"".join(path_hashes)
    return MeshCorePacket(
        route=route,
        payload_type=payload_type,
        version=version,
        path_len=len(path_hashes),
        path=path,
        payload=payload,
    )


def build_trace_packet(
    route: RouteType,
    version: PayloadVersion,
    trace_entries: list[tuple[float, bytes]],
    payload: bytes,
) -> MeshCorePacket:
    path_bytes = bytearray()
    for snr, h in trace_entries:
        snr_byte = int(max(0, min(255, snr * 4)))
        path_bytes.append(snr_byte)
        path_bytes += h

    return MeshCorePacket(
        route=route,
        payload_type=PayloadType.TRACE,
        version=version,
        path_len=len(trace_entries),
        path=bytes(path_bytes),
        payload=payload,
    )


def build_raw_custom(payload: bytes, version: PayloadVersion = PayloadVersion.V1) -> MeshCorePacket:
    return MeshCorePacket(
        route=RouteType.FLOOD,
        payload_type=PayloadType.RAW_CUSTOM,
        version=version,
        path_len=0,
        path=b"",
        payload=payload,
    )
