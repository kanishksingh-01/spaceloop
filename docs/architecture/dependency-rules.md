# Dependency Rules
- `domain` layer has ZERO dependencies on frameworks or external libraries.
- `database` and `integrations` implement domain interfaces.
- `app/api` depends on modules and domain, not vice-versa.
