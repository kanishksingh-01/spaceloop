FROM python:3.11-slim

WORKDIR /workspace

# Install system utilities (curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application source is mounted or copied
COPY . .

ENV PYTHONPATH=/workspace

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
