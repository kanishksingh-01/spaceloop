# Module Boundaries & Decoupling
1. Modules in `backend/modules/` own their domain logic and models.
2. Cross-module operations execute through domain events (`backend/domain/events/`) or explicit service contracts.
3. No direct inter-module cross-table writes.
