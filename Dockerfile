FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home app \
    && mkdir -p /data \
    && chown -R app:app /data

COPY backend/ ./backend/

USER app
WORKDIR /srv/backend

EXPOSE 8000

# Forwarded headers are interpreted by SecurityMiddleware only when TRUST_PROXY=1.
# Do not enable Uvicorn's wildcard forwarded-IP trust.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
