from typing import Generic, TypeVar, Dict, Optional

K = TypeVar('K')
V = TypeVar('V')

class LRUCacheNode(Generic[K, V]):
    __slots__ = "key", "value", "prev", "next"
    
    def __init__(self, key: K, value: V):
        self.key = key
        self.value = value
        self.prev: Optional['LRUCacheNode[K, V]'] = None
        self.next: Optional['LRUCacheNode[K, V]'] = None
        

class LRUCache(Generic[K, V]):
    __slots__ = "capacity", "cache", "head", "tail"
    
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache: Dict[K, LRUCacheNode[K, V]] = {}
        self.head: LRUCacheNode[K, V] = LRUCacheNode(None, None)  # type: ignore
        self.tail: LRUCacheNode[K, V] = LRUCacheNode(None, None)  # type: ignore
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, node: LRUCacheNode[K, V]) -> None:
        prev = node.prev
        next = node.next
        if prev is not None and next is not None:
            prev.next = next
            next.prev = prev

    def _add(self, node: LRUCacheNode[K, V]) -> None:
        prev = self.tail.prev
        if prev is not None:
            prev.next = node
            node.prev = prev
            node.next = self.tail
            self.tail.prev = node

    def get(self, key: K) -> Optional[V]:
        if key in self.cache:
            node = self.cache[key]
            self._remove(node)
            self._add(node)
            return node.value
        return None

    def put(self, key: K, value: V) -> None:
        if key in self.cache:
            self._remove(self.cache[key])
        node = LRUCacheNode(key, value)
        self._add(node)
        self.cache[key] = node
        if len(self.cache) > self.capacity:
            lru = self.head.next
            if lru is not None:
                self._remove(lru)
                del self.cache[lru.key]
