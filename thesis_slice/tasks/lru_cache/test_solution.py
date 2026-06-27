from solution import LRUCache


def test_basic_get_put():
    c = LRUCache(2)
    c.put(1, 1)
    c.put(2, 2)
    assert c.get(1) == 1


def test_eviction_of_lru():
    c = LRUCache(2)
    c.put(1, 1)
    c.put(2, 2)
    c.put(3, 3)          # evicts key 1 (least recently used)
    assert c.get(1) == -1
    assert c.get(2) == 2
    assert c.get(3) == 3


def test_get_refreshes_recency():
    c = LRUCache(2)
    c.put(1, 1)
    c.put(2, 2)
    assert c.get(1) == 1  # 1 is now most-recently-used
    c.put(3, 3)           # evicts key 2, not key 1
    assert c.get(1) == 1
    assert c.get(2) == -1


def test_update_existing():
    c = LRUCache(2)
    c.put(1, 1)
    c.put(1, 10)
    assert c.get(1) == 10
