FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY src/agent_backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source packages (agent_backend depends on data_layer + spirit_card)
COPY src/ src/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Run the application — use PYTHONPATH so relative imports resolve correctly
ENV PYTHONPATH=/app/src
CMD ["uvicorn", "agent_backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
