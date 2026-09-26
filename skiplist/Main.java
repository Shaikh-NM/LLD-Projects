import java.util.ArrayList;
import java.util.List;

class Skiplist {

    private static class Node {
        int val;
        Node right;
        Node down;

        Node(int val, Node right, Node down) {
            this.val = val;
            this.right = right;
            this.down = down;
        }

        Node(int val) {
            this(val, null, null);
        }
    }

    private static final int MAX_LEVEL = 16;
    private final Node head;
    private long seed;

    public Skiplist() {
        this.head = new Node(-1);
        Node curr = this.head;
        for (int i = 0; i < MAX_LEVEL - 1; i++) {
            curr.down = new Node(-1);
            curr = curr.down;
        }
        this.seed = 123456789L;
    }

    private int randomLevel() {
        int lvl = 1;
        while (lvl < MAX_LEVEL) {
            seed = (seed * 1664525L + 1013904223L) & 0xFFFFFFFFL;
            if ((seed & 1L) == 0) {
                break;
            }
            lvl++;
        }
        return lvl;
    }

    public boolean search(int target) {
        Node curr = head;
        while (curr != null) {
            while (curr.right != null && curr.right.val < target) {
                curr = curr.right;
            }

            if (curr.right != null && curr.right.val == target) {
                return true;
            }

            curr = curr.down;
        }
        return false;
    }

    public void add(int num) {
        int lvl = randomLevel();
        Node curr = head;

        int currentLevel = MAX_LEVEL;
        while (currentLevel > lvl) {
            while (curr.right != null && curr.right.val < num) {
                curr = curr.right;
            }
            curr = curr.down;
            currentLevel--;
        }

        List<Node> nodesToUpdate = new ArrayList<>();
        while (curr != null) {
            while (curr.right != null && curr.right.val < num) {
                curr = curr.right;
            }
            nodesToUpdate.add(curr);
            curr = curr.down;
        }

        Node downNode = null;
        for (int i = nodesToUpdate.size() - 1; i >= 0; i--) {
            Node prev = nodesToUpdate.get(i);
            Node newNode = new Node(num, prev.right, downNode);
            prev.right = newNode;
            downNode = newNode;
        }
    }

    public boolean erase(int num) {
        Node curr = head;
        boolean found = false;

        while (curr != null) {
            while (curr.right != null && curr.right.val < num) {
                curr = curr.right;
            }

            if (curr.right != null && curr.right.val == num) {
                curr.right = curr.right.right;
                found = true;
            }

            curr = curr.down;
        }
        return found;
    }
}