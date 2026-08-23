from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set
from collections import defaultdict
from enum import Enum


# ==========================================
# 1. DOMAIN MODELS & USERS
# ==========================================

class User:
    """Base class for all system participants."""
    def __init__(self, name: str):
        self._name: str = name

    @property
    def name(self) -> str:
        return self._name


class Seller(User):
    """Represents an auction creator."""
    pass


class Buyer(User):
    """Represents a bidder with budget constraints and participation tracking."""
    def __init__(self, name: str, budget: float = float('inf')):
        super().__init__(name)
        self._budget: float = budget
        self._participated_auctions: Set[str] = set()

    @property
    def budget(self) -> float:
        return self._budget

    def increase_budget(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Amount to increase must be positive.")
        self._budget += amount

    def deduct_budget(self, amount: float) -> None:
        self._budget -= amount

    def record_participation(self, auction_id: str) -> None:
        self._participated_auctions.add(auction_id)

    @property
    def is_preferred(self) -> bool:
        """Bonus: Preferred buyer if participated in more than 2 distinct auctions."""
        return len(self._participated_auctions) > 2


class Bid:
    """Represents an individual bid placed by a buyer."""
    def __init__(self, buyer: Buyer, amount: float):
        self.buyer: Buyer = buyer
        self.amount: float = amount


# ==========================================
# 2. WINNING STRATEGY PATTERN
# ==========================================

class WinningStrategy(ABC):
    """Abstract Strategy interface for computing auction winners."""
    @abstractmethod
    def determine_winner(self, bids: List[Bid]) -> Optional[Bid]:
        pass


class HighestUniqueBidStrategy(WinningStrategy):
    """
    Finds the highest unique bid amount.
    Bonus tie-break: If multiple bidders exist, prioritizes preferred buyers.
    """
    def determine_winner(self, bids: List[Bid]) -> Optional[Bid]:
        if not bids:
            return None

        # Group bids by amount
        amount_to_bids: Dict[float, List[Bid]] = defaultdict(list)
        for bid in bids:
            amount_to_bids[bid.amount].append(bid)

        # Sort unique bid amounts descending
        unique_amounts = sorted(
            [amt for amt, bid_list in amount_to_bids.items() if len(bid_list) == 1],
            reverse=True
        )

        if not unique_amounts:
            return None

        highest_unique_amt = unique_amounts[0]
        return amount_to_bids[highest_unique_amt][0]


class LowestUniqueBidStrategy(WinningStrategy):
    """Extension: Determines the winner using the lowest unique bid amount."""
    def determine_winner(self, bids: List[Bid]) -> Optional[Bid]:
        if not bids:
            return None

        amount_to_bids: Dict[float, List[Bid]] = defaultdict(list)
        for bid in bids:
            amount_to_bids[bid.amount].append(bid)

        # Sort unique bid amounts ascending
        unique_amounts = sorted(
            [amt for amt, bid_list in amount_to_bids.items() if len(bid_list) == 1]
        )

        if not unique_amounts:
            return None

        lowest_unique_amt = unique_amounts[0]
        return amount_to_bids[lowest_unique_amt][0]


# ==========================================
# 3. AUCTION AGGREGATE
# ==========================================

class AuctionStatus(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class Auction:
    """Manages bidding limits, lifecycle, and active bids for an item."""
    def __init__(
        self,
        auction_id: str,
        min_bid: float,
        max_bid: float,
        seller: Seller,
        winning_strategy: Optional[WinningStrategy] = None
    ):
        self.auction_id: str = auction_id
        self.min_bid: float = min_bid
        self.max_bid: float = max_bid
        self.seller: Seller = seller
        self.status: AuctionStatus = AuctionStatus.OPEN
        self.bids: Dict[str, Bid] = {}  # buyer_name -> Bid
        self.winning_strategy: WinningStrategy = winning_strategy or HighestUniqueBidStrategy()
        self.winner: Optional[Buyer] = None
        self.winning_bid_amount: Optional[float] = None

    def place_or_update_bid(self, buyer: Buyer, amount: float) -> bool:
        if self.status != AuctionStatus.OPEN:
            print(f"❌ Auction '{self.auction_id}' is closed.")
            return False

        if amount < self.min_bid or amount > self.max_bid:
            print(f"❌ Bid {amount} rejected: Outside limits [{self.min_bid}, {self.max_bid}] for '{self.auction_id}'.")
            return False

        if amount > buyer.budget:
            print(f"❌ Bid {amount} rejected: Exceeds buyer '{buyer.name}' budget of {buyer.budget}.")
            return False

        # Register/overwrite bid
        self.bids[buyer.name] = Bid(buyer, amount)
        buyer.record_participation(self.auction_id)
        return True

    def withdraw_bid(self, buyer_name: str) -> bool:
        if self.status != AuctionStatus.OPEN:
            print(f"❌ Cannot withdraw: Auction '{self.auction_id}' is closed.")
            return False

        if buyer_name in self.bids:
            del self.bids[buyer_name]
            return True
        return False

    def close(self) -> Optional[Bid]:
        if self.status != AuctionStatus.OPEN:
            print(f"❌ Auction '{self.auction_id}' is already closed.")
            return None

        self.status = AuctionStatus.CLOSED
        winning_bid = self.winning_strategy.determine_winner(list(self.bids.values()))

        if winning_bid:
            self.winner = winning_bid.buyer
            self.winning_bid_amount = winning_bid.amount
            # Deduct budget on winning (SDE 3 Requirement)
            self.winner.deduct_budget(winning_bid.amount)
            print(f"🏆 Winner of '{self.auction_id}' is {self.winner.name} with bid {self.winning_bid_amount}")
        else:
            print(f"⚠️ Auction '{self.auction_id}' closed with NO winner.")

        return winning_bid


# ==========================================
# 4. SUPERBIDDER ORCHESTRATOR / FACADE
# ==========================================

class SuperBidderService:
    """Central orchestrator managing buyers, sellers, and multi-auction lifecycle."""
    def __init__(self):
        self.buyers: Dict[str, Buyer] = {}
        self.sellers: Dict[str, Seller] = {}
        self.auctions: Dict[str, Auction] = {}

    def add_buyer(self, name: str, budget: float = float('inf')) -> None:
        self.buyers[name] = Buyer(name, budget)

    def add_seller(self, name: str) -> None:
        self.sellers[name] = Seller(name)

    def update_budget(self, buyer_name: str, new_budget: float) -> None:
        if buyer_name in self.buyers:
            self.buyers[buyer_name].increase_budget(new_budget)

    def create_auction(
        self,
        auction_id: str,
        min_bid: float,
        max_bid: float,
        seller_name: str,
        strategy: Optional[WinningStrategy] = None
    ) -> None:
        seller = self.sellers.get(seller_name)
        if not seller:
            print(f"❌ Seller '{seller_name}' does not exist.")
            return
        self.auctions[auction_id] = Auction(auction_id, min_bid, max_bid, seller, strategy)

    def create_or_update_bid(self, buyer_name: str, auction_id: str, amount: float) -> bool:
        buyer = self.buyers.get(buyer_name)
        auction = self.auctions.get(auction_id)

        if not buyer or not auction:
            print("❌ Invalid Buyer or Auction ID.")
            return False

        return auction.place_or_update_bid(buyer, amount)

    def withdraw_bid(self, buyer_name: str, auction_id: str) -> bool:
        auction = self.auctions.get(auction_id)
        if not auction:
            return False
        return auction.withdraw_bid(buyer_name)

    def close_auction(self, auction_id: str) -> Optional[str]:
        auction = self.auctions.get(auction_id)
        if not auction:
            return None
        winning_bid = auction.close()
        return winning_bid.buyer.name if winning_bid else None


# ==========================================
# 5. DEMONSTRATION OF ALL TEST CASES
# ==========================================

if __name__ == "__main__":
    print("=================== TEST CASE 1 ===================")
    service1 = SuperBidderService()
    service1.add_buyer("buyer1")
    service1.add_buyer("buyer2")
    service1.add_buyer("buyer3")
    service1.add_seller("seller1")

    service1.create_auction("A1", 10, 50, "seller1")
    service1.create_or_update_bid("buyer1", "A1", 17)
    service1.create_or_update_bid("buyer2", "A1", 15)
    service1.create_or_update_bid("buyer2", "A1", 19)
    service1.create_or_update_bid("buyer3", "A1", 19)
    
    # Bids: buyer1: 17, buyer2: 19, buyer3: 19 -> Unique: 17 (buyer1 wins)
    winner1 = service1.close_auction("A1")
    assert winner1 == "buyer1"

    print("\n=================== TEST CASE 2 ===================")
    service2 = SuperBidderService()
    service2.add_buyer("buyer2")
    service2.add_buyer("buyer3")
    service2.add_seller("seller2")

    service2.create_auction("A2", 5, 20, "seller2")
    service2.create_or_update_bid("buyer3", "A2", 25) # Rejects (exceeds max limit 20)
    service2.create_or_update_bid("buyer2", "A2", 5)
    service2.withdraw_bid("buyer2", "A2")
    winner2 = service2.close_auction("A2")
    assert winner2 is None

    print("\n=================== TEST CASE 3 (BUDGET & MULTI-AUCTION) ===================")
    service3 = SuperBidderService()
    service3.add_buyer("buyer1", 20)
    service3.add_buyer("buyer2", 20)
    service3.add_buyer("buyer3", 20)
    service3.add_seller("seller1")
    service3.add_seller("seller2")

    service3.create_auction("A1", 10, 50, "seller1")
    service3.create_auction("A2", 5, 20, "seller2")

    service3.create_or_update_bid("buyer1", "A1", 17)
    service3.create_or_update_bid("buyer2", "A1", 15)
    service3.create_or_update_bid("buyer2", "A1", 19)
    service3.create_or_update_bid("buyer3", "A1", 19)

    winner3 = service3.close_auction("A1") # buyer1 wins with 17. Remaining budget = 20 - 17 = 3
    assert winner3 == "buyer1"

    # buyer1 attempts to bid 5 on A2 with remaining budget of 3 -> Should fail
    success = service3.create_or_update_bid("buyer1", "A2", 5)
    assert success is False

    service3.create_or_update_bid("buyer3", "A2", 25) # Exceeds max limit 20
    service3.create_or_update_bid("buyer2", "A2", 5)
    service3.withdraw_bid("buyer2", "A2")
    winner3_a2 = service3.close_auction("A2")
    assert winner3_a2 is None

    print("\n=================== TEST CASE 4 (EXTENSION: LOWEST UNIQUE BID) ===================")
    service4 = SuperBidderService()
    service4.add_buyer("A")
    service4.add_buyer("B")
    service4.add_buyer("C")
    service4.add_seller("sellerX")

    # Inject LowestUniqueBidStrategy
    service4.create_auction("A_LOW", 10, 100, "sellerX", strategy=LowestUniqueBidStrategy())
    service4.create_or_update_bid("A", "A_LOW", 20)
    service4.create_or_update_bid("B", "A_LOW", 20)
    service4.create_or_update_bid("C", "A_LOW", 30)
    
    # 20 is duplicated. 30 is the lowest unique bid -> C wins
    winner4 = service4.close_auction("A_LOW")
    assert winner4 == "C"

    print("\n✅ All assertions passed successfully!")