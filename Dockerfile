FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5080 \
    FLASK_ENV=production

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Ensure instance and uploads directories exist with proper permissions
RUN mkdir -p instance uploads && chmod -R 755 instance uploads

EXPOSE 5080

CMD ["gunicorn", "wsgi:app", "--workers", "4", "--threads", "2", "--bind", "0.0.0.0:5080"]
