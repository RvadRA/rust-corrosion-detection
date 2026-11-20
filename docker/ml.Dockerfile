# syntax=docker/dockerfile:1
# ------------------------------------------------------------------------------
# Стейдж 1: сборка зависимостей
# ------------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY src/ml/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ------------------------------------------------------------------------------
# Стейдж 2: финальный runtime образ
# ------------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH"

# Копируем виртуальное окружение из builder
COPY --from=builder /opt/venv /opt/venv

# Создаем непривилегированного пользователя appuser
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -s /bin/bash -m appuser && \
    mkdir -p /app/data /models && \
    chown -R appuser:appuser /app /models

# Копируем исходный код ML
COPY --chown=appuser:appuser src/ml /app/src/ml

USER appuser

EXPOSE 8001

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; sys_exit = 0 if urllib.request.urlopen('http://localhost:8001/health').getcode() == 200 else 1; exit(sys_exit)"

CMD ["uvicorn", "src.ml.service:app", "--host", "0.0.0.0", "--port", "8001"]
