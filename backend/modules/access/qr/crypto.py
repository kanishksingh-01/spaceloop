import hashlib
def sign_room_token(token, secret):
    return hashlib.sha256(f'{token}:{secret}'.encode()).hexdigest()
