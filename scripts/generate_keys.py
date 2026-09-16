import secrets
import hashlib
print("Generated SECRET_KEY:", secrets.token_hex(32))
print("Generated DPDP_SALT:", secrets.token_hex(16))
