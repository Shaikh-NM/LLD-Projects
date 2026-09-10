from heapq import heappop, heappush

class StockPrice:

    def __init__(self):
        self.timestamp_to_price = {}
        self.latest_timestamp = 0
        
        self.min_heap = []
        self.max_heap = []

    def update(self, timestamp: int, price: int) -> None:
        self.timestamp_to_price[timestamp] = price
        if timestamp > self.latest_timestamp:
            self.latest_timestamp = timestamp

        heappush(self.min_heap, (price, timestamp))
        heappush(self.max_heap, (-price, timestamp))

    def current(self) -> int:
        return self.timestamp_to_price[self.latest_timestamp]

    def maximum(self) -> int:
        while self.max_heap:
            neg_price, timestamp = self.max_heap[0]
            if -neg_price == self.timestamp_to_price[timestamp]:
                return -neg_price
            heappop(self.max_heap)

    def minimum(self) -> int:
        while self.min_heap:
            price, timestamp = self.min_heap[0]
            if price == self.timestamp_to_price[timestamp]:
                return price
            heappop(self.min_heap)