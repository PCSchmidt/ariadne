# lru_cache

Implement the `LRUCache` class in `solution.py`.

- `LRUCache(capacity)` creates a cache holding at most `capacity` items.
- `get(key)` returns the value if present, else `-1`. A successful get counts as
  a use (marks the key most-recently-used).
- `put(key, value)` inserts or updates. If inserting a new key exceeds capacity,
  evict the least-recently-used key first. Updating an existing key counts as a use.
