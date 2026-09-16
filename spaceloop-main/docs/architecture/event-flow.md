# Event Flow Architecture
- `BookingCreatedEvent` -> Notifies host, reserves calendar block.
- `CheckinSuccessEvent` -> Activates live In-Room HUD session console.
- `CheckoutCompletedEvent` -> Triggers CV diff task and OTI score recalculation.
- `EscrowRefundedEvent` -> Dispatches instant UPI release to student VPA.
