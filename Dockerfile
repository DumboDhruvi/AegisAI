# ==============================================================================
# AegisAI API Backend Dockerfile
# Multi-stage production build for FastAPI Evaluation Platform
# ==============================================================================

# --- Stage 1: Build & Dependency Resolution ---
FROM python:3.10-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment for clean dependency isolation
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy pyproject.toml and install package dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir .

# --- Stage 2: Production Runtime ---
FROM python:3.10-slim AS runtime

# Install minimal runtime dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-privileged system user for container security
RUN groupadd -r aegis && useradd -r -g aegis -s /bin/false -d /app aegis

WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy application source code
COPY src/ /app/src/
COPY pyproject.toml /app/

# Set ownership to non-root user
RUN chown -R aegis:aegis /app

# Switch to non-root user
USER aegis

# Expose FastAPI port
EXPOSE 8000

# Health check probe against API health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start production ASGI server
CMD ["uvicorn", "aegis.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
