---
trigger: always_on
---

6. Keep Integrations Replaceable
Clean Service Interfaces
External services such as UPI, KYC, DigiLocker, and electricity/discom-related integrations should be accessed through clean service interfaces.
Mocks and Adapters
Use mocks or adapters where real credentials or APIs are unavailable.
No False Pretenses
Never pretend that a mock integration is a real external transaction or verification.
Rule ID: 6-keep-integrations-replaceable
Priority: High
Scope: External integrations, services