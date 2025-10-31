FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Set PYTHONPATH so Python can find the src module
ENV PYTHONPATH=/app/src

# System deps for Playwright/Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
    libxrandr2 libasound2 libpango-1.0-0 libpangocairo-1.0-0 \
    libgbm1 libgtk-3-0 fonts-liberation libcurl4 ca-certificates \
    wget unzip && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m playwright install --with-deps chromium

COPY . .

# Default to production uvicorn command; Render will set $PORT
# Use shell form to allow environment variable expansion
# PYTHONPATH is set above so 'app' can be found directly
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}


