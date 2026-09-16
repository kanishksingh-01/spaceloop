from .base import DomainEvent

class BookingCreatedEvent(DomainEvent):
    def __init__(self, booking_id, space_id, renter_id, hours, total_price):
        super().__init__()
        self.booking_id = booking_id
        self.space_id = space_id
        self.renter_id = renter_id
        self.hours = hours
        self.total_price = total_price
