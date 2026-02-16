# ---- Stage 1: Builder (install deps only) ----
FROM python:3.12-slim AS builder

WORKDIR /build

COPY pyproject.toml .
COPY localnotion/ localnotion/

# Install the package (to resolve all dependencies)
RUN pip install --no-cache-dir .

# ---- Stage 2: Runtime ----
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Copy application source (including static frontend build)
COPY localnotion/ /app/localnotion/

# Use PYTHONPATH so localnotion package resolves from /app/ (includes static files)
ENV PYTHONPATH=/app

# Install the CLI entry point only
COPY --from=builder /usr/local/bin/localnotion /usr/local/bin/localnotion

EXPOSE 8000

ENV LN_LOG_LEVEL=INFO
ENV LN_DATA_DIR=/data

VOLUME ["/data"]

# Run uvicorn directly (bypasses CLI entry point import path issues)
CMD ["python", "-m", "uvicorn", "localnotion.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
