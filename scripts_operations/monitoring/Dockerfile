# Multi-stage Dockerfile for UCG Monitoring Dashboard
# This creates a production-ready container image

# Build stage
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VERSION
ARG VCS_REF

# Labels
LABEL maintainer="UCG DevOps Team"
LABEL org.label-schema.build-date=$BUILD_DATE
LABEL org.label-schema.name="UCG Monitoring Dashboard"
LABEL org.label-schema.description="Real-time monitoring dashboard for UCG DevOps system"
LABEL org.label-schema.version=$VERSION
LABEL org.label-schema.vcs-ref=$VCS_REF
LABEL org.label-schema.schema-version="1.0"

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Set work directory
WORKDIR /app

# Copy dependency files
COPY requirements.txt pyproject.toml ./
COPY uv.lock ./

# Install Python dependencies
RUN uv sync --frozen --no-dev

# Production stage
FROM python:3.11-slim as production

# Set build arguments
ARG BUILD_DATE
ARG VERSION
ARG VCS_REF

# Labels
LABEL maintainer="UCG DevOps Team"
LABEL org.label-schema.build-date=$BUILD_DATE
LABEL org.label-schema.name="UCG Monitoring Dashboard"
LABEL org.label-schema.description="Real-time monitoring dashboard for UCG DevOps system"
LABEL org.label-schema.version=$VERSION
LABEL org.label-schema.vcs-ref=$VCS_REF
LABEL org.label-schema.schema-version="1.0"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r ucg && useradd -r -g ucg -d /app -s /bin/bash ucg

# Set work directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --chown=ucg:ucg . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/backups \
    && chown -R ucg:ucg /app

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV UCG_ENVIRONMENT=production
ENV MONITOR_HOST=0.0.0.0
ENV MONITOR_PORT=8000
ENV MONITOR_LOG_LEVEL=INFO
ENV MONITOR_AUTO_BROWSER=false

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Expose port
EXPOSE 8000

# Switch to non-root user
USER ucg

# Default command
CMD ["uvicorn", "src.core.ai_activity_adapter.monitoring.web_app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]