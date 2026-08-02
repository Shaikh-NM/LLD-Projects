from abc import ABC, abstractmethod
from typing import Optional

class PaymentStrategy(ABC):
    @abstractmethod
    def process_payment(self, amount: float) -> bool:
        pass
    
class CardPaymentStrategy(PaymentStrategy):
    def __init__(self, card_number: str, cvv: str, expiry: str):
        self._card_number: str = card_number
        self._cvv: str = cvv
        self._expiry: str = expiry

    def process_payment(self, amount: float) -> bool:
        masked_card = f"XXXX-XXXX-XXXX-{self._card_number[-4:]}"
        print(f"💳 Routing ${amount:.2f} via Card Processor [Card: {masked_card}]...")
        print("   -> Tokenizing metadata credentials... Checking fraud limits...")
        print("   -> Transaction Approved!")
        return True
    
class UPIPaymentStrategy(PaymentStrategy):
    def __init__(self, upi_id: str):
        self._upi_id: str = upi_id

    def process_payment(self, amount):
        print(f"📱 Requesting ${amount:.2f} via UPI Gateway [VPA: {self._upi_id}]...")
        print(f"   -> Pushing collection notification alert request token down to user phone...")
        print("   -> Mobile MPIN verification successful! Transaction Approved!")
        return True
    
class WalletPaymentStrategy(PaymentStrategy):
    def __init__(self, wallet_id: str, secret_token: str):
        self._wallet_id: str = wallet_id
        self._secret_token: str = secret_token

    def process_payment(self, amount):
        print(f"👛 Deducting ${amount:.2f} directly from Digital Wallet Account [ID: {self._wallet_id}]...")
        print("   -> Verifying oauth bearer handshake tokens... Confirming balance headroom...")
        print("   -> Balance deducted! Transaction Approved!")
        return True
    
class CheckoutProcessor:
    def __init__(self):
        self._payment_strategy: Optional[PaymentStrategy] = None

    def set_payment_strategy(self, strategy: PaymentStrategy) -> None:
        self._payment_strategy = strategy
        print(f"⚙️ Runtime Setup: Strategy swapped to {strategy.__class__.__name__}.")
    
    def complete_checkout(self, order_total: float) -> bool:
        if not self._payment_strategy:
            raise ValueError("Checkout Denied: No active payment strategy has been selected.")
        
        print(f"\n🛒 Initiating checkout processing workflows for Order Total: ${order_total:.2f}")

        is_success = self._payment_strategy.process_payment(order_total)
        if is_success:
            print("📦 Order Fulfillment Triggered: Generating tracking invoices and printing labels!")
            return True
        else:
            print("❌ Order Fulfillment Halted: Transaction was rejected by payment provider.")
            return False
        
if __name__ == "__main__":
    checkout_engine = CheckoutProcessor()

    print("--- Scenario A: User chooses Card Checkout at payment screen ---")
    VISA_CARD = CardPaymentStrategy(card_number="1234567890123456", cvv="999", expiry="12/30")

    checkout_engine.set_payment_strategy(VISA_CARD)
    checkout_engine.complete_checkout(order_total=194.50)

    print("\n--- Scenario B: User switches payment type to a quick UPI scan ---")
    GOOGLE_PAY_UPI = UPIPaymentStrategy()
    
    checkout_engine.set_payment_strategy(upi_id="john.doe@bank")
    checkout_engine.complete_checkout(order_total=149.50)

    print("\n--- Scenario C: User uses pre-funded Wallet option ---")
    APPLE_WALLET = WalletPaymentStrategy(wallet_id="WLT-5512", secret_token="TOKEN_SEC_99")

    checkout_engine.set_payment_strategy(APPLE_WALLET)
    checkout_engine.complete_checkout(order_total=95.67)

    