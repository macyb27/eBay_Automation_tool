# 🚀 eBay Automation Tool - Blazing Fast Docker Image
# Multi-stage build für minimale Image-Größe und maximale Performance

FROM python:3.12-slim-bullseye as base

# 🔧 SYSTEM DEPENDENCIES
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    libwebp-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 🎯 WORKING DIRECTORY
WORKDIR /app

# ⚡ PYTHON OPTIMIZATIONS
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 📦 DEPENDENCY INSTALLATION (Layer Caching)
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# 🔥 DEVELOPMENT STAGE
FROM base as development
ENV ENVIRONMENT=development
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# 🚀 PRODUCTION STAGE  
FROM base as production

# 🏗️ BUILD OPTIMIZATIONS
ENV ENVIRONMENT=production

# 👤 NON-ROOT USER für Security
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN mkdir -p /app/uploads && chown -R appuser:appuser /app

# 📁 COPY APPLICATION CODE
COPY --chown=appuser:appuser . .

# 🔒 SWITCH TO NON-ROOT USER
USER appuser

# 🌐 EXPOSE PORT
EXPOSE 8000

# 🔥 PRODUCTION SERVER (Gunicorn mit Uvicorn Workers)
CMD ["gunicorn", "main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "60", \
     "--keep-alive", "30", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--preload"]

# 🩺 HEALTHCHECK
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1