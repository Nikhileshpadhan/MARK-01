import time
import hashlib
import json
from typing import Any, Optional


class TTLCache:
    """Lightweight in-memory TTL cache. Replace with Redis for production."""

    def __init__(self, default_ttl: int = 300):
        self._store: dict[str, tuple[Any, float]] = {}
        self.default_ttl = default_ttl

    def _key(self, *args) -> str:
        raw = json.dumps(args, sort_keys=True, default=str)
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl or self.default_ttl
        self._store[key] = (value, time.time() + ttl)

    def make_key(self, *args) -> str:
        return self._key(*args)

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()


# Global cache instance
cache = TTLCache()
