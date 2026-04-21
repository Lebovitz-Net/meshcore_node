# meshcore_py_node

A standalone Python implementation of the **MeshCore over-the-air (OTA) protocol**.

This library implements the full MeshCore radio-layer protocol directly in Python — packet parsing, encryption, routing, and identity management — with a hardware-agnostic design. The radio (or any other transport) is injected via a simple `send_raw(bytes)` callback, so the library runs on a Raspberry Pi with a real SX1262 radio, in a simulator, or as part of a larger application without any hardware changes.

---

## Features

- Full MeshCore OTA packet parser and serializer (header, routing, path, payload)
- Protocol V1 (MeshCore <= 1.113) and V2 (MeshCore 1.114.0+, 2-byte trace IDs) support
- Flood and direct routing with hop-by-hop PATH and TRACE appending
- AES-128-GCM encrypted direct (peer-to-peer) messages
- AES-128-GCM encrypted group (shared-secret broadcast) messages
- ADVERT, TXT_MSG, GRP_TXT, GRP_DATA, ACK, PATH, TRACE, RAW_CUSTOM packet handling
- Persistent identity, group channels, and peer store (300-peer cap, auto-culled by recency)
- In-memory TTL-based packet dedup
- Two node roles: `MeshCoreCompanion` (decrypts + emits events) and `MeshCoreRouter` (forwards only)

---

## Repository layout

```
meshcore_py_node/          # Core library package
|
+-- node.py                # MeshCoreNode base class
+-- builder.py             # Packet builders for all payload types
+-- constants.py           # Protocol constants (hash sizes, MAC length, path limits)
+-- group.py               # GroupChannel -- shared-secret group encryption
+-- local_store.py         # Persistent identity, groups, and peer store
|
+-- packet/
|   +-- header.py          # RouteType, PayloadType, PayloadVersion enums
|   +-- packet.py          # MeshCorePacket -- binary serialization/parsing
|   +-- advert.py          # Advertisement payload parser/builder
|
+-- routing/
|   +-- forwarding.py      # ForwardingRouter -- inbound routing decisions
|   +-- outbound.py        # OutboundRouter -- outbound path preparation
|   +-- dedupe.py          # TTL-based packet dedup table
|
+-- crypto/
    +-- identity.py        # Identity (public) and LocalIdentity (with private keys)
    +-- utils.py           # AES-128-GCM, SHA-256 helpers

companion_node.py          # MeshCoreCompanion convenience subclass
router_node.py             # MeshCoreRouter convenience subclass
meshcore_py_node.py        # Hardware entrypoint -- wires SX1262 to MeshCoreNode
quick_start.py             # Minimal no-hardware example
```

---

## Dependencies

### Core (always required)

| Package | Purpose |
|---|---|
| `cryptography >= 41.0.0` | AES-128-GCM encryption, Ed25519 signing, X25519 key agreement |

### Hardware optional extra

| Package | Purpose |
|---|---|
| `sx1262_driver` | SX1262 LoRa radio driver (Raspberry Pi / SPI hardware only) |

The `sx1262_driver` is only needed when running `meshcore_py_node.py` on physical hardware. It is declared as the `sx1262` optional extra and is **not** installed by default.

---

## Installation

### Core library only (development, simulation, or companion-over-serial)

```bash
pip install meshcore-py-node
```

### With SX1262 hardware support (Raspberry Pi target)

```bash
pip install meshcore-py-node[sx1262]
```

### From source (local development)

```bash
git clone https://github.com/Lebovitz-Net/meshcore_py_node
cd meshcore_py_node
pip install -e .
```

If `sx1262_driver` is a local sibling repo (not yet published to PyPI):

```bash
pip install -e ../sx1262_driver
pip install -e .
```

---

## Quick start (no hardware)

```python
from meshcore_py_node import MeshCoreNode, LocalStore

def send_raw(data: bytes):
    print("TX:", data.hex())   # swap in your radio / serial / UDP send here

def emit_event(event: str, data: dict):
    print("EVENT:", event, data)

store = LocalStore()
node = MeshCoreNode(
    identity=store.identity,
    send_raw=send_raw,
    emit_event=emit_event,
    store=store,
)

# Broadcast an advertisement
node.send_advert(b"hello")

# Feed inbound radio packets into the node
node.on_raw_packet(raw_bytes, snr=snr, rssi=rssi)
```

See `quick_start.py` for a self-contained runnable version.

---

## Running on hardware (SX1262 / Raspberry Pi)

`meshcore_py_node.py` is the full hardware entrypoint. It initialises the SX1262 radio over SPI, configures LoRa modulation to match MeshCore network settings, and wires the radio callbacks to a `MeshCoreNode`.

### MeshCore US radio parameters

These are the standard MeshCore LoRa parameters for US operation. All nodes on the same network must use identical settings.

| Parameter | Value | Notes |
|---|---|---|
| Frequency | 910.525 MHz | US ISM band |
| Bandwidth | 62.5 kHz | |
| Spreading Factor | SF7 | |
| Coding Rate | 4/5 | |
| Sync Word | `0x1242` | MeshCore-specific — **not** LoRaWAN public (`0x3444`) |
| Header type | Explicit | |
| Preamble length | 12 symbols | |
| CRC | Enabled | |
| IQ inversion | Disabled | |

> **Note:** The MeshCore sync word `0x1242` is distinct from the LoRaWAN public sync word. Using the wrong sync word is a common misconfiguration — nodes will not hear each other.

**Pin defaults** (edit at the top of `meshcore_py_node.py` to match your wiring):

| Signal | GPIO (BCM) |
|---|---|
| BUSY | 20 |
| RESET | 18 |
| NSS (CS) | 21 |
| SPI bus | 0 |
| SPI device | 0 |

**Run:**

```bash
python meshcore_py_node.py
```

The node will enter `RX_CONTINUOUS` and print received events to stdout. Press `Ctrl+C` to stop.

---

## Protocol versions

| Version flag | `PayloadVersion` | Hash size | Firmware |
|---|---|---|---|
| V1 (default) | `PayloadVersion.V1` | 1 byte | MeshCore <= 1.113 |
| V2 | `PayloadVersion.V2` | 2 bytes | MeshCore 1.114.0+ |

To run in V2 mode:

```python
from meshcore_py_node.packet.header import PayloadVersion
from companion_node import MeshCoreCompanion

node = MeshCoreCompanion(identity, send_raw, emit_event, store, version=PayloadVersion.V2)
```

---

## Node roles

### `MeshCoreCompanion`

A user-facing node. Decrypts incoming direct and group messages and emits events. Can originate ADVERT, TXT_MSG, GRP_TXT, PATH, TRACE, and RAW_CUSTOM packets.

### `MeshCoreRouter`

A forwarding-only node. Requires an identity (used to append its hash to PATH/TRACE hops) but does not decrypt or emit user-level events. All `send_*` methods raise `RuntimeError`.

---

## Integration pattern

```python
mesh_node = MeshCoreNode(
    identity=local_identity,
    send_raw=radio.send,        # or serial write, UDP socket, etc.
    emit_event=my_event_bus,
    store=store,
)

def on_radio_packet(raw_bytes: bytes, snr: float, rssi: float):
    mesh_node.on_raw_packet(raw_bytes, snr=snr, rssi=rssi)

radio.on("rx_done", on_radio_packet)
```

Events emitted: `advert`, `direct_message`, `group_message`, `ack`, `path`, `trace`, `raw_custom`,
`direct_not_for_us`, `direct_unknown_peer`, `direct_mac_fail`, `group_unknown_channel`,
`group_mac_fail`, `unknown_payload_type`.

---

## License

MIT
