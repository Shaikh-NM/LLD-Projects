from typing import List, Dict, Optional
import bisect


# ==========================================
# 1. VALUE OBJECTS & MODELS
# ==========================================

class TrainOccupancy:
    """Represents a scheduled block of time a train occupies a platform."""
    def __init__(self, train_id: str, platform_id: int, start_time: int, departure_time: int, delay: int):
        self._train_id: str = train_id
        self._platform_id: int = platform_id
        self._start_time: int = start_time
        self._departure_time: int = departure_time
        self._delay: int = delay

    @property
    def train_id(self) -> str:
        return self._train_id

    @property
    def platform_id(self) -> int:
        return self._platform_id

    @property
    def start_time(self) -> int:
        return self._start_time

    @property
    def departure_time(self) -> int:
        return self._departure_time

    @property
    def delay(self) -> int:
        return self._delay

    def is_active_at(self, timestamp: int) -> bool:
        """Inclusive boundary check: start_time <= timestamp <= departure_time."""
        return self._start_time <= timestamp <= self._departure_time


# ==========================================
# 2. PLATFORM ENTITY
# ==========================================

class Platform:
    """Manages consecutive time slots and schedules on a single platform track."""
    def __init__(self, platform_id: int):
        self._platform_id: int = platform_id
        self._schedule: List[TrainOccupancy] = []

    @property
    def platform_id(self) -> int:
        return self._platform_id

    def get_earliest_available_time(self) -> int:
        """Returns the earliest timestamp this platform can receive a new train."""
        if not self._schedule:
            return 0
        # Platform becomes available exactly 1 unit after last departure
        return self._schedule[-1].departure_time + 1

    def calculate_delay(self, arrival_time: int) -> int:
        available_time = max(arrival_time, self.get_earliest_available_time())
        return available_time - arrival_time

    def schedule_train(self, train_id: str, arrival_time: int, wait_time: int) -> TrainOccupancy:
        delay = self.calculate_delay(arrival_time)
        start_time = arrival_time + delay
        departure_time = start_time + wait_time - 1  # Inclusive interval

        occupancy = TrainOccupancy(
            train_id=train_id,
            platform_id=self._platform_id,
            start_time=start_time,
            departure_time=departure_time,
            delay=delay
        )
        self._schedule.append(occupancy)
        return occupancy

    def get_train_at(self, timestamp: int) -> str:
        """Finds the train on this platform at a specific timestamp via binary search."""
        if not self._schedule:
            return ""

        # Binary search by departure_time
        # Find first interval where departure_time >= timestamp
        idx = bisect.bisect_left([occ.departure_time for occ in self._schedule], timestamp)
        
        if idx < len(self._schedule):
            candidate = self._schedule[idx]
            if candidate.is_active_at(timestamp):
                return candidate.train_id

        return ""


# ==========================================
# 3. MANAGER / ORCHESTRATOR HUB
# ==========================================

class TrainPlatformManager:
    """Central orchestrator managing platform assignments and time-based queries."""

    def __init__(self, platform_count: int):
        if platform_count < 1 or platform_count > 20:
            raise ValueError("Platform count must be between 1 and 20.")
        
        self._platforms: List[Platform] = [Platform(i) for i in range(platform_count)]
        self._train_registry: Dict[str, TrainOccupancy] = {}

    def assign_platform(self, train_id: str, arrival_time: int, wait_time: int) -> str:
        """
        Assigns the train to the optimal platform with the lowest delay.
        Ties are broken by lowest platform index.
        Returns: "platformNumber,delayTime"
        """
        best_platform: Optional[Platform] = None
        min_delay: int = float('inf')

        for platform in self._platforms:
            delay = platform.calculate_delay(arrival_time)
            # Strict '<' naturally prefers lower platform index on ties
            if delay < min_delay:
                min_delay = delay
                best_platform = platform

        # Commit schedule assignment
        occupancy = best_platform.schedule_train(train_id, arrival_time, wait_time)
        self._train_registry[train_id] = occupancy

        return f"{best_platform.platform_id},{occupancy.delay}"

    def get_train_at_platform(self, platform_number: int, timestamp: int) -> str:
        """Returns occupying trainId or '' if none."""
        if 0 <= platform_number < len(self._platforms):
            return self._platforms[platform_number].get_train_at(timestamp)
        return ""

    def get_platform_of_train(self, train_id: str, timestamp: int) -> int:
        """Returns platform index (0-based) or -1 if train is not active at the timestamp."""
        if train_id in self._train_registry:
            occupancy = self._train_registry[train_id]
            if occupancy.is_active_at(timestamp):
                return occupancy.platform_id
        return -1


# ==========================================
# 4. VERIFICATION / EXAMPLE RUNNER
# ==========================================

if __name__ == "__main__":
    mgr = TrainPlatformManager(3)

    # 1) First arrivals
    assert mgr.assign_platform("T1", 0, 5) == "0,0"
    assert mgr.assign_platform("T2", 2, 3) == "1,0"
    assert mgr.assign_platform("T3", 4, 4) == "2,0"

    # 2) Handoff on P0
    assert mgr.assign_platform("T4", 5, 5) == "0,0"

    # 3) Earliest free time tie-breaks
    assert mgr.assign_platform("T5", 9, 1) == "1,0"
    assert mgr.assign_platform("T6", 9, 2) == "2,0"

    # 4) Delayed assignment with tie-break
    assert mgr.assign_platform("T7", 9, 3) == "0,1"

    # Point-in-time platform queries
    assert mgr.get_train_at_platform(0, 4) == "T1"
    assert mgr.get_train_at_platform(0, 5) == "T4"
    assert mgr.get_train_at_platform(1, 9) == "T5"
    assert mgr.get_train_at_platform(2, 10) == "T6"
    assert mgr.get_train_at_platform(0, 10) == "T7"

    # Train-centric queries
    assert mgr.get_platform_of_train("T7", 9) == -1   # Still waiting
    assert mgr.get_platform_of_train("T7", 10) == 0   # Active on P0
    assert mgr.get_platform_of_train("T5", 10) == -1  # Already departed
    assert mgr.get_platform_of_train("T6", 11) == -1  # Already departed

    print("✅ All test assertions passed successfully!")