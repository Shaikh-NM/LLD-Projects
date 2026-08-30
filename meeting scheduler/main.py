from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Set, Optional
import bisect


# ==========================================
# 1. VALUE OBJECTS & ENUMS
# ==========================================

class RSVPStatus(Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class TimeInterval:
    """Immutable value object representing a continuous time range [start, end)."""
    def __init__(self, start_time: int, end_time: int):
        if start_time >= end_time:
            raise ValueError(f"Invalid interval: start ({start_time}) must be < end ({end_time}).")
        self._start_time: int = start_time
        self._end_time: int = end_time

    @property
    def start_time(self) -> int:
        return self._start_time

    @property
    def end_time(self) -> int:
        return self._end_time

    @property
    def duration(self) -> int:
        return self._end_time - self._start_time

    def overlaps(self, other: 'TimeInterval') -> bool:
        """Returns True if two half-open intervals [s1, e1) and [s2, e2) overlap."""
        return max(self._start_time, other.start_time) < min(self._end_time, other.end_time)

    def __lt__(self, other: 'TimeInterval') -> bool:
        return (self._start_time, self._end_time) < (other.start_time, other.end_time)

    def __repr__(self) -> str:
        return f"[{self._start_time}..{self._end_time})"


# ==========================================
# 2. OBSERVER PATTERN (Notifications)
# ==========================================

class NotificationObserver(ABC):
    @abstractmethod
    def on_meeting_scheduled(self, meeting: 'Meeting', recipient: 'User') -> None:
        pass

    @abstractmethod
    def on_meeting_canceled(self, meeting: 'Meeting', recipient: 'User') -> None:
        pass


class EmailNotificationService(NotificationObserver):
    def on_meeting_scheduled(self, meeting: 'Meeting', recipient: 'User') -> None:
        print(f"📧 [Email] To: {recipient.email} | New Invite: '{meeting.title}' at {meeting.interval}")

    def on_meeting_canceled(self, meeting: 'Meeting', recipient: 'User') -> None:
        print(f"📧 [Email] To: {recipient.email} | CANCELED: '{meeting.title}'")


# ==========================================
# 3. DOMAIN MODELS & ENTITIES
# ==========================================

class User:
    """Represents a platform user with an email and personal calendar."""
    def __init__(self, user_id: str, name: str, email: str):
        self.user_id: str = user_id
        self.name: str = name
        self.email: str = email
        self.calendar: 'Calendar' = Calendar(user_id)

    def __repr__(self) -> str:
        return f"User({self.name})"


class Meeting:
    """Represents a scheduled event with participants, interval, and RSVP states."""
    def __init__(
        self,
        meeting_id: str,
        title: str,
        organizer: User,
        interval: TimeInterval,
        participants: List[User],
        room_id: Optional[str] = None
    ):
        self.meeting_id: str = meeting_id
        self.title: str = title
        self.organizer: User = organizer
        self.interval: TimeInterval = interval
        self.participants: List[User] = participants
        self.room_id: Optional[str] = room_id
        self.rsvp_status_map: Dict[str, RSVPStatus] = {
            u.user_id: RSVPStatus.PENDING for u in participants
        }
        # Organizer automatically accepts
        self.rsvp_status_map[organizer.user_id] = RSVPStatus.ACCEPTED

    def set_rsvp(self, user_id: str, status: RSVPStatus) -> None:
        if user_id in self.rsvp_status_map:
            self.rsvp_status_map[user_id] = status


# ==========================================
# 4. CALENDAR & AVAILABILITY ENGINE
# ==========================================

class Calendar:
    """Manages scheduled intervals for a user with binary search conflict detection."""
    def __init__(self, owner_id: str):
        self.owner_id: str = owner_id
        self._meetings: List[Meeting] = []

    def get_busy_intervals(self) -> List[TimeInterval]:
        return [m.interval for m in self._meetings]

    def is_available(self, target_interval: TimeInterval) -> bool:
        """Binary search check to determine if target_interval overlaps any existing meeting."""
        if not self._meetings:
            return True

        intervals = [m.interval for m in self._meetings]
        # Locate insertion index based on start_time
        idx = bisect.bisect_right([i.start_time for i in intervals], target_interval.start_time)

        # Check left neighbor
        if idx > 0 and intervals[idx - 1].overlaps(target_interval):
            return False

        # Check right neighbor
        if idx < len(intervals) and intervals[idx].overlaps(target_interval):
            return False

        return True

    def add_meeting(self, meeting: Meeting) -> None:
        bisect.insort_left(self._meetings, meeting, key=lambda m: m.interval)

    def remove_meeting(self, meeting_id: str) -> Optional[Meeting]:
        for i, m in enumerate(self._meetings):
            if m.meeting_id == meeting_id:
                return self._meetings.pop(i)
        return None


# ==========================================
# 5. SLOT FINDER STRATEGY (Interval Fusion)
# ==========================================

class SlotFinderStrategy(ABC):
    @abstractmethod
    def find_common_free_slots(
        self,
        users: List[User],
        day_start: int,
        day_end: int,
        duration: int
    ) -> List[TimeInterval]:
        pass


class SweepingLineSlotFinder(SlotFinderStrategy):
    """
    Merges all busy intervals across all users, then computes inverse free gaps >= duration.
    Complexity: O(M log M) where M is total number of meetings across all users.
    """
    def find_common_free_slots(
        self,
        users: List[User],
        day_start: int,
        day_end: int,
        duration: int
    ) -> List[TimeInterval]:
        # 1. Collect all busy intervals from all requested users
        all_busy: List[TimeInterval] = []
        for user in users:
            all_busy.extend(user.calendar.get_busy_intervals())

        if not all_busy:
            return [TimeInterval(day_start, day_end)] if (day_end - day_start) >= duration else []

        # 2. Sort intervals by start time
        all_busy.sort()

        # 3. Merge overlapping or adjacent busy intervals
        merged_busy: List[TimeInterval] = []
        current = all_busy[0]

        for nxt in all_busy[1:]:
            if nxt.start_time <= current.end_time:
                # Merge
                current = TimeInterval(current.start_time, max(current.end_time, nxt.end_time))
            else:
                merged_busy.append(current)
                current = nxt
        merged_busy.append(current)

        # 4. Find free gaps between day_start and day_end
        free_slots: List[TimeInterval] = []
        cursor = day_start

        for busy in merged_busy:
            if busy.start_time > cursor:
                gap = busy.start_time - cursor
                if gap >= duration:
                    free_slots.append(TimeInterval(cursor, min(busy.start_time, day_end)))
            cursor = max(cursor, busy.end_time)

        if day_end - cursor >= duration:
            free_slots.append(TimeInterval(cursor, day_end))

        return free_slots


# ==========================================
# 6. SCHEDULER FACADE
# ==========================================

class MeetingSchedulerService:
    """Central orchestrator for meeting creation, resolution, and notifications."""
    def __init__(
        self,
        notification_service: Optional[NotificationObserver] = None,
        slot_finder: Optional[SlotFinderStrategy] = None
    ):
        self._meetings: Dict[str, Meeting] = {}
        self._notifier: NotificationObserver = notification_service or EmailNotificationService()
        self._slot_finder: SlotFinderStrategy = slot_finder or SweepingLineSlotFinder()

    def find_available_slots(
        self,
        users: List[User],
        day_start: int,
        day_end: int,
        duration: int
    ) -> List[TimeInterval]:
        return self._slot_finder.find_common_free_slots(users, day_start, day_end, duration)

    def schedule_meeting(
        self,
        meeting_id: str,
        title: str,
        organizer: User,
        participants: List[User],
        interval: TimeInterval,
        room_id: Optional[str] = None
    ) -> Optional[Meeting]:
        all_attendees = [organizer] + [p for p in participants if p.user_id != organizer.user_id]

        # 1. Conflict Check: Ensure everyone is available
        for attendee in all_attendees:
            if not attendee.calendar.is_available(interval):
                print(f"❌ Scheduling Conflict: {attendee.name} is busy during {interval}.")
                return None

        # 2. Instantiate and add meeting to all calendars
        meeting = Meeting(meeting_id, title, organizer, participants, room_id)
        for attendee in all_attendees:
            attendee.calendar.add_meeting(meeting)

        self._meetings[meeting_id] = meeting
        print(f"✅ Successfully Scheduled: '{title}' ({interval})")

        # 3. Trigger notification updates
        for attendee in participants:
            self._notifier.on_meeting_scheduled(meeting, attendee)

        return meeting

    def cancel_meeting(self, meeting_id: str) -> bool:
        if meeting_id not in self._meetings:
            return False

        meeting = self._meetings.pop(meeting_id)
        all_attendees = [meeting.organizer] + meeting.participants

        for attendee in all_attendees:
            attendee.calendar.remove_meeting(meeting_id)
            if attendee.user_id != meeting.organizer.user_id:
                self._notifier.on_meeting_canceled(meeting, attendee)

        print(f"🗑️ Meeting '{meeting.title}' successfully canceled.")
        return True


# ==========================================
# 7. RUNTIME DEMONSTRATION & TEST CASES
# ==========================================

if __name__ == "__main__":
    scheduler = MeetingSchedulerService()

    # 1. Instantiate Users
    alice = User("u1", "Alice", "alice@example.com")
    bob = User("u2", "Bob", "bob@example.com")
    charlie = User("u3", "Charlie", "charlie@example.com")

    # Day working hours: 9:00 AM (900) to 5:00 PM (1700)
    DAY_START = 900
    DAY_END = 1700

    print("--- 1. Schedule Individual Meetings ---")
    # Alice has standup: [900..930)
    scheduler.schedule_meeting("m1", "Daily Standup", alice, [alice], TimeInterval(900, 930))
    # Bob has client review: [1000..1130)
    scheduler.schedule_meeting("m2", "Client Sync", bob, [bob], TimeInterval(1000, 1130))

    print("\n--- 2. Find Common Free 60-Minute Slots for Alice & Bob ---")
    common_slots = scheduler.find_available_slots([alice, bob], DAY_START, DAY_END, duration=60)
    for slot in common_slots:
        print(f"  🕒 Free Slot: {slot} (Duration: {slot.duration} mins)")

    print("\n--- 3. Schedule Team Meeting in a Free Slot ---")
    # Book slot [1300..1400) for Alice, Bob, and Charlie
    team_meeting = scheduler.schedule_meeting(
        meeting_id="m3",
        title="Architecture Deep Dive",
        organizer=alice,
        participants=[bob, charlie],
        interval=TimeInterval(1300, 1400)
    )
    assert team_meeting is not None

    print("\n--- 4. Attempt to Double-Book Overlapping Slot ---")
    # Attempt meeting for Bob during [1330..1430) -> Should fail
    conflicting = scheduler.schedule_meeting(
        meeting_id="m4",
        title="Emergency Fix",
        organizer=charlie,
        participants=[bob],
        interval=TimeInterval(1330, 1430)
    )
    assert conflicting is None

    print("\n--- 5. Cancel Meeting & Verify Free Slot Recovery ---")
    scheduler.cancel_meeting("m3")
    # Bob should now be free for [1330..1430)
    recovered = scheduler.schedule_meeting(
        meeting_id="m4",
        title="Emergency Fix",
        organizer=charlie,
        participants=[bob],
        interval=TimeInterval(1330, 1430)
    )
    assert recovered is not None