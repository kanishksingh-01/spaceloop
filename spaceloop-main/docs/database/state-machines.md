# Booking Session State Machine
```mermaid
stateDiagram-v2
    [*] --> confirmed: Booking Created (₹100 Escrow Held)
    confirmed --> checked_in: QR Scanned + GPS Radar <50m
    checked_in --> checked_out: Exit Photo Diff + Appliances OFF
    checked_out --> completed: ₹100 UPI Refunded
```
