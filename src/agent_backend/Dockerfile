# Agent Backend 容器镜像
#
# 构建上下文必须是仓库根目录：
#   docker build -f src/agent_backend/Dockerfile -t roco-agent-backend .
# 对应 docker-compose.yml 的 `context: .` 配置。
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY src/agent_backend/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code (保留 src 包结构以支持 `agent_backend.main` 导入)
COPY src/agent_backend /app/src/agent_backend
COPY src/data_layer    /app/src/data_layer
COPY src/spirit_card   /app/src/spirit_card
COPY src/__init__.py   /app/src/__init__.py

ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Run the application
#   agent_backend.main:app 需要 PYTHONPATH=/app/src 以正确解析相对导入。
CMD ["uvicorn", "agent_backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
