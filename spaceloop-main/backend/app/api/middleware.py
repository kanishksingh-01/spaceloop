import time
from flask import request
from security import ai_rate_limiter

def rate_limit_middleware():
    ip = request.remote_addr or '127.0.0.1'
    return ai_rate_limiter.is_allowed(ip)
