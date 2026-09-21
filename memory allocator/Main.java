import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

class Allocator {

    // Helper class to track each allocated block interval [start, size]
    private static class Block {
        int start;
        int size;

        Block(int start, int size) {
            this.start = start;
            this.size = size;
        }
    }

    private final int n;
    private final int[] memory;
    private final Map<Integer, List<Block>> idToBlocks;

    public Allocator(int n) {
        this.n = n;
        this.memory = new int[n];
        this.idToBlocks = new HashMap<>();
    }

    public int allocate(int size, int mID) {
        int freeCount = 0;

        for (int i = 0; i < n; i++) {
            if (memory[i] == 0) {
                freeCount++;
                if (freeCount == size) {
                    int startIdx = i - size + 1;

                    // Fill the allocated block with mID
                    Arrays.fill(memory, startIdx, startIdx + size, mID);

                    // Track the block coordinates for quick deallocation
                    idToBlocks.computeIfAbsent(mID, k -> new ArrayList<>()).add(new Block(startIdx, size));
                    return startIdx;
                }
            } else {
                freeCount = 0;
            }
        }

        return -1;
    }

    public int freeMemory(int mID) {
        if (!idToBlocks.containsKey(mID)) {
            return 0;
        }

        List<Block> blocks = idToBlocks.remove(mID);
        int totalFreed = 0;

        for (Block block : blocks) {
            Arrays.fill(memory, block.start, block.start + block.size, 0);
            totalFreed += block.size;
        }

        return totalFreed;
    }
}