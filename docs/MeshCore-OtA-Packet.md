markdown
# MeshCore LoRa Protocol: Insights Derived from `Mesh.cpp`

This document summarizes ten major insights about the MeshCore on‑air packet format, derived from analysis of the MeshCore firmware source (`Mesh.cpp`). These findings align with empirical packet captures and provide a strong foundation for building a MeshCore sniffer, parser, or full driver.

---

## 1. MeshCore Uses Raw LoRa Payloads (Not LoRaWAN)
MeshCore does not use LoRaWAN or SX1262 framing. The radio transmits **raw opaque byte arrays**, and all packet structure is implemented in software.  
This means:

- Sniffer captures show the *exact* MeshCore packet bytes.
- No additional headers or footers are added by the radio.
- All routing, addressing, and encryption are MeshCore‑defined.

---

## 2. Packet Structure Is Explicitly Defined in Software
Every MeshCore packet contains:

- **Header byte**  
  Encodes payload type and routing mode.
- **Path length + path[]**  
  Used for routing (flood or direct).
- **Payload length + payload[]**  
  Contains unencrypted metadata followed by encrypted content.

The header is constructed as:

header = (PAYLOAD_TYPE << PH_TYPE_SHIFT) | ROUTE_TYPE

Code

This matches the stable first byte seen in captures.

---

## 3. Unencrypted vs Encrypted Regions Are Clearly Separated
MeshCore packets contain a small unencrypted prefix followed by encrypted data.

### Unencrypted fields include:
- Header byte  
- Path length  
- Path[] (routing hashes or SNR values)  
- First 1–2 bytes of payload (dest_hash, src_hash)  
- Some metadata for special packet types  

### Encrypted region begins immediately after:
[dest_hash][src_hash]

Code

Encrypted region =  
MAC (16 bytes?) + encrypted protobuf payload

Code

This matches the high‑entropy region in your captures.

---

## 4. Routing Path Format Is Fully Exposed
Routing packets contain:

- `path_len` (in bytes)
- `path[]` (sequence of 1‑byte hashes or SNR values)

Key facts:

- `PATH_HASH_SIZE == 1`
- Flood routing appends this node’s hash
- Direct routing copies the sender’s path
- TRACE packets append SNR values instead of hashes

This explains the repeating 1‑byte patterns in routing frames.

---

## 5. ACK Packets Are Tiny and Unencrypted
ACK packets contain:

payload = [4‑byte CRC]

Code

No encryption.  
No MAC.  
No hashes.  
No routing metadata.

This matches the very short packets you observed.

Multipart ACKs use:

payload[0] = (remaining << 4) | PAYLOAD_TYPE_ACK
payload[1..4] = ack_crc

Code

---

## 6. Advertisement Packets Reveal Identity Structure
Advertisement packets contain:

- 32‑byte public key  
- 4‑byte timestamp  
- 64‑byte signature  
- Application data (variable length)

Signature is computed over:

pubkey || timestamp || app_data

Code

This explains the long packets with consistent 32‑byte and 64‑byte blocks.

---

## 7. Flood vs Direct Routing Is Encoded in the Header
Routing mode is encoded in the lower bits of the header:

header &= ~PH_ROUTE_MASK
header |= ROUTE_TYPE_FLOOD or ROUTE_TYPE_DIRECT

Code

This explains the consistent patterns in the first byte of each packet.

Flood routing:

- Appends this node’s hash to path[]
- Uses increasing priority based on hop distance

Direct routing:

- Uses sender‑provided path[]
- Does not modify path except for ACKs and TRACE

---

## 8. Multipart Packet Format Is Explicit
Multipart packets begin with:

[upper nibble = remaining][lower nibble = payload type]

Code

Example for multipart ACK:

payload[0] = (remaining << 4) | PAYLOAD_TYPE_ACK
payload[1..4] = ack_crc

Code

This matches nibble‑encoded first bytes in your captures.

---

## 9. Hash‑Based Addressing Is Confirmed
MeshCore uses **1‑byte hashes** for:

- Destination identity  
- Source identity  
- Routing path entries  
- Group channel identifiers  

This explains:

- The small, stable values at the start of many payloads  
- The 1‑byte path entries  
- The ability to route without exposing full public keys

---

## 10. What This Code Does *Not* Reveal
The following remain unknown:

- The protobuf schema inside encrypted payloads  
- The exact bit layout of the header byte  
- The meaning of version bits (`getPayloadVer()`)  
- The key derivation method for shared secrets  
- The MAC size (likely 16 bytes but not explicitly shown)

However, the unencrypted structure is now fully mapped.

---

# Summary
This source file provides enough information to:

- Build a complete MeshCore packet classifier  
- Extract routing paths  
- Identify packet types  
- Parse unencrypted metadata  
- Prepare for future decryption  
- Build a full MeshCore driver once protobuf schemas or keys are known  

It confirms nearly all structural assumptions derived from your sniffer captures and fills in the missing architectural details.
