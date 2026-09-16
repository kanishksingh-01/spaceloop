FROM python:3.14-slim AS base
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY . /app
RUN pip install --no-cache-dir Flask Flask-SQLAlchemy requests groq google-genai
EXPOSE 5001
CMD ["python3", "app.py"]
