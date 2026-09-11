from typing import List

class TreeAncestor:
    def __init__(self, n: int, parent: List[int]):
        self.LOG = 16
        self.up = [[-1] * n for _ in range(self.LOG)]
        self.up[0] = parent[:]
        for i in range(1, self.LOG):
            for node in range(n):
                ancestor = self.up[i - 1][node]
                if ancestor != -1:
                    self.up[i][node] = self.up[i - 1][ancestor]

    def getKthAncestor(self, node: int, k: int) -> int:
        for i in range(self.LOG):
            if (k >> i) & 1:
                node = self.up[i][node]
                if node == -1:
                    return -1
        return node

# Your TreeAncestor object will be instantiated and called as such:
# obj = TreeAncestor(n, parent)
# param_1 = obj.getKthAncestor(node,k)