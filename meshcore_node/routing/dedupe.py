# meshcore_node/routing/dedupe.py

from __future__ import annotations
import time
from typing import Dict


class DedupeTable:
    """
    Simple in-memory dedupe with TTL.
    """

    def __init__(self, ttl_seconds: int = 60):
        self.ttl = ttl_seconds
        self._entries: Dict[bytes, float] = {}

    def _cleanup(self):
        now = time.time()
        expired = [h for h, t in self._entries.items() if now - t > self.ttl]
        for h in expired:
            del self._entries[h]

    def has_seen(self, packet_hash: bytes) -> bool:
        self._cleanup()
        return packet_hash in self._entries

    def mark_seen(self, packet_hash: bytes):
        self._cleanup()
        self._entries[packet_hash] = time.time()
