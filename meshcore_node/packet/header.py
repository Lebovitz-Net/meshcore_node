# meshcore_node/packet/header.py

from __future__ import annotations
from enum import IntEnum


class RouteType(IntEnum):
    ZERO_HOP = 0
    DIRECT = 1
    FLOOD = 2
    # Room for more (transport, etc.)


class PayloadType(IntEnum):
    ADVERT = 0x01
    TXT_MSG = 0x02
    GRP_TXT = 0x03
    GRP_DATA = 0x04
    ACK = 0x05
    PATH = 0x06
    TRACE = 0x07
    RAW_CUSTOM = 0x08
    # Others reserved


class PayloadVersion(IntEnum):
    V1 = 1
