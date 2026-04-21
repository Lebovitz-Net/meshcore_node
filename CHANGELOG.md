# Changelog

All notable changes to this project will be documented in this file.

---

## [Unreleased] — 2026-04-21

### Fixed

- **`meshcore_py_node/node.py`** — `OutboundRouter` and `ForwardingRouter` were being passed `self` (the full `MeshCoreNode` instance) instead of `identity_hash: bytes`. Now correctly passes `identity.hash(hash_size)`.
- **`router_node.py`** — `MeshCoreRouter.__init__` previously accepted `identity=None`, which would crash at runtime when the hash was needed for path/trace appending. Now raises `ValueError` if `identity` is `None`.
- **`meshcore_py_node/routing/forwarding.py`** — Removed dead `RouteType.ZERO_HOP` check. `ZERO_HOP` is not a valid wire-protocol value (only 4 values fit in 2 bits: `TRANSPORT_FLOOD`, `FLOOD`, `DIRECT`, `TRANSPORT_DIRECT`). `TRANSPORT_FLOOD` (0x00) packets now correctly fall through to flood handling.
- **`meshcore_py_node/routing/outbound.py`** — Removed `prepare_zero_hop()`, which referenced the non-existent `RouteType.ZERO_HOP`.
- **`meshcore_py_node/routing/outbound.py`** — `trim_path()` was using the hardcoded `PATH_HASH_SIZE` constant (always 1) instead of `pkt.hash_size`. Now version-aware.
- **`companion_node.py` / `router_node.py`** — Both files were missing all `import` statements and would fail to run standalone. Added `from meshcore_py_node.node import MeshCoreNode` and `from meshcore_py_node.packet.header import PayloadVersion`.

### Added

- **MeshCore 1.114.0 (V2 protocol) support** — 2-byte trace ID / hash support throughout:

  - **`meshcore_py_node/crypto/identity.py`** — `Identity.hash()` now accepts `hash_size: int = 1`. Pass `hash_size=2` for V2 (1.114.0+) 2-byte identity hashes. Defaults to `1` for full backward compatibility.

  - **`meshcore_py_node/group.py`** — `GroupChannel` now stores a 2-byte `_hash_prefix` internally. New `get_hash(hash_size: int = 1)` method returns 1 or 2 bytes. The `hash` property remains as a 1-byte V1 backward-compat alias.

  - **`meshcore_py_node/builder.py`** — All builders now accept `version: PayloadVersion = PayloadVersion.V1`:
    - `build_advert()`
    - `build_direct_datagram()` — dest/src hashes sized by version
    - `build_group_datagram()` — channel hash sized by version
    - `build_ack()`
    - `build_raw_custom()`
    - (`build_path_packet()` and `build_trace_packet()` already accepted `version`)

  - **`meshcore_py_node/node.py`** — Added `version: PayloadVersion = PayloadVersion.V1` constructor parameter (stored as `self.version`). All `send_*` methods pass `version=self.version` to builders. `_handle_direct` and `_handle_group` use `pkt.hash_size` for payload slicing instead of hardcoded `[0:1]`. Group lookup falls back to 1-byte key when receiving a V2 packet against a V1-keyed store.

  - **`companion_node.py` / `router_node.py`** — `version` parameter forwarded to `MeshCoreNode`.

### Usage — enabling V2 mode

```python
from meshcore_py_node.packet.header import PayloadVersion

# V1 (default, MeshCore < 1.114.0)
node = MeshCoreCompanion(identity, send_raw, emit_event, store)

# V2 (MeshCore 1.114.0+, 2-byte trace IDs)
node = MeshCoreCompanion(identity, send_raw, emit_event, store, version=PayloadVersion.V2)
```

---

## [0.1.0] — Initial release

- Standalone OTA MeshCore node implementation in Python
- SX1262 radio via injected `send_raw` callback (hardware-agnostic)
- Flood and direct routing with hop-by-hop PATH and TRACE appending
- AES-128-GCM encrypted direct and group messages
- ADVERT, TXT_MSG, GRP_TXT, GRP_DATA, ACK, PATH, TRACE, RAW_CUSTOM packet handling
- `LocalStore` — persistent identity, group channels, 300-peer cap, TTL dedup
- `MeshCoreCompanion` and `MeshCoreRouter` node roles
