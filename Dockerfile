FROM python:3.13-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements from pyproject.toml
COPY pyproject.toml README.md ./

# Install Python dependencies directly without installing the package
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        fastapi>=0.104.0 \
        uvicorn[standard]>=0.23.2 \
        sqlalchemy>=2.0.23 \
        alembic>=1.12.1 \
        pydantic>=2.4.2 \
        pydantic-settings>=2.0.3 \
        psycopg2-binary>=2.9.9 \
        python-multipart>=0.0.6 \
        boto3>=1.28.62 \
        python-jose[cryptography]>=3.3.0 \
        passlib[bcrypt]>=1.7.4 \
        httpx>=0.25.0 \
        email-validator>=2.0.0

# Production stage
FROM python:3.13-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -s /bin/bash appuser && \
    chown -R appuser:appuser /app

USER appuser

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
