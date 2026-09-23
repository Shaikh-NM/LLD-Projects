import java.util.ArrayDeque;
import java.util.HashSet;
import java.util.Queue;
import java.util.Set;

class PhoneDictionary {

    private final Queue<Integer> availableQueue;
    private final Set<Integer> availableSet;

    public PhoneDictionary(int maxNumbers) {
        this.availableQueue = new ArrayDeque<>();
        this.availableSet = new HashSet<>();
        for (int i = 0; i < maxNumbers; i++) {
            this.availableQueue.offer(i);
            this.availableSet.add(i);
        }
    }

    public int get() {
        if (availableQueue.isEmpty()) {
            return -1;
        }

        int num = availableQueue.poll();
        availableSet.remove(num);
        return num;
    }

    public boolean check(int num) {
        return availableSet.contains(num);
    }

    public void release(int num) {
        if (!availableSet.contains(num)) {
            availableSet.add(num);
            availableQueue.offer(num);
        }
    }
}