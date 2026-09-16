from datetime import datetime

class DomainEvent:
    def __init__(self):
        self.occurred_on = datetime.utcnow()
