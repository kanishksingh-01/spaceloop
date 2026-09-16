# Entity Relationship Diagram (ERD)
```mermaid
erDiagram
    USER ||--o{ SPACE : owns
    USER ||--o{ BOOKING : rents
    SPACE ||--o{ BOOKING : hosts
    SPACE ||--o{ REVIEW : has
    SPACE ||--o{ SPACE_INQUIRY : receives
    BOOKING ||--o{ TELEMETRY_LOG : records
```
