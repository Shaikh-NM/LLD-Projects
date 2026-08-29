from abc import ABC, abstractmethod
from enum import Enum
import random
from typing import List, Optional


# ==========================================
# 1. CARD & DECK MODELS
# ==========================================

class Suit(Enum):
    HEARTS = "Hearts"
    DIAMONDS = "Diamonds"
    CLUBS = "Clubs"
    SPADES = "Spades"


class Rank(Enum):
    TWO = (2, "2")
    THREE = (3, "3")
    FOUR = (4, "4")
    FIVE = (5, "5")
    SIX = (6, "6")
    SEVEN = (7, "7")
    EIGHT = (8, "8")
    NINE = (9, "9")
    TEN = (10, "10")
    JACK = (10, "J")
    QUEEN = (10, "Q")
    KING = (10, "K")
    ACE = (11, "A")

    def __init__(self, value: int, symbol: str):
        self.value = value
        self.symbol = symbol


class Card:
    """Represents a single immutable playing card."""
    def __init__(self, suit: Suit, rank: Rank):
        self.suit: Suit = suit
        self.rank: Rank = rank

    def __repr__(self) -> str:
        return f"{self.rank.symbol}{self.suit.value[0]}"


class Shoe:
    """Represents a shoe containing multiple shuffled decks of cards."""
    def __init__(self, num_decks: int = 4):
        self.num_decks: int = num_decks
        self._cards: List[Card] = []
        self._reset_and_shuffle()

    def _reset_and_shuffle(self) -> None:
        self._cards.clear()
        for _ in range(self.num_decks):
            for suit in Suit:
                for rank in Rank:
                    self._cards.append(Card(suit, rank))
        random.shuffle(self._cards)

    def draw_card(self) -> Card:
        # Reshuffle if shoe runs low (< 20% remaining)
        if len(self._cards) < (52 * self.num_decks * 0.2):
            self._reset_and_shuffle()
        return self._cards.pop()


# ==========================================
# 2. HAND & SCORING MECHANICS
# ==========================================

class HandStatus(Enum):
    ACTIVE = "ACTIVE"
    STAND = "STAND"
    BUSTED = "BUSTED"
    BLACKJACK = "BLACKJACK"


class Hand:
    """Manages cards, dynamic Ace adjustments, and scoring for a player/dealer."""
    def __init__(self, bet: float = 0.0):
        self.cards: List[Card] = []
        self.bet: float = bet
        self.status: HandStatus = HandStatus.ACTIVE

    def add_card(self, card: Card) -> None:
        self.cards.append(card)
        score = self.get_score()
        if score > 21:
            self.status = HandStatus.BUSTED
        elif score == 21 and len(self.cards) == 2:
            self.status = HandStatus.BLACKJACK

    def get_score(self) -> int:
        """Calculates optimal score treating Aces as 11 or 1 dynamically."""
        total = 0
        aces = 0

        for card in self.cards:
            total += card.rank.value
            if card.rank == Rank.ACE:
                aces += 1

        # Downgrade Ace from 11 to 1 if busting
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1

        return total

    @property
    def is_blackjack(self) -> bool:
        return len(self.cards) == 2 and self.get_score() == 21

    def __repr__(self) -> str:
        return f"{self.cards} (Score: {self.get_score()})"


# ==========================================
# 3. ACTORS (Player & Dealer)
# ==========================================

class Participant(ABC):
    def __init__(self, name: str):
        self.name: str = name
        self.hand: Hand = Hand()

    def reset_hand(self, bet: float = 0.0) -> None:
        self.hand = Hand(bet)


class Player(Participant):
    """A human or automated table player with bankroll."""
    def __init__(self, name: str, bankroll: float):
        super().__init__(name)
        self.bankroll: float = bankroll

    def place_bet(self, amount: float) -> bool:
        if amount <= 0 or amount > self.bankroll:
            return False
        self.bankroll -= amount
        self.reset_hand(bet=amount)
        return True

    def credit_winnings(self, amount: float) -> None:
        self.bankroll += amount


class Dealer(Participant):
    """Dealer entity following strict house rules (hits on < 17)."""
    def __init__(self):
        super().__init__("Dealer")

    def should_hit(self) -> bool:
        return self.hand.get_score() < 17


# ==========================================
# 4. GAME ORCHESTRATOR / TABLE
# ==========================================

class TableState(Enum):
    BETTING = "BETTING"
    DEALING = "DEALING"
    PLAYER_TURNS = "PLAYER_TURNS"
    DEALER_TURN = "DEALER_TURN"
    SETTLEMENT = "SETTLEMENT"


class BlackjackTable:
    """Orchestrates rounds, turns, bets, and payout settlements."""
    def __init__(self, num_decks: int = 4):
        self.shoe: Shoe = Shoe(num_decks)
        self.dealer: Dealer = Dealer()
        self.players: List[Player] = []
        self.state: TableState = TableState.BETTING

    def add_player(self, player: Player) -> None:
        self.players.append(player)

    def initial_deal(self) -> None:
        """Deals 2 cards to each player and 2 to dealer (1 face down)."""
        print("\n🃏 --- Dealing Initial Cards ---")
        for _ in range(2):
            for p in self.players:
                p.hand.add_card(self.shoe.draw_card())
            self.dealer.hand.add_card(self.shoe.draw_card())

        for p in self.players:
            print(f"👤 {p.name}: {p.hand}")
        print(f"🎩 Dealer shows: [{self.dealer.hand.cards[0]}, ??]")

    def player_hit(self, player: Player) -> Card:
        card = self.shoe.draw_card()
        player.hand.add_card(card)
        return card

    def player_stand(self, player: Player) -> None:
        if player.hand.status == HandStatus.ACTIVE:
            player.hand.status = HandStatus.STAND

    def execute_dealer_turn(self) -> None:
        print(f"\n🎩 Dealer reveals hole card: {self.dealer.hand}")
        while self.dealer.should_hit():
            card = self.shoe.draw_card()
            self.dealer.hand.add_card(card)
            print(f"🎩 Dealer hits: draws {card} -> {self.dealer.hand}")

        if self.dealer.hand.status == HandStatus.BUSTED:
            print("💥 Dealer BUSTED!")
        else:
            print(f"🎩 Dealer STANDS with score: {self.dealer.hand.get_score()}")

    def settle_bets(self) -> None:
        print("\n💰 --- Settling Bets ---")
        dealer_score = self.dealer.hand.get_score()
        dealer_busted = self.dealer.hand.status == HandStatus.BUSTED
        dealer_bj = self.dealer.hand.is_blackjack

        for p in self.players:
            bet = p.hand.bet
            player_score = p.hand.get_score()

            # Case 1: Player Busted -> Loses Bet
            if p.hand.status == HandStatus.BUSTED:
                print(f"❌ {p.name} Busted (Score: {player_score}). Loses ${bet:.2f}.")

            # Case 2: Player has Natural Blackjack
            elif p.hand.is_blackjack:
                if dealer_bj:
                    p.credit_winnings(bet)  # Push
                    print(f"🤝 {p.name} Push with Dealer Blackjack. Bet ${bet:.2f} returned.")
                else:
                    payout = bet + (bet * 1.5)  # 3:2 payout
                    p.credit_winnings(payout)
                    print(f"🌟 {p.name} WON with BLACKJACK! Payout: ${payout:.2f} (Profit: ${bet*1.5:.2f}).")

            # Case 3: Dealer Busted -> Player Wins
            elif dealer_busted:
                p.credit_winnings(bet * 2)
                print(f"🏆 {p.name} WON! Dealer busted. Payout: ${bet * 2:.2f}.")

            # Case 4: Standard Score Comparison
            elif player_score > dealer_score:
                p.credit_winnings(bet * 2)
                print(f"🏆 {p.name} WON ({player_score} vs {dealer_score})! Payout: ${bet * 2:.2f}.")
            elif player_score == dealer_score:
                p.credit_winnings(bet)  # Push
                print(f"🤝 {p.name} PUSH ({player_score} vs {dealer_score}). Bet ${bet:.2f} returned.")
            else:
                print(f"❌ {p.name} LOST ({player_score} vs {dealer_score}). Loses ${bet:.2f}.")


# ==========================================
# 5. RUNTIME GAMEPLAY DEMONSTRATION
# ==========================================

if __name__ == "__main__":
    # 1. Setup Table & Players
    table = BlackjackTable(num_decks=6)
    alice = Player("Alice", bankroll=500.0)
    bob = Player("Bob", bankroll=300.0)

    table.add_player(alice)
    table.add_player(bob)

    # 2. Place Bets
    alice.place_bet(50.0)
    bob.place_bet(25.0)

    # 3. Deal Initial Cards
    table.initial_deal()

    # 4. Player Turns
    print("\n--- Players' Action Phase ---")
    # Alice plays (e.g. Hits if score < 16)
    while alice.hand.get_score() < 16 and alice.hand.status == HandStatus.ACTIVE:
        card = table.player_hit(alice)
        print(f"👤 Alice hits: drew {card} -> {alice.hand}")
    table.player_stand(alice)

    # Bob stands
    table.player_stand(bob)
    print(f"👤 Bob stands with {bob.hand}")

    # 5. Dealer Turn
    table.execute_dealer_turn()

    # 6. Settle Round
    table.settle_bets()

    print(f"\n📊 Final Bankrolls: Alice: ${alice.bankroll:.2f} | Bob: ${bob.bankroll:.2f}")