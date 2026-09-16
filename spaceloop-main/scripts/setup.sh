#!/usr/bin/env bash
set -e
echo "Setting up SpaceLoop environment..."
python3 -m pip install --upgrade pip
python3 -m pip install Flask Flask-SQLAlchemy requests groq google-genai
python3 scripts/seed_db.py
echo "Setup complete! Run 'python3 app.py' to launch SpaceLoop."
