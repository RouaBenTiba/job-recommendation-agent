FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-fra \
    && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home appuser \
    && mkdir -p /app/storage \
    && chown -R appuser:appuser /app/storage
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
