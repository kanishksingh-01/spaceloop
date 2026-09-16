# Database Index Strategy
- `users(email)`: Unique index.
- `spaces(room_qr_token)`: Unique index for sub-5ms door QR lookups.
- `spaces(category, city)`: Composite index for search filtering.
- `bookings(space_id, session_state)`: Composite index for active reservation tracking.
