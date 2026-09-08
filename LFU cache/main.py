from collections import defaultdict, OrderedDict
class LFUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.min_freq = 0
        self.val_map = defaultdict(int)
        self.freq_map = defaultdict(int)
        self.freq_bucket = defaultdict(OrderedDict)

    def _update(self, key):
        freq = self.freq_map[key]
        del self.freq_bucket[freq][key]

        if not self.freq_bucket[freq]:
            del self.freq_bucket[freq]
            if self.min_freq == freq:
                self.min_freq += 1

        self.freq_map[key] = freq+1
        self.freq_bucket[freq+1][key] = None

    def get(self, key: int) -> int:
        if key not in self.val_map:
            return -1
        self._update(key)
        return self.val_map[key]

    def put(self, key: int, value: int) -> None:
        if key in self.val_map:
            self.val_map[key] = value
            self._update(key)
            return
        
        if len(self.val_map) >= self.capacity:
            evict_key, _ = self.freq_bucket[self.min_freq].popitem(last=False)
            del self.val_map[evict_key]
            del self.freq_map[evict_key]
        
        self.val_map[key] = value
        self.freq_map[key] = 1
        self.freq_bucket[1][key] = None
        self.min_freq = 1


# Your LFUCache object will be instantiated and called as such:
# obj = LFUCache(capacity)
# param_1 = obj.get(key)
# obj.put(key,value)