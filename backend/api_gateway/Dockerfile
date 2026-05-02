FROM python:3.12-alpine

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --retries 10 --timeout 120 -r /app/requirements.txt

COPY . /app

EXPOSE 8080
ENV PORT=8080

# Honor PORT from Railway / Fly / Kubernetes; default 8080.
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
