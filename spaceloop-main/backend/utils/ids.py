import secrets
def generate_id(prefix="SP"):
    return f"{prefix}-{secrets.token_hex(4).upper()}"
