from .base import DomainEvent

class EscrowHeldEvent(DomainEvent):
    def __init__(self, booking_id, amount):
        super().__init__()
        self.booking_id = booking_id
        self.amount = amount

class EscrowRefundedEvent(DomainEvent):
    def __init__(self, booking_id, renter_vpa, tx_hash):
        super().__init__()
        self.booking_id = booking_id
        self.renter_vpa = renter_vpa
        self.tx_hash = tx_hash
