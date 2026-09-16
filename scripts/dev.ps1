$env:FLASK_ENV="development"
$env:PORT="5001"
Write-Host "Starting SpaceLoop on http://127.0.0.1:5001..."
python app.py
