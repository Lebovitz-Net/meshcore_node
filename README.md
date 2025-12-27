# MeshCore Node (Python)

A clean, standalone implementation of the **MeshCore OTA protocol** in Python.
This package provides:

- A full MeshCore OTA packet parser and serializer  
- A complete MeshCore node (`MeshCoreNode`)  
- Persistent identity, groups, and peers (capped at 300)  
- In-memory dedupe  
- Routing (forwarding + outbound routing)  
- Direct and group message encryption/decryption  
- ADVERT, PATH, TRACE, ACK, RAW_CUSTOM support  

This is the reference Python implementation of a MeshCore radio node.

---

## 📦 Installation

```bash
pip install meshcore-node
