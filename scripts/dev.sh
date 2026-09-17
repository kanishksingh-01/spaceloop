#!/usr/bin/env bash
export FLASK_ENV=development
export PORT=5001
echo "Starting SpaceLoop development server on http://127.0.0.1:5001..."
python3 app.py
