from collections import defaultdict
class Allocator:
    def __init__(self, n: int):
        self.n = n
        self.memory = [0]*n
        self.id_to_blocks = defaultdict(list)

    def allocate(self, size: int, mID: int) -> int:
        free_count = 0
        for i in range(self.n):
            if self.memory[i] == 0:
                free_count += 1
                if free_count == size:
                    start_idx = i-size+1
                
                    for j in range(start_idx, i+1):
                        self.memory[j] = mID

                    self.id_to_blocks[mID].append((start_idx, size))
                    return start_idx
            else:
                free_count = 0
        return - 1

    def freeMemory(self, mID: int) -> int:
        if mID not in self.id_to_blocks:
            return 0

        total_freed = 0
        for start_idx, size in self.id_to_blocks[mID]:
            for j in range(start_idx, start_idx+size):
                self.memory[j] = 0
            total_freed += size
        
        del self.id_to_blocks[mID]
        return total_freed


# Your Allocator object will be instantiated and called as such:
# obj = Allocator(n)
# param_1 = obj.allocate(size,mID)
# param_2 = obj.freeMemory(mID)