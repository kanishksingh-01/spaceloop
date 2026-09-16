from .base import DomainEvent

class InspectionCompletedEvent(DomainEvent):
    def __init__(self, booking_id, score, appliances_off):
        super().__init__()
        self.booking_id = booking_id
        self.score = score
        self.appliances_off = appliances_off
