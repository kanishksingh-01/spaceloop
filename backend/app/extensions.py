from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

login_manager = LoginManager()
login_manager.login_view = "auth_login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"

csrf = CSRFProtect()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per minute"],
    storage_uri="memory://",
)
