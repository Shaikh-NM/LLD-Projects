from abc import ABC, abstractmethod
from enum import Enum
import threading
import time
from typing import List, Dict, Optional, Set


# ==========================================
# 1. DOMAIN ENUMS & VALUE OBJECTS
# ==========================================

class TableType(Enum):
    INDOOR = "INDOOR"
    OUTDOOR = "OUTDOOR"
    BOOTH = "BOOTH"
    BAR = "BAR"


class ReservationStatus(Enum):
    PENDING_HOLD = "PENDING_HOLD"
    CONFIRMED = "CONFIRMED"
    SEATED = "SEATED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Table:
    """Represents a physical table with seating capacity."""
    def __init__(self, table_id: str, capacity: int, table_type: TableType):
        self.table_id: str = table_id
        self.capacity: int = capacity
        self.table_type: TableType = table_type


class TimeSlot:
    """Represents a discrete reservation window (e.g., 19:00 - 21:00 on 2026-09-01)."""
    def __init__(self, date_str: str, start_hour: int, duration_hours: int = 2):
        self.date_str: str = date_str          # "YYYY-MM-DD"
        self.start_hour: int = start_hour      # 24-hr format (e.g., 19 for 7 PM)
        self.end_hour: int = start_hour + duration_hours

    @property
    def slot_key(self) -> str:
        pass
        # return f"{self.date_str}_{self.start_hour:02d}:00"

    def __repr__(self) -> str:
        return f"[{self.date_str} {self.start_hour:02d}:00 - {self.end_hour:02d}:00]"


# ==========================================
# 2. OBSERVER PATTERN (Notifications)
# ==========================================
class NotificationObserver(ABC):
    @abstractmethod
    def on_reservation_updated(self, reservation: 'Reservation') -> None:
        pass


class EmailNotificationService(NotificationObserver):
    def on_reservation_updated(self, reservation: 'Reservation') -> None:
        print(f"📧 [Email Alert] Reservation {reservation.reservation_id} for '{reservation.customer_name}' "
              f"is now {reservation.status.value} at Table {reservation.table.table_id}.")


class SMSNotificationService(NotificationObserver):
    def on_reservation_updated(self, reservation: 'Reservation') -> None:
        print(f"📱 [SMS Alert] Dear {reservation.customer_name}, Table {reservation.table.table_id} "
              f"status: {reservation.status.value} for slot {reservation.slot}.")


# ==========================================
# 3. RESERVATION ENTITY & LOCK MANAGER
# ==========================================

class Reservation:
    def __init__(self, res_id: str, customer_name: str, party_size: int, table: Table, slot: TimeSlot):
        self.reservation_id: str = res_id
        self.customer_name: str = customer_name
        self.party_size: int = party_size
        self.table: Table = table
        self.slot: TimeSlot = slot
        self.status: ReservationStatus = ReservationStatus.PENDING_HOLD
        self.hold_expiry: float = 0.0


class RestaurantBranch:
    """Manages tables, time-slot bookings, and thread-safe lock management."""
    def __init__(self, branch_id: str, name: str, tables: List[Table], hold_timeout_sec: float = 2.0):
        self.branch_id: str = branch_id
        self.name: str = name
        self.tables: Dict[str, Table] = {t.table_id: t for t in tables}
        self.hold_timeout_sec: float = hold_timeout_sec

        # slot_key -> table_id -> Reservation
        self._table_reservations: Dict[str, Dict[str, Reservation]] = {}
        self._lock: threading.Lock = threading.Lock()

    def get_available_tables(self, slot: TimeSlot, party_size: int) -> List[Table]:
        with self._lock:
            now = time.time()
            slot_bookings = self._table_reservations.get(slot.slot_key, {})
            available: List[Table] = []

            for table in self.tables.values():
                if table.capacity < party_size:
                    continue  # Table too small

                if table.table_id in slot_bookings:
                    res = slot_bookings[table.table_id]
                    # Check if active or if pending hold expired
                    if res.status == ReservationStatus.CONFIRMED:
                        continue
                    if res.status == ReservationStatus.PENDING_HOLD and now <= res.hold_expiry:
                        continue

                available.append(table)
            return available

    def place_hold(self, res_id: str, customer_name: str, party_size: int, table: Table, slot: TimeSlot) -> Optional[Reservation]:
        with self._lock:
            now = time.time()
            slot_bookings = self._table_reservations.setdefault(slot.slot_key, {})

            if table.table_id in slot_bookings:
                existing = slot_bookings[table.table_id]
                if existing.status == ReservationStatus.CONFIRMED:
                    return None
                if existing.status == ReservationStatus.PENDING_HOLD and now <= existing.hold_expiry:
                    return None  # Busy under active hold

            # Create temporary hold
            res = Reservation(res_id, customer_name, party_size, table, slot)
            res.hold_expiry = now + self.hold_timeout_sec
            slot_bookings[table.table_id] = res
            return res

    def confirm_hold(self, res_id: str, table_id: str, slot: TimeSlot) -> bool:
        with self._lock:
            slot_bookings = self._table_reservations.get(slot.slot_key, {})
            res = slot_bookings.get(table_id)

            if not res or res.reservation_id != res_id:
                return False
            if res.status != ReservationStatus.PENDING_HOLD or time.time() > res.hold_expiry:
                return False  # Hold timed out or stolen

            res.status = ReservationStatus.CONFIRMED
            res.hold_expiry = 0.0
            return True

    def cancel_reservation(self, table_id: str, slot: TimeSlot) -> bool:
        with self._lock:
            slot_bookings = self._table_reservations.get(slot.slot_key, {})
            if table_id in slot_bookings:
                slot_bookings[table_id].status = ReservationStatus.CANCELLED
                del slot_bookings[table_id]
                return True
            return False


# ==========================================
# 4. TABLE ASSIGNMENT STRATEGY (Strategy Pattern)
# ==========================================

class TableAssignmentStrategy(ABC):
    @abstractmethod
    def assign_table(self, candidates: List[Table], party_size: int) -> Optional[Table]:
        pass


class BestFitCapacityStrategy(TableAssignmentStrategy):
    """
    Minimizes wasted capacity: Picks the smallest available table >= party_size.
    e.g., For party of 2, prefers 2-top over 4-top, and 4-top over 8-top.
    """
    def assign_table(self, candidates: List[Table], party_size: int) -> Optional[Table]:
        valid_tables = [t for t in candidates if t.capacity >= party_size]
        if not valid_tables:
            return None
        # Sort by lowest capacity first (Best fit)
        return min(valid_tables, key=lambda t: t.capacity)


# ==========================================
# 5. ORCHESTRATOR HUB (Facade)
# ==========================================

class RestaurantReservationService:
    """Facade exposing unified reservation API with notification dispatch."""
    def __init__(self, strategy: Optional[TableAssignmentStrategy] = None):
        self._branches: Dict[str, RestaurantBranch] = {}
        self._strategy: TableAssignmentStrategy = strategy or BestFitCapacityStrategy()
        self._observers: List[NotificationObserver] = [
            EmailNotificationService(),
            SMSNotificationService()
        ]

    def register_branch(self, branch: RestaurantBranch) -> None:
        self._branches[branch.branch_id] = branch

    def register_observer(self, observer: NotificationObserver) -> None:
        self._observers.append(observer)

    def _notify(self, res: Reservation) -> None:
        for obs in self._observers:
            obs.on_reservation_updated(res)

    def reserve_table(
        self,
        branch_id: str,
        res_id: str,
        customer_name: str,
        party_size: int,
        slot: TimeSlot
    ) -> Optional[Reservation]:
        branch = self._branches.get(branch_id)
        if not branch:
            print(f"❌ Branch [{branch_id}] not found.")
            return None

        # 1. Fetch free tables
        candidates = branch.get_available_tables(slot, party_size)
        best_table = self._strategy.assign_table(candidates, party_size)

        if not best_table:
            print(f"❌ No suitable table available for party of {party_size} during {slot}.")
            return None

        # 2. Place temporary lock/hold
        reservation = branch.place_hold(res_id, customer_name, party_size, best_table, slot)
        if not reservation:
            print(f"❌ Table acquisition conflict during locking.")
            return None

        # 3. Simulate payment/customer confirmation handshake
        if branch.confirm_hold(res_id, best_table.table_id, slot):
            self._notify(reservation)
            return reservation

        return None

    def cancel(self, branch_id: str, table_id: str, slot: TimeSlot) -> bool:
        branch = self._branches.get(branch_id)
        if branch and branch.cancel_reservation(table_id, slot):
            print(f"🔄 Reservation at Table {table_id} for {slot} successfully cancelled.")
            return True
        return False


# ==========================================
# 6. RUNTIME DEMONSTRATION & TEST CASES
# ==========================================

if __name__ == "__main__":
    # Setup Branch with 3 tables of different sizes
    tables = [
        Table("T1_2P", capacity=2, table_type=TableType.INDOOR),
        Table("T2_4P", capacity=4, table_type=TableType.BOOTH),
        Table("T3_8P", capacity=8, table_type=TableType.OUTDOOR),
    ]
    branch = RestaurantBranch("B1", "Bistro Downtown", tables, hold_timeout_sec=1.0)

    service = RestaurantReservationService()
    service.register_branch(branch)

    slot_dinner = TimeSlot("2026-09-01", start_hour=19, duration_hours=2)

    print("=================== TEST 1: BEST-FIT CAPACITY MATCHING ===================")
    # Party of 2 should get T1_2P (not the 4P or 8P table)
    res1 = service.reserve_table("B1", "R101", "Alice", party_size=2, slot=slot_dinner)
    assert res1 is not None
    assert res1.table.table_id == "T1_2P"
    print("✅ Alice matched to Best-Fit 2-Person table (T1_2P).")

    print("\n=================== TEST 2: NEXT BEST-FIT CAPACITY ===================")
    # Another party of 2 arrives. T1_2P is occupied -> System picks smallest available (T2_4P)
    res2 = service.reserve_table("B1", "R102", "Bob", party_size=2, slot=slot_dinner)
    assert res2 is not None
    assert res2.table.table_id == "T2_4P"
    print("✅ Bob matched to next available 4-Person table (T2_4P).")

    print("\n=================== TEST 3: CAPACITY OVERFLOW ===================")
    # Party of 10 requests table -> Max capacity is 8 -> Rejected
    res3 = service.reserve_table("B1", "R103", "Charlie", party_size=10, slot=slot_dinner)
    assert res3 is None
    print("✅ Charlie's party of 10 rejected gracefully (Exceeds max table capacity).")

    print("\n=================== TEST 4: CANCELLATION & RE-BOOKING ===================")
    # Cancel Alice's booking on T1_2P
    assert service.cancel("B1", "T1_2P", slot_dinner) is True

    # New party of 2 can now claim T1_2P
    res4 = service.reserve_table("B1", "R104", "Diana", party_size=2, slot=slot_dinner)
    assert res4 is not None
    assert res4.table.table_id == "T1_2P"
    print("✅ Diana re-booked newly freed T1_2P.")

    print("\n🎉 All restaurant reservation assertions passed successfully!")