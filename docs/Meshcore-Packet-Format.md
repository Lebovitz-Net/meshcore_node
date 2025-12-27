markdown
# MeshCore LoRa Packet Header Format (Derived from `Packet.h`)

This document describes the MeshCore on‑air packet header format as defined in the MeshCore firmware.  
The header is a single byte containing **routing mode**, **payload type**, and **payload version**.

7 6 | 5 4 3 2 | 1 0
VER |  TYPE   | ROUTE

Code

- **ROUTE**: 2 bits  
- **TYPE**: 4 bits  
- **VER**: 2 bits  

---

## 1. Header Bit Layout

### **Bit fields**
| Bits | Mask | Meaning |
|------|------|---------|
| 0–1 | `PH_ROUTE_MASK = 0x03` | Routing mode |
| 2–5 | `PH_TYPE_MASK = 0x0F` (shifted by `PH_TYPE_SHIFT = 2`) | Payload type |
| 6–7 | `PH_VER_MASK = 0x03` (shifted by `PH_VER_SHIFT = 6`) | Payload version |

### **Header composition**
header =
(route_type & 0x03)
| ((payload_type & 0x0F) << 2)
| ((payload_version & 0x03) << 6)

Code

This matches the stable first byte seen in LoRa captures.

---

## 2. Routing Modes (ROUTE_TYPE_*)

Routing mode occupies the **lowest 2 bits** of the header.

| Value | Name | Meaning |
|-------|------|---------|
| `0x00` | `ROUTE_TYPE_TRANSPORT_FLOOD` | Flood routing + transport codes |
| `0x01` | `ROUTE_TYPE_FLOOD` | Flood routing, path[] built hop‑by‑hop |
| `0x02` | `ROUTE_TYPE_DIRECT` | Direct routing, path[] supplied by sender |
| `0x03` | `ROUTE_TYPE_TRANSPORT_DIRECT` | Direct routing + transport codes |

### Notes
- Flood routing appends this node’s hash to `path[]`.
- Direct routing preserves the sender‑provided path.
- Transport modes add two 16‑bit transport codes (rarely used).

---

## 3. Payload Types (PAYLOAD_TYPE_*)

Payload type occupies **bits 2–5** of the header.

| Value | Name | Description |
|-------|------|-------------|
| `0x00` | `PAYLOAD_TYPE_REQ` | Encrypted request (dest/src hash + MAC + encrypted blob) |
| `0x01` | `PAYLOAD_TYPE_RESPONSE` | Response to REQ or ANON_REQ |
| `0x02` | `PAYLOAD_TYPE_TXT_MSG` | Encrypted text message |
| `0x03` | `PAYLOAD_TYPE_ACK` | Simple ACK (4‑byte CRC, unencrypted) |
| `0x04` | `PAYLOAD_TYPE_ADVERT` | Identity advertisement (pubkey + timestamp + signature + app data) |
| `0x05` | `PAYLOAD_TYPE_GRP_TXT` | Group text message (channel hash + MAC + encrypted text) |
| `0x06` | `PAYLOAD_TYPE_GRP_DATA` | Group datagram (channel hash + MAC + encrypted blob) |
| `0x07` | `PAYLOAD_TYPE_ANON_REQ` | Anonymous request (dest hash + ephemeral pubkey + MAC + encrypted data) |
| `0x08` | `PAYLOAD_TYPE_PATH` | Returned path (dest/src hash + MAC + encrypted path + extra) |
| `0x09` | `PAYLOAD_TYPE_TRACE` | Trace packet (collects SNR per hop) |
| `0x0A` | `PAYLOAD_TYPE_MULTIPART` | Multipart packet (remaining count in upper nibble) |
| `0x0F` | `PAYLOAD_TYPE_RAW_CUSTOM` | Raw custom payload (no encryption) |

### Notes
- Types 0x00–0x02, 0x05–0x08 all share the same encrypted structure:
[dest_hash][src_hash or channel_hash][MAC][encrypted protobuf]

Code
- ACKs and TRACE packets are mostly unencrypted.
- Multipart packets encode `(remaining << 4) | type` in payload[0].

---

## 4. Payload Versions (PAYLOAD_VER_*)

Payload version occupies **bits 6–7** of the header.

| Value | Name | Meaning |
|-------|------|---------|
| `0x00` | `PAYLOAD_VER_1` | 1‑byte hashes, 2‑byte MAC (current) |
| `0x01` | `PAYLOAD_VER_2` | Future: 2‑byte hashes, 4‑byte MAC |
| `0x02` | `PAYLOAD_VER_3` | Reserved |
| `0x03` | `PAYLOAD_VER_4` | Reserved |

### Notes
- All packets observed in the wild use **version 1**.
- Versioning allows future expansion without breaking compatibility.

---

## 5. Packet Class Structure (On‑Air Representation)

The `Packet` class contains:

uint8_t  header;          // 1 byte
uint16_t payload_len;     // length of payload[]
uint16_t path_len;        // length of path[]
uint16_t transport_codes[2]; // optional, only if transport mode
uint8_t  path[MAX_PATH_SIZE]; // routing path (hashes or SNRs)
uint8_t  payload[MAX_PACKET_PAYLOAD]; // unencrypted prefix + encrypted data
int8_t   _snr;            // SNR of received packet

Code

### On‑air order (wire format)
[header]
[path_len]
[path bytes...]
[payload_len]
[payload bytes...]

Code

The encrypted region begins inside `payload[]` depending on payload type.

---

## 6. Helper Methods Confirm Behavior

### Routing helpers
- `isRouteFlood()`
- `isRouteDirect()`
- `hasTransportCodes()`

### Type helpers
- `getPayloadType()`
- `getPayloadVer()`

### Special behavior
- `markDoNotRetransmit()` sets header to `0xFF`  
  (used internally to suppress rebroadcast)

### SNR
- `_snr` is stored as quarter‑dB units  
  (`getSNR() = _snr / 4.0f`)

---

## 7. Summary of What This Header Tells Us

- The **first byte** of every LoRa packet fully describes:
  - routing mode  
  - payload type  
  - payload version  

- The MeshCore on‑air protocol is **bit‑packed**, efficient, and stable.

- The header format matches your empirical captures exactly:
  - consistent high‑order bits for version  
  - mid‑bits for type  
  - low bits for routing  

- This header file completes the structural map of the MeshCore LoRa protocol.
