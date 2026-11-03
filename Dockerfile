FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
RUN useradd --create-home app && mkdir /data && chown app /data
USER app
WORKDIR /srv/backend
EXPOSE 8000
# --proxy-headers lets the app see the original scheme/IP from nginx.
# Only expose port 8000 to the nginx container (see deploy/docker-compose.yml), never publicly.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
