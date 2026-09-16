from .base import DomainEvent

class StudentVerifiedEvent(DomainEvent):
    def __init__(self, user_id, masked_aadhaar, college_email):
        super().__init__()
        self.user_id = user_id
        self.masked_aadhaar = masked_aadhaar
        self.college_email = college_email
