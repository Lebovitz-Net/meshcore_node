# meshcore_py_node/routing/outbound.py

from __future__ import annotations

from meshcore_py_node.packet.packet import MeshCorePacket
from meshcore_py_node.packet.header import RouteType, PayloadType, PayloadVersion
from meshcore_py_node.constants import MAX_PATH_LEN


class OutboundRouter:
    """
    Decides outbound routing properties:
      - route type
      - initial path
      - path trimming
    """

    def __init__(self, identity_hash: bytes):
        self.identity_hash = identity_hash  # 1-byte hash

    def prepare_direct(self, pkt: MeshCorePacket, dest_hash: bytes) -> MeshCorePacket:
        return MeshCorePacket(
            route=RouteType.DIRECT,
            payload_type=pkt.payload_type,
            version=pkt.version,
            path_len=0,
            path=b"",
            payload=pkt.payload,
        )

    def prepare_flood(
        self,
        pkt: MeshCorePacket,
        include_initial_hop: bool = True,
    ) -> MeshCorePacket:
        if include_initial_hop:
            path = self.identity_hash
            path_len = 1
        else:
            path = b""
            path_len = 0

        return MeshCorePacket(
            route=RouteType.FLOOD,
            payload_type=pkt.payload_type,
            version=pkt.version,
            path_len=path_len,
            path=path,
            payload=pkt.payload,
        )

    def trim_path(self, pkt: MeshCorePacket, max_hops: int) -> MeshCorePacket:
        if pkt.path_len <= max_hops:
            return pkt

        if pkt.payload_type != PayloadType.TRACE:
            new_path = pkt.path[:max_hops * pkt.hash_size]
        else:
            per_hop = 1 + pkt.hash_size
            new_path = pkt.path[: max_hops * per_hop]

        return MeshCorePacket(
            route=pkt.route,
            payload_type=pkt.payload_type,
            version=pkt.version,
            path_len=max_hops,
            path=new_path,
            payload=pkt.payload,
            snr=pkt.snr,
            rssi=pkt.rssi,
        )
