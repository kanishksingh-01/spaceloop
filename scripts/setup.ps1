Write-Host "Setting up SpaceLoop environment..."
python -m pip install --upgrade pip
python -m pip install Flask Flask-SQLAlchemy requests groq google-genai
python scripts/seed_db.py
Write-Host "Setup complete! Run 'python app.py' to launch."
