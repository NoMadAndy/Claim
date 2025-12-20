FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY *.sql ./
COPY *.py ./
COPY CHANGELOG.md ./
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

# Create non-root user
RUN useradd -m -u 1000 claim && chown -R claim:claim /app
USER claim

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/health >/dev/null || exit 1

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
