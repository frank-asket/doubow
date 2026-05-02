# API gateway image when the build context is the repository root (Railway, CI, etc.).
# For local builds from backend/api_gateway only, use backend/api_gateway/Dockerfile instead.
FROM python:3.12-alpine

WORKDIR /app

COPY backend/api_gateway/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --retries 10 --timeout 120 -r /app/requirements.txt

COPY backend/api_gateway /app

EXPOSE 8080
ENV PORT=8080

# Railway and other hosts inject PORT; default 8080 matches Fly.io template and local compose mapping.
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
