# Threat Model (STRIDE)
- Spoofing: Prevented via DigiLocker OTP tokenization & Discom CA validation.
- Tampering: Server-side financial recomputation prevents client price alteration.
- Repudiation: Immutable telemetry logs record GPS coordinates and QR token verification.
- Denial of Service: Sliding-window rate limiter restricts clients to 20 calls/min.
