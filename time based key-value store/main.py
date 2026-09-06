from collections import defaultdict
class TimeMap:
    def __init__(self):
        self.cache = defaultdict(list)

    def set(self, key, value, timestamp):
        if key not in self.cache:
            self.cache[key] = []
        self.cache[key].append((timestamp, value))

    def get(self, key, timestamp):
        if key not in self.cache:
            return ""

        arr = self.cache[key]
        lo, hi = 0, len(arr)-1
        res = ""
        while lo <= hi:
            mid = lo+(hi-lo)//2
            if arr[mid][0] <= timestamp:
                res = arr[mid][1]
                lo = mid+1
            else:
                hi = mid-1
        return res

if __name__ == "__main__":
    time_map = TimeMap()
