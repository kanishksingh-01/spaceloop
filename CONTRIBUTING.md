# Contributing to SpaceLoop

Thank you for contributing to SpaceLoop! We welcome contributions to our Zero-Hardware India Stack micro-leasing platform.

## Development Workflow
1. Fork and clone the repository.
2. Run setup: `bash scripts/setup.sh` or `make setup`.
3. Start the dev server: `bash scripts/dev.sh` or `make dev`.
4. Ensure all test suites pass before submitting PRs:
   ```bash
   make test
   ```

## Architectural Guidelines
- **Modularity**: Place domain-specific logic in `backend/modules/<domain>/`.
- **Security**: Never store raw Aadhaar numbers or biometrics. Always use `backend/utils/security.py` for tokenization and hashing.
- **Legal Safeguards**: All micro-leases must adhere strictly to Section 52 of the Indian Easements Act, 1882.
- **Testing**: Maintain 100% pass rates across unit, security, and functional test suites.
