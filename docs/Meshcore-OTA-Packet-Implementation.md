markdown
# MeshCore LoRa Wire Format (Derived from `Packet.cpp`)

This document describes the exact byte‑level wire format of MeshCore packets as transmitted over LoRa.  
The format is defined by `Packet::writeTo()` and parsed by `Packet::readFrom()`.

---

## 1. Wire Format Overview

Every MeshCore packet transmitted over LoRa has the following structure:

[ header ]
[ optional transport codes (4 bytes) ]
[ path_len ]
[ path bytes... ]
[ payload bytes... ]

Code

There is **no length prefix** for the payload.  
The receiver infers payload length from the total packet length.

---

## 2. Field‑by‑Field Breakdown

### **2.1 Header (1 byte)**  
Bit‑packed structure:

7 6 | 5 4 3 2 | 1 0
VER |  TYPE   | ROUTE

Code

- ROUTE: 2 bits  
- TYPE: 4 bits  
- VER: 2 bits  

See `Packet.h` for full definitions.

---

### **2.2 Optional Transport Codes (4 bytes)**  
Present only if:

route_type == ROUTE_TYPE_TRANSPORT_FLOOD
or ROUTE_TYPE_TRANSPORT_DIRECT

Code

Format:

[ uint16_t transport_code_0 ]
[ uint16_t transport_code_1 ]

Code

Little‑endian.

---

### **2.3 Path Length (1 byte)**  
Number of bytes in `path[]`.

path_len = src[i++]

Code

Maximum: `MAX_PATH_SIZE` (64 bytes).

---

### **2.4 Path Bytes (path_len bytes)**  
Routing path:

- In flood mode: appended hop‑by‑hop (1‑byte hashes)
- In direct mode: supplied by sender
- In TRACE mode: contains SNR values instead of hashes

---

### **2.5 Payload Bytes (remaining bytes)**  
Everything after the path is payload:

payload_len = total_packet_length - i

Code

Payload structure depends on payload type:

- ACK: 4‑byte CRC (unencrypted)
- ADVERT: pubkey + timestamp + signature + app data
- REQ/RESP/TXT/PATH/GROUP:  
[dest_hash][src_hash or channel_hash][MAC][encrypted protobuf]

Code
- MULTIPART:  
[nibble-coded header][rest of payload]

Code

---

## 3. Full Serialization Logic

### **3.1 Encoding (writeTo)**

i = 0
dest[i++] = header

if hasTransportCodes():
write 4 bytes of transport codes

dest[i++] = path_len
copy path bytes
copy payload bytes

return i  // total length

Code

---

### **3.2 Decoding (readFrom)**

i = 0
header = src[i++]

if hasTransportCodes():
read 4 bytes of transport codes
else:
zero transport codes

path_len = src[i++]
copy path bytes

payload_len = total_len - i
copy payload bytes

Code

Validation rules:

- path_len must not exceed MAX_PATH_SIZE
- payload_len must not exceed MAX_PACKET_PAYLOAD
- i must not exceed total length

---

## 4. Raw Length Calculation

raw_length = 2 + path_len + payload_len + (hasTransportCodes() ? 4 : 0)

Code

The `2` accounts for:

- header (1 byte)
- path_len (1 byte)

---

## 5. Packet Hashing

Used for deduplication:

SHA256( payload_type || [path_len if TRACE] || payload )

Code

This explains why TRACE packets include path_len in the hash.

---

## 6. Summary

The MeshCore LoRa wire format is:

[1] header
[0 or 4] transport codes
[1] path_len
[path_len] path[]
[payload_len] payload[]

Code

This file provides everything needed to:

- Encode packets for transmission
- Decode packets from a sniffer
- Build a full MeshCore driver
- Build a Wireshark dissector
- Build a Python parser for MeshCore packets

🎯 What This Means for Your Driver
You now have all required information to implement:

A complete encoder

A complete decoder

A packet classifier

A routing path extractor

A payload type decoder

A version‑aware parser

A transport‑code‑aware parser

You can now reconstruct any MeshCore packet from raw LoRa bytes.

If you want, I can now generate:

