FROM python:3.11-slim

# Metadata
LABEL maintainer="Stundenplan Team"
LABEL description="Backend für Stundenplan-Management System"
LABEL version="1.0.0"

# Arbeitsverzeichnis setzen
WORKDIR /app

# System Dependencies installieren
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python Dependencies installieren (Cache-optimiert)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Application Code kopieren
COPY . .

# Verzeichnisse erstellen
RUN mkdir -p uploads logs

# Environment Variables
ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Non-root User erstellen
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Health Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Port exposieren
EXPOSE 5000

# Start Command
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "run:app"]