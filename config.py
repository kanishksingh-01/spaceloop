import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Fill this in when you add LLM-based mood detection / symptom notes.
    # e.g. GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
