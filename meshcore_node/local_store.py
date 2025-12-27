# meshcore_node/local_store.py

from __future__ import annotations
import json
import os
from typing import Optional, Dict

from meshcore_node.crypto.identity import LocalIdentity, Identity
from meshcore_node.group import GroupChannel
from meshcore_node.routing.dedupe import DedupeTable


DEFAULT_DIR = os.path.expanduser("~/.meshcore_node")
IDENTITY_FILE = os.path.join(DEFAULT_DIR, "identity.json")
GROUPS_FILE = os.path.join(DEFAULT_DIR, "groups.json")
PEERS_FILE = os.path.join(DEFAULT_DIR, "peers.json")

MAX_CONTACTS = 300


class LocalStore:
    """
    Persistent store for a standalone MeshCore node.
    Persists:
      - LocalIdentity
      - Group channels
      - Peer identities (capped at 300)
    Keeps in memory:
      - dedupe table
    """

    def __init__(self, base_dir: str = DEFAULT_DIR, dedupe_ttl: int = 60):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

        self.identity = self._load_or_create_identity()
        self.groups = self._load_groups()
        self.peers = self._load_peers()

        self.dedupe = DedupeTable(ttl_seconds=dedupe_ttl)

    # Identity ---------------------------------------------------
    def _load_or_create_identity(self) -> LocalIdentity:
        if os.path.exists(IDENTITY_FILE):
            with open(IDENTITY_FILE, "r") as f:
                data = json.load(f)
            prv = bytes.fromhex(data["private_key"])
            return LocalIdentity(prv_key=prv)

        ident = LocalIdentity()
        self.save_identity(ident)
        return ident

    def save_identity(self, ident: LocalIdentity):
        data = {
            "private_key": ident.prv_key.hex(),
            "public_key": ident.pub_key.hex(),
        }
        with open(IDENTITY_FILE, "w") as f:
            json.dump(data, f, indent=2)

    # Groups -----------------------------------------------------
    def _load_groups(self) -> Dict[bytes, GroupChannel]:
        if not os.path.exists(GROUPS_FILE):
            return {}
        with open(GROUPS_FILE, "r") as f:
            raw = json.load(f)

        groups: Dict[bytes, GroupChannel] = {}
        for entry in raw:
            h = bytes.fromhex(entry["hash"])
            secret = bytes.fromhex(entry["secret"])
            groups[h] = GroupChannel(hash=h, secret=secret)
        return groups

    def save_groups(self):
        data = [
            {"hash": h.hex(), "secret": g.secret.hex()}
            for h, g in self.groups.items()
        ]
        with open(GROUPS_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def add_group(self, group: GroupChannel):
        self.groups[group.hash] = group
        self.save_groups()

    # Peers ------------------------------------------------------
    def _load_peers(self) -> Dict[bytes, Identity]:
        if not os.path.exists(PEERS_FILE):
            return {}
        with open(PEERS_FILE, "r") as f:
            raw = json.load(f)

        peers: Dict[bytes, Identity] = {}
        for entry in raw:
            h = bytes.fromhex(entry["hash"])
            pub = bytes.fromhex(entry["pubkey"])
            peers[h] = Identity(pub_key=pub)
        return peers

    def _save_peers(self):
        data = []
        for h, ident in self.peers.items():
            data.append({
                "hash": h.hex(),
                "pubkey": ident.pub_key.hex(),
                "last_seen": getattr(ident, "last_seen", 0),
            })

        data.sort(key=lambda x: x["last_seen"], reverse=True)
        data = data[:MAX_CONTACTS]

        with open(PEERS_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def register_peer(self, identity: Identity, timestamp: int):
        h = identity.hash()
        identity.last_seen = timestamp
        self.peers[h] = identity
        self._save_peers()

    def lookup_peer(self, h: bytes) -> Optional[Identity]:
        return self.peers.get(h)

    # Dedupe bridge ----------------------------------------------
    def has_seen(self, packet_hash: bytes) -> bool:
        return self.dedupe.has_seen(packet_hash)

    def mark_seen(self, packet_hash: bytes):
        self.dedupe.mark_seen(packet_hash)
