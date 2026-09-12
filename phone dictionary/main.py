from collections import deque

class PhoneDictionary:
    def __init__(self, maxNumbers):
        self.available_queue = deque(range(maxNumbers))
        self.available_set = set(range(maxNumbers))

    def get(self):
        if  not self.available_queue:
            return -1

        num = self.available_queue.popleft()
        self.available_set.remove(num)
        return num

    def check(self, num):
        if num in self.available_set:
            return True
        return False

    def release(self, num):
        if num not in self.available_set:
            self.available_set.add(num)
            self.available_queue.append(num)