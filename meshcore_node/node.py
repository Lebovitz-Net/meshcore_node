from __future__ import annotations
from typing import Callable, Optional
import time

from meshcore_node.packet.packet import MeshCorePacket
from meshcore_node.packet.header import PayloadType
from meshcore_node.crypto.identity import Identity, LocalIdentity
from meshcore_node.group import GroupChannel
from meshcore_node.routing.forwarding import Router
from meshcore_node.routing.outbound import OutboundRouter


class MeshCoreNode:
    """
    MeshCore OTA logic layer (Python equivalent of Mesh.cpp, logic only).

    Responsibilities:
      - Parse inbound packets
      - Dedupe (via store.dedupe)
      - Dispatch to per-type handlers
      - Decrypt direct/group messages
      - Emit events upstream
      - Invoke Router for forwarding decisions
      - Use OutboundRouter for outbound routing selection
    """

    def __init__(
        self,
        identity: LocalIdentity,
        send_raw: Callable[[bytes], None],
        emit_event: Callable[[str, dict], None],
        store,
    ):
        """
        :param identity: LocalIdentity (holds private/public keys)
        :param send_raw: callback to actually TX bytes over radio/transport
        :param emit_event: callback to send decoded events upward
        :param store: LocalStore instance (identity, groups, peers, dedupe)
        """
        self.identity = identity
        self.send_raw = send_raw
        self.emit_event = emit_event
        self.store = store

        # Store-backed registries
        self._groups = store.groups      # dict[bytes, GroupChannel]
        self._dedupe = store.dedupe      # DedupeTable-like

        # Routing helpers
        self.router = Router(self.identity.hash())
        self.outbound = OutboundRouter(self.identity.hash())

    # ------------------------------------------------------------
    # Inbound entry point
    # ------------------------------------------------------------
    def on_raw_packet(
        self,
        raw: bytes,
        snr: Optional[float] = None,
        rssi: Optional[float] = None,
    ):
        """
        Entry point from the radio/transport.
        """
        try:
            pkt = MeshCorePacket.from_bytes(raw)
        except Exception:
            # Malformed packet
            return

        pkt.snr = snr
        pkt.rssi = rssi

        # Dedupe: compute and check hash using MeshCorePacket helper
        packet_hash = pkt.compute_hash()
        if self.store.has_seen(packet_hash):
            return
        self.store.mark_seen(packet_hash)

        # Dispatch to type-specific handler
        self._handle_packet(pkt)

        # Routing: decide whether to forward
        decision = self.router.decide(pkt)
        if decision.forward and decision.packet is not None:
            self.send_raw(decision.packet.to_bytes())

    # ------------------------------------------------------------
    # Packet dispatcher
    # ------------------------------------------------------------
    def _handle_packet(self, pkt: MeshCorePacket):
        pt = pkt.payload_type

        if pt == PayloadType.ADVERT:
            self._handle_advert(pkt)
        elif pt == PayloadType.TXT_MSG:
            self._handle_direct(pkt)
        elif pt in (PayloadType.GRP_TXT, PayloadType.GRP_DATA):
            self._handle_group(pkt)
        elif pt == PayloadType.ACK:
            self._handle_ack(pkt)
        elif pt == PayloadType.PATH:
            self._handle_path(pkt)
        elif pt == PayloadType.TRACE:
            self._handle_trace(pkt)
        elif pt == PayloadType.RAW_CUSTOM:
            self._handle_raw(pkt)
        else:
            self.emit_event("unknown_payload_type", {"packet": pkt, "payload_type": pt})

    # ------------------------------------------------------------
    # ADVERT
    # ------------------------------------------------------------
    def _handle_advert(self, pkt: MeshCorePacket):
        from meshcore_node.packet.advert import parse_advert

        advert = parse_advert(pkt.payload)
        identity = advert.identity
        timestamp = advert.timestamp

        # Persist peer (store enforces 300-contact limit)
        self.store.register_peer(identity, timestamp)

        self.emit_event("advert", {
            "packet": pkt,
            "identity": identity,
            "timestamp": timestamp,
        })

    # ------------------------------------------------------------
    # DIRECT (TXT_MSG)
    # ------------------------------------------------------------
    def _handle_direct(self, pkt: MeshCorePacket):
        """
        Direct messages layout:
          dest_hash[1] | src_hash[1] | enc_and_mac[..]
        """
        if len(pkt.payload) < 2:
            return

        dest_hash = pkt.payload[0:1]
        src_hash = pkt.payload[1:2]
        enc_and_mac = pkt.payload[2:]

        # Only decrypt if addressed to us
        if dest_hash != self.identity.hash():
            # Not for us; we rely on Router to handle forwarding, so just emit for diagnostics.
            self.emit_event("direct_not_for_us", {
                "packet": pkt,
                "dest_hash": dest_hash,
                "src_hash": src_hash,
            })
            return

        # Lookup sender identity from store
        sender_identity = self.store.lookup_peer(src_hash)
        if sender_identity is None:
            self.emit_event("direct_unknown_peer", {
                "packet": pkt,
                "src_hash": src_hash,
                "encrypted_payload": enc_and_mac,
            })
            return

        # Decrypt using LocalIdentity helper
        plaintext = self.identity.decrypt_from(sender_identity, enc_and_mac)
        if plaintext is None:
            self.emit_event("direct_mac_fail", {
                "packet": pkt,
                "src": sender_identity,
            })
            return

        self.emit_event("direct_message", {
            "packet": pkt,
            "src": sender_identity,
            "plaintext": plaintext,
        })

    # ------------------------------------------------------------
    # GROUP (GRP_TXT / GRP_DATA)
    # ------------------------------------------------------------
    def _handle_group(self, pkt: MeshCorePacket):
        if len(pkt.payload) < 1:
            return

        chan_hash = pkt.payload[0:1]
        enc_and_mac = pkt.payload[1:]

        group = self._groups.get(chan_hash)
        if group is None:
            self.emit_event("group_unknown_channel", {
                "packet": pkt,
                "channel_hash": chan_hash,
                "encrypted_payload": enc_and_mac,
            })
            return

        plaintext = group.decrypt(enc_and_mac)
        if plaintext is None:
            self.emit_event("group_mac_fail", {
                "packet": pkt,
                "channel": group,
            })
            return

        self.emit_event("group_message", {
            "packet": pkt,
            "channel": group,
            "plaintext": plaintext,
        })

    # ------------------------------------------------------------
    # ACK
    # ------------------------------------------------------------
    def _handle_ack(self, pkt: MeshCorePacket):
        """
        ACK payload = 2-byte CRC16 (little-endian)
        """
        if len(pkt.payload) < 2:
            return

        crc = int.from_bytes(pkt.payload[:2], "little", signed=False)

        self.emit_event("ack", {
            "packet": pkt,
            "crc": crc,
        })

    # ------------------------------------------------------------
    # PATH
    # ------------------------------------------------------------
    def _handle_path(self, pkt: MeshCorePacket):
        hops = list(pkt.iter_path_hashes())

        self.emit_event("path_packet", {
            "packet": pkt,
            "hops": hops,
        })

    # ------------------------------------------------------------
    # TRACE
    # ------------------------------------------------------------
    def _handle_trace(self, pkt: MeshCorePacket):
        entries = list(pkt.iter_trace_entries())

        self.emit_event("trace_packet", {
            "packet": pkt,
            "entries": entries,   # list of (snr, hash)
        })

    # ------------------------------------------------------------
    # RAW_CUSTOM
    # ------------------------------------------------------------
    def _handle_raw(self, pkt: MeshCorePacket):
        """
        RAW_CUSTOM packets are opaque application-defined payloads.
        MeshCore does not interpret them; they are delivered as-is.
        """
        self.emit_event("raw_custom", {
            "packet": pkt,
            "payload": pkt.payload,
            "snr": pkt.snr,
            "rssi": pkt.rssi,
        })

    # ------------------------------------------------------------
    # Outbound API
    # ------------------------------------------------------------
    def send_advert(self, app_data: bytes = b""):
        from meshcore_node import builder

        timestamp = int(time.time())
        pkt = builder.build_advert(self.identity, timestamp, app_data)
        routed = self.outbound.prepare_flood(pkt)
        self.send_raw(routed.to_bytes())

    def send_direct(self, dest: Identity, plaintext: bytes):
        from meshcore_node import builder

        pkt = builder.build_direct_datagram(self.identity, dest, plaintext)
        routed = self.outbound.prepare_direct(pkt, dest.hash())
        self.send_raw(routed.to_bytes())

    def send_group(self, group: GroupChannel, plaintext: bytes):
        from meshcore_node import builder

        pkt = builder.build_group_datagram(group, plaintext)
        routed = self.outbound.prepare_flood(pkt)
        self.send_raw(routed.to_bytes())

    def send_path(self, path_hashes: list[bytes], payload: bytes):
        from meshcore_node import builder
        from meshcore_node.packet.header import RouteType, PayloadVersion

        pkt = builder.build_path_packet(
            route=RouteType.FLOOD,
            payload_type=PayloadType.PATH,
            version=PayloadVersion.V1,
            path_hashes=path_hashes,
            payload=payload,
        )
        routed = self.outbound.prepare_flood(pkt, include_initial_hop=False)
        self.send_raw(routed.to_bytes())

    def send_trace(self, trace_entries: list[tuple[float, bytes]], payload: bytes):
        from meshcore_node import builder
        from meshcore_node.packet.header import RouteType, PayloadVersion

        pkt = builder.build_trace_packet(
            route=RouteType.FLOOD,
            version=PayloadVersion.V1,
            trace_entries=trace_entries,
            payload=payload,
        )
        routed = self.outbound.prepare_flood(pkt, include_initial_hop=False)
        self.send_raw(routed.to_bytes())

    def send_raw_custom(self, payload: bytes):
        from meshcore_node import builder

        pkt = builder.build_raw_custom(payload)
        routed = self.outbound.prepare_flood(pkt)
        self.send_raw(routed.to_bytes())
