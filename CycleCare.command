#!/bin/bash
# ==========================================================
# Cycle Care & Partner Connect - Desktop App Launcher (macOS)
# Double-click this file to launch the local application!
# ==========================================================

cd "$(dirname "$0")"

echo "🌸 Starting Cycle Care & Partner Connect..."

# Find Python in .venv or system
if [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "❌ Error: Python 3 not found. Please install Python 3 or set up .venv."
    read -p "Press Enter to exit..."
    exit 1
fi

PORT=5001
export PORT

# Check if port 5001 is already active
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "⚡ Cycle Care is already running on port $PORT!"
else
    echo "🚀 Booting backend server on port $PORT..."
    $PYTHON_CMD app.py &
    SERVER_PID=$!
    sleep 1.5
fi

echo "✨ Opening Cycle Care in your browser..."
open "http://localhost:$PORT"

echo ""
echo "=========================================================="
echo "Cycle Care is live at: http://localhost:$PORT"
echo "To install as a native Desktop App:"
echo "1. In Google Chrome or Microsoft Edge, look at the right"
echo "   side of your address bar and click the 'Install' icon ⊕"
echo "2. Or open Safari > File > 'Add to Dock' (macOS Sonoma+)"
echo "=========================================================="
echo ""
echo "Keep this window open while using the app. Press Ctrl+C to stop."

# Wait for process if started
if [ -n "$SERVER_PID" ]; then
    wait $SERVER_PID
fi
