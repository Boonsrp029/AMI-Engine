# =====================================================================
# STAGE 1: Builder Stage
# =====================================================================
FROM python:3.12-slim AS builder

# Prevent Python from writing bytecode (.pyc) and force unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install essential C/C++ compilation tools required for building native wheel extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create isolated virtual environment for binary portability using Python 3.12
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy pinned requirements first to optimize Docker layer caching
COPY requirements.txt .

# Install and build dependency wheel packages
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt


# =====================================================================
# STAGE 2: Runtime Production Stage
# =====================================================================
FROM python:3.12-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install minimal runtime dependencies (including headless Java runtime for PySpark local execution)
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jre-headless \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-compiled virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create unprivileged user to enforce container security least-privilege principle
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser && \
    chown -R appuser:appgroup /app

# Copy application source code into runtime image
COPY --chown=appuser:appgroup . /app

# Switch context to non-root user
USER appuser

# Expose ports for agent API endpoints / MLflow UI
EXPOSE 5000 8000

# Default execution entrypoint
CMD ["python", "main.py"]