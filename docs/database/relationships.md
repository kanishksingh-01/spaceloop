# Model Relationships & Cascades
- `User.owned_spaces`: 1-to-many, cascade all, delete-orphan.
- `Space.bookings`: 1-to-many, cascade all, delete-orphan.
- `Booking.telemetry_logs`: 1-to-many, cascade all, delete-orphan.
