# syntax=docker/dockerfile:1

# =============================================================================
# Nebu Agent - Multi-stage Dockerfile optimizado
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Instala dependencias y compila
# -----------------------------------------------------------------------------
ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim AS builder

# Variables de entorno para optimización
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias de compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copiar archivos de dependencias
COPY pyproject.toml requirements.lock ./

# Instalar dependencias pinned desde lock file
RUN pip install --target=/build/deps -r requirements.lock

# -----------------------------------------------------------------------------
# Stage 2: Runtime - Imagen final mínima
# -----------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS runtime

# Labels OCI estándar
LABEL org.opencontainers.image.title="Nebu Agent" \
      org.opencontainers.image.description="LiveKit Voice Agent - Nebu" \
      org.opencontainers.image.version="2.0.0" \
      org.opencontainers.image.vendor="Flow Telligence" \
      org.opencontainers.image.source="https://github.com/flow-telligence/nebu-agent"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:/app/deps \
    PATH="/app/deps/bin:$PATH" \
    HF_HOME=/app/.cache/huggingface

# Crear usuario no privilegiado
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/app" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    appuser

WORKDIR /app

# Copiar dependencias del builder
COPY --from=builder /build/deps /app/deps

# Copiar código fuente
COPY src/ ./src/

# Download turn detector model files from HuggingFace
RUN OPENAI_API_KEY=dummy \
    ELEVENLABS_API_KEY=dummy \
    LIVEKIT_URL=ws://dummy \
    LIVEKIT_API_KEY=dummy \
    LIVEKIT_API_SECRET=dummy \
    python src/agent.py download-files

# Cambiar ownership
RUN chown -R appuser:appuser /app

# Cambiar a usuario no privilegiado
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5)" || exit 1

# Exponer puerto del health server de LiveKit y API REST
EXPOSE 8081 8000

# Comando por defecto
CMD ["python", "src/agent.py", "start"]
