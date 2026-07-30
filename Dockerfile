# =============================================================================
# CreditGuard — Dockerfile
# Production-ready single-stage build for Streamlit deployment.
# =============================================================================

FROM python:3.11-slim

# Metadata
LABEL maintainer="CreditGuard Project"
LABEL description="CreditGuard Credit Risk Analytics Dashboard"
LABEL version="1.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true

# Create non-root user for security
RUN groupadd -r creditguard && useradd -r -g creditguard creditguard

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (layer cache optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app.py .
COPY dashboard/ ./dashboard/
COPY data/ ./data/
COPY models/ ./models/
COPY reports/ ./reports/
COPY .streamlit/ ./.streamlit/

# Create required runtime directories
RUN mkdir -p data/backups data/processed data/raw logs && \
    chown -R creditguard:creditguard /app

# Switch to non-root user
USER creditguard

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Start the application
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
