FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Production: gunicorn with uvicorn workers.
# Workers default to (2 × CPU cores + 1); override with GUNICORN_WORKERS env var.
CMD ["sh", "-c", \
  "alembic upgrade head && \
   gunicorn app.main:app \
   --worker-class uvicorn.workers.UvicornWorker \
   --workers ${GUNICORN_WORKERS:-2} \
   --bind 0.0.0.0:8000 \
   --timeout 120 \
   --access-logfile -"]