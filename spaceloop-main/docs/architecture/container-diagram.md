# Container Diagram (C4 Level 2)
```mermaid
graph TD
    Client[Web Browser / Mobile PWA] -->|HTTPS / WSS| NGINX[Nginx Reverse Proxy]
    NGINX -->|HTTP| FlaskApp[Flask Modular Monolith App]
    FlaskApp -->|ORM / SQL| SQLiteDB[(Relational DB: SQLite / PostgreSQL)]
    FlaskApp -->|Background Async Jobs| Worker[Background Worker]
    FlaskApp -->|Inference Fallback| AICluster[Dual AI: Groq / Gemini / Heuristics]
```
