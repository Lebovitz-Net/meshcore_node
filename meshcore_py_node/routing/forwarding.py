# meshcore_py_node/routing/forwarding.py

from __future__ import annotations
from typing import Optional

from meshcore_py_node.packet.packet import MeshCorePacket
from meshcore_py_node.packet.header import RouteType, PayloadType
from meshcore_py_node.constants import PATH_HASH_SIZE


class ForwardingDecision:
    def __init__(self, forward: bool, packet: Optional[MeshCorePacket] = None):
        self.forward = forward
        self.packet = packet


class ForwardingRouter:
    """
    Implements inbound routing decisions and PATH/TRACE modifications.
    """

    def __init__(self, identity_hash: bytes):
        self.identity_hash = identity_hash  # 1-byte hash of local identity

    def decide(self, pkt: MeshCorePacket) -> ForwardingDecision:
        rt = pkt.route

        # Direct packets: forward only if not addressed to us
        if rt == RouteType.DIRECT:
            if not self._is_direct_for_me(pkt):
                return ForwardingDecision(True, pkt)
            return ForwardingDecision(False)

        # Flood packets: may need PATH/TRACE modification
        if rt == RouteType.FLOOD:
            return self._handle_flood(pkt)

        # Transport modes (if any) default to flood behavior
        return self._handle_flood(pkt)

    def _is_direct_for_me(self, pkt: MeshCorePacket) -> bool:
        if len(pkt.payload) < 1:
            return False
        dest_hash = pkt.payload[0:1]
        return dest_hash == self.identity_hash

    def _handle_flood(self, pkt: MeshCorePacket) -> ForwardingDecision:
        if pkt.payload_type == PayloadType.PATH:
            return ForwardingDecision(True, self._append_path(pkt))

        if pkt.payload_type == PayloadType.TRACE:
            return ForwardingDecision(True, self._append_trace(pkt))

        return ForwardingDecision(True, pkt)

    def _append_path(self, pkt: MeshCorePacket) -> MeshCorePacket:
        new_path = pkt.path + self.identity_hash
        return MeshCorePacket(
            route=pkt.route,
            payload_type=pkt.payload_type,
            version=pkt.version,
            path_len=pkt.path_len + 1,
            path=new_path,
            payload=pkt.payload,
            snr=pkt.snr,
            rssi=pkt.rssi,
        )

    def _append_trace(self, pkt: MeshCorePacket) -> MeshCorePacket:
        snr = pkt.snr if pkt.snr is not None else 0.0
        snr_byte = int(max(0, min(255, snr * 4)))
        new_path = pkt.path + bytes([snr_byte]) + self.identity_hash

        return MeshCorePacket(
            route=pkt.route,
            payload_type=pkt.payload_type,
            version=pkt.version,
            path_len=pkt.path_len + 1,
            path=new_path,
            payload=pkt.payload,
            snr=pkt.snr,
            rssi=pkt.rssi,
        )
