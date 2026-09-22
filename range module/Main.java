class RangeModule {

    private static class SegmentTreeNode {
        int l, r, mid;
        SegmentTreeNode left, right;
        boolean tracked;
        int lazy; // 0: no pending update, 1: addRange (true), -1: removeRange (false)

        SegmentTreeNode(int l, int r) {
            this.l = l;
            this.r = r;
            this.mid = l + (r - l) / 2;
            this.tracked = false;
            this.lazy = 0;
        }
    }

    private final SegmentTreeNode root;

    public RangeModule() {
        // Range spans up to 10^9 as per constraints
        this.root = new SegmentTreeNode(1, 1_000_000_000);
    }

    private void update(SegmentTreeNode node, int ql, int qr, boolean val) {
        if (ql <= node.l && node.r <= qr) {
            node.tracked = val;
            node.lazy = val ? 1 : -1;
            return;
        }

        pushDown(node);

        if (ql <= node.mid) {
            update(node.left, ql, qr, val);
        }
        if (qr > node.mid) {
            update(node.right, ql, qr, val);
        }

        node.tracked = node.left.tracked && node.right.tracked;
    }

    private void pushDown(SegmentTreeNode node) {
        if (node.left == null) {
            node.left = new SegmentTreeNode(node.l, node.mid);
        }
        if (node.right == null) {
            node.right = new SegmentTreeNode(node.mid + 1, node.r);
        }

        if (node.lazy != 0) {
            boolean val = (node.lazy == 1);
            node.left.tracked = val;
            node.left.lazy = node.lazy;
            node.right.tracked = val;
            node.right.lazy = node.lazy;
            node.lazy = 0;
        }
    }

    private boolean query(SegmentTreeNode node, int ql, int qr) {
        if (ql <= node.l && node.r <= qr) {
            return node.tracked;
        }

        pushDown(node);

        boolean res = true;
        if (ql <= node.mid) {
            res = res && query(node.left, ql, qr);
        }
        if (qr > node.mid) {
            res = res && query(node.right, ql, qr);
        }

        return res;
    }

    public void addRange(int left, int right) {
        update(root, left, right - 1, true);
    }

    public boolean queryRange(int left, int right) {
        return query(root, left, right - 1);
    }

    public void removeRange(int left, int right) {
        update(root, left, right - 1, false);
    }
}