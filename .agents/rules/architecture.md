# Architecture Rules
- Pattern: Modular Monolith with Domain-Driven Design (DDD).
- Boundaries: Modules in `backend/modules/` communicate via well-defined service interfaces or domain events.
- Zero-Hardware Access: Physical access relies entirely on software layers (GPS radar <50m, QR passes, dynamic PINs).
- Unidirectional Dependency: Domain -> Database/Modules -> API Layer.
