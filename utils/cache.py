from typing import Optional
from datetime import datetime

def get_current_time() -> int:
    return int(datetime.now().timestamp())

class LRUCacheNode:
    __slots__ = "key", "value", "last_access_timestamp", "prev_key", "next_key"
    
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.last_access_timestamp: int = get_current_time()
        self.prev_key: Optional[object] = None
        self.next_key: Optional[object] = None
        

class LRUCache:
    __slots__ = "capacity", "expire_seconds", "cache", "head_key", "tail_key"
    
    def __init__(self, capacity: int, expire_seconds: int):
        self.capacity: int = capacity
        self.expire_seconds: int = expire_seconds
        self.cache: dict[object, LRUCacheNode] = {}
        self.head_key = None
        self.tail_key = None

    def _remove(self, key: object) -> None:
        node = self.cache[key]
        prev_key = node.prev_key
        next_key = node.next_key
        
        if prev_key is not None:
            self.cache[prev_key].next_key = next_key
        else:
            self.head_key = next_key
            
        if next_key is not None:
            self.cache[next_key].prev_key = prev_key
        else:
            self.tail_key = prev_key

    def _add(self, key: object) -> None:
        node = self.cache[key]
        node.last_access_timestamp = get_current_time()
        node.prev_key = self.tail_key
        node.next_key = None
        
        if self.tail_key is not None:
            self.cache[self.tail_key].next_key = key
        else:
            self.head_key = key
        
        self.tail_key = key

    def get(self, key: object) -> Optional[object]:
        "Remember to handle KeyError"
        if key not in self.cache:
            raise KeyError(f"Key {key} not found")
        node = self.cache[key]
        if (self.expire_seconds > 0) and (node.last_access_timestamp + self.expire_seconds < get_current_time()):
            self._remove(key)
            del self.cache[key]
            raise KeyError(f"Key {key} has expired")
        self._remove(key)
        self._add(key)
        return node.value

    def put(self, key: object, value: object) -> None:
        if key in self.cache:
            self._remove(key)
        node = LRUCacheNode(key, value)
        self.cache[key] = node
        self._add(key)
        if len(self.cache) > self.capacity:
            lru_key = self.head_key
            if lru_key is not None:
                self._remove(lru_key)
                del self.cache[lru_key]
    
    def delete(self, key: object) -> None:
        if key in self.cache:
            self._remove(key)
            del self.cache[key]
