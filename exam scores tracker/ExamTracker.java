import java.util.ArrayList;
import java.util.List;

class ExamTracker {
    private final List<Integer> times;
    private final List<Long> prefixScores;

    public ExamTracker() {
        this.times = new ArrayList<>();
        this.prefixScores = new ArrayList<>();
        this.prefixScores.add(0L);
    }

    public void record(int time, int score) {
        times.add(time);
        long lastSum = prefixScores.get(prefixScores.size() - 1);
        prefixScores.add(lastSum + score);
    }

    public long totalScore(int startTime, int endTime) {
        int leftIdx = lowerBound(startTime);
        int rightIdx = upperBound(endTime) - 1;

        if (leftIdx > rightIdx) {
            return 0L;
        }

        return prefixScores.get(rightIdx + 1) - prefixScores.get(leftIdx);
    }

    // Equivalent to bisect_left: first index with time >= target
    private int lowerBound(int target) {
        int lo = 0, hi = times.size();
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (times.get(mid) >= target) {
                hi = mid;
            } else {
                lo = mid + 1;
            }
        }
        return lo;
    }

    // Equivalent to bisect_right: first index with time > target
    private int upperBound(int target) {
        int lo = 0, hi = times.size();
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (times.get(mid) > target) {
                hi = mid;
            } else {
                lo = mid + 1;
            }
        }
        return lo;
    }
}

/**
 * Your ExamTracker object will be instantiated and called as such:
 * ExamTracker obj = new ExamTracker();
 * obj.record(time, score);
 * long param_2 = obj.totalScore(startTime, endTime);
 */