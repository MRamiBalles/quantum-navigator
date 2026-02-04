# ============================================================================
# Q-Orchestrator Backend - Production Docker Image
# ============================================================================
# Multi-stage build for optimal image size and security
# Based on Python 3.11 with quantum computing dependencies
# ============================================================================

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim as runtime

LABEL maintainer="Q-Orchestrator Team <quantum@q-orchestrator.dev>"
LABEL version="5.1"
LABEL description="Quantum Navigator Backend API - Industrial Grade Middleware"

# Create non-root user for security
RUN groupadd -r quantum && useradd -r -g quantum quantum

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=quantum:quantum . .

# Remove test files from production image
RUN rm -rf tests/ benchmarks/*.csv benchmarks/*.json 2>/dev/null || true

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    ENV=production \
    PORT=8000

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# Switch to non-root user
USER quantum

# Run with uvicorn
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
