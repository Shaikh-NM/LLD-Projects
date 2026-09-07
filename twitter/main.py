from collections import defaultdict
import heapq
from typing import List

class Twitter:
    def __init__(self):
        self.time = 0
        self.tweets = defaultdict(list)
        self.following = defaultdict(set)

    def postTweet(self, userId: int, tweetId: int) -> None:
        self.time += 1
        self.tweets[userId].append((self.time, tweetId))

    def getNewsFeed(self, userId: int) -> List[int]:
        users = set(self.following[userId])
        users.add(userId)
        
        max_heap = []
        for u in users:
            if self.tweets[u]:
                last_idx = len(self.tweets[u]) - 1
                t, tw_id = self.tweets[u][last_idx]
                heapq.heappush(max_heap, (-t, tw_id, u, last_idx - 1))
                
        feed = []
        while max_heap and len(feed) < 10:
            neg_t, tw_id, u, next_idx = heapq.heappop(max_heap)
            feed.append(tw_id)
            
            if next_idx >= 0:
                t, next_tw_id = self.tweets[u][next_idx]
                heapq.heappush(max_heap, (-t, next_tw_id, u, next_idx - 1))
        return feed

    def follow(self, followerId: int, followeeId: int) -> None:
        if followerId != followeeId:
            self.following[followerId].add(followeeId)

    def unfollow(self, followerId: int, followeeId: int) -> None:
        self.following[followerId].discard(followeeId)