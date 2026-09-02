from typing import Optional
from collections import deque

class Node:
    def __init__(self, val):
        self.val = val
        self.left = None
        self.right = None

class SerializeAndDeserializeBST:
    def __init__(self):
        pass

    def serialize(self, root: Optional[Node])->str:
        vals = []
        def f(node):
            if not node:
                return

            vals.append(str(node.val))
            f(node.left)
            f(node.right)      

        f(root)
        return " ".join(vals)

    def deserialize(self, data: str)->Optional[Node]:
        if not data:
            return None

        queue = deque(int(x) for x in data.split())

        def f(lower_bound, upper_bound)->Optional[Node]:
            if not queue:
                return None

            val = queue[0]

            if not (lower_bound < val < upper_bound):
                return None

            queue.popleft()
            node = Node(val)
            node.left = f(lower_bound, val)
            node.right = f(val, upper_bound)
            return node
        return f(float('-inf'), float('inf'))