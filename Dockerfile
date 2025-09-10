# Multi-stage build for optimized uv-based patent analysis deployment
FROM python:3.12-slim as builder

# Install system dependencies for building and patent analysis
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    # Additional dependencies for patent analysis
    pkg-config \
    libcairo2-dev \
    libgirepository1.0-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv with specific version for stability
COPY --from=ghcr.io/astral-sh/uv:0.4.18 /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files first for better Docker layer caching
COPY pyproject.toml ./
COPY uv.lock ./

# Set uv configuration for optimal performance
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_CACHE_DIR=/tmp/uv-cache

# Create virtual environment and install dependencies
# Use --no-dev for production, --dev for development
ARG INSTALL_DEV=false
RUN --mount=type=cache,target=/tmp/uv-cache \
    if [ "$INSTALL_DEV" = "true" ]; then \
        uv sync --frozen --no-install-project; \
    else \
        uv sync --frozen --no-dev --no-install-project; \
    fi

# Install the project itself
COPY src/ src/
COPY config/ config/
RUN --mount=type=cache,target=/tmp/uv-cache \
    uv sync --frozen --no-deps

# Production stage
FROM python:3.12-slim as production

# Install runtime system dependencies for patent analysis
RUN apt-get update && apt-get install -y \
    # For weasyprint PDF generation
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libfontconfig1 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    # For matplotlib and data visualization
    libfreetype6-dev \
    libpng16-16 \
    # For web crawling and HTTP requests
    ca-certificates \
    # For general operations and health checks
    curl \
    # For patent data processing
    libxml2 \
    libxslt1.1 \
    # Fonts for PDF generation
    fonts-dejavu-core \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install uv in production with same version as builder
COPY --from=ghcr.io/astral-sh/uv:0.4.18 /uv /bin/uv

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -m appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application code
COPY --chown=appuser:appuser src/ src/
COPY --chown=appuser:appuser config/ config/
COPY --chown=appuser:appuser templates/ templates/
COPY --chown=appuser:appuser pyproject.toml ./

# Create necessary directories for patent analysis and set permissions
RUN mkdir -p \
    logs \
    reports/patent \
    data/raw \
    data/processed \
    cache/patent \
    tmp/downloads \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set environment variables for patent analysis optimization
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV UV_SYSTEM_PYTHON=1
# Patent analysis specific environment variables
ENV PATENT_CACHE_DIR="/app/cache/patent"
ENV PATENT_REPORT_DIR="/app/reports/patent"
ENV PATENT_DATA_DIR="/app/data"
ENV MATPLOTLIB_CACHE_DIR="/app/tmp/matplotlib"
ENV MPLCONFIGDIR="/app/tmp/matplotlib"

# Health check with patent-specific endpoints
HEALTHCHECK --interval=30s --timeout=30s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health && \
        curl -f http://localhost:8000/api/v1/system/status || exit 1

# Expose port
EXPOSE 8000

# Use uv to run the application with production optimizations
CMD ["uv", "run", "--no-sync", "uvicorn", "src.multi_agent_service.main:app", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "1", "--loop", "uvloop", "--http", "httptools"]