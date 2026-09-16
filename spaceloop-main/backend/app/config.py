import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'spaceloop_super_secret_hack2ignite_2026_key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///spaceloop.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PORT = int(os.environ.get('PORT', 5001))
