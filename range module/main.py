class SegmentTreeNode:
    def __init__(self, l, r):
        self.l = l
        self.r = r
        self.mid = l+(r-l)//2
        self.left = None
        self.right = None
        self.tracked = False
        self.lazy = 0

class RangeModule:
    def __init__(self):
        self.root = SegmentTreeNode(1, 10**9)

    def _update(self, node, ql, qr, val):
        if ql <= node.l and node.r <= qr:
            node.tracked = val
            node.lazy = 1 if val else -1
            return 

        self._push_down(node)
        if ql <= node.mid:
            self._update(node.left, ql, qr, val)
        if qr > node.mid:
            self._update(node.right, ql, qr, val)

        node.tracked = node.left.tracked and node.right.tracked
        
    def _push_down(self, node):
        if not node.left:
            node.left = SegmentTreeNode(node.l, node.mid)
        if not node.right:
            node.right = SegmentTreeNode(node.mid+1, node.r)

        if node.lazy != 0:
            val = (node.lazy == 1)
            node.left.tracked = val
            node.left.lazy = node.lazy
            node.right.tracked = val
            node.right.lazy = node.lazy
            node.lazy = 0

    def _query(self, node, ql, qr):
        if ql <= node.l and ql <= node.r:
            return node.tracked

        self._push_down(node)
        res = True
        if ql <= node.mid:
            res = res and self._query(node.left, ql, qr)
        if qr > node.mid:
            res = res and self._query(node.right, ql, qr)
        return res
    
    def addRange(self, left: int, right: int) -> None:
        self._update(self.root, left, right-1, True)

    def queryRange(self, left: int, right: int) -> bool:
        self._query(self.root, left, right-1)
        
    def removeRange(self, left: int, right: int) -> None:
        self._update(self.root, left, right-1, False)

# Your RangeModule object will be instantiated and called as such:
# obj = RangeModule()
# obj.addRange(left,right)
# param_2 = obj.queryRange(left,right)
# obj.removeRange(left,right)