from bisect import bisect_left, bisect_right

class ExamTracker:
    def __init__(self):
        self.times = []
        self.prefix_scores = [0]

    def record(self, time: int, score: int) -> None:
        self.times.append(time)
        self.prefix_scores.append(self.prefix_scores[-1] + score)

    def totalScore(self, startTime: int, endTime: int) -> int:
        left_idx = bisect_left(self.times, startTime)
        right_idx = bisect_right(self.times, endTime) - 1

        if left_idx > right_idx:
            return 0
        return self.prefix_scores[right_idx + 1] - self.prefix_scores[left_idx]


# Your ExamTracker object will be instantiated and called as such:
# obj = ExamTracker()
# obj.record(time,score)
# param_2 = obj.totalScore(startTime,endTime)