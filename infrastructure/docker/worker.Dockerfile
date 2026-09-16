FROM python:3.14-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir Flask Flask-SQLAlchemy requests
CMD ["python3", "-c", "import time; print('SpaceLoop Background Telemetry Worker Started'); time.sleep(86400)"]
