class Node:
    __slots__ = ('val', 'right', 'down')

    def __init__(self, val=-1, right=None, down=None):
        self.val = val
        self.right = right
        self.down = down

class Skiplist:
    MAX_LEVEL = 16
    def __init__(self):
        self.head = Node(-1)
        curr = self.head
        for _ in range(self.MAX_LEVEL - 1):
            curr.down = Node(-1)
            curr = curr.down
            
        self._seed = 123456789

    def _random_level(self) -> int:
        lvl = 1
        while lvl < self.MAX_LEVEL:
            self._seed = (self._seed * 1664525 + 1013904223) & 0xFFFFFFFF
            if (self._seed & 1) == 0:
                break
            lvl += 1
        return lvl

    def search(self, target: int) -> bool:
        curr = self.head
        while curr:
            while curr.right and curr.right.val < target:
                curr = curr.right

            if curr.right and curr.right.val == target:
                return True

            curr = curr.down
        return False

    def add(self, num: int) -> None:
        lvl = self._random_level()
        curr = self.head
        
        current_level = self.MAX_LEVEL
        while current_level > lvl:
            while curr.right and curr.right.val < num:
                curr = curr.right
            curr = curr.down
            current_level -= 1

        down_node = None
        nodes_to_update = []
        while curr:
            while curr.right and curr.right.val < num:
                curr = curr.right
            nodes_to_update.append(curr)
            curr = curr.down

        for prev in reversed(nodes_to_update):
            new_node = Node(num, prev.right, down_node)
            prev.right = new_node
            down_node = new_node

    def erase(self, num: int) -> bool:
        curr = self.head
        found = False
        
        while curr:
            while curr.right and curr.right.val < num:
                curr = curr.right

            if curr.right and curr.right.val == num:
                curr.right = curr.right.right
                found = True
            
            curr = curr.down
        return found


# Your Skiplist object will be instantiated and called as such:
# obj = Skiplist()
# param_1 = obj.search(target)
# obj.add(num)
# param_3 = obj.erase(num)