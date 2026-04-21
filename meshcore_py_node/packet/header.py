# meshcore_py_node/packet/header.py

from __future__ import annotations
from enum import IntEnum


class RouteType(IntEnum):
    """Route mode occupies bits 0-1 of the header byte."""
    TRANSPORT_FLOOD = 0x00   # flood routing + transport codes
    FLOOD = 0x01             # flood routing, path[] built hop-by-hop
    DIRECT = 0x02            # direct routing, path[] supplied by sender
    TRANSPORT_DIRECT = 0x03  # direct routing + transport codes


class PayloadType(IntEnum):
    """Payload type occupies bits 2-5 of the header byte (shifted by 2)."""
    REQ = 0x00        # encrypted request
    RESPONSE = 0x01   # response to REQ or ANON_REQ
    TXT_MSG = 0x02    # encrypted text message
    ACK = 0x03        # simple ACK (4-byte CRC32, unencrypted)
    ADVERT = 0x04     # identity advertisement
    GRP_TXT = 0x05    # group text message
    GRP_DATA = 0x06   # group datagram
    ANON_REQ = 0x07   # anonymous request
    PATH = 0x08       # returned path
    TRACE = 0x09      # trace packet (SNR per hop)
    MULTIPART = 0x0A  # multipart packet
    RAW_CUSTOM = 0x0F # raw custom payload (no encryption)


class PayloadVersion(IntEnum):
    """
    Payload version occupies bits 6-7 of the header byte (shifted by 6).
    Determines hash size for addressing and path entries.
    """
    V1 = 0  # 1-byte hashes (all firmware before 1.114.0)
    V2 = 1  # 2-byte hashes (MeshCore 1.114.0+, 2-byte tracing)
