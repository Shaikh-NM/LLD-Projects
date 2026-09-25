import java.util.ArrayDeque;
import java.util.Queue;

class TreeNode {
    int val;
    TreeNode left;
    TreeNode right;

    TreeNode(int val) {
        this.val = val;
    }
}

public class Codec {

    // Encodes a tree to a single string using Preorder traversal
    public String serialize(TreeNode root) {
        StringBuilder sb = new StringBuilder();
        serializeHelper(root, sb);
        return sb.toString().trim();
    }

    private void serializeHelper(TreeNode node, StringBuilder sb) {
        if (node == null) {
            return;
        }

        sb.append(node.val).append(" ");
        serializeHelper(node.left, sb);
        serializeHelper(node.right, sb);
    }

    // Decodes your encoded data to tree using BST bounds
    public TreeNode deserialize(String data) {
        if (data == null || data.trim().isEmpty()) {
            return null;
        }

        Queue<Integer> queue = new ArrayDeque<>();
        for (String valStr : data.trim().split("\\s+")) {
            queue.offer(Integer.parseInt(valStr));
        }

        return deserializeHelper(Long.MIN_VALUE, Long.MAX_VALUE, queue);
    }

    private TreeNode deserializeHelper(long lowerBound, long upperBound, Queue<Integer> queue) {
        if (queue.isEmpty()) {
            return null;
        }

        int val = queue.peek();
        if (val <= lowerBound || val >= upperBound) {
            return null;
        }

        queue.poll();
        TreeNode node = new TreeNode(val);
        node.left = deserializeHelper(lowerBound, val, queue);
        node.right = deserializeHelper(val, upperBound, queue);

        return node;
    }
}